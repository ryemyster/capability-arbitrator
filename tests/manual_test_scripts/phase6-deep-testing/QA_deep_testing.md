# Phase 6 Manual QA Tests (Multi-Agent Deep Testing & LLM-as-a-Judge)

## Objective
Verify that the `DeepTester` red-team agent and `OutcomeJudge` LLM-as-a-judge successfully run an autonomous evaluation loop against the Capability Arbitrator, grading metrics like routing accuracy, response quality, and token cost.

## How to Test
1. Run the deep test suite:
   ```bash
   uv run python tests/scripts/phase6-deep-testing/test_deep_testing.py
   ```
2. Verify that:
   - The red-team agent generates complex edge cases.
   - The Capability Arbitrator processes them.
   - The Judge agent scores them and produces a final KPI scorecard summary in the terminal.

## Validation Sign-off
- [ ] DeepTester generates diverse developer prompts.
- [ ] OutcomeJudge parses traces and grades metrics accurately.
- [ ] Test loop completes automatically and produces score metrics.

---
*Created: 2026-06-24T11:38:38-06:00*
