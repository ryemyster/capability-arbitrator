# Performance Outcomes & KPI Dashboard Metrics
### Value Realization and Resource Savings

This document outlines the performance outcomes, core KPIs, and value metrics tracked by the Capability Arbitrator telemetry suite.

---

## ⚡ Outcome 1: Eradicate "Context Rot" & Maximize the Reasoning Budget

Monolithic agents load all system rules and tool descriptions into memory upfront. This eats up active context, degrades logic reasoning, and increases API costs. The Capability Arbitrator resolves this by loading tools dynamically via **Progressive Disclosure**.

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

> [!NOTE]
> **Dashboard Availability:** Run `uv run agents-cli dev` and navigate to `/dashboard` to view these KPIs plotted on visual charts in real-time.
