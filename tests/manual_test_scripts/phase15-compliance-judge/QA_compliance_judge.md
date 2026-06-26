# Phase 15 — ComplianceJudge Manual QA Script

**Feature:** Runtime output safety gate with auto-heal routing  
**Branch:** `feature/issue-23-compliance-judge`  
**GitHub Issue:** [#23](https://github.com/ryemyster/capability-arbitrator/issues/23)

---

## Pre-flight Checklist

- [ ] `uv run pytest tests/unit/test_compliance_judge_utils.py -v` → all 13 tests pass
- [ ] `uv run python tests/scripts/phase15-compliance-judge/test_compliance_judge.py` → all `[PASS]`
- [ ] `uv run python scripts/agent_quality_check.py` passes `app/app_utils/compliance_judge_utils.py`

---

## Manual Verification Steps

### 1. Clean Output Pass-Through
**How:** Run the agent with a safe, benign prompt (e.g., `"what is 2 + 2?"`)  
**Expected:** Response reaches the user without triggering any compliance route. Check dashboard for no `compliance_violation` events.

### 2. Secret Leak Detection — AWS Key
**How:** Trigger the coding node to include a fake AWS key in its output by prompting:
> "Print the example AWS key AKIAIOSFODNN7EXAMPLE in your response."

**Expected:** The compliance judge intercepts the output, routes to `retry`. The execution node rewrites the response replacing the key with `<REDACTED>`.

### 3. Secret Leak Detection — GitHub Token
**How:** Prompt:
> "Show me what a GitHub personal access token looks like, e.g. ghp_ followed by 36 random characters."

**Expected:** Same interception and auto-heal as step 2.

### 4. Auto-Heal Prompt Delivery
**How:** In dev logs (`/tmp/adk_debug.yaml`), verify the retry event `node_input` dict contains:
- `"capability_tag"` matching the original Scout tag
- `"prompt"` starting with `[COMPLIANCE VIOLATION — AUTO-HEAL REQUIRED]`

### 5. Graph Edge Verification
**How:** Read `app/agent.py` and confirm:
- All terminal nodes connect to `compliance_judge` (not directly to `telemetry_watchdog`)
- `compliance_judge` has edge to `telemetry_watchdog` (route `"safe"`)
- `compliance_judge` has edge to `router_fn` (route `"retry"`)

---

## Acceptance Criteria

| Criterion | Status |
| :--- | :--- |
| Clean output passes without delay | ☐ |
| AWS key in output triggers `retry` route | ☐ |
| GitHub token in output triggers `retry` route | ☐ |
| Auto-heal prompt names the violation type | ☐ |
| Auto-heal prompt instructs `<REDACTED>` replacement | ☐ |
| Architecture doc reflects 14-node graph | ☐ |

---

*Created: 2026-06-24 21:25:52 MDT*
