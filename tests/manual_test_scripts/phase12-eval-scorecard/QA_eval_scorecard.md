# Phase 12 Manual QA Test Script: Evaluation Scorecard Metrics

## Purpose
This script guides the manual validation of the new capability arbitrator scorecard evaluation metrics (`latency_seconds`, `token_efficiency`, and `pii_redaction_accuracy`).

## Verification Steps
1. Verify the setup of the metrics by running the automated validation test script:
   ```bash
   uv run python tests/scripts/phase12-eval-scorecard/test_eval_scorecard.py
   ```
   Ensure all sub-tests return `[PASS]`.

2. Run the evaluation dataset generation to run the arbitrator on the test suite cases:
   ```bash
   agents-cli eval generate --dataset tests/eval/datasets/routing-eval.json
   ```

3. Perform the evaluation grading step:
   ```bash
   agents-cli eval grade
   ```

4. Confirm that the terminal outputs an **Evaluation Summary** scorecard containing:
   - `latency_seconds` with a valid mean score.
   - `token_efficiency` with a valid mean score.
   - `pii_redaction_accuracy` with a valid mean score (ideally close to 1.0/100%).

5. Verify that the results files are successfully written under `artifacts/grade_results/` in both JSON and HTML formats.

*Created: 2026-06-24T18:28:00-06:00*
