# Phase 17 Manual QA — Quality Flywheel Offline Optimizer

**Date:** 2026-06-25
**Issue:** #18 — Autonomic Quality Flywheel & Self-Healing Prompt Optimizer

---

## Verification Steps

### 1. Confirm KPI config file is present
```bash
cat config/kpi_config.yaml
```
Expected: shows `product_agent` and `flywheel` sections with thresholds.

### 2. Run unit tests
```bash
uv run pytest tests/unit/test_flywheel_utils.py -v
```
All tests should pass (LLM calls are mocked).

### 3. Run phase smoke tests
```bash
uv run python tests/scripts/phase17-quality-flywheel/test_flywheel.py
```
All 6/6 should report `[PASS]`.

### 4. Confirm previous unit tests still pass (product_agent_utils now uses kpi_config_loader)
```bash
uv run pytest tests/unit/test_product_agent_utils.py -v
```
All 17 tests should pass.

### 5. Verify flywheel CLI is registered
```bash
uv run agents-cli flywheel --help
```
Expected output should show `--window`, `--threshold`, and `--dry-run` flags.

### 6. Dry-run with seeded violations
Seed `telemetry_db.json` with 4 stride routing_confidence violations:
```bash
python - <<'EOF'
import json, time
db = [{"scout_tag": "stride", "outcome_violations": ["routing_confidence"], "timestamp": time.time()} for _ in range(4)]
with open("telemetry_db.json", "w") as f:
    json.dump(db, f, indent=2)
EOF
```
Then run the dry-run:
```bash
uv run agents-cli flywheel --dry-run
```
Expected: prints detected tag (`stride`), shows generated example input, exits without writing files.

### 7. Full flywheel run (requires LLM API access + GitHub auth)
With the seeded violations:
```bash
uv run agents-cli flywheel
```
Expected sequence:
1. Detects stride violations
2. Calls Gemini to generate a new example
3. Appends to `app/skills/stride/few_shots.json` (now 3 examples)
4. Runs phase6 deep-testing validation
5. If accuracy >= 60%: creates branch `flywheel/optimize-stride-<date>` and opens PR to `develop`
6. If accuracy < 60%: reverts `few_shots.json` and exits with code 1

---

## Acceptance Criteria

| Criterion | Pass Condition |
| :--- | :--- |
| KPI thresholds live in `config/kpi_config.yaml` | File exists; product_agent_utils and flywheel_utils both read from it |
| Flywheel detects violations from telemetry | `detect_violations()` returns affected tags for ≥ threshold violations |
| Non-optimizable tags excluded | `math`, `devops` never appear in flywheel output |
| Validation gate works | Flywheel reverts and exits non-zero when deep-testing accuracy < 60% |
| Dry-run leaves no files changed | No writes to `few_shots.json`, no git activity |
| Happy path opens PR to develop | `app/skills/stride/few_shots.json` gains one example; PR URL printed |
