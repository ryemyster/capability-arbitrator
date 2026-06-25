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
File: test_compliance_judge_utils.py
Purpose: Unit tests for the ComplianceJudge runtime output safety gate.
Why it exists: Verify that secret patterns are detected and trigger auto-heal routing.
How it works: Sends clean and tainted execution outputs into the node and checks routes.
"""

from unittest.mock import patch

from app.app_utils.compliance_judge_utils import (
    _extract_text,
    _scan_for_secrets,
    compliance_judge_node,
)


# --- _extract_text ---

def test_extract_text_from_string() -> None:
    assert _extract_text("hello world") == "hello world"


def test_extract_text_from_dict_result_key() -> None:
    assert _extract_text({"result": "some output"}) == "some output"


def test_extract_text_from_dict_output_key() -> None:
    assert _extract_text({"output": "alt output"}) == "alt output"


def test_extract_text_from_unknown_type_falls_back_to_str() -> None:
    result = _extract_text(42)
    assert "42" in result


# --- _scan_for_secrets ---

def test_scan_finds_github_token() -> None:
    text = "Set GH_TOKEN=ghp_" + "A" * 36
    violations = _scan_for_secrets(text)
    assert "GitHub Token" in violations


def test_scan_finds_aws_access_key() -> None:
    text = "Use AKIA" + "A" * 16 + " to authenticate"
    violations = _scan_for_secrets(text)
    assert "AWS Access Key" in violations


def test_scan_finds_private_key_block() -> None:
    text = "-----BEGIN RSA PRIVATE KEY-----\nMIIEowIBAAK..."
    violations = _scan_for_secrets(text)
    assert "Private Key Block" in violations


def test_scan_finds_generic_secret() -> None:
    text = "password=supersecret123"
    violations = _scan_for_secrets(text)
    assert "Generic Secret" in violations


def test_scan_returns_empty_for_clean_output() -> None:
    text = "Here is a summary of your research findings. No secrets here."
    assert _scan_for_secrets(text) == []


# --- compliance_judge_node ---

def test_judge_routes_clean_output_to_safe() -> None:
    """Clean execution output passes through unchanged."""
    clean_output = "The result of 2 + 2 is 4."
    event = compliance_judge_node(ctx=None, node_input=clean_output)  # type: ignore[arg-type]
    assert event.actions.route == "safe"
    assert event.output == clean_output


def test_judge_routes_leaked_secret_to_retry() -> None:
    """Output containing an API key is flagged and routed for auto-healing."""
    tainted = "Your api_key=abcdef1234567890abcdef1234567890 was used."
    with patch(
        "app.app_utils.compliance_judge_utils.get_current_telemetry",
        return_value={"scout_tag": "coding", "prompt": "write a config file"},
    ):
        event = compliance_judge_node(ctx=None, node_input=tainted)  # type: ignore[arg-type]

    assert event.actions.route == "retry"
    assert isinstance(event.output, dict)
    assert event.output["capability_tag"] == "coding"
    assert "COMPLIANCE VIOLATION" in event.output["prompt"]
    assert "<REDACTED>" in event.output["prompt"]


def test_judge_retry_falls_back_to_coding_tag_when_no_telemetry() -> None:
    """Default capability tag is 'coding' when telemetry context is unavailable."""
    tainted = "Token: ghp_" + "B" * 36
    with patch(
        "app.app_utils.compliance_judge_utils.get_current_telemetry",
        return_value=None,
    ):
        event = compliance_judge_node(ctx=None, node_input=tainted)  # type: ignore[arg-type]

    assert event.actions.route == "retry"
    assert event.output["capability_tag"] == "coding"


def test_judge_includes_violation_type_in_heal_prompt() -> None:
    """The auto-heal prompt names the specific secret type detected."""
    tainted = "AKIAIOSFODNN7EXAMPLE is your AWS key"
    with patch(
        "app.app_utils.compliance_judge_utils.get_current_telemetry",
        return_value={"scout_tag": "mcp", "prompt": "fetch config"},
    ):
        event = compliance_judge_node(ctx=None, node_input=tainted)  # type: ignore[arg-type]

    assert "AWS Access Key" in event.output["prompt"]
