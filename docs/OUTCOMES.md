# Outcomes & KPI Dashboard Metrics
### Evidence Boundaries, Runtime Signals and Baseline Estimates

This document outlines the performance outcomes, core KPIs, and value metrics tracked by the Capability Arbitrator telemetry suite.

---

## Outcome Readiness Matrix

This table answers the practical question: "What does the current implementation actually support?"

| Outcome | Runtime Support | Eval/Test Support | Current Readiness |
| :--- | :--- | :--- | :--- |
| **Outcome 1: Context Budget Awareness** | Scout records routing metadata, Router executes one selected branch, and Telemetry Watchdog watches tokens/latency. | `token_efficiency`, `latency_seconds`, `watchdog_recovery_compliance`, and dashboard telemetry. | **Prototype-ready.** Token and cost savings are baseline estimates unless token source is marked `actual`. |
| **Outcome 2: High-Fidelity Routing** | Scout, Scout Supervisor, Router, Math Node, DevOps Node, Coding Node, MCP Node, Research Node, and STRIDE Node. | BDD routing tests plus `routing_accuracy`, `scout_confidence_gate`, and `deterministic_offload_accuracy`. | **Ready.** Closed-form math and devops/linter work now have deterministic paths. |
| **Outcome 3: Secure Operations** | Security Screen detects PII before the Scout, Approval Node handles HITL, Compliance Judge scans outputs, and Scout Supervisor escalates low-confidence routes. | PII unit/BDD coverage, the legacy-named `pii_redaction_accuracy` metric, HITL scenario tests, Compliance Judge tests, and Scout Supervisor tests. | **Ready for prototype.** Production deployment should still add external audit logging and policy review. |
| **Outcome 4: Opt-In Improvement Loops** | Quality Flywheel CLI and STRIDE Self-Healing CLI can act on telemetry or STRIDE findings when explicitly enabled. Ambient observers can log signals after telemetry writes. | Unit tests for Flywheel, config loaders, patch-agent utilities, and ambient supervisor behavior. | **Experimental.** Disabled by default; ambient mode observes/logs only in the current implementation. |

The simple rule is: every outcome needs three things to count as real:
1. **A graph behavior** that changes how the agent runs.
2. **A metric** that measures whether the behavior happened.
3. **A test or eval** that keeps the behavior from quietly regressing.

---

## Outcome 1: Reduce Prompt Bloat And Track Context Budget

Monolithic agents often attach many instructions and tool descriptions to every request. Capability Arbitrator reduces that pressure by classifying first, then executing one selected branch.

### What Is Measured vs. Estimated

The telemetry system separates these sources:

* **Actual:** Scout token counts when the GenAI SDK reports usage.
* **Deterministic zero:** Math and DevOps execution paths that do not call an LLM.
* **Estimated:** Execution-node token counts when ADK does not expose downstream LLM usage.
* **Baseline estimate:** Monolithic comparison footprint and dollar savings.

### Key Performance Indicators:

#### 1. Token Saturation Ratio (TSR)
* **Definition:** A target ratio for useful task context versus total prompt context.
* **Target:** `> 85%` useful context saturation.
* **Evidence Level:** Target / evaluation metric. It should not be presented as a production-measured value unless backed by run data.

#### 2. Cost per Execution (CpE)
* **Definition:** The estimated cloud API and token cost per run.
* **Target:** `> 80%` reduction vs. Naive Monolithic Agent.
* **Evidence Level:** Baseline estimate. The implementation currently compares the arbitrator footprint against `prompt_tokens + 13000` monolithic input tokens in telemetry.

---

## Outcome 2: High-Fidelity Task Execution

By routing tasks to dedicated execution branches, the system can choose a better environment for the task: an LLM skill, deterministic Python code, MCP-backed filesystem tools, or human approval.

### Key Performance Indicators:

#### 1. Routing Accuracy & Precision
* **Definition:** The rate at which the lightweight Scout node correctly classifies prompt intent (e.g. `devops`, `coding`, `research`).
* **Target:** `> 95%` routing accuracy.
* **Evidence Level:** Test/eval target. Current quality is checked by BDD tests and LLM-as-a-judge scorecards.

