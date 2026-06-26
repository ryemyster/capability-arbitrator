# Created: 2026-06-24T18:35:00-06:00
"""
File: test_watchdog.py
Purpose: Executable test script for validating the TelemetryWatchdog node and behavior.
Why it exists: Part of the Phase Completion Verification Workflow for Phase 13.
How it works: Mocks the ADK Context and Session events to trigger threshold violations, verifying that
             the watchdog correctly prunes the context and switches downstream models.
"""
import sys
import os
import asyncio
from unittest.mock import MagicMock, AsyncMock, patch

# Add project root to python path
sys.path.insert(0, "/Users/rmcdonald/Repos/agy-cli-projects/capability-arbitrator")

from app.app_utils.watchdog_utils import telemetry_watchdog_fn, global_model
from google.adk.events.event import Event
from google.genai import types

async def run_watchdog_test() -> None:
    print("============================================================")
    print("PHASE 13: TELEMETRY WATCHDOG NODE VALIDATION")
    print("============================================================")
    
    try:
        # Test 1: Below threshold behavior
        mock_ctx_below = MagicMock()
        mock_ctx_below.session = MagicMock()
        
        # Create normal events with low token counts
        normal_event = Event(
            author="user",
            content=types.Content(parts=[types.Part.from_text(text="Hello")]),
            usage_metadata=types.GenerateContentResponseUsageMetadata(total_token_count=100)
        )
        mock_ctx_below.session.events = [normal_event]
        
        # Reset model
        global_model.model = "gemini-3.1-flash-lite"
        
        # Run watchdog
        res = await telemetry_watchdog_fn(mock_ctx_below, "test_input")
        assert global_model.model == "gemini-3.1-flash-lite", "Model should not have changed"
        assert len(mock_ctx_below.session.events) == 1, "Context should not have been pruned"
        print("Sub-test 1 (Below Threshold Pass-through) [PASS]")
        
        # Test 2: Above threshold triggering model switch and context pruning
        mock_ctx_above = MagicMock()
        mock_ctx_above.session = MagicMock()
        
        # Create events with high token count (e.g. 15,000 tokens)
        large_event_1 = Event(
            author="user",
            content=types.Content(parts=[types.Part.from_text(text="A massive prompt...")]),
            usage_metadata=types.GenerateContentResponseUsageMetadata(total_token_count=8000)
        )
        large_event_2 = Event(
            author="model",
            content=types.Content(parts=[types.Part.from_text(text="A massive response...")]),
            usage_metadata=types.GenerateContentResponseUsageMetadata(total_token_count=7000)
        )
        mock_ctx_above.session.events = [large_event_1, large_event_2]
        
        # Mock genai.Client inside the summarize helper
        mock_response = MagicMock()
        mock_response.text = "This is a summary of the conversation."
        
        mock_client = MagicMock()
        mock_client.aio.models.generate_content = AsyncMock(return_value=mock_response)
        
        with patch("google.genai.Client", return_value=mock_client):
            res_above = await telemetry_watchdog_fn(mock_ctx_above, "test_input")
            
        assert global_model.model == "gemini-2.0-flash-lite", f"Expected gemini-2.0-flash-lite, got {global_model.model}"
        assert len(mock_ctx_above.session.events) == 1, f"Expected 1 pruned event, got {len(mock_ctx_above.session.events)}"
        assert "[CONTEXT PRUNED" in mock_ctx_above.session.events[0].content.parts[0].text, "Event should contain context pruned text"
        print("Sub-test 2 (Above Threshold Pruning and Switching) [PASS]")
        
        print("[PASS] Telemetry Watchdog functionality validated successfully.")
        
    except Exception as e:
        print(f"[FAIL] Telemetry Watchdog validation failed. Error: {e}")
        sys.exit(1)
        
    print("============================================================")

if __name__ == "__main__":
    asyncio.run(run_watchdog_test())
