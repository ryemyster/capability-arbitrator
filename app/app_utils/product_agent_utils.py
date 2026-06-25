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
File: product_agent_utils.py
Purpose: Runtime KPI auditor that verifies execution outcomes against the Capability Arbitrator's performance contracts.
Why it exists: Provides a continuous feedback loop between each live transaction and the offline eval scorecard,
               flagging KPI violations as structured telemetry so the dashboard can surface regressions in real time.
How it works: Reads the active run's telemetry after execution, checks each KPI threshold defined in docs/OUTCOMES.md,
              writes an outcome_verdicts dict back into the telemetry record (persisted by save_run()), and passes
              the output through unchanged so the Telemetry Watchdog can perform its budget checks.
"""

import copy
import time
from typing import Any

from google.adk.agents.context import Context
from google.adk.events.event import Event
from google.adk.workflow import FunctionNode

from app.app_utils.kpi_config_loader import load_kpi_config
from app.app_utils.telemetry import calculate_savings, get_current_telemetry, update_telemetry


def _pa_cfg() -> dict:
    return load_kpi_config()["product_agent"]


def _check_routing_confidence(telemetry: dict[str, Any]) -> dict[str, Any]:
    threshold = _pa_cfg()["routing_confidence_threshold"]
    confidence = float(telemetry.get("scout_confidence", 0.0))
    return {
        "pass": confidence >= threshold,
        "scout_confidence": confidence,
        "threshold": threshold,
    }


def _check_deterministic_offload(telemetry: dict[str, Any]) -> dict[str, Any]:
    tag = telemetry.get("scout_tag", "")
    node_source = telemetry.get("node_token_source", "")
    if tag in ("math", "devops"):
        passed = node_source == "deterministic_zero"
        return {"pass": passed, "scout_tag": tag, "node_token_source": node_source}
    return {"pass": True, "scout_tag": tag, "note": "deterministic offload N/A for LLM nodes"}


def _check_pii_compliance(telemetry: dict[str, Any]) -> dict[str, Any]:
    pii_detected = bool(telemetry.get("pii_detected", False))
    hitl_escalated = bool(telemetry.get("hitl_escalated", False))
    issue = "PII detected but HITL not triggered" if pii_detected and not hitl_escalated else None
    return {
        "pass": not (pii_detected and not hitl_escalated),
        "pii_detected": pii_detected,
        "hitl_escalated": hitl_escalated,
        **({"issue": issue} if issue else {}),
    }


def _check_latency(telemetry: dict[str, Any]) -> dict[str, Any]:
    threshold = _pa_cfg()["latency_threshold_seconds"]
    elapsed = time.time() - float(telemetry.get("timestamp", time.time()))
    return {
        "pass": elapsed < threshold,
        "elapsed_seconds": round(elapsed, 2),
        "threshold": threshold,
    }


def _check_token_efficiency(telemetry: dict[str, Any]) -> dict[str, Any]:
    threshold = _pa_cfg()["token_savings_threshold"]
    run_copy = copy.deepcopy(telemetry)
    run_copy = calculate_savings(run_copy)
    token_savings = int(run_copy.get("token_savings", 0))
    monolithic_in = int(run_copy.get("monolithic_in_tokens", 1))
    savings_ratio = token_savings / monolithic_in if monolithic_in > 0 else 0.0
    return {
        "pass": savings_ratio >= threshold,
        "savings_ratio": round(savings_ratio, 3),
        "threshold": threshold,
        "token_savings": token_savings,
    }


def product_agent_node(ctx: Context, node_input: Any) -> Event:
    telemetry = get_current_telemetry()
    if not telemetry:
        return Event(output=node_input)  # type: ignore[arg-type]

    verdicts: dict[str, Any] = {
        "routing_confidence": _check_routing_confidence(telemetry),
        "deterministic_offload": _check_deterministic_offload(telemetry),
        "pii_compliance": _check_pii_compliance(telemetry),
        "latency": _check_latency(telemetry),
        "token_efficiency": _check_token_efficiency(telemetry),
    }

    violations = [k for k, v in verdicts.items() if not v.get("pass", True)]

    remediation: dict[str, str] = {}
    if not verdicts["latency"]["pass"]:
        remediation["latency_alert"] = "Telemetry watchdog will switch to cheaper model."
    if not verdicts["token_efficiency"]["pass"]:
        remediation["token_alert"] = "Token savings below 80% — scout classification may be suboptimal."
    if not verdicts["routing_confidence"]["pass"]:
        remediation["routing_alert"] = "Scout confidence below threshold — may need retraining."
    if not verdicts["pii_compliance"]["pass"]:
        remediation["pii_alert"] = "HITL was not escalated for PII — security policy violated."
    if not verdicts["deterministic_offload"]["pass"]:
        tag = verdicts["deterministic_offload"].get("scout_tag", "")
        remediation["offload_alert"] = f"LLM tokens billed for {tag} — should use deterministic path."

    update_telemetry({
        "outcome_verdicts": verdicts,
        "outcome_violations": violations,
        "outcome_remediation": remediation,
    })

    return Event(output=node_input)  # type: ignore[arg-type]


product_agent = FunctionNode(name="product_agent", func=product_agent_node)
