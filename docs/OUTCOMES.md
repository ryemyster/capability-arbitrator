# Capability Arbitrator Outcomes & KPIs

This document outlines the performance outcomes, metric dimensions, and business value indicators tracked by the Capability Arbitrator.

## Purpose
Establishes the criteria for proving that a "capability-first" architecture outperforms monolithic agents in speed, cost, quality, and security.

## Why We Track This
Without empirical benchmarks, it is impossible to verify if breaking the context cache and dynamically routing prompts actually improves system efficiency, saves money, or increases safety.

## How to Measure
These metrics are calculated at runtime by our telemetry layers (stored in `app/app_utils/telemetry.py`) and visually presented in the "Stats for Nerds" overlay and dashboard.

---

### Outcome 1: Eradicate "Context Rot" and Maximize the Reasoning Budget
The primary goal of the Capability Arbitrator is to stop treating models like digital hoarders. By dynamically loading tools on-demand, we preserve the model's cognitive overhead for actual problem-solving rather than parsing bloated system prompts.

*   **KPI 1.1: Context Window Efficiency**
    *   **Dimension: Token Overhead Reduction** (The difference in token count between loading all tools in a monolithic prompt vs. dynamically loading a single `SKILL.md` via Progressive Disclosure).
    *   **Dimension: Tool Bloat Ratio** (The percentage of tools loaded into the context window that are actually utilized during the task).
*   **KPI 1.2: System Latency**
    *   **Dimension: Scout Node Time-to-First-Token (TTFT)** (The execution speed of the lightweight Gemini 3.5 Flash intent classifier before any heavy skills are loaded).
    *   **Dimension: Overall Task Duration** (The end-to-end time from user prompt to final execution).

### Outcome 2: High-Fidelity Task Execution via Capability Routing
Instead of relying on a single model to guess the right tool, the system guarantees that tasks are handled by the optimal execution target (Model, Skill, MCP, or Code). 

*   **KPI 2.1: Routing Accuracy**
    *   **Dimension: Intent Classification Precision** (The percentage of user prompts correctly tagged by the Scout node into categories like `math`, `research`, `coding`, `mcp`, or `stride`).
    *   **Dimension: Deterministic Offloading Rate** (How often closed-form tasks, like math or database schema validation, are successfully routed to deterministic Python scripts rather than burning LLM tokens).
*   **KPI 2.2: Output Quality & Reliability**
    *   **Dimension: Autonomous Evaluation Score** (The pass/fail grade assigned by the `OutcomeJudge` scorecard running via the `google-agents-cli-eval` skill during deep testing).
    *   **Dimension: Hallucination Reduction Rate** (The decrease in false tool calls or invented syntax due to the agent having a focused, progressively disclosed context).

### Outcome 3: Secure, Trust-Verified Enterprise Operations
The system must shift from casual "vibe coding" to disciplined "agentic engineering" by ensuring that ambient, autonomous actions are strictly gated, secure, and compliant.

*   **KPI 3.1: Threat Mitigation & Data Privacy**
    *   **Dimension: Pre-LLM Filter Success Rate** (The percentage of prompt-injection attempts and sensitive data like PII/SSNs successfully caught and redacted by the security screen *before* reaching the LLM).
    *   **Dimension: Threat Modeling Coverage** (The frequency that the STRIDE threat modeling skill is successfully utilized to map out security risks during the planning phase). 
*   **KPI 3.2: Human-in-the-Loop (HITL) Oversight**
    *   **Dimension: Escalation Accuracy** (The rate at which high-risk or high-cost tasks are successfully intercepted and paused via `RequestInput` nodes).
    *   **Dimension: Manager Resolution Latency** (How quickly a human reviewer approves or rejects a paused task from the frontend deployment dashboard).

---

## When to Review
- **During Code Reviews:** Ensure any new node or skill does not degrade the Context Window Efficiency or increase Scout TTFT.
- **Before Production Deployment:** Verify that the Autonomous Evaluation Score is above 95% and Threat Modeling Coverage is complete.
