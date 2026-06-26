# Created: 2026-06-24T06:32:00-06:00
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
File: test_telemetry_dashboard.py
Purpose: Programmatic verification script for Phase 9 Telemetry Dashboard.
Why it exists: Asserts that dashboard is running, endpoints are active, and telemetry logic works.
How it works: Executes FastAPI TestClient requests and asserts expected status codes, printing [PASS] or [FAIL].
"""

import sys
import os

# Setup path so imports work correctly
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from fastapi.testclient import TestClient
from app.fast_api_app import app

def run_tests() -> bool:
    client = TestClient(app)
    all_passed = True

    print("Running Phase 9 - Telemetry Dashboard Verification...")

    # Test 1: HTML Serving
    try:
        res = client.get("/dashboard")
        if res.status_code == 200 and "Capability Arbitrator" in res.text:
            print("[PASS] Dashboard root endpoint serves HTML successfully.")
        else:
            print("[FAIL] Dashboard root served incorrect response:", res.status_code)
            all_passed = False
    except Exception as e:
        print("[FAIL] Dashboard root check crashed:", e)
        all_passed = False

    # Test 2: Metrics GET
    try:
        res = client.get("/api/metrics")
        if res.status_code == 200 and isinstance(res.json(), list):
            print("[PASS] Telemetry metrics database endpoint is active.")
        else:
            print("[FAIL] Telemetry metrics endpoint served incorrect response:", res.status_code)
            all_passed = False
    except Exception as e:
        print("[FAIL] Telemetry metrics check crashed:", e)
        all_passed = False

    # Test 3: Agent Execution
    try:
        res = client.post("/api/run", json={"prompt": "Solve 5 + 5"})
        if res.status_code == 200:
            print("[PASS] Streaming playground execution endpoint is active.")
        else:
            print("[FAIL] Streaming endpoint served incorrect response:", res.status_code)
            all_passed = False
    except Exception as e:
        print("[FAIL] Streaming endpoint check crashed:", e)
        all_passed = False

    return all_passed

if __name__ == "__main__":
    success = run_tests()
    if success:
        print("\n🎉 PHASE 9 SYSTEM VERIFICATION: [PASS]")
        sys.exit(0)
    else:
        print("\n❌ PHASE 9 SYSTEM VERIFICATION: [FAIL]")
        sys.exit(1)
