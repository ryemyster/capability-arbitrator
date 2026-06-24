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
How it works: Serves the custom dashboard at the root path (/) and delegates execution to the unified fast_api_app routing logic.
"""

import os
import sys
from typing import Any
import uvicorn
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, StreamingResponse

# Setup path so imports work correctly
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.app_utils.telemetry import get_history
from app.fast_api_app import event_generator

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
def get_metrics() -> list[dict[str, Any]]:
    """Retrieve execution metrics logs database."""
    return get_history()


@app.post("/api/run")
async def run_agent(request: Request) -> StreamingResponse:
    """Execute target workflow locally using InMemoryRunner and stream chunks."""
    payload = await request.json()
    prompt: str = payload.get("prompt", "")

    # Enforce local integration test running logic
    os.environ["INTEGRATION_TEST"] = "TRUE"

    return StreamingResponse(event_generator(prompt), media_type="text/event-stream")


def main() -> None:
    """Launch the FastAPI dashboard application locally."""
    port = int(os.environ.get("PORT", 8000))
    print(f"🚀 Starting Capability Arbitrator Telemetry Dashboard on http://127.0.0.1:{port}...")
    uvicorn.run(app, host="127.0.0.1", port=port)


if __name__ == "__main__":
    main()
