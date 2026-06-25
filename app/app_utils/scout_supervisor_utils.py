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
File: scout_supervisor_utils.py
Purpose: Checks Scout routing confidence before the prompt reaches execution nodes.
Why it exists: Ambiguous routing should pause for a human instead of guessing.
How it works: It reads the Scout tag and confidence score, then routes low-confidence
              decisions to approval and high-confidence decisions to the router.
"""

from typing import Any

from google.adk.agents.context import Context
from google.adk.events.event import Event
from google.adk.workflow import FunctionNode

CONFIDENCE_THRESHOLD = 75.0


def _read_confidence(node_input: Any) -> float:
    """Extracts a confidence score and clamps it to a 0-100 range."""
    if isinstance(node_input, dict):
        raw_score = node_input.get("confidence_score", 0.0)
    else:
        raw_score = getattr(node_input, "confidence_score", 0.0)

    try:
        score = float(raw_score)
    except (TypeError, ValueError):
        score = 0.0

    return max(0.0, min(score, 100.0))


def _read_capability_tag(node_input: Any) -> str:
    """Extracts the Scout capability tag from a dict or structured object."""
    if isinstance(node_input, dict):
        return str(node_input.get("capability_tag", "approval"))
    return str(getattr(node_input, "capability_tag", "approval"))


def scout_supervisor_node(ctx: Context, node_input: Any) -> Event:
    """Routes low-confidence Scout decisions to human approval."""
    tag = _read_capability_tag(node_input)
    confidence = _read_confidence(node_input)

    if confidence < CONFIDENCE_THRESHOLD:
        summary = (
            "Scout Supervisor requires human review: "
            f"Scout selected '{tag}' with {confidence:.1f}% confidence, "
            f"below the {CONFIDENCE_THRESHOLD:.0f}% approval threshold."
        )
        return Event(output=summary, route="approval")  # type: ignore[arg-type]

    return Event(output={"capability_tag": tag, "confidence_score": confidence}, route="continue")  # type: ignore[arg-type]


scout_supervisor = FunctionNode(
    name="scout_supervisor",
    func=scout_supervisor_node,
)
