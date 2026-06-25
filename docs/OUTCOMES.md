# Performance Outcomes & KPI Dashboard Metrics
### Value Realization and Resource Savings

This document outlines the performance outcomes, core KPIs, and value metrics tracked by the Capability Arbitrator telemetry suite.

---

## Outcome Readiness Matrix

This table answers the practical question: "Can the current architecture actually drive these outcomes?"

| Outcome | Runtime Support | Eval/Test Support | Current Readiness |
| :--- | :--- | :--- | :--- |
| **Outcome 1: Context Rot Reduction** | Scout loads a small capability menu, Router loads only the selected branch, and Telemetry Watchdog watches tokens/latency. | `token_efficiency`, `latency_seconds`, `watchdog_recovery_compliance`, and dashboard telemetry. | **Ready.** The system measures token savings and has a budget guardrail. |
| **Outcome 2: High-Fidelity Routing** | Scout, Scout Supervisor, Router, Math Node, DevOps Node, Coding Node, MCP Node, Research Node, and STRIDE Node. | BDD routing tests plus `routing_accuracy`, `scout_confidence_gate`, and `deterministic_offload_accuracy`. | **Ready.** Closed-form math and devops/linter work now have deterministic paths. |
| **Outcome 3: Secure Operations** | Security Screen blocks PII before the Scout, Approval Node handles HITL, and Scout Supervisor escalates low-confidence routes. | PII unit/BDD coverage, `pii_redaction_accuracy`, HITL scenario tests, and Scout Supervisor tests. | **Ready for prototype.** Production deployment should still add external audit logging and policy review. |

The simple rule is: every outcome needs three things to count as real:
1. **A graph behavior** that changes how the agent runs.
2. **A metric** that measures whether the behavior happened.
3. **A test or eval** that keeps the behavior from quietly regressing.

---

## ⚡ Outcome 1: Eradicate "Context Rot" & Maximize the Reasoning Budget

Monolithic agents load all system rules and tool descriptions into memory upfront. This eats up active context, degrades logic reasoning, and increases API costs. The Capability Arbitrator resolves this by loading tools dynamically via **Progressive Disclosure**.

### Root Cause Resolution vs. Symptom Workarounds

The reason this architecture is fundamentally better than workarounds like token compression, proxying, or shrinking is because it attacks the root cause of the problem rather than just treating the symptoms.

The industry has been treating LLMs like digital hoarders, dumping thousands of tokens of instructions into a single, massive system prompt. The common workaround is trying to compress or shrink that massive payload so it fits into the context window. However, the problem with shrinking or compressing tokens is that the model still has to hold all of those irrelevant instructions in its active memory.

When irrelevant instructions saturate the context window, the model's reasoning degrades, leading to high latency, financial waste, and hallucinations—a problem known as **"Context Rot"** or **"Tool Bloat"**.

The Capability Arbitrator addresses this via **Agent Skills** and **Progressive Disclosure**:

*   **Preserving the "Reasoning Budget":** Instead of forcing the model to process compressed tokens of every possible tool, this architecture only exposes the model to a lightweight "menu" of metadata. The heavy procedural knowledge (the actual `SKILL.md` instructions and scripts) is only loaded at the exact moment the Scout node triggers it. This preserves the model's cognitive overhead entirely for solving the actual problem rather than trying to parse bloated instructions.
*   **Dynamic Skill Dispatching over Linear Loading:** Other solutions still rely on "Linear Context Loading," where everything is pushed into the prompt at once. By shifting to "Dynamic Skill Dispatching," the agent acts as a generalist that can seamlessly flex into highly specialized roles on demand.
*   **Procedural Memory vs. Passive Retrieval:** Other developers try to solve this by dumping data into a database and using RAG (Retrieval-Augmented Generation). But RAG is just passive data retrieval. Agent Skills give the AI **procedural memory**—step-by-step expertise on *how* to execute a workflow, not just *what* facts exist.
*   **Lower Latency and Cost:** Compressing a massive monolithic prompt is still computationally expensive. By keeping the context window incredibly lean and gating what enters it, we eradicate the financial waste and slow response times associated with bloated agents.

In short, tokenizing and compressing are just ways to build a slightly more efficient "everything agent." The Capability Arbitrator recognizes that the era of the "everything agent" is over. By focusing on **infrastructure discipline**, we prove that you don't need to shrink the context if you only give the agent exactly what it needs, exactly when it needs it.

### Key Performance Indicators:

