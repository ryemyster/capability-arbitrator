"""
File: routing_utils.py
Purpose: Provides utility functions for workflow routing and context message parsing.
Why it exists: Extracts parameters like the original user prompt text from ADK Context objects in a modular way.
How it works: Inspects the Context message parts structure and joins text parts dynamically.
"""

from google.adk.agents.context import Context

def get_prompt_text(ctx: Context) -> str:
    """Helper to retrieve the original user prompt text from the context.
    We need this because down-stream nodes like the math node only receive the route output by default.
    """
    if ctx.user_content and ctx.user_content.parts:
        parts = []
        for p in ctx.user_content.parts:
            if hasattr(p, "text") and p.text:
                parts.append(p.text)
        return " ".join(parts)
    return ""
