# Phase 16 Manual QA — Product Agent KPI Auditor

**Date:** 2026-06-24  
**Issue:** #20 — Product Agent Layer  
**Node:** `product_agent` (`FunctionNode`, `app/app_utils/product_agent_utils.py`)

---

## Verification Steps

### 1. Confirm graph wiring
```bash
grep -n "product_agent" app/agent.py
```
Expected output should show the import and two edges:
- `compliance_judge → product_agent` (route="safe")
- `product_agent → telemetry_watchdog`

### 2. Run unit tests
```bash
uv run pytest tests/unit/test_product_agent_utils.py -v
```
All 17 tests should pass.

### 3. Run phase smoke tests
```bash
uv run python tests/scripts/phase16-product-agent/test_product_agent.py
```
All 6/6 should report `[PASS]`.

### 4. Verify KPI verdicts appear in telemetry after a run
Start the playground and submit any prompt:
```bash
uv run agents-cli playground
```
Then inspect `telemetry_db.json` — the most recent entry should contain:
```json
{
  "outcome_verdicts": { ... },
  "outcome_violations": [ ... ],
  "outcome_remediation": { ... }
}
```

### 5. Verify violation flags appear for known bad inputs
Submit a prompt that triggers a latency overrun (mock 45s elapsed) or low confidence
routing, then confirm the corresponding key appears in `outcome_violations`.

---

## Acceptance Criteria

| Criterion | Pass Condition |
| :--- | :--- |
| All 5 KPI checks run on every transaction | `outcome_verdicts` has 5 keys in every telemetry row |
| Clean runs produce zero violations | `outcome_violations == []` for happy-path runs |
| Violations list remediation for each failure | `len(outcome_remediation) == len(outcome_violations)` |
| Original output passes through unchanged | `product_agent` does not alter the execution node's response |
| Node is positioned between Compliance Judge and Telemetry Watchdog | Confirmed via `grep -n product_agent app/agent.py` |