#### 2. Deterministic Offloading Rate
* **Definition:** The percentage of closed-form tasks (math calculations, linter checks) successfully routed to pure Python code, bypassing LLMs.
* **Target:** `100%` accuracy on covered math and DevOps routing cases.
* **Why it matters:** LLMs can struggle with precise math and execution loops. Routing covered closed-form tasks to Python functions gives deterministic behavior and avoids LLM billing for those execution paths.
* **Current implementation:** The `math` capability routes arithmetic to the deterministic Math Node. The `devops` capability routes test, lint, and quality-check prompts to the deterministic DevOps Node. The scorecard metric `deterministic_offload_accuracy` checks both paths.

---

## Outcome 3: Secure & Compliant Operations

Enterprise operations require strict controls around data privacy, ambient permissions, and high-risk executions.

### Key Performance Indicators:

#### 1. Pre-LLM Filter Success Rate
* **Definition:** The percentage of prompts containing configured PII patterns that are detected before reaching the Scout and routed to human approval.
* **Target:** `100%` detection and escalation rate on covered patterns.
* **Why it matters:** Prevents known sensitive input patterns from flowing into normal LLM execution without human review.

#### 2. HITL Escalation Accuracy
* **Definition:** The percentage of high-risk or low-confidence operations correctly suspended for human validation.
* **Target:** `100%` intercept rate on dangerous actions (e.g. database deletes).
* **Why it matters:** Ensures the agent cannot execute irreversible, destructive, or high-cost actions without explicit manager approval.

---

## Telemetry Reporting Infrastructure

These metrics are calculated at runtime by the telemetry logger ([app/app_utils/telemetry.py](../app/app_utils/telemetry.py)) and displayed on the custom dashboard.

The dashboard is intentionally explicit about data provenance:

* **Run source** shows whether the row came from the dashboard playground, Pub/Sub integration, local test runner, or Agent Runtime.
* **Scout token source** is `actual` when the GenAI SDK reports usage and `estimated` when usage metadata is missing.
* **Execution token source** is `deterministic_zero` for Math and DevOps offload, `actual` when a node reports tokens, and `estimated` when ADK does not expose downstream LLM node usage.
* **Monolithic footprint and dollar savings** are baseline estimates used for comparison, not bills from Google Cloud.

## Dashboard Metric Map

The live dashboard is the human-readable view of this file. Its labels should map back to these outcomes and evidence levels.

### Cumulative Efficiency Gains

These cards aggregate all rows currently persisted in `telemetry_db.json`.

| Dashboard Label | Source Fields | Calculation | Outcome Link |
| :--- | :--- | :--- | :--- |
| **Token Savings Rate** | `arbitrator_in_tokens`, `arbitrator_out_tokens`, `monolithic_in_tokens`, `monolithic_out_tokens` | `(total_monolithic_tokens - total_arbitrator_tokens) / total_monolithic_tokens` | Outcome 1: Context Budget Awareness |
| **Est. Financial Savings** | `cost_savings_usd` | Sum of estimated cost savings across telemetry rows | Outcome 1: Cost per Execution estimate |
| **Scout Node TTFT** | `scout_latency` | Average Scout latency across telemetry rows | Outcome 2: Routing latency signal |
| **Deterministic Offload** | `scout_tag` | Percent of runs routed to `math` or `devops` | Outcome 2: Deterministic offload |
| **PII Screens Triggered** | `pii_detected` | Count of telemetry rows where PII detection was true | Outcome 3: PII detection and escalation |
| **HITL Interrupt events** | `hitl_escalated` | Count of telemetry rows where approval was requested | Outcome 3: Human-in-the-loop governance |
| **MCP Tool Actions** | `mcp_tool_calls` | Sum of MCP tool calls recorded in telemetry | Execution observability |

### Latest Run Verified Outcomes

The dashboard also highlights the most recent telemetry row.

| Dashboard Section | Source Fields | Meaning |
| :--- | :--- | :--- |
| **Context Window Efficiency (KPI 1.1)** | `token_savings`, `arbitrator_in_tokens`, `monolithic_in_tokens` | Shows how many baseline tokens the current run avoided under the monolithic estimate. |
| **Reduction Rate** | `arbitrator_in_tokens`, `monolithic_in_tokens` | `(monolithic_in_tokens - arbitrator_in_tokens) / monolithic_in_tokens`. |
| **Tool Bloat Ratio** | `scout_tag` | `0%` for deterministic `math`/`devops`; `20% (1/5 active skills loaded)` for LLM branches in the current dashboard model. |
| **Execution & Quality (KPI 2.1 & 2.2)** | `scout_latency`, `total_latency`, `scout_tag` | Shows classification latency, total run duration and whether the run used deterministic offload or an LLM branch. |