#### 1. Token Saturation Ratio (TSR)
* **Definition:** The percentage of *useful context tokens* relative to *total prompt tokens* per transaction.
* **Target:** `> 85%` useful context saturation.
* **Why it matters:** Monolithic agents average `< 15%` TSR due to loading dozens of unused skills. Progressively disclosing single targeted skills (like `research`) keeps TSR high, reducing model confusion and preventing hallucinations.

#### 2. Cost per Execution (CpE)
* **Definition:** The calculated cloud API and token cost (input/output tokens) per run.
* **Target:** `> 80%` reduction vs. Naive Monolithic Agent.
* **Why it matters:** Loading 15+ skills on every prompt uses over 250,000 input tokens. The Capability Arbitrator averages 42,000 input tokens (Scout node classification + 1 specialized skill), resulting in immediate financial savings at scale.

---

## ⚡ Outcome 2: High-Fidelity Task Execution

By routing tasks to dedicated, isolated execution branches, we guarantee that tasks are solved by the optimal environment (e.g. LLM, custom code script, or human manager).

### Key Performance Indicators:

#### 1. Routing Accuracy & Precision
* **Definition:** The rate at which the lightweight Scout node correctly classifies prompt intent (e.g. `devops`, `coding`, `research`).
* **Target:** `> 95%` routing accuracy.
* **Why it matters:** Ensures tasks are sent to the correct environment, avoiding execution failures or costly re-routing overhead.

#### 2. Deterministic Offloading Rate
* **Definition:** The percentage of closed-form tasks (math calculations, linter checks) successfully routed to pure Python code, bypassing LLMs.
* **Target:** `100%` accuracy on math and linter operations.
* **Why it matters:** LLMs struggle with precise math and execution loops. Routing closed-form tasks to Python functions guarantees absolute accuracy and eliminates LLM billing.
* **Current implementation:** The `math` capability routes arithmetic to the deterministic Math Node. The `devops` capability routes test, lint, and quality-check prompts to the deterministic DevOps Node. The scorecard metric `deterministic_offload_accuracy` checks both paths.

---

## ⚡ Outcome 3: Secure & Compliant Operations

Enterprise operations require strict controls around data privacy, ambient permissions, and high-risk executions.

### Key Performance Indicators:

#### 1. Pre-LLM Filter Success Rate
* **Definition:** The percentage of prompts containing sensitive GDPR-scoped PII (SSNs, credit cards, emails, phone numbers) intercepted and redacted before reaching the LLM.
* **Target:** `100%` redaction rate.
* **Why it matters:** Prevents leakage of customer secrets or sensitive data into public model training datasets.

#### 2. HITL Escalation Accuracy
* **Definition:** The percentage of high-risk or low-confidence operations correctly suspended for human validation.
* **Target:** `100%` intercept rate on dangerous actions (e.g. database deletes).
* **Why it matters:** Ensures the agent cannot execute irreversible, destructive, or high-cost actions without explicit manager approval.

---

## 🎯 Telemetry Reporting Infrastructure

These metrics are calculated at runtime by our telemetry logger ([app/app_utils/telemetry.py](file:///Users/rmcdonald/Repos/agy-cli-projects/capability-arbitrator/app/app_utils/telemetry.py)) and displayed on the FastAPI HUD dashboard.

The architecture support lives in:

* **Graph routing:** [app/agent.py](file:///Users/rmcdonald/Repos/agy-cli-projects/capability-arbitrator/app/agent.py)
* **Scout classification:** [app/app_utils/scout_utils.py](file:///Users/rmcdonald/Repos/agy-cli-projects/capability-arbitrator/app/app_utils/scout_utils.py)
* **Confidence gate:** [app/app_utils/scout_supervisor_utils.py](file:///Users/rmcdonald/Repos/agy-cli-projects/capability-arbitrator/app/app_utils/scout_supervisor_utils.py)
* **Math offload:** [app/app_utils/math_node_utils.py](file:///Users/rmcdonald/Repos/agy-cli-projects/capability-arbitrator/app/app_utils/math_node_utils.py)
* **DevOps offload:** [app/app_utils/devops_utils.py](file:///Users/rmcdonald/Repos/agy-cli-projects/capability-arbitrator/app/app_utils/devops_utils.py)
* **Eval scorecard:** [tests/eval/eval_config.yaml](file:///Users/rmcdonald/Repos/agy-cli-projects/capability-arbitrator/tests/eval/eval_config.yaml)

> [!NOTE]
> **Dashboard Availability:** Run `uv run agents-cli dev` and navigate to `/dashboard` to view these KPIs plotted on visual charts in real-time.
