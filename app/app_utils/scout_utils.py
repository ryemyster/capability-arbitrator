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
File: scout_utils.py
Purpose: Builds and runs the Scout intent classifier.
Why it exists: The graph file should wire nodes together, while this module owns Scout-specific logic.
How it works: It creates the structured Scout response schema, prompts Gemini, and returns tag plus confidence.
"""

import json
import time
from typing import Any, Literal

from google import genai
from google.adk.agents.context import Context
from google.adk.events.event import Event
from google.adk.workflow import FunctionNode
from google.genai import types
from pydantic import Field, create_model

from app.app_utils.config_loader import CapabilityDefinition
from app.app_utils.routing_utils import get_prompt_text
from app.app_utils.telemetry import record_scout
from app.app_utils.watchdog_utils import LOCATION, PROJECT_ID
from app.config import MODEL


def _is_dangerous_database_prompt(prompt: str) -> bool:
    """Checks for high-risk database actions that should always require approval."""
    prompt_lower = prompt.lower()
    destructive_words = ["delete", "drop", "wipe", "destroy"]
    database_words = ["database", "db", "production", "prod", "schema"]
    return any(word in prompt_lower for word in destructive_words) and any(
        word in prompt_lower for word in database_words
    )


def _build_scout_instruction(capabilities: list[CapabilityDefinition]) -> str:
    """Builds Scout instructions from the active capability list."""
    lines = [
        "You are the 'Scout' node. Assign a capability tag and a confidence_score from 0 to 100.",
        "Use lower confidence when the prompt could reasonably fit multiple capabilities.",
    ]
    for cap in capabilities:
        lines.append(f"- '{cap.tag}': {cap.description}.")
    return "\n".join(lines)


def _build_scout_schema(capabilities: list[CapabilityDefinition]) -> type[Any]:
    """Creates the structured response schema for Scout output."""
    cap_tags = [cap.tag for cap in capabilities]
    if "approval" not in cap_tags:
        cap_tags.append("approval")

    return create_model(
        "ScoutOutput",
        capability_tag=(
            Literal[tuple(cap_tags)],  # type: ignore
            Field(description="The capability required to handle the user's prompt."),
        ),
        confidence_score=(
            float,
            Field(
                ge=0.0,
                le=100.0,
                description="The Scout's confidence from 0 to 100.",
            ),
        ),
    )


def _parse_scout_payload(response_text: str | None) -> tuple[str, float]:
    """Reads the Scout JSON response and falls back to approval on bad data."""
    tag = "approval"
    confidence = 0.0
    try:
        if response_text:
            payload = json.loads(response_text)
            tag = payload.get("capability_tag", "approval")
            confidence = float(payload.get("confidence_score", 0.0))
    except Exception:
        pass
    return tag, confidence


def _read_usage_tokens(response: Any) -> tuple[int, int]:
    """Extracts input and output token counts from a GenAI response."""
    if not response.usage_metadata:
        return 0, 0
    return (
        response.usage_metadata.prompt_token_count,
        response.usage_metadata.candidates_token_count,
    )


def build_scout_node(capabilities: list[CapabilityDefinition]) -> FunctionNode:
    """Creates the ADK FunctionNode that classifies prompts into capabilities."""
    scout_output = _build_scout_schema(capabilities)
    async def llm_scout_fn(ctx: Context, node_input: Any) -> Event:
        """Classifies the prompt and returns a capability tag plus confidence."""
        prompt = get_prompt_text(ctx) or (str(node_input) if node_input else "")
        if _is_dangerous_database_prompt(prompt):
            record_scout("approval", 0.0, 0, 0, 100.0)
            return Event(
                output={"capability_tag": "approval", "confidence_score": 100.0}
            )

        client = genai.Client(vertexai=True, project=PROJECT_ID, location=LOCATION)
        start_time = time.time()
        response = await client.aio.models.generate_content(
            model=MODEL,
            contents=prompt,
            config=types.GenerateContentConfig(
                system_instruction=_build_scout_instruction(capabilities),
                response_mime_type="application/json",
                response_schema=scout_output,
            ),
        )
        latency = time.time() - start_time

        tag, confidence = _parse_scout_payload(response.text)
        in_tok, out_tok = _read_usage_tokens(response)
        record_scout(tag, latency, in_tok, out_tok, confidence)
        return Event(output={"capability_tag": tag, "confidence_score": confidence})

    return FunctionNode(name="llm_scout", func=llm_scout_fn)
