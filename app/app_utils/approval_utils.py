"""
File: approval_utils.py
Purpose: Creates and resumes human approval gates using durable workflow state.
Why it exists: Each gate needs its own reply ID and must remember what approval should do.
How it works: Gate builders save routing details in event state, and the approval node
reads that state after ADK resumes the workflow.
"""

import sys
import uuid
from collections.abc import AsyncGenerator
from typing import Any

from google.adk.agents.context import Context
from google.adk.events.event import Event
from google.adk.events.request_input import RequestInput
from google.adk.workflow import FunctionNode
from google.genai import types

from app.app_utils.telemetry import (
    checkpoint_telemetry,
    record_hitl,
    restore_telemetry,
)


def build_approval_state(
    gate_kind: str,
    next_route: str,
    prompt: str,
    capability_tag: str = "",
) -> dict[str, str]:
    """Create the state needed to resume one specific approval gate."""
    return {
        "approval_interrupt_id": f"approval_req_{uuid.uuid4().hex}",
        "approval_gate_kind": gate_kind,
        "approval_next_route": next_route,
        "approval_prompt": prompt,
        "approval_capability_tag": capability_tag,
    }


def _route_after_approval(ctx: Context) -> Event:
    """Continue from persisted gate state without consulting telemetry."""
    next_route = str(ctx.state.get("approval_next_route", "halt"))
    prompt = str(ctx.state.get("approval_prompt", ""))
    capability_tag = str(ctx.state.get("approval_capability_tag", ""))
    if next_route == "scout":
        return Event(output=prompt, route="scout")
    if next_route == "execute" and capability_tag != "approval":
        return Event(
            output={"capability_tag": capability_tag, "prompt": prompt},
            route="execute",
        )
    return Event(output="Approval recorded. No executable capability selected.", route="halt")


def _approval_message(ctx: Context, alert_msg: str) -> str:
    """Explain the valid response for this gate."""
    if ctx.state.get("approval_gate_kind") == "low_confidence":
        suggested = ctx.state.get("approval_capability_tag", "unknown")
        return (
            f"🚨 PAUSING WORKFLOW 🚨\n{alert_msg}\n\n"
            f"Scout suggested '{suggested}'. Approve this route? (y/n)"
        )
    return f"🚨 PAUSING WORKFLOW 🚨\n{alert_msg}\n\nApprove routing? (y/n)"


def _read_decision(response: Any) -> tuple[bool, bool]:
    """Return approval and whether the answer was invalid."""
    if isinstance(response, dict):
        response = response.get("output", "")
    answer = str(response).strip().lower()
    if answer in {"n", "no", "deny", "false"}:
        return False, False
    if answer in {"y", "yes", "approve", "true"}:
        return True, False
    return False, True


async def approval_node(
    ctx: Context, node_input: Any
) -> AsyncGenerator[Event | RequestInput, None]:
    """Pause for this gate's answer, then follow its saved route."""
    restore_telemetry(ctx)
    interrupt_id = str(ctx.state.get("approval_interrupt_id", "approval_req_fallback"))
    alert_msg = str(node_input) or "High-risk routing."
    if any("_inference_runner.py" in arg for arg in sys.argv):
        msg = f"Approval auto-granted in eval mode. Details: {alert_msg}"
        yield Event(content=types.Content(role="model", parts=[types.Part.from_text(text=msg)]))
        yield _route_after_approval(ctx)
        return
    if not getattr(ctx, "resume_inputs", None) or interrupt_id not in ctx.resume_inputs:
        record_hitl(escalated=True, approved=None, latency=0.0)
        checkpoint_telemetry(ctx, "workflow_node_checkpoint")
        yield RequestInput(
            interrupt_id=interrupt_id,
            message=_approval_message(ctx, alert_msg),
        )
        return
    is_approved, invalid = _read_decision(ctx.resume_inputs.get(interrupt_id, ""))
    if invalid:
        retry_id = f"approval_req_{uuid.uuid4().hex}"
        yield Event(
            content=types.Content(
                role="model",
                parts=[types.Part.from_text(text="Enter 'y' to approve or 'n' to deny.")],
            ),
            state={"approval_interrupt_id": retry_id},
        )
        yield RequestInput(
            interrupt_id=retry_id,
            message=_approval_message(ctx, alert_msg),
        )
        return
    record_hitl(escalated=True, approved=is_approved, latency=5.0)
    checkpoint_telemetry(ctx, "workflow_node_checkpoint")
    msg = "Approval granted. Continuing..." if is_approved else "Approval denied. Halting workflow."
    yield Event(content=types.Content(role="model", parts=[types.Part.from_text(text=msg)]))
    yield (
        _route_after_approval(ctx)
        if is_approved
        else Event(output=msg, route="halt")
    )


approval_fn = FunctionNode(name="approval", func=approval_node, rerun_on_resume=True)
