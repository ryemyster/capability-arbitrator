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


def decode_pubsub_payload(data: str) -> str:
    """Decodes base64 data and extracts prompt string or JSON prompt.

    Args:
        data: The base64-encoded string from Pub/Sub.

    Returns:
        The extracted prompt string.
    """
    import base64
    import json
    decoded_str = base64.b64decode(data).decode("utf-8")
    try:
        data_json = json.loads(decoded_str)
        if isinstance(data_json, dict) and "prompt" in data_json:
            return str(data_json["prompt"])
    except (json.JSONDecodeError, TypeError):
        pass
    return decoded_str

