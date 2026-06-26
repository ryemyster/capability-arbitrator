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
File: compliance_judge_utils.py
Purpose: Runtime output safety gate that scans execution responses for secret leaks before delivery.
Why it exists: Ensures no API keys, credentials, or private tokens ever reach the end user, and
              enables auto-healing by routing violations back through the router for correction.
How it works: Extracts text from the execution node output, applies regex patterns for common secret
              formats, and routes to 'safe' (telemetry watchdog) or 'retry' (router with an
              enriched prompt that instructs the node to redact and rewrite its response).
"""

import re
from typing import Any

from google.adk.agents.context import Context
from google.adk.events.event import Event
from google.adk.workflow import FunctionNode

from app.app_utils.telemetry import get_current_telemetry

# Secret patterns that should never appear in model outputs
_SECRET_PATTERNS: dict[str, str] = {
    "API Key (Generic)": r"(?i)(api[_\-]?key|apikey)\s*[=:]\s*['\"]?[\w\-]{20,}",
    "Bearer Token": r"(?i)bearer\s+[a-zA-Z0-9\-._~+/]{20,}",
    "Private Key Block": r"-----BEGIN (RSA |EC |OPENSSH )?PRIVATE KEY-----",
    "AWS Access Key": r"AKIA[0-9A-Z]{16}",
    "Google Service Account Key": r"\"private_key\":\s*\"-----BEGIN",
    "GitHub Token": r"ghp_[a-zA-Z0-9]{36}",
    "Slack Token": r"xox[baprs]-[0-9a-zA-Z\-]{10,}",
    "Generic Secret": r"(?i)(secret|password|passwd)\s*[=:]\s*['\"]?[^\s'\"]{8,}",
}


def _extract_text(node_input: Any) -> str:
    """Pull plain text from whatever an execution node returns."""
    if isinstance(node_input, str):
        return node_input
    if isinstance(node_input, dict):
        return str(node_input.get("result", node_input.get("output", str(node_input))))
    if hasattr(node_input, "content") and node_input.content:
        parts = getattr(node_input.content, "parts", [])
        return " ".join(p.text for p in parts if hasattr(p, "text") and p.text)
    return str(node_input)


def _scan_for_secrets(text: str) -> list[str]:
    """Return violation labels for any secret patterns matched in text."""
    return [label for label, pattern in _SECRET_PATTERNS.items() if re.search(pattern, text)]


def compliance_judge_node(ctx: Context, node_input: Any) -> Event:
    """Inspects execution output for secret leaks; routes to 'safe' or 'retry'.

    Think of this like a spell-checker at the exit door. Before the agent's
    answer reaches the user, this node reads it and checks for anything that
    looks like a password, API key, or secret token. If it finds one, it sends
    the agent back to redo its work with clear instructions to remove the leak.
    """
    output_text = _extract_text(node_input)
    violations = _scan_for_secrets(output_text)

    if not violations:
        return Event(output=node_input, route="safe")  # type: ignore[arg-type]

    telemetry = get_current_telemetry()
    original_tag = telemetry.get("scout_tag", "coding") if telemetry else "coding"
    original_prompt = telemetry.get("prompt", "") if telemetry else ""
    violation_summary = ", ".join(violations)

    healed_prompt = (
        f"[COMPLIANCE VIOLATION — AUTO-HEAL REQUIRED]\n"
        f"Your previous response leaked sensitive data: {violation_summary}.\n"
        f"Rewrite your response WITHOUT including any secrets, API keys, tokens, "
        f"or credentials. Replace all sensitive values with '<REDACTED>'.\n\n"
        f"Original request: {original_prompt}"
    )

    return Event(  # type: ignore[arg-type]
        output={"capability_tag": original_tag, "prompt": healed_prompt},
        route="retry",
    )


compliance_judge = FunctionNode(name="compliance_judge", func=compliance_judge_node)
