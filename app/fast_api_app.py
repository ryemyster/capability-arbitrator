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
_, project_id = google.auth.default()
logging_client = google_cloud_logging.Client()
logger = logging_client.logger(__name__)
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


@app.post("/api/run")
async def run_agent(request: Request) -> StreamingResponse:
    """Execute target workflow locally using InMemoryRunner and stream chunks."""
    payload = await request.json()
    prompt: str = payload.get("prompt", "")

    # Enforce local integration test running logic
    os.environ["INTEGRATION_TEST"] = "TRUE"

    from app.agent_runtime_app import agent_runtime

    async def event_generator() -> AsyncGenerator[str, None]:
        try:
            async for event in agent_runtime.async_stream_query(
                message=prompt,
                user_id="dashboard-user",
                session_id="dashboard-session",
            ):
                if hasattr(event, "content") and event.content:
                    for part in event.content.parts:
                        if hasattr(part, "text") and part.text:
                            yield f"data: {json.dumps({'type': 'content', 'text': part.text})}\n\n"
                elif hasattr(event, "output") and event.output:
                    # Capture final routing payload
                    yield f"data: {json.dumps({'type': 'output', 'text': str(event.output)})}\n\n"
        except Exception as e:
            yield f"data: {json.dumps({'type': 'error', 'text': str(e)})}\n\n"

    return StreamingResponse(event_generator(), media_type="text/event-stream")


# Main execution
if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
