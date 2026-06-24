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
File: test_dashboard.py
Purpose: Unit tests for the FastAPI telemetry dashboard app.
Why it exists: Verifies the routing, HTML page serving, and API functionality of the dashboard endpoints.
How it works: Uses FastAPI's TestClient to call endpoints and assert response codes and content types.
"""

from fastapi.testclient import TestClient
from app.fast_api_app import app

client = TestClient(app)

def test_dashboard_serve_root() -> None:
    """Verifies that the /dashboard path serves the HTML template successfully."""
    response = client.get("/dashboard")
    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]
    assert "Capability Arbitrator" in response.text

def test_dashboard_serve_metrics() -> None:
    """Verifies that the /api/metrics endpoint returns the historical logs list."""
    response = client.get("/api/metrics")
    assert response.status_code == 200
    assert isinstance(response.json(), list)
