"""
File: test_agent.py
Purpose: Implements BDD tests for agent streaming behavior using Gherkin.
Why it exists: Enforces Gherkin BDD coverage across all integration tests.
How it works: Runs the agent with StreamingMode enabled and asserts that SSE chunks contain valid model text.
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
from pytest_bdd import given, when, then, scenarios
from google.adk.agents.run_config import RunConfig, StreamingMode
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.genai import types

from app.agent import root_agent

# Bind Gherkin scenarios
scenarios("features/agent_stream.feature")


@pytest.fixture
def session_service() -> InMemorySessionService:
    return InMemorySessionService()


@pytest.fixture
def runner(session_service: InMemorySessionService) -> Runner:
    return Runner(agent=root_agent, session_service=session_service, app_name="test")


@pytest.fixture
def test_context() -> dict:
    return {}


@given("the Capability Arbitrator is active")
def check_active(runner: Runner) -> None:
    assert runner.agent is not None


@when('the user requests streaming for "Why is the sky blue?"')
def request_streaming(runner: Runner, test_context: dict) -> None:
    session_service = runner.session_service
    session = session_service.create_session_sync(user_id="test_user", app_name="test")
    message = types.Content(
        role="user", parts=[types.Part.from_text(text="Why is the sky blue?")]
    )
    events = list(
        runner.run(
            new_message=message,
            user_id="test_user",
            session_id=session.id,
            run_config=RunConfig(streaming_mode=StreamingMode.SSE),
        )
    )
    test_context["events"] = events


@then("the agent returns at least one streaming response chunk containing text")
def verify_streaming_chunks(test_context: dict) -> None:
    events = test_context["events"]
    assert len(events) > 0, "Expected at least one event in stream"
    
    has_text_content = False
    for event in events:
        if (
            event.content
            and event.content.parts
            and any(part.text for part in event.content.parts)
        ):
            has_text_content = True
            break
    assert has_text_content, "Expected at least one event containing text content"
