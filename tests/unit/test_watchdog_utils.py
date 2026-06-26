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
File: test_watchdog_utils.py
Purpose: Unit tests for the TelemetryWatchdog runtime budget guardrail.
Why it exists: The watchdog protects the graph from long, expensive, or oversized runs.
How it works: It mocks ADK session events so threshold behavior can be tested offline.
"""

from types import SimpleNamespace
from typing import Any

import pytest
from google.adk.events.event import Event
from google.genai import types

from app.app_utils import telemetry
from app.app_utils.watchdog_utils import (
    CHEAPER_MODEL,
    global_model,
    telemetry_watchdog_fn,
)


def _event(text: str, tokens: int, author: str = "user") -> Event:
    """Builds an ADK event with fake token usage for watchdog tests."""
    return Event(
        author=author,
        content=types.Content(parts=[types.Part.from_text(text=text)]),
        usage_metadata=types.GenerateContentResponseUsageMetadata(
            total_token_count=tokens
        ),
    )


def _context(events: list[Event]) -> Any:
    """Builds the small context shape the watchdog reads during execution."""
    return SimpleNamespace(session=SimpleNamespace(events=events))


@pytest.mark.asyncio
async def test_watchdog_remains_idle_below_budget(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Verifies normal runs pass through without pruning or model switching."""
    starting_model = "gemini-test-start"
    global_model.model = starting_model
    monkeypatch.setattr(telemetry, "get_current_telemetry", lambda: {"timestamp": 99.0})
    monkeypatch.setattr("app.app_utils.watchdog_utils.time.time", lambda: 100.0)

    ctx = _context([_event("short prompt", 100)])
    result = await telemetry_watchdog_fn(ctx, "normal output")

    assert result.output == "normal output"
    assert len(ctx.session.events) == 1
    assert global_model.model == starting_model


@pytest.mark.asyncio
async def test_watchdog_prunes_and_switches_model_above_token_budget(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Verifies token overruns trigger context pruning and cheaper model fallback."""

    async def fake_summarize(*_args: Any, **_kwargs: Any) -> str:
        return "summary of the oversized conversation"

    global_model.model = "gemini-test-start"
    monkeypatch.setattr(telemetry, "get_current_telemetry", lambda: {"timestamp": 99.0})
    monkeypatch.setattr(
        "app.app_utils.watchdog_utils.summarize_prior_turns",
        fake_summarize,
    )

    ctx = _context(
        [
            _event("large prompt", 7000, author="user"),
            _event("large response", 5000, author="model"),
        ]
    )

    result = await telemetry_watchdog_fn(ctx, "oversized output")

    assert result.output == "oversized output"
    assert global_model.model == CHEAPER_MODEL
    assert len(ctx.session.events) == 1
    pruned_text = ctx.session.events[0].content.parts[0].text
    assert "[CONTEXT PRUNED" in pruned_text
    assert "summary of the oversized conversation" in pruned_text


@pytest.mark.asyncio
async def test_watchdog_switches_model_above_latency_budget(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Verifies slow runs trigger the cheaper model fallback even with low tokens."""
    global_model.model = "gemini-test-start"
    monkeypatch.setattr(telemetry, "get_current_telemetry", lambda: {"timestamp": 1.0})
    monkeypatch.setattr("app.app_utils.watchdog_utils.time.time", lambda: 40.5)

    ctx = _context([_event("slow prompt", 100)])
    await telemetry_watchdog_fn(ctx, "slow output")

    assert global_model.model == CHEAPER_MODEL
    assert len(ctx.session.events) == 1
