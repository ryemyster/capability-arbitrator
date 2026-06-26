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

"""Unit tests for product_agent_utils.py — KPI auditor node."""

import time
from unittest.mock import MagicMock, patch

import pytest

from app.app_utils.product_agent_utils import (
    _check_deterministic_offload,
    _check_latency,
    _check_pii_compliance,
    _check_routing_confidence,
    _check_token_efficiency,
    product_agent_node,
)


# ---------------------------------------------------------------------------
# _check_routing_confidence
# ---------------------------------------------------------------------------

def test_routing_confidence_passes_above_threshold():
    result = _check_routing_confidence({"scout_confidence": 80.0})
    assert result["pass"] is True
    assert result["scout_confidence"] == 80.0


def test_routing_confidence_fails_below_threshold():
    result = _check_routing_confidence({"scout_confidence": 60.0})
    assert result["pass"] is False


def test_routing_confidence_passes_at_exact_threshold():
    result = _check_routing_confidence({"scout_confidence": 75.0})
    assert result["pass"] is True


def test_routing_confidence_defaults_zero_when_missing():
    result = _check_routing_confidence({})
    assert result["pass"] is False
    assert result["scout_confidence"] == 0.0


# ---------------------------------------------------------------------------
# _check_deterministic_offload
# ---------------------------------------------------------------------------

def test_deterministic_offload_passes_for_math_with_zero_tokens():
    result = _check_deterministic_offload({"scout_tag": "math", "node_token_source": "deterministic_zero"})
    assert result["pass"] is True


def test_deterministic_offload_fails_for_devops_with_llm_tokens():
    result = _check_deterministic_offload({"scout_tag": "devops", "node_token_source": "actual"})
    assert result["pass"] is False


def test_deterministic_offload_skipped_for_llm_node():
    result = _check_deterministic_offload({"scout_tag": "coding", "node_token_source": "actual"})
    assert result["pass"] is True
    assert "N/A" in result["note"]


# ---------------------------------------------------------------------------
# _check_pii_compliance
# ---------------------------------------------------------------------------

def test_pii_compliance_passes_when_no_pii():
    result = _check_pii_compliance({"pii_detected": False, "hitl_escalated": False})
    assert result["pass"] is True


def test_pii_compliance_passes_when_pii_and_hitl_both_triggered():
    result = _check_pii_compliance({"pii_detected": True, "hitl_escalated": True})
    assert result["pass"] is True


def test_pii_compliance_fails_when_pii_detected_but_hitl_skipped():
    result = _check_pii_compliance({"pii_detected": True, "hitl_escalated": False})
    assert result["pass"] is False
    assert "issue" in result


# ---------------------------------------------------------------------------
# _check_latency
# ---------------------------------------------------------------------------

def test_latency_passes_for_fast_run():
    recent_ts = time.time() - 5.0
    result = _check_latency({"timestamp": recent_ts})
    assert result["pass"] is True
    assert result["elapsed_seconds"] < 30.0


def test_latency_fails_for_slow_run():
    old_ts = time.time() - 45.0
    result = _check_latency({"timestamp": old_ts})
    assert result["pass"] is False
    assert result["elapsed_seconds"] > 30.0


# ---------------------------------------------------------------------------
# _check_token_efficiency
# ---------------------------------------------------------------------------

def test_token_efficiency_passes_with_high_savings():
    telemetry = {
        "prompt": "calculate 2+2",
        "scout_input_tokens": 100,
        "scout_output_tokens": 10,
        "node_input_tokens": 0,
        "node_output_tokens": 0,
        "node_name": "math",
        "scout_token_source": "actual",
        "node_token_source": "deterministic_zero",
    }
    result = _check_token_efficiency(telemetry)
    assert result["pass"] is True
    assert result["savings_ratio"] >= 0.80


def test_token_efficiency_fails_with_low_savings():
    # Simulate a case where arbitrator_in > 80% of monolithic_in
    # Force this by providing huge node tokens so savings_ratio drops
    telemetry = {
        "prompt": "x",
        "scout_input_tokens": 6000,
        "scout_output_tokens": 200,
        "node_input_tokens": 6000,
        "node_output_tokens": 200,
        "node_name": "coding",
        "scout_token_source": "actual",
        "node_token_source": "actual",
    }
    result = _check_token_efficiency(telemetry)
    # arbitrator_in=12000 vs monolithic_in=~13002 => savings ~7.7% < 80%
    assert result["pass"] is False


# ---------------------------------------------------------------------------
# product_agent_node — integration
# ---------------------------------------------------------------------------

def test_product_agent_node_stores_verdicts_and_passes_through():
    mock_ctx = MagicMock()
    telemetry = {
        "timestamp": time.time() - 3.0,
        "prompt": "calculate 2+2",
        "scout_confidence": 90.0,
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
        result = product_agent_node(mock_ctx, "4")

    assert result.output == "4"
    stored = mock_update.call_args[0][0]
    assert "outcome_verdicts" in stored
    assert "outcome_violations" in stored
    assert "outcome_remediation" in stored


def test_product_agent_node_flags_violations():
    mock_ctx = MagicMock()
    telemetry = {
        "timestamp": time.time() - 45.0,  # latency exceeded
        "prompt": "x",
        "scout_confidence": 50.0,          # routing miss
        "scout_tag": "math",
        "node_token_source": "actual",      # deterministic offload miss
        "pii_detected": True,
        "hitl_escalated": False,            # pii miss
        "scout_input_tokens": 0,
        "scout_output_tokens": 0,
        "node_input_tokens": 0,
        "node_output_tokens": 0,
        "scout_token_source": "deterministic_zero",
        "node_name": "math",
    }
    with patch("app.app_utils.product_agent_utils.get_current_telemetry", return_value=telemetry), \
         patch("app.app_utils.product_agent_utils.update_telemetry") as mock_update:
        product_agent_node(mock_ctx, "result")

    stored = mock_update.call_args[0][0]
    violations = stored["outcome_violations"]
    assert "latency" in violations
    assert "routing_confidence" in violations
    assert "pii_compliance" in violations
    assert "deterministic_offload" in violations
    assert len(stored["outcome_remediation"]) == len(violations)


def test_product_agent_node_no_op_when_telemetry_missing():
    mock_ctx = MagicMock()
    with patch("app.app_utils.product_agent_utils.get_current_telemetry", return_value=None):
        result = product_agent_node(mock_ctx, "original_output")
    assert result.output == "original_output"
