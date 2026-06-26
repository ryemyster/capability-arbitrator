# Created: 2026-06-24T17:37:45-06:00
"""
File: test_pubsub.py
Purpose: Executable test script for validating Pub/Sub event integration.
Why it exists: Part of the Phase Completion Verification Workflow for Phase 11.
How it works: Executes unit-like and endpoint-level checks, printing a clean [PASS] or [FAIL] indicator.
"""
import asyncio
import base64
import json
import sys
import os

# Add project root to python path
sys.path.insert(0, "/Users/rmcdonald/Repos/agy-cli-projects/capability-arbitrator")

# Enforce local integration test mode
os.environ["INTEGRATION_TEST"] = "TRUE"

from fastapi.testclient import TestClient
from app.fast_api_app import app
from app.app_utils.routing_utils import decode_pubsub_payload
from app.agent_runtime_app import agent_runtime


async def run_pubsub_test() -> None:
    print("============================================================")
    print("PHASE 11: PUB/SUB INTEGRATION NODE VALIDATION")
    print("============================================================")

    # Initialize agent runtime in integration test mode
    if agent_runtime:
        agent_runtime.set_up()


    # Initialize fastapi TestClient
    client = TestClient(app)

    try:
        # Test 1: Helper function decode_pubsub_payload with raw text
        raw_text = "What is 15 plus 30"
        encoded_raw = base64.b64encode(raw_text.encode("utf-8")).decode("utf-8")
        decoded_raw = decode_pubsub_payload(encoded_raw)
        assert decoded_raw == raw_text, f"Expected {raw_text}, got {decoded_raw}"
        print("Sub-test 1 (Raw Base64 Decoding) [PASS]")

        # Test 2: Helper function decode_pubsub_payload with JSON payload
        json_data = {"prompt": "Conduct academic research on quantum computing breakthroughs."}
        encoded_json = base64.b64encode(json.dumps(json_data).encode("utf-8")).decode("utf-8")
        decoded_json = decode_pubsub_payload(encoded_json)
        assert decoded_json == json_data["prompt"], f"Expected {json_data['prompt']}, got {decoded_json}"
        print("Sub-test 2 (JSON Base64 Decoding) [PASS]")

        # Test 3: Webhook endpoint execution using local integration test mode
        # This will route the prompt to the real or mock agent engine and return the result
        pubsub_payload = {
            "message": {
                "data": encoded_json,
                "messageId": "pubsub-test-message-id",
                "attributes": {}
            },
            "subscription": "projects/test-project/subscriptions/test-sub"
        }

        print("Sending POST request to /pubsub webhook endpoint...")
        response = client.post("/pubsub", json=pubsub_payload)
        
        # Verify endpoint status code and response payload structure
        assert response.status_code == 200, f"Expected 200, got {response.status_code}. Response: {response.text}"
        res_json = response.json()
        assert res_json.get("status") == "success", f"Expected success status, got {res_json.get('status')}. Detail: {res_json}"

        assert res_json["prompt"] == json_data["prompt"], f"Expected prompt {json_data['prompt']}, got {res_json['prompt']}"
        assert any(w in res_json["output"].lower() for w in ["quantum", "research", "methodology"]), f"Expected output to contain research/quantum keywords, got '{res_json['output']}'"
        print("Sub-test 3 (Webhook Endpoint POST /pubsub) [PASS]")


        print("[PASS] Pub/Sub Event Integration validated successfully.")

    except Exception as e:
        print(f"[FAIL] Pub/Sub Event Integration validation failed. Error: {e}")
        sys.exit(1)

    print("============================================================")


if __name__ == "__main__":
    asyncio.run(run_pubsub_test())
