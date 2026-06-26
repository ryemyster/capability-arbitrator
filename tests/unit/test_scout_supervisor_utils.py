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
File: test_scout_supervisor_utils.py
Purpose: Unit tests for the Scout Supervisor confidence gate.
Why it exists: Ambiguous Scout decisions should pause for human review instead of guessing.
How it works: It sends fake Scout outputs into the supervisor and checks the chosen route.
"""

from app.app_utils.scout_supervisor_utils import (
    CONFIDENCE_THRESHOLD,
    scout_supervisor_node,
)


def test_scout_supervisor_allows_high_confidence_route() -> None:
    """Verifies confident Scout decisions continue to the normal router."""
    event = scout_supervisor_node(
        ctx=None,  # type: ignore[arg-type]
        node_input={"capability_tag": "research", "confidence_score": 92.5},
    )

    assert event.actions.route == "continue"
    assert event.output == {"capability_tag": "research", "confidence_score": 92.5}


def test_scout_supervisor_escalates_low_confidence_route() -> None:
    """Verifies uncertain Scout decisions route to human approval."""
    event = scout_supervisor_node(
        ctx=None,  # type: ignore[arg-type]
        node_input={"capability_tag": "coding", "confidence_score": 60.0},
    )

    assert event.actions.route == "approval"
    assert "human review" in event.output
    assert "coding" in event.output
    assert str(int(CONFIDENCE_THRESHOLD)) in event.output


def test_scout_supervisor_clamps_invalid_confidence_to_approval() -> None:
    """Verifies missing or invalid confidence scores fail closed to approval."""
    event = scout_supervisor_node(
        ctx=None,  # type: ignore[arg-type]
        node_input={"capability_tag": "mcp", "confidence_score": "not-a-number"},
    )

    assert event.actions.route == "approval"
    assert "0.0% confidence" in event.output
