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
File: watchdog_utils.py
Purpose: Implements the TelemetryWatchdog workflow node and conversation history summarization.
Why it exists: To prevent execution budget overruns (latency, tokens, cost) and perform dynamic context pruning.
How it works: Inspects session events for cumulative token counts and elapsed time. If thresholds are exceeded,
             summarizes past turns and configures the global LLM model to a cheaper fallback.
"""

import time
import os
from typing import Any
from functools import cached_property
from google import genai
from google.adk.agents.context import Context
from google.adk.events.event import Event
from google.adk.workflow import FunctionNode
from google.adk.models.google_llm import Gemini
from google.genai import types
from app.config import MODEL

PROJECT_ID = os.environ.get("GOOGLE_CLOUD_PROJECT", "kaggle-capstone-500322")
LOCATION = os.environ.get("GOOGLE_CLOUD_LOCATION", "global")
CHEAPER_MODEL = "gemini-2.0-flash-lite"

class GlobalGemini(Gemini):
    @cached_property
    def api_client(self) -> genai.Client:
        return genai.Client(vertexai=True, project=PROJECT_ID, location=LOCATION)

global_model = GlobalGemini(model=MODEL)

async def summarize_prior_turns(
    ctx: Context,
    model_name: str,
    project_id: str,
    location: str
) -> str:
    """Helper to summarize prior conversation turns using GenAI Client.
    
    Args:
        ctx: The ADK agent workflow context.
        model_name: The current model identifier.
        project_id: The Google Cloud project ID.
        location: The API endpoint region.
        
    Returns:
        A concise summary string of the conversation history.
    """
    history_texts: list[str] = []
    # Collect texts from all events in the conversation history
    for event in ctx.session.events:
        author = event.author or "unknown"
        if event.content and event.content.parts:
            for p in event.content.parts:
                if hasattr(p, "text") and p.text:
                    history_texts.append(f"{author}: {p.text}")
                    
    if not history_texts:
        return "No history."
    full_text = "\n".join(history_texts)
    
    # Instantiate client and call Gemini to summarize
    client = genai.Client(vertexai=True, project=project_id, location=location)
    prompt = f"Summarize this conversation history concisely for context retention:\n\n{full_text}"
    response = await client.aio.models.generate_content(
        model=model_name,
        contents=prompt
    )
    return response.text or "Summary of conversation history."

async def telemetry_watchdog_fn(ctx: Context, node_input: Any) -> Event:
    """Watchdog node that monitors execution cost, latency, and tokens, taking corrective actions if needed."""
    # 1. Sum up all tokens used so far in the session
    total_tokens = 0
    for e in ctx.session.events:
        if e.usage_metadata:
            total_tokens += e.usage_metadata.total_token_count or 0
            
    # 2. Retrieve elapsed time since request started
    from app.app_utils.telemetry import get_current_telemetry
    telemetry = get_current_telemetry()
    elapsed = 0.0
    if telemetry and "timestamp" in telemetry:
        elapsed = time.time() - telemetry["timestamp"]
    else:
        elapsed = time.time() - (ctx.session.events[0].timestamp if ctx.session.events else time.time())
        
    # Check thresholds: 10,000 tokens or 30 seconds
    token_exceeded = total_tokens > 10000
    latency_exceeded = elapsed > 30.0
    
    if token_exceeded or latency_exceeded:
        # Dynamically trigger context pruning if there are prior turns
        if len(ctx.session.events) > 1:
            try:
                summary = await summarize_prior_turns(ctx, MODEL, PROJECT_ID, LOCATION)
                summary_event = Event(
                    author="system",
                    content=types.Content(
                        role="model",
                        parts=[types.Part.from_text(text=f"[CONTEXT PRUNED - Summary of prior conversation]: {summary}")]
                    )
                )
                ctx.session.events = [summary_event]
            except Exception:
                pass
                
        # Switch model configuration to a cheaper/faster model for the remainder of the session
        global_model.model = CHEAPER_MODEL
        
    if isinstance(node_input, Event):
        return node_input
    return Event(output=node_input)

telemetry_watchdog = FunctionNode(name="telemetry_watchdog", func=telemetry_watchdog_fn)
