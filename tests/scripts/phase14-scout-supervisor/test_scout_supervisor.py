# Created: 2026-06-24T19:20:32-06:00
"""
File: test_scout_supervisor.py
Purpose: Phase 14 validation script for the Scout Supervisor confidence gate.
Why it exists: Phase testing needs a simple executable proof that ambiguous Scout routing pauses.
How it works: It calls the supervisor with high, low, and invalid confidence scores and prints PASS or FAIL.
"""

import sys

from app.app_utils.scout_supervisor_utils import scout_supervisor_node


def _assert_route(payload: dict[str, object], expected_route: str) -> None:
    """Checks one fake Scout payload against the expected supervisor route."""
    event = scout_supervisor_node(ctx=None, node_input=payload)  # type: ignore[arg-type]
    if event.actions.route != expected_route:
        raise AssertionError(
            f"Expected route {expected_route}, got {event.actions.route}"
        )


def main() -> None:
    """Runs Phase 14 Scout Supervisor checks."""
    print("============================================================")
    print("PHASE 14: SCOUT SUPERVISOR CONFIDENCE VALIDATION")
    print("============================================================")

    try:
        _assert_route(
            {"capability_tag": "research", "confidence_score": 95.0},
            "continue",
        )
        print("Sub-test 1 (High Confidence Continues) [PASS]")

        _assert_route(
            {"capability_tag": "coding", "confidence_score": 62.0},
            "approval",
        )
        print("Sub-test 2 (Low Confidence Approval) [PASS]")

        _assert_route(
            {"capability_tag": "mcp", "confidence_score": "unknown"},
            "approval",
        )
        print("Sub-test 3 (Invalid Confidence Fails Closed) [PASS]")
    except Exception as exc:
        print(f"[FAIL] Scout Supervisor validation failed. Error: {exc}")
        sys.exit(1)

    print("[PASS] Scout Supervisor functionality validated successfully.")
    print("============================================================")


if __name__ == "__main__":
    main()
