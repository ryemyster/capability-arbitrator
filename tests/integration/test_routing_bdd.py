"""
File: test_routing_bdd.py
Purpose: Implements pytest-bdd step definitions for behavior-driven arbitrator routing.
Why it exists: Disconnect standard python test loops from the Gherkin specifications to fulfill the Kaggle rubric.
How it works: Resolves user prompts through an InMemoryRunner and asserts routing decisions and final node outputs.
Updated: 2026-06-23T13:17:56-06:00
"""

import asyncio

import pytest
from google.adk.runners import InMemoryRunner
from google.genai import types
from pytest_bdd import given, parsers, scenarios, then, when

from app.agent import app

# Bind Gherkin scenarios
scenarios("features/routing.feature")


@pytest.fixture
def event_loop():
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def runner():
    return InMemoryRunner(app=app)


@pytest.fixture
def test_context():
    return {}


@given("the Capability Arbitrator is active")
def check_active(runner):
    assert runner.app is not None


@when(parsers.parse('the user inputs "{prompt}"'))
def user_input(runner, prompt, test_context):
    # Run async function synchronously in the event loop for pytest compatibility
    async def run():
        session = await runner.session_service.create_session(
            app_name=app.name, user_id="test_user"
        )
        events = []
        async for event in runner.run_async(
            user_id="test_user",
            session_id=session.id,
            new_message=types.Content(
                role="user", parts=[types.Part.from_text(text=prompt)]
            ),
        ):
            events.append(event)
        return events

    test_context["events"] = asyncio.run(run())


@then(parsers.parse('the prompt is routed to the "{tag}" capability'))
def check_routing(test_context, tag):
    events = test_context["events"]
    routes = []
    for e in events:
        # Check explicit route parameter on Event actions
        if (
            hasattr(e, "actions")
            and e.actions
            and hasattr(e.actions, "route")
            and e.actions.route
        ):
            routes.append(e.actions.route)
        # Check custom route metadata on node_info if available
        elif hasattr(e, "route") and e.route:
            routes.append(e.route)

    assert tag in routes


@then("the final response contains a DevOps execution status")
def check_devops_output(test_context):
    events = test_context["events"]
    outputs = []
    for e in events:
        if e.output:
            outputs.append(str(e.output))
        if e.content and e.content.parts:
            outputs.extend(part.text for part in e.content.parts if part.text)
    combined = "\n".join(outputs)
    assert any(x in combined for x in ["DevOps Engine", "STDOUT", "exit_code", "pytest", "verify_code.py"])


@then("the agent yields an interrupt requesting human authorization")
def check_hitl(test_context):
    events = test_context["events"]
    has_interrupt = False
    for e in events:
        if e.content and e.content.parts:
            for part in e.content.parts:
                if (
                    part.function_call
                    and part.function_call.name == "adk_request_input"
                ):
                    has_interrupt = True
                    break
    assert has_interrupt


@then("the final response contains the researcher SOP sections")
def check_researcher_sop(test_context):
    events = test_context["events"]
    outputs = []
    for e in events:
        if e.output:
            outputs.append(str(e.output))
        if e.content and e.content.parts:
            outputs.extend(part.text for part in e.content.parts if part.text)
    combined = "\n".join(outputs)
    assert "Executive Summary" in combined
    assert "Methodology" in combined


@then("the final response contains coding instructions or a code block")
def check_coding_output(test_context):
    events = test_context["events"]
    outputs = []
    for e in events:
        if e.output:
            outputs.append(str(e.output))
        if e.content and e.content.parts:
            outputs.extend(part.text for part in e.content.parts if part.text)
    combined = "\n".join(outputs).lower()
    assert any(
        x in combined
        for x in ["def ", "import ", "python", "code", "function", "ready"]
    )


@then("the final response contains a deterministic math result")
def check_math_output(test_context):
    events = test_context["events"]
    outputs = []
    for e in events:
        if e.output:
            outputs.append(str(e.output))
        if e.content and e.content.parts:
            outputs.extend(part.text for part in e.content.parts if part.text)
    combined = "\n".join(outputs)
    assert "Math Engine result: 10000" in combined
