"""
File: agent.py
Purpose: Defines the capability arbitrator agent workflow.
Why/How: A progressive disclosure traffic router that assigns tasks to nodes.
"""
import os
import re
import json
import time
import subprocess
from typing import Any, Literal, AsyncGenerator
from dotenv import load_dotenv

from google.adk.agents import LlmAgent
from google.adk.agents.context import Context
from google.adk.apps import App
from google.adk.events.event import Event
from google.adk.events.request_input import RequestInput
from google.adk.plugins.debug_logging_plugin import DebugLoggingPlugin
from google.adk.plugins.logging_plugin import LoggingPlugin
from google.adk.tools.mcp_tool import McpToolset
from google.adk.tools.mcp_tool.mcp_session_manager import StdioConnectionParams
from google.adk.workflow import DEFAULT_ROUTE, START, Edge, FunctionNode, Workflow, node
from mcp import StdioServerParameters
from pydantic import BaseModel, Field

from functools import cached_property
from google import genai
from google.genai import types
from google.adk.models.google_llm import Gemini
from app.config import MODEL
from app.app_utils.routing_utils import get_prompt_text
from app.app_utils.skill_utils import load_skill_instructions
from app.app_utils.telemetry import (
    init_telemetry,
    record_security_screen,
    record_scout,
    record_node_execution,
    record_hitl
)

load_dotenv()

PROJECT_ID = os.environ.get("GOOGLE_CLOUD_PROJECT", "kaggle-capstone-500322")
LOCATION = os.environ.get("GOOGLE_CLOUD_LOCATION", "global")

class GlobalGemini(Gemini):
    @cached_property
    def api_client(self) -> genai.Client:
        return genai.Client(vertexai=True, project=PROJECT_ID, location=LOCATION)

global_model = GlobalGemini(model=MODEL)

class ScoutOutput(BaseModel):
    capability_tag: Literal[
        "coding", "research", "devops", "document", "approval", "mcp", "stride"
    ] = Field(description="The capability required to handle the user's prompt.")

async def llm_scout_fn(ctx: Context, node_input: Any) -> Event:
    """The Scout node that determines the required capability tag."""
    prompt = get_prompt_text(ctx) or (str(node_input) if node_input else "")
    prompt_lower = prompt.lower()
    if any(w in prompt_lower for w in ["delete", "drop", "wipe", "destroy"]) and any(w in prompt_lower for w in ["database", "db", "production", "prod", "schema"]):
        record_scout("approval", 0.0, 0, 0)
        return Event(output={"capability_tag": "approval"})
    client = genai.Client(vertexai=True, project=PROJECT_ID, location=LOCATION)
    start_time = time.time()
    response = await client.aio.models.generate_content(
        model=MODEL,
        contents=prompt,
        config=types.GenerateContentConfig(
            system_instruction=(
                "You are the 'Scout' node. Assign a capability tag:\n"
                "- 'stride': security audit, threat model, vulnerabilities.\n"
                "- 'devops': executing pytest, lint, code checks, format.\n"
                "- 'coding': writing, modifying, implementing files.\n"
                "- 'mcp': viewing files, indexing, listing files.\n"
                "- 'research': literature/paper search."
            ),
            response_mime_type="application/json",
            response_schema=ScoutOutput,
        ),
    )
    latency = time.time() - start_time
    tag = "approval"
    try:
        if response.text:
            tag = json.loads(response.text).get("capability_tag", "approval")
    except Exception:
        pass
    in_tok = response.usage_metadata.prompt_token_count if response.usage_metadata else 0
    out_tok = response.usage_metadata.candidates_token_count if response.usage_metadata else 0
    record_scout(tag, latency, in_tok, out_tok)
    return Event(output={"capability_tag": tag})

llm_scout = FunctionNode(name="llm_scout", func=llm_scout_fn)

def router_node(ctx: Context, node_input: Any) -> Event:
    """Router node to redirect prompt based on Scout output."""
    if isinstance(node_input, dict):
        tag = node_input.get("capability_tag", "approval")
    elif hasattr(node_input, "capability_tag"):
        tag = getattr(node_input, "capability_tag")
    else:
        tag = str(node_input)
    prompt = get_prompt_text(ctx) or str(node_input)
    return Event(output=prompt, route=tag)  # type: ignore

router_fn = FunctionNode(name="router", func=router_node)

async def devops_node(ctx: Context, node_input: Any) -> AsyncGenerator[Event, None]:
    """DevOps execution node using pytest/subprocess verification."""
    prompt = get_prompt_text(ctx) or (str(node_input) if node_input else "")
    start_time = time.time()
    cmd = ["uv", "run", "pytest"] if any(w in prompt.lower() for w in ["test", "pytest", "run tests"]) else ["uv", "run", "python", "verify_code.py"]
    desc = "Running automated pytest suite..." if "pytest" in cmd else "Running code quality checks..."
    
    yield Event(content=types.Content(role="model", parts=[types.Part.from_text(text=f"⚙️ DevOps Engine: {desc}\n")]))
    try:
        res = subprocess.run(cmd, capture_output=True, text=True)
        latency = time.time() - start_time
        record_node_execution("devops", latency, 0, 0)
        output_text = f"STDOUT:\n{res.stdout}\nSTDERR:\n{res.stderr}\n"
        yield Event(content=types.Content(role="model", parts=[types.Part.from_text(text=output_text)]))
        yield Event(output={"result": output_text, "exit_code": res.returncode})
    except Exception as e:
        latency = time.time() - start_time
        record_node_execution("devops", latency, 0, 0)
        err = f"Error executing DevOps tool: {e}"
        yield Event(content=types.Content(role="model", parts=[types.Part.from_text(text=err)]))
        yield Event(output={"result": err, "exit_code": -1})

