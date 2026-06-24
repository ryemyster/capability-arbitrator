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
File: dashboard.py
Purpose: Exposes a FastAPI management dashboard and playground for the Capability Arbitrator.
Why it exists: Provides developers and stakeholders with a premium, real-time visualization of cost, latency, and token savings.
How it works: Launches a FastAPI server, reading a separate HTML template and executing local agent runs via InMemoryRunner.
"""

import json
import os
import sys
from typing import Any, AsyncGenerator, Dict, List
import uvicorn
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, StreamingResponse

# Setup path so imports work correctly
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

app = FastAPI(title="Capability Arbitrator Dashboard")

TEMPLATE_PATH = os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "templates", "index.html"
)

@app.get("/", response_class=HTMLResponse)
def serve_dashboard() -> HTMLResponse:
    """Serve the single-page premium glassmorphic dashboard."""
    try:
        with open(TEMPLATE_PATH, "r") as f:
            content = f.read()
        return HTMLResponse(content=content)
    except Exception as e:
        return HTMLResponse(content=f"<h1>Error loading dashboard: {e}</h1>", status_code=500)

@app.get("/api/metrics")
def get_metrics() -> List[Dict[str, Any]]:
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

def main() -> None:
    """Launch the FastAPI dashboard application locally."""
    port = int(os.environ.get("PORT", 8000))
    print(f"🚀 Starting Capability Arbitrator Telemetry Dashboard on http://127.0.0.1:{port}...")
    uvicorn.run(app, host="127.0.0.1", port=port)

if __name__ == "__main__":
    main()
