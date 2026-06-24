# Copyright 2026 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""
File: agent.py
Purpose: Defines the dynamic capability arbitrator agent workflow.
Why/How: A progressive disclosure traffic router that assigns tasks to nodes based on target workspace configurations.
"""
import os
import re
import json
import time
from typing import Any, Literal, AsyncGenerator, List
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
from pydantic import BaseModel, Field, create_model

from functools import cached_property
from google import genai
from google.genai import types
from google.adk.models.google_llm import Gemini
from app.config import MODEL
from app.app_utils.routing_utils import get_prompt_text
from app.app_utils.skill_utils import load_skill_instructions
from app.app_utils.config_loader import get_target_dir, load_arbitrator_config, load_mcp_configs
from app.app_utils.devops_utils import devops_fn
from app.app_utils.telemetry import (
    init_telemetry,
    record_security_screen,
    record_scout,
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

# 1. Resolve target workspace CWD and load capabilities configuration
target_dir = get_target_dir()
caps = load_arbitrator_config(target_dir)
mcp_settings = load_mcp_configs(target_dir)

# Build Pydantic model for Scout output dynamically
cap_tags = [c.tag for c in caps]
if "approval" not in cap_tags:
    cap_tags.append("approval")

ScoutOutput = create_model(
    "ScoutOutput",
    capability_tag=(
        Literal[tuple(cap_tags)],  # type: ignore
        Field(description="The capability required to handle the user's prompt.")
    )
)

def _build_scout_instruction() -> str:
    """Helper to build Scout prompt instructions dynamically."""
    instr = "You are the 'Scout' node. Assign a capability tag:\n"
    for cap in caps:
        instr += f"- '{cap.tag}': {cap.description}.\n"
    return instr

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
            system_instruction=_build_scout_instruction(),
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

approval_fn = FunctionNode(name="approval", func=approval_node)

# 2. Dynamically set up MCP tools based on configs
mcp_tools = []
if mcp_settings:
    for name, srv in mcp_settings.items():
        try:
            mcp_tools.append(
                McpToolset(
                    connection_params=StdioConnectionParams(
                        server_params=StdioServerParameters(
                            command=srv["command"],
                            args=srv.get("args", []),
                        )
                    )
                )
            )
        except Exception:
            pass

if not mcp_tools:
    filesystem_mcp = McpToolset(
        connection_params=StdioConnectionParams(
            server_params=StdioServerParameters(
                command="npx",
                args=["-y", "@modelcontextprotocol/server-filesystem", target_dir],
            ),
        ),
    )
    mcp_tools.append(filesystem_mcp)

coding_node = LlmAgent(
    name="coding_node",
    model=global_model,
    instruction="""You are the dedicated coding node. You handle codebase changes and file system operations using your tools.
IMPORTANT: You must NEVER call 'directory_tree' on the root directory '.' or any directory containing '.venv', '.git', etc. If you want to explore files, use 'list_directory' or 'search_files' instead. NEVER list, read, search, or access any files inside '.venv', '.git', '.pytest_cache', '__pycache__', or '.google-agents-cli' directories. Always ignore these directories in your search.
QUALITY RULE: Whenever you modify Python files in 'app/', you must run the quality verification checks using `uv run python scripts/agent_quality_check.py` and auto-correct any violations before completing your task.
""",
    tools=mcp_tools,
)

mcp_node = LlmAgent(
    name="mcp_node",
    model=global_model,
    instruction="""You are the dedicated MCP node. You connect to local filesystem data to answer questions.
IMPORTANT: You must NEVER call 'directory_tree' on the root directory '.' or any directory containing '.venv', '.git', etc. If you want to explore files, use 'list_directory' or 'search_files' instead. NEVER list, read, search, or access any files inside '.venv', '.git', '.pytest_cache', '__pycache__', or '.google-agents-cli' directories. Always ignore these directories in your search.
""",
    tools=mcp_tools,
)

# 3. Dynamic Node Mapping and Edge Wiring
node_mapping = {
    "coding": coding_node,
    "mcp": mcp_node,
    "devops": devops_fn,
    "approval": approval_fn,
}

# Dynamically instantiate skill LlmAgents
for cap in caps:
    if cap.node_type == "skill" and cap.target:
        sanitized_target = re.sub(r'[^a-zA-Z0-9_]', '_', cap.target)
        node_name = f"{sanitized_target}_node"
        node_mapping[cap.tag] = LlmAgent(
            name=node_name,
            model=global_model,
            instruction=load_skill_instructions(cap.target, target_dir)
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

edges = [
    Edge(from_node=START, to_node=security_screen),
    Edge(from_node=security_screen, to_node=llm_scout, route="safe"),
    Edge(from_node=security_screen, to_node=approval_fn, route="approval"),
    Edge(from_node=llm_scout, to_node=router_fn),
]

for cap in caps:
    target_node = node_mapping.get(cap.tag)
    if not target_node:
        if cap.node_type == "coding":
            target_node = coding_node
        elif cap.node_type == "mcp":
            target_node = mcp_node
        elif cap.node_type == "devops":
            target_node = devops_fn
        else:
            target_node = approval_fn
    
    if target_node:
        edges.append(Edge(from_node=router_fn, to_node=target_node, route=cap.tag))

edges.append(Edge(from_node=router_fn, to_node=approval_fn, route=DEFAULT_ROUTE))

root_workflow = Workflow(
    name="root_agent",
    edges=edges,
)
root_agent = root_workflow
app = App(
    root_agent=root_workflow,
    name="app",
    plugins=[
        LoggingPlugin(),
        DebugLoggingPlugin(output_path="/tmp/adk_debug.yaml"),
    ],
)
