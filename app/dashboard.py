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
Purpose: Launches the unified FastAPI server locally.
Why it exists: Provides developers and stakeholders with a local runner for the custom telemetry dashboard.
How it works: Imports the unified app instance from fast_api_app and runs it under Uvicorn.
"""

import os
import sys
import uvicorn

# Setup path so imports work correctly
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.fast_api_app import app

def main() -> None:
    """Launch the FastAPI dashboard application locally."""
    port = int(os.environ.get("PORT", 8000))
    print(f"🚀 Starting Capability Arbitrator Telemetry Dashboard on http://127.0.0.1:{port}...")
    uvicorn.run(app, host="127.0.0.1", port=port)

if __name__ == "__main__":
    main()
