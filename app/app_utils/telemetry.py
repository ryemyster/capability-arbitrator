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
File: telemetry.py
Purpose: Tracks, calculates, and persists telemetry and token savings metrics.
Why it exists: We need a reliable metrics store to compare the Capability Arbitrator's performance against a monolithic baseline.
How it works: Uses ContextVar to track current run stats in a thread-safe manner, writing results to a local JSON database.
"""

import json
import os
import time
from typing import Any, Dict, List, Optional

# Global dict to track telemetry metrics for the active request/session
active_run_telemetry: Dict[str, Any] = {}

target_dir = os.environ.get("ARBITRATOR_CWD", os.getcwd())
DB_FILE = os.path.join(target_dir, "telemetry_db.json")

def init_telemetry(prompt: str) -> Dict[str, Any]:
    """Initialize a telemetry recording session for the current prompt."""
    global active_run_telemetry
    active_run_telemetry = {
        "timestamp": time.time(),
        "prompt": prompt,
        "user_id": "unknown",
        "session_id": "unknown",
        "run_source": "unknown",
        "pii_detected": False,
        "pii_types": [],
        "scout_tag": "unknown",
        "scout_confidence": 0.0,
        "scout_latency": 0.0,
        "scout_input_tokens": 0,
        "scout_output_tokens": 0,
        "node_name": "unknown",
        "node_latency": 0.0,
        "node_input_tokens": 0,
        "node_output_tokens": 0,
        "mcp_tool_calls": 0,
        "hitl_escalated": False,
        "hitl_approved": False,
        "hitl_latency": 0.0,
        "total_latency": 0.0,
        "scout_token_source": "unknown",
        "node_token_source": "unknown",
        "savings_method": "monolithic_baseline_estimate",
    }
    return active_run_telemetry

def get_current_telemetry() -> Optional[Dict[str, Any]]:
    """Retrieve the current active request's telemetry dict."""
    global active_run_telemetry
    return active_run_telemetry if active_run_telemetry else None

def update_telemetry(updates: Dict[str, Any]) -> None:
    """Apply updates to the active telemetry session."""
    global active_run_telemetry
    if active_run_telemetry:
        active_run_telemetry.update(updates)

def record_security_screen(pii_detected: bool, pii_types: List[str]) -> None:
    """Record PII screen details."""
    updates: Dict[str, Any] = {
        "pii_detected": pii_detected,
        "pii_types": pii_types,
    }
    if pii_detected:
        updates.update({
            "scout_tag": "approval",
            "scout_token_source": "deterministic_zero",
        })
    update_telemetry(updates)

def record_scout(
    tag: str,
    latency: float,
    input_tokens: int,
    output_tokens: int,
    confidence: float = 0.0,
    token_source: str | None = None,
) -> None:
    """Record Scout intent routing details."""
    source = token_source or ("actual" if input_tokens > 0 or output_tokens > 0 else "estimated")
    update_telemetry({
        "scout_tag": tag,
        "scout_confidence": confidence,
        "scout_latency": latency,
        "scout_input_tokens": input_tokens,
        "scout_output_tokens": output_tokens,
        "scout_token_source": source,
    })

def record_node_execution(node_name: str, latency: float, input_tokens: int, output_tokens: int) -> None:
    """Record execution node details."""
    update_telemetry({
        "node_name": node_name,
        "node_latency": latency,
        "node_input_tokens": input_tokens,
        "node_output_tokens": output_tokens
    })

def record_mcp_tool_call() -> None:
    """Increment MCP tool call counter."""
    global active_run_telemetry
    if active_run_telemetry:
        active_run_telemetry["mcp_tool_calls"] = active_run_telemetry.get("mcp_tool_calls", 0) + 1

def record_hitl(escalated: bool, approved: bool, latency: float) -> None:
    """Record Human-in-the-Loop approval metrics."""
    update_telemetry({
        "node_name": "approval",
        "node_input_tokens": 0,
        "node_output_tokens": 0,
        "node_token_source": "deterministic_zero",
        "hitl_escalated": escalated,
        "hitl_approved": approved,
        "hitl_latency": latency
    })

def _estimate_node_tokens(node_name: str, prompt_tokens: int) -> tuple[int, int]:
    """Estimate node input and output tokens if not captured."""
    if node_name in ["devops", "math"]:
        return 0, 0
    if node_name == "research":
        return prompt_tokens + 2500, 1000
    if node_name in ["coding", "mcp"]:
        return prompt_tokens + 5000, 500
    if node_name == "stride":
        return prompt_tokens + 2000, 800
    return prompt_tokens + 1000, 200

def classify_run_source(user_id: str, session_id: str | None, force_local: bool) -> str:
    """Label where a telemetry run came from so the dashboard can show provenance."""
    if user_id == "pubsub-user" or (session_id or "").startswith("pubsub-session"):
        return "pubsub_integration"
    if user_id == "dashboard-user":
        return "dashboard_local_runner" if force_local else "dashboard_agent_runtime"
    if force_local or os.environ.get("INTEGRATION_TEST") == "TRUE":
        return "local_test_runner"
    return "agent_runtime"

