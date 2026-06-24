"""
File: test_agent_runtime_app.py
Purpose: Implements Gherkin BDD step definitions for the Agent Runtime App.
Why it exists: Enforces BDD Gherkin usage for all integration tests.
How it works: Resolves step scenarios for streaming queries and user feedback registration.
"""

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

import pytest
from pytest_bdd import given, when, then, scenarios, parsers
from google.adk.events.event import Event
from app.agent_runtime_app import AgentEngineApp

# Bind Gherkin scenarios
scenarios("features/agent_runtime.feature")


@pytest.fixture
def agent_app(monkeypatch: pytest.MonkeyPatch) -> AgentEngineApp:
    """Fixture to create and set up AgentEngineApp instance"""
    monkeypatch.setenv("INTEGRATION_TEST", "TRUE")
    from app.agent_runtime_app import agent_runtime
    agent_runtime.set_up()
    return agent_runtime


@pytest.fixture
def test_context() -> dict:
    return {}


@given("the Agent Runtime App is active")
def check_app_active(agent_app: AgentEngineApp) -> None:
    assert agent_app is not None


@when(parsers.parse('the user sends a stream query "{query}"'))
def send_stream_query(agent_app: AgentEngineApp, query: str, test_context: dict) -> None:
    import asyncio
    async def run() -> list:
        events = []
        async for event in agent_app.async_stream_query(message=query, user_id="test"):
            events.append(event)
        return events
    test_context["events"] = asyncio.run(run())


@then("the runtime app returns a streaming response with text")
def verify_app_stream_text(test_context: dict) -> None:
    events = test_context["events"]
    assert len(events) > 0, "Expected at least one chunk in response"

    has_text_content = False
    for event in events:
        validated_event = Event.model_validate(event)
        content = validated_event.content
        if (
            content is not None
            and content.parts
            and any(part.text for part in content.parts)
        ):
            has_text_content = True
            break

    assert has_text_content, "Expected at least one event with text content"


@when(parsers.parse('the user submits valid feedback score {score:d} and text "{text}"'))
def submit_valid_feedback(agent_app: AgentEngineApp, score: int, text: str, test_context: dict) -> None:
    test_context["feedback_data"] = {
        "score": score,
        "text": text,
        "user_id": "test-user-456",
        "session_id": "test-session-456",
    }


@then("the feedback is successfully registered")
def verify_feedback_registered(agent_app: AgentEngineApp, test_context: dict) -> None:
    # Should not raise any exceptions
    agent_app.register_feedback(test_context["feedback_data"])


@then(parsers.parse('submitting feedback with invalid score "{invalid_score}" raises a value error'))
def verify_invalid_feedback(agent_app: AgentEngineApp, invalid_score: str) -> None:
    with pytest.raises(ValueError):
        invalid_feedback = {
            "score": invalid_score,
            "text": "Bad feedback",
            "user_id": "test-user-789",
            "session_id": "test-session-789",
        }
        agent_app.register_feedback(invalid_feedback)
