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
Unit tests for the Capability Arbitrator core helper functions in app/agent.py.
Tests deterministic math solving, prompt parsing, and skill instruction loading.
"""

from unittest.mock import MagicMock

from app.agent import security_screen
from app.app_utils.routing_utils import get_prompt_text
from app.app_utils.math_utils import solve_math
from app.app_utils.skill_utils import load_skill_instructions


def test_solve_math_operations() -> None:
    """Verifies deterministic math solving for different arithmetic operations."""
    assert solve_math("What is 2500 multiplied by 4?") == "10000"
    assert solve_math("what is 15 plus 30") == "45"
    assert solve_math("100 minus 25") == "75"
    assert solve_math("50 divided by 2") == "25"
    assert solve_math("50 divided by 0") == "Error evaluating math expression: division by zero"
    assert solve_math("WHats 9000 / 45 + 62 * pi") == "394.7787445226"
    assert solve_math("unparsable text here") == "Could not parse math expression."


def test_get_prompt_text_extraction() -> None:
    """Tests the helper function for extracting user prompt text from Context."""
    # Mocking Context and parts
    mock_part = MagicMock()
    mock_part.text = "Tell me a joke"

    mock_content = MagicMock()
    mock_content.parts = [mock_part]

    mock_ctx = MagicMock()
    mock_ctx.user_content = mock_content

    assert get_prompt_text(mock_ctx) == "Tell me a joke"


def test_load_researcher_instructions() -> None:
    """Verifies that the researcher SOP is correctly loaded or falls back gracefully."""
    instructions = load_skill_instructions("researcher")
    assert instructions is not None
    # Check that either the fallback or actual SOP markdown is returned
    assert "research" in instructions.lower() or "sop" in instructions.lower()


def test_load_stride_instructions() -> None:
    """Verifies that the STRIDE threat modeling SOP is correctly loaded or falls back gracefully."""
    instructions = load_skill_instructions("stride")
    assert instructions is not None
    assert "stride" in instructions.lower() or "sop" in instructions.lower()


def test_security_screen_pii_detection() -> None:
    """Verifies that the security_screen node correctly detects and tags different types of PII."""
    # Clean input
    event_safe = security_screen._func("What is 10 plus 20?")
    assert event_safe.actions.route == "safe"
    assert event_safe.output == "What is 10 plus 20?"

    # SSN
    event_ssn = security_screen._func("My SSN is 123-45-6789.")
    assert event_ssn.actions.route == "approval"
    assert "Social Security Number" in event_ssn.output

    # Email
    event_email = security_screen._func("Contact me at user@example.com for details.")
    assert event_email.actions.route == "approval"
    assert "Email Address" in event_email.output

    # Phone
    event_phone = security_screen._func("Call 123-456-7890 immediately.")
    assert event_phone.actions.route == "approval"
    assert "Phone Number" in event_phone.output

    # Credit Card
    event_cc = security_screen._func("My card is 1111-2222-3333-4444.")
    assert event_cc.actions.route == "approval"
    assert "Credit Card Number" in event_cc.output

    # IP Address
    event_ip = security_screen._func("The server IP is 192.168.1.1.")
    assert event_ip.actions.route == "approval"
    assert "IP Address" in event_ip.output