### Stats For Nerds HUD

The HUD is the detailed row inspector for the latest run.

| HUD Label | Telemetry Field |
| :--- | :--- |
| **Run Source** | `run_source` |
| **Scout Model** | Dashboard display label for the configured Scout model |
| **Scout Latency (TTFT)** | `scout_latency` |
| **Active Exec Node** | `node_name` |
| **Exec Node Latency** | `node_latency` |
| **Total Tracing Latency** | `total_latency` |
| **PII Detected** | `pii_detected` |
| **HITL Intercept** | `hitl_escalated` |
| **Scout Context footprint** | `scout_input_tokens` |
| **Scout Token Source** | `scout_token_source` |
| **Exec Node Context footprint** | `node_input_tokens` |
| **Exec Token Source** | `node_token_source` |
| **Total Arbitrator Window** | `arbitrator_in_tokens` |
| **Simulated Monolithic Prompt** | `monolithic_in_tokens` |
| **Context Window Reduction** | `(monolithic_in_tokens - arbitrator_in_tokens) / monolithic_in_tokens` |

### Pricing Assumption

The dashboard uses the same illustrative Gemini Flash pricing assumptions as telemetry:

| Token Type | Rate |
| :--- | :--- |
| Input | `$0.075 / 1M tokens` |
| Output | `$0.30 / 1M tokens` |

These are estimates for comparison. For current billing truth, verify against the linked Vertex AI Gemini pricing page.

The architecture support lives in:

* **Runtime KPI auditing:** [app/app_utils/product_agent_utils.py](../app/app_utils/product_agent_utils.py) — Product KPI Auditor node, wired between the Compliance Judge and Telemetry Watchdog. Checks all five KPI thresholds per transaction and writes `outcome_verdicts`, `outcome_violations`, and `outcome_remediation` into telemetry.
* **Quality Flywheel CLI:** [app/app_utils/flywheel_utils.py](../app/app_utils/flywheel_utils.py) — Offline optimizer. Reads `outcome_violations` from `telemetry_db.json`, generates improved few-shot examples for supported skills via Gemini, validates routing accuracy, and opens a PR when enabled and triggered.
* **STRIDE Self-Healing CLI:** [app/app_utils/patch_agent_utils.py](../app/app_utils/patch_agent_utils.py) — Offline security optimizer. Audits a target file, parses STRIDE findings, generates a patch, verifies it, reverts on failed verification, and opens a PR only in `open_pr` mode.
* **Ambient observer hook:** [app/app_utils/ambient_supervisor.py](../app/app_utils/ambient_supervisor.py) — Experimental telemetry hook called by `save_run()`. It observes/logs Flywheel and STRIDE signals when ambient flags are enabled; it does not patch files or open PRs in the current implementation.
* **Centralised KPI thresholds:** [config/kpi_config.yaml](../config/kpi_config.yaml) — Shared source for product-agent thresholds and Flywheel detection defaults.
* **Surface controls:** [config/quality_flywheel.yaml](../config/quality_flywheel.yaml), [config/stride_self_healing.yaml](../config/stride_self_healing.yaml), and `.env.example` control whether CLI and ambient surfaces are enabled.
* **Graph routing:** [app/agent.py](../app/agent.py)
* **Scout classification:** [app/app_utils/scout_utils.py](../app/app_utils/scout_utils.py)
* **Confidence gate:** [app/app_utils/scout_supervisor_utils.py](../app/app_utils/scout_supervisor_utils.py)
* **Math offload:** [app/app_utils/math_node_utils.py](../app/app_utils/math_node_utils.py)
* **DevOps offload:** [app/app_utils/devops_utils.py](../app/app_utils/devops_utils.py)
* **Eval scorecard:** [tests/eval/eval_config.yaml](../tests/eval/eval_config.yaml)

> [!NOTE]
> **Dashboard Availability:** Run `uv run arbitrator dashboard` and open `http://127.0.0.1:8000/` for the standalone dashboard. Run `uv run uvicorn app.fast_api_app:app --host 127.0.0.1 --port 8000` and open `/dashboard` for the unified FastAPI service.
