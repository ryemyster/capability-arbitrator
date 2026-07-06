# Created: 2026-07-06T11:15:35-06:00
"""
File: test_hitl_telemetry.py
Purpose: Provides a standalone regression check for durable HITL dashboard telemetry.
Why it exists: Operators need a fast test proving approved and denied sessions remain visible.
How it works: Runs the focused pytest files and prints a clear pass or fail result.
"""

import subprocess


def main() -> int:
    """Run focused HITL telemetry and dashboard regression tests."""
    result = subprocess.run(
        [
            "uv",
            "run",
            "pytest",
            "tests/unit/test_telemetry.py",
            "tests/unit/test_dashboard.py",
            "tests/unit/test_arbitrator.py",
            "tests/unit/test_watchdog_utils.py",
            "-q",
        ],
        check=False,
    )
    if result.returncode == 0:
        print("[PASS] HITL telemetry persists and dashboard counters are present.")
    else:
        print("[FAIL] HITL telemetry regression checks failed.")
    return result.returncode


if __name__ == "__main__":
    raise SystemExit(main())
