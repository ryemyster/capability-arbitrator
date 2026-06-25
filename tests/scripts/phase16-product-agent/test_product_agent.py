"""
Phase 16 smoke tests — Product Agent KPI auditor node.
# Created: 2026-06-24 MDT
"""

import time
from unittest.mock import MagicMock, patch

from app.app_utils.product_agent_utils import (
    _check_deterministic_offload,
    _check_latency,
    _check_pii_compliance,
    _check_routing_confidence,
    _check_token_efficiency,
    product_agent_node,
)

PASS = "[PASS]"
FAIL = "[FAIL]"


def run(label: str, condition: bool) -> bool:
    print(f"  {PASS if condition else FAIL} {label}")
    return condition


def test_all_kpis_pass_on_clean_run() -> bool:
    telemetry = {
        "timestamp": time.time() - 3.0,
        "prompt": "what is 2+2",
        "scout_confidence": 92.0,
        "scout_tag": "math",
        "node_token_source": "deterministic_zero",
        "pii_detected": False,
        "hitl_escalated": False,
        "scout_input_tokens": 0,
        "scout_output_tokens": 0,
        "node_input_tokens": 0,
        "node_output_tokens": 0,
        "scout_token_source": "deterministic_zero",
        "node_name": "math",
    }
    with patch("app.app_utils.product_agent_utils.get_current_telemetry", return_value=telemetry), \
         patch("app.app_utils.product_agent_utils.update_telemetry") as mock_update:
        product_agent_node(MagicMock(), "4")
    stored = mock_update.call_args[0][0]
    violations = stored["outcome_violations"]
    return run("all KPIs pass on clean math run", violations == [])


def test_routing_confidence_violation_flagged() -> bool:
    result = _check_routing_confidence({"scout_confidence": 40.0})
    return run("routing_confidence violation flagged at 40%", result["pass"] is False)


def test_deterministic_offload_violation_flagged() -> bool:
    result = _check_deterministic_offload({"scout_tag": "devops", "node_token_source": "actual"})
    return run("deterministic_offload violation flagged for devops+actual", result["pass"] is False)


def test_pii_without_hitl_violation_flagged() -> bool:
    result = _check_pii_compliance({"pii_detected": True, "hitl_escalated": False})
    return run("pii_compliance violation flagged when PII not escalated", result["pass"] is False)


def test_latency_violation_flagged() -> bool:
    result = _check_latency({"timestamp": time.time() - 60.0})
    return run("latency violation flagged for 60s run", result["pass"] is False)


def test_verdicts_persisted_to_telemetry() -> bool:
    telemetry = {
        "timestamp": time.time() - 2.0,
        "prompt": "p",
        "scout_confidence": 80.0,
        "scout_tag": "coding",
        "node_token_source": "estimated",
        "pii_detected": False,
        "hitl_escalated": False,
        "scout_input_tokens": 0,
        "scout_output_tokens": 0,
        "node_input_tokens": 0,
        "node_output_tokens": 0,
        "scout_token_source": "estimated",
        "node_name": "coding",
    }
    with patch("app.app_utils.product_agent_utils.get_current_telemetry", return_value=telemetry), \
         patch("app.app_utils.product_agent_utils.update_telemetry") as mock_update:
        product_agent_node(MagicMock(), "response")
    stored = mock_update.call_args[0][0]
    keys_present = all(k in stored for k in ("outcome_verdicts", "outcome_violations", "outcome_remediation"))
    return run("outcome_verdicts/violations/remediation written to telemetry", keys_present)


if __name__ == "__main__":
    print("\n=== Phase 16: Product Agent KPI Auditor Smoke Tests ===\n")
    results = [
        test_all_kpis_pass_on_clean_run(),
        test_routing_confidence_violation_flagged(),
        test_deterministic_offload_violation_flagged(),
        test_pii_without_hitl_violation_flagged(),
        test_latency_violation_flagged(),
        test_verdicts_persisted_to_telemetry(),
    ]
    passed = sum(results)
    total = len(results)
    print(f"\n{'=' * 50}")
    print(f"Results: {passed}/{total} passed")
    if passed < total:
        raise SystemExit(1)
