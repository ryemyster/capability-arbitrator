# QA Manual Verification: Scout Supervisor Confidence Gate

This checklist verifies that the Scout Supervisor sits after the Scout node and pauses ambiguous routing decisions before they reach execution nodes.

## Why

The Scout can sometimes be unsure which capability should handle a prompt. The Scout Supervisor prevents guesses by sending low-confidence decisions to human approval.

## What

The expected flow is:

1. `security_screen` clears the prompt.
2. `llm_scout` selects a capability and emits `confidence_score`.
3. `scout_supervisor` checks the score.
4. Scores below `75%` route to `approval`.
5. Scores at or above `75%` continue to the normal router.

## How to Verify

1. Run the automated Phase 14 script:
   ```bash
   uv run python tests/scripts/phase14-scout-supervisor/test_scout_supervisor.py
   ```
2. Confirm the terminal output includes:
   - `[PASS] High Confidence Continues`
   - `[PASS] Low Confidence Approval`
   - `[PASS] Invalid Confidence Fails Closed`
3. Run the focused unit tests:
   ```bash
   uv run pytest tests/unit/test_scout_supervisor_utils.py
   ```
4. Optional manual playground check:
   ```bash
   agents-cli playground
   ```
   Use prompts that could fit multiple routes, such as:
   - `Can you inspect my repo and explain whether the auth flow is secure?`
   - `Review this deployment script and tell me if it needs code changes.`

## Expected Result

- Clear prompts still route normally when Scout confidence is high.
- Ambiguous prompts pause for human review when Scout confidence is low.
- The user sees an approval request instead of silent routing to the wrong node.

## Sign-Off

- [ ] Phase 14 script passes.
- [ ] Focused unit tests pass.
- [ ] Ambiguous prompt behavior is understandable in the terminal or playground.
- [ ] No model name was changed while implementing the supervisor.

*Created: 2026-06-24T19:20:32-06:00*
