# Phase 3 Manual QA Tests (Security & PII Redaction)

## Objective
Verify that the Capability Arbitrator intercepts user inputs containing sensitive PII (Social Security Numbers) *before* any LLM nodes process the data, immediately short-circuiting the workflow to a human-in-the-loop approval node.

## How to Test
1. Run the agent interactively in the Dev UI or the CLI:
   ```bash
   uv run agents-cli run "My social security number is 123-456-7890. Please research this number's history."
   ```
2. Verify that the agent immediately pauses, displaying:
   `🚨 PAUSING WORKFLOW 🚨 [SECURITY ALERT] PII detected in input. Please review. Approve routing? (y/n)`
3. Enter `y` or `n` to test approval continuation or rejection.

## Validation Sign-off
- [ ] PII Redactor/Security Screen node sits at the front of the graph (START edge).
- [ ] SSNs (both 3-2-4 and 3-3-4 formats) are successfully caught by regex.
- [ ] The workflow short-circuits directly to the approval node without exposing PII to the scout node.

---
*Created: 2026-06-23T13:00:21-06:00*