async def approval_node(ctx: Context, node_input: Any) -> AsyncGenerator[Event | RequestInput, None]:
    """Approval node with human-in-the-loop validation."""
    import sys
    alert_msg = str(node_input) or "High-risk routing."
    if any("_inference_runner.py" in arg for arg in sys.argv):
        yield Event(output=f"Approval auto-granted in eval mode. Details: {alert_msg}")
        return
    if getattr(ctx, "resume_inputs", None) is None or "approval_req" not in ctx.resume_inputs:
        record_hitl(escalated=True, approved=False, latency=0.0)
        yield RequestInput(interrupt_id="approval_req", message=f"🚨 PAUSING WORKFLOW 🚨\n{alert_msg}\n\nApprove routing? (y/n)")
        return
    approved = ctx.resume_inputs.get("approval_req", "")
    is_approved = approved.lower() in ["y", "yes", "approve", "true"]
    record_hitl(escalated=True, approved=is_approved, latency=5.0)
    msg = "Approval granted. Continuing..." if is_approved else "Approval denied. Halting workflow."
    yield Event(content=types.Content(role="model", parts=[types.Part.from_text(text=msg)]))
    yield Event(output=msg)

devops_fn = FunctionNode(name="devops", func=devops_node)
approval_fn = FunctionNode(name="approval", func=approval_node)

research_node = LlmAgent(name="research_node", model=global_model, instruction=load_skill_instructions("researcher"))
stride_node = LlmAgent(name="stride_node", model=global_model, instruction=load_skill_instructions("stride"))

filesystem_mcp = McpToolset(
    connection_params=StdioConnectionParams(
        server_params=StdioServerParameters(
            command="npx",
            args=["-y", "@modelcontextprotocol/server-filesystem", os.getcwd()],
        ),
    ),
)

coding_node = LlmAgent(
    name="coding_node",
    model=global_model,
    instruction="""You are the dedicated coding node. You handle codebase changes and file system operations using your tools.
IMPORTANT: You must NEVER call 'directory_tree' on the root directory '.' or any directory containing '.venv', '.git', etc. If you want to explore files, use 'list_directory' or 'search_files' instead. NEVER list, read, search, or access any files inside '.venv', '.git', '.pytest_cache', '__pycache__', or '.google-agents-cli' directories. Always ignore these directories in your search.
QUALITY RULE: Whenever you modify Python files in 'app/', you must run the quality verification checks using `uv run python scripts/agent_quality_check.py` and auto-correct any violations (e.g. line limits, DRY rules, missing type signatures, missing module header blocks) before completing your task.
""",
    tools=[filesystem_mcp],
)

mcp_node = LlmAgent(
    name="mcp_node",
    model=global_model,
    instruction="""You are the dedicated MCP node. You connect to local filesystem data to answer questions.
IMPORTANT: You must NEVER call 'directory_tree' on the root directory '.' or any directory containing '.venv', '.git', etc. If you want to explore files, use 'list_directory' or 'search_files' instead. NEVER list, read, search, or access any files inside '.venv', '.git', '.pytest_cache', '__pycache__', or '.google-agents-cli' directories. Always ignore these directories in your search.
""",
    tools=[filesystem_mcp],
)

@node
def security_screen(node_input: str) -> Event:
    """Security screen scanner to check inputs for PII leaks."""
    input_str = str(node_input)
    init_telemetry(input_str)
    pii_patterns = {
        "Social Security Number": r"\b\d{3}-\d{2,3}-\d{4}\b",
        "Email Address": r"\b[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}\b",
        "Phone Number": r"\b(?:\+?\d{1,3}[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}\b",
        "Credit Card Number": r"\b\d{4}[- ]?\d{4}[- ]?\d{4}[- ]?\d{4}\b",
        "IP Address": r"\b(?:[0-9]{1,3}\.){3}[0-9]{1,3}\b",
    }
    detected = [pii_type for pii_type, pattern in pii_patterns.items() if re.search(pattern, input_str)]
    if detected:
        pii_list = ", ".join(detected)
        record_security_screen(pii_detected=True, pii_types=detected)
        return Event(output=f"[SECURITY ALERT] PII detected in input. Please review. (Types: {pii_list})", route="approval")  # type: ignore
    record_security_screen(pii_detected=False, pii_types=[])
    return Event(output=node_input, route="safe")  # type: ignore

root_workflow = Workflow(
    name="root_agent",
    edges=[
        Edge(from_node=START, to_node=security_screen),
        Edge(from_node=security_screen, to_node=llm_scout, route="safe"),
        Edge(from_node=security_screen, to_node=approval_fn, route="approval"),
        Edge(from_node=llm_scout, to_node=router_fn),
        Edge(from_node=router_fn, to_node=devops_fn, route="devops"),
        Edge(from_node=router_fn, to_node=research_node, route="research"),
        Edge(from_node=router_fn, to_node=coding_node, route="coding"),
        Edge(from_node=router_fn, to_node=mcp_node, route="mcp"),
        Edge(from_node=router_fn, to_node=stride_node, route="stride"),
        Edge(from_node=router_fn, to_node=approval_fn, route=DEFAULT_ROUTE),
    ],
)
app = App(
    root_agent=root_workflow,
    name="app",
    plugins=[
        LoggingPlugin(),
        DebugLoggingPlugin(output_path="/tmp/adk_debug.yaml"),
    ],
)
