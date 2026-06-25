"""
File: math_node_utils.py
Purpose: Provides the deterministic Math workflow node.
Why it exists: Simple arithmetic should be solved by Python code instead of spending LLM tokens.
How it works: Extracts the user prompt, runs the safe math helper, records zero-token execution telemetry, and returns the result.
"""

import time
from typing import Any

from google.adk.agents.context import Context
from google.adk.events.event import Event
from google.adk.workflow import FunctionNode
from google.genai import types

from app.app_utils.math_utils import solve_math
from app.app_utils.routing_utils import get_prompt_text
from app.app_utils.telemetry import record_node_execution


def math_node(ctx: Context, node_input: Any) -> Event:
    """Solve closed-form math prompts without calling an LLM."""
    started = time.time()
    prompt = get_prompt_text(ctx) or str(node_input)
    result = solve_math(prompt)
    latency = time.time() - started
    record_node_execution("math", latency, 0, 0)

    message = f"Math Engine result: {result}"
    return Event(
        content=types.Content(
            role="model",
            parts=[types.Part.from_text(text=message)],
        ),
        output=message,
    )


math_fn = FunctionNode(name="math", func=math_node)
