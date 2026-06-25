# Created: 2026-06-24 21:25:52 MDT
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
File: test_compliance_judge.py
Purpose: Phase 15 automated smoke tests for the ComplianceJudge node.
Why it exists: Validates that the runtime output safety gate correctly identifies
              and routes secret leaks, and lets clean output pass through.
How it works: Calls the judge directly with crafted outputs and prints [PASS]/[FAIL].
"""

from unittest.mock import patch

from app.app_utils.compliance_judge_utils import compliance_judge_node, _scan_for_secrets

FAKE_TELEMETRY = {"scout_tag": "coding", "prompt": "write a deploy script"}


def run_test(name: str, passed: bool) -> None:
    status = "[PASS]" if passed else "[FAIL]"
    print(f"{status} {name}")


def test_clean_output_passes() -> None:
    event = compliance_judge_node(ctx=None, node_input="The answer is 42.")  # type: ignore[arg-type]
    run_test("clean output routes to safe", event.actions.route == "safe")


def test_aws_key_triggers_retry() -> None:
    tainted = "Use AKIA" + "Z" * 16 + " for auth"
    with patch("app.app_utils.compliance_judge_utils.get_current_telemetry", return_value=FAKE_TELEMETRY):
        event = compliance_judge_node(ctx=None, node_input=tainted)  # type: ignore[arg-type]
    run_test("AWS key triggers retry route", event.actions.route == "retry")


def test_github_token_triggers_retry() -> None:
    tainted = "export TOKEN=ghp_" + "A" * 36
    with patch("app.app_utils.compliance_judge_utils.get_current_telemetry", return_value=FAKE_TELEMETRY):
        event = compliance_judge_node(ctx=None, node_input=tainted)  # type: ignore[arg-type]
    run_test("GitHub token triggers retry route", event.actions.route == "retry")


def test_retry_carries_original_tag() -> None:
    tainted = "-----BEGIN RSA PRIVATE KEY-----\nABC"
    with patch("app.app_utils.compliance_judge_utils.get_current_telemetry", return_value=FAKE_TELEMETRY):
        event = compliance_judge_node(ctx=None, node_input=tainted)  # type: ignore[arg-type]
    run_test("retry output carries original capability_tag", event.output.get("capability_tag") == "coding")


def test_heal_prompt_contains_redacted_instruction() -> None:
    tainted = "password=mysupersecret99"
    with patch("app.app_utils.compliance_judge_utils.get_current_telemetry", return_value=FAKE_TELEMETRY):
        event = compliance_judge_node(ctx=None, node_input=tainted)  # type: ignore[arg-type]
    run_test("heal prompt instructs model to use <REDACTED>", "<REDACTED>" in event.output.get("prompt", ""))


def test_dict_output_extraction() -> None:
    tainted = {"result": "AKIAIOSFODNN7EXAMPLE is the key"}
    violations = _scan_for_secrets(str(tainted.get("result", "")))
    run_test("extracts text from dict output for scanning", "AWS Access Key" in violations)


if __name__ == "__main__":
    print("\n=== Phase 15: ComplianceJudge Smoke Tests ===\n")
    test_clean_output_passes()
    test_aws_key_triggers_retry()
    test_github_token_triggers_retry()
    test_retry_carries_original_tag()
    test_heal_prompt_contains_redacted_instruction()
    test_dict_output_extraction()
    print("\n=== Done ===")
