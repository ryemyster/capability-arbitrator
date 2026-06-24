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
File: fast_api_app.py
Purpose: Exposes a FastAPI application that unifies both the ADK agent endpoints and the custom telemetry dashboard.
Why it exists: To support a single containerized Cloud Run deployment hosting the dashboard frontend and the ADK execution API.
How it works: Obtains the standard ADK FastAPI app, mounts custom dashboard/telemetry routes, and serves them.
"""
import json
import os
from typing import Any, AsyncGenerator

import google.auth
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, StreamingResponse
from google.adk.cli.fast_api import get_fast_api_app
from google.cloud import logging as google_cloud_logging

from app.app_utils.telemetry import setup_telemetry
from app.app_utils.typing import Feedback

setup_telemetry()
try:
    _, project_id = google.auth.default()
    logging_client = google_cloud_logging.Client()
    logger = logging_client.logger(__name__)
except Exception:
    project_id = os.environ.get("GOOGLE_CLOUD_PROJECT", "mock-project-id")
    class MockLogger:
        def log_struct(self, info: dict, severity: str = "INFO") -> None:
            pass
    logger = MockLogger()
allow_origins = (
    os.getenv("ALLOW_ORIGINS", "").split(",") if os.getenv("ALLOW_ORIGINS") else None
)

# Artifact bucket for ADK (created by Terraform, passed via env var)
logs_bucket_name = os.environ.get("LOGS_BUCKET_NAME")

AGENT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
# In-memory session configuration - no persistent storage
session_service_uri = None

artifact_service_uri = f"gs://{logs_bucket_name}" if logs_bucket_name else None

app: FastAPI = get_fast_api_app(
    agents_dir=AGENT_DIR,
    web=True,
    artifact_service_uri=artifact_service_uri,
    allow_origins=allow_origins,
    session_service_uri=session_service_uri,
    otel_to_cloud=True,
)
app.title = "capability-arbitrator"
app.description = "API for interacting with the Agent capability-arbitrator"


@app.post("/feedback")
def collect_feedback(feedback: Feedback) -> dict[str, str]:
    """Collect and log feedback.

    Args:
        feedback: The feedback data to log

    Returns:
        Success message
    """
    logger.log_struct(feedback.model_dump(), severity="INFO")
    return {"status": "success"}


TEMPLATE_PATH = os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "templates", "index.html"
)


@app.get("/dashboard", response_class=HTMLResponse)
def serve_dashboard() -> HTMLResponse:
    """Serve the single-page premium glassmorphic dashboard."""
    try:
        with open(TEMPLATE_PATH, "r") as f:
            content = f.read()
        return HTMLResponse(content=content)
    except Exception as e:
        return HTMLResponse(content=f"<h1>Error loading dashboard: {e}</h1>", status_code=500)


@app.get("/api/metrics")
def get_metrics() -> list[dict[str, Any]]:
    """Retrieve execution metrics logs database."""
    from app.app_utils.telemetry import get_history
    return get_history()

def get_trace_event(event: Any) -> list[str]:
    """Inspects an ADK event and returns list of trace logs describing execution.

    Args:
        event: The incoming ADK event object.

    Returns:
        List of trace messages.
    """
    traces = []
    if hasattr(event, "actions") and event.actions:
        route = getattr(event.actions, "route", None)
        if route == "safe":
            traces.append("✅ Security Screen: Prompt cleared (No PII / injection vectors found). Safe to execute.")
            traces.append("🧠 Scout Node: Activating low-cost classifier to inspect capability tags...")
        elif route == "approval":
            traces.append("🚨 Security Screen: PII or sensitive operation detected! Workflow routing escalated to approval.")
        elif route and route != "safe":
            if route == "devops":
                traces.append("⚡ Deterministic Offloading: Routing to local DevOps engine (0 LLM tokens, 100% savings).")
            else:
                traces.append(f"🚀 Execution Node: Routing task to the specialized {route.upper()} executor...")

    if hasattr(event, "output") and isinstance(event.output, dict) and "capability_tag" in event.output:
        tag = event.output["capability_tag"]
        traces.append(f"🎯 Scout Node: Intent classified. Target capability: {tag.upper()}")
        traces.append(f"🔀 Router Node: Progressive disclosure triggered. Swapping out standard prompt and loading specialized instructions/tools for capability: {tag.upper()}")
        if tag == "devops":
            traces.append("Pruned all LLM execution tools/skills. Handed execution off to deterministic DevOps toolchain.")
        else:
            traces.append("Pruned 4 unused skills/tool sets to prevent context saturation and hallucinatory behavior.")
            
    return traces


async def event_generator(prompt: str) -> AsyncGenerator[str, None]:
    """Generate server-sent events for prompt routing and trace execution."""
    yield f"data: {json.dumps({'type': 'trace', 'text': '🛡️ Security Screen: Scanning user prompt for PII and security threats...'})}\n\n"
    has_exec_node = False
    from app.agent_runtime_app import agent_runtime
    try:
        async for event in agent_runtime.async_stream_query(
            message=prompt,
            user_id="dashboard-user",
            session_id="dashboard-session",
        ):
            # Generate and yield verbose trace events
            for trace_text in get_trace_event(event):
                yield f"data: {json.dumps({'type': 'trace', 'text': trace_text})}\n\n"

            # Standard Content stream
            if hasattr(event, "content") and event.content:
                for part in event.content.parts:
                    if hasattr(part, "text") and part.text:
                        has_exec_node = True
                        yield f"data: {json.dumps({'type': 'content', 'text': part.text})}\n\n"

            # Final output
            elif hasattr(event, "output") and event.output:
                if isinstance(event.output, dict) and "capability_tag" in event.output:
                    continue
                yield f"data: {json.dumps({'type': 'output', 'text': str(event.output)})}\n\n"
        
        # Output final progressive disclosure statistics
        from app.app_utils.telemetry import get_current_telemetry, calculate_savings
        run_data = get_current_telemetry()
        if run_data:
            run_data = calculate_savings(run_data)
            saved = run_data.get("token_savings", 0)
            pct = (saved / run_data["monolithic_in_tokens"] * 100) if run_data["monolithic_in_tokens"] > 0 else 0.0
            financial = run_data.get("cost_savings_usd", 0.0)
            yield f"data: {json.dumps({'type': 'trace', 'text': f'💡 progressive disclosure math: Saved {saved:,} tokens ({pct:.2f}% reduction) and ${financial:.5f} in LLM API cost!'})}\n\n"

        yield f"data: {json.dumps({'type': 'trace', 'text': '🏁 Execution completed successfully. Telemetry and savings calculated.'})}\n\n"
    except Exception as e:
        yield f"data: {json.dumps({'type': 'error', 'text': str(e)})}\n\n"


@app.post("/api/run")
async def run_agent(request: Request) -> StreamingResponse:
    """Execute target workflow locally using InMemoryRunner and stream chunks."""
    payload = await request.json()
    prompt: str = payload.get("prompt", "")

    # Enforce local integration test running logic
    os.environ["INTEGRATION_TEST"] = "TRUE"

    return StreamingResponse(event_generator(prompt), media_type="text/event-stream")


# Main execution
if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