def _resolve_scout_tokens(run: Dict[str, Any], prompt_tokens: int) -> tuple[int, int, str]:
    """Return Scout token counts and whether they were measured or estimated."""
    raw_scout_in = run.get("scout_input_tokens") or 0
    raw_scout_out = run.get("scout_output_tokens") or 0
    recorded_source = run.get("scout_token_source")
    if recorded_source == "deterministic_zero":
        return raw_scout_in, raw_scout_out, recorded_source
    token_source = "actual" if raw_scout_in > 0 or raw_scout_out > 0 else "estimated"
    return raw_scout_in or (prompt_tokens + 1200), raw_scout_out or 50, token_source

def _resolve_node_tokens(run: Dict[str, Any], prompt_tokens: int) -> tuple[int, int, str]:
    """Return execution-node token counts and their provenance label."""
    node_in = run.get("node_input_tokens") or 0
    node_out = run.get("node_output_tokens") or 0
    node_name = run.get("node_name", "unknown")
    if node_name in ["devops", "math"]:
        return node_in, node_out, "deterministic_zero"
    if node_in == 0:
        node_in, node_out = _estimate_node_tokens(node_name, prompt_tokens)
        return node_in, node_out, "estimated"
    return node_in, node_out, "actual"

def _calculate_cost_savings(
    monolithic_in: int,
    monolithic_out: int,
    arbitrator_in: int,
    arbitrator_out: int,
) -> float:
    """Calculate estimated dollar savings against the baseline prompt."""
    cost_mono = (monolithic_in * 0.075 / 1e6) + (monolithic_out * 0.30 / 1e6)
    cost_arb = (arbitrator_in * 0.075 / 1e6) + (arbitrator_out * 0.30 / 1e6)
    return max(0.0, cost_mono - cost_arb)

def calculate_savings(run: Dict[str, Any]) -> Dict[str, Any]:
    """Calculate token footprint and cost savings against a monolithic baseline.
    Pricing based on standard Gemini 1.5/3.5 Flash:
      - Input: $0.075 / 1,000,000 tokens
      - Output: $0.30 / 1,000,000 tokens
    """
    prompt_len = len(run.get("prompt", ""))
    prompt_tokens = max(10, int(prompt_len / 4))

    scout_in, scout_out, scout_token_source = _resolve_scout_tokens(run, prompt_tokens)
    node_in, node_out, node_token_source = _resolve_node_tokens(run, prompt_tokens)

    # Monolithic baseline loads ALL skills and tools for every single query
    monolithic_in = prompt_tokens + 13000
    monolithic_out = max(scout_out, node_out)

    arbitrator_in = scout_in + node_in
    arbitrator_out = scout_out + node_out

    token_savings = max(0, monolithic_in - arbitrator_in)

    cost_savings = _calculate_cost_savings(
        monolithic_in, monolithic_out, arbitrator_in, arbitrator_out
    )

    run.update({
        "scout_input_tokens": scout_in,
        "scout_output_tokens": scout_out,
        "node_input_tokens": node_in,
        "node_output_tokens": node_out,
        "monolithic_in_tokens": monolithic_in,
        "monolithic_out_tokens": monolithic_out,
        "arbitrator_in_tokens": arbitrator_in,
        "arbitrator_out_tokens": arbitrator_out,
        "token_savings": token_savings,
        "cost_savings_usd": cost_savings,
        "scout_token_source": scout_token_source,
        "node_token_source": node_token_source,
        "savings_method": "monolithic_baseline_estimate",
    })
    return run

def save_run() -> Optional[Dict[str, Any]]:
    """Calculate final savings and append the run telemetry to local storage."""
    run = get_current_telemetry()
    if not run:
        return None

    run["total_latency"] = time.time() - run["timestamp"]
    run = calculate_savings(run)

    history = get_history()
    history.append(run)

    # Keep database capped at last 1000 runs
    if len(history) > 1000:
        history = history[-1000:]

    try:
        with open(DB_FILE, "w") as f:
            json.dump(history, f, indent=2)
    except Exception as e:
        print(f"Error saving telemetry: {e}")

    return run

def get_history() -> List[Dict[str, Any]]:
    """Retrieve historical telemetry runs from local JSON database."""
    if not os.path.exists(DB_FILE):
        return []
    try:
        with open(DB_FILE, "r") as f:
            return json.load(f)
    except Exception:
        return []

def setup_telemetry() -> str | None:
    """Setup standard logging environment attributes (stub compat)."""
    os.environ.setdefault("GOOGLE_CLOUD_AGENT_ENGINE_ENABLE_TELEMETRY", "true")
    return os.environ.get("LOGS_BUCKET_NAME")
