# Phase 13 Manual QA Test Script: Telemetry Watchdog

## Purpose
This script guides the manual validation of the Telemetry Watchdog node, which enforces runtime cost, token, and latency budget guardrails.

## Verification Steps
1. Run the automated watchdog validation test script:
   ```bash
   uv run python tests/scripts/phase13-telemetry-watchdog/test_watchdog.py
   ```
   Ensure both sub-tests return `[PASS]`:
   - `Sub-test 1 (Below Threshold Pass-through) [PASS]`
   - `Sub-test 2 (Above Threshold Pruning and Switching) [PASS]`

2. Confirm that when thresholds are violated (e.g., token count exceeding 10,000):
   - The downstream model configuration successfully switches to `gemini-2.0-flash-lite`.
   - The conversation events are pruned and replaced with a single consolidated summary event.

*Created: 2026-06-24T18:35:00-06:00*
