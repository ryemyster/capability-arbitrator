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
File: test_pubsub.py
Purpose: Unit tests for the GCP Pub/Sub push webhook integration endpoint.
Why it exists: Ensures Pub/Sub push messages are correctly received, base64 decoded, and routed to the agent engine.
How it works: Employs FastAPI's TestClient to POST mocked Pub/Sub messages and validates the endpoint's behavior.
"""

import base64
import json
from unittest.mock import AsyncMock, patch
from fastapi.testclient import TestClient
from google.adk.events.event import Event
from google.genai import types

from app.fast_api_app import app
from app.app_utils.routing_utils import decode_pubsub_payload

client = TestClient(app)


def test_decode_pubsub_payload_raw() -> None:
    """Verifies that raw text encoded in base64 is decoded correctly."""
    # We base64 encode a simple prompt
    encoded = base64.b64encode(b"Calculate 10 + 20").decode("utf-8")
    result = decode_pubsub_payload(encoded)
    assert result == "Calculate 10 + 20"


def test_decode_pubsub_payload_json() -> None:
    """Verifies that a JSON object containing a prompt is parsed correctly."""
    # We encode a JSON dictionary with the "prompt" key
    payload_dict = {"prompt": "What is the capital of France?"}
    payload_str = json.dumps(payload_dict)
    encoded = base64.b64encode(payload_str.encode("utf-8")).decode("utf-8")
    result = decode_pubsub_payload(encoded)
    assert result == "What is the capital of France?"


@patch("app.agent_runtime_app.agent_runtime.async_stream_query")
def test_handle_pubsub_endpoint(mock_stream_query: AsyncMock) -> None:
    """Tests the /pubsub FastAPI endpoint with a mocked agent execution stream."""
    # Setup the mock async stream query generator to yield a single response event
    async def mock_generator(*args: list, **kwargs: dict) -> AsyncMock:
        yield Event(content=types.Content(role="model", parts=[types.Part.from_text(text="Mocked output")]))

    mock_stream_query.return_value = mock_generator()

    # Create a base64 encoded prompt payload
    encoded_prompt = base64.b64encode(b"Run test prompt").decode("utf-8")

    # Pub/Sub push message payload envelope format
    pubsub_payload = {
        "message": {
            "data": encoded_prompt,
            "messageId": "12345-test",
            "attributes": {}
        },
        "subscription": "projects/test-project/subscriptions/test-sub"
    }

    # Perform the HTTP POST request to the /pubsub endpoint
    response = client.post("/pubsub", json=pubsub_payload)

    # Validate response status and content
    assert response.status_code == 200
    res_json = response.json()
    assert res_json["status"] == "success"
    assert res_json["prompt"] == "Run test prompt"
    assert res_json["output"] == "Mocked output"
