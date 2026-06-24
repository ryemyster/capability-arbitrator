# Kaggle Rubric Alignment & Codebase Citation Guide

This document lists the master rubric requirements for our Kaggle AI Agents Capstone submission, explains how they are met, and provides clickable file and line citations.

---

## 1. Runtime Guardrails (Production Execution)

These guardrails govern the live, production path of the agent, ensuring execution safety and intent classification accuracy.

### 📐 Uses ADK 2.0 Graph (Workflow)
* **What:** The orchestrator is built as a workflow topology of nodes and edges rather than a script.
* **Citation:** Defined in [app/agent.py:L205-219](file:///Users/rmcdonald/Repos/agy-cli-projects/capability-arbitrator/app/agent.py#L205-219) via `root_workflow`.

### 🔀 Conditional Branching
* **What:** Dynamic routing of the user's prompt based on classifications.
* **Citation:** Configured via `router_node` in [app/agent.py:L98-109](file:///Users/rmcdonald/Repos/agy-cli-projects/capability-arbitrator/app/agent.py#L98-109) and the conditional edges in [app/agent.py:L212-217](file:///Users/rmcdonald/Repos/agy-cli-projects/capability-arbitrator/app/agent.py#L212-217).

### 🔒 Security Screen
* **What:** Pre-LLM filter scanning for GDPR-scoped PII (SSNs, emails, credit cards, phone numbers, IP addresses).
* **Citation:** Implemented in [app/agent.py:L185-204](file:///Users/rmcdonald/Repos/agy-cli-projects/capability-arbitrator/app/agent.py#L185-204) and verified by [tests/unit/test_arbitrator.py:L55-84](file:///Users/rmcdonald/Repos/agy-cli-projects/capability-arbitrator/tests/unit/test_arbitrator.py#L55-84).

### 📖 Persistent Context file (`CONTEXT.md`)
* **What:** System-wide prompt rules enforced via ADK configurations.
* **Citation:** Configured in [.agents/CONTEXT.md](file:///Users/rmcdonald/Repos/agy-cli-projects/capability-arbitrator/.agents/CONTEXT.md) and registered in [agents-cli-manifest.yaml](file:///Users/rmcdonald/Repos/agy-cli-projects/capability-arbitrator/agents-cli-manifest.yaml).

### 🚨 Human-in-the-Loop (HITL) Node
* **What:** Pause-and-resume workflow gate for dangerous commands or low-confidence routing.
* **Citation:** Implemented via `RequestInput` in [app/agent.py:L133-150](file:///Users/rmcdonald/Repos/agy-cli-projects/capability-arbitrator/app/agent.py#L133-150).

---

## 2. CI/CD Checks (Build & Push Gates)

These validation scripts are executed locally and via GitHub Actions to block regressions during development.

### 🤖 Code Quality Checks (Linting)
* **What:** Automated checking for function length, file length, explicit type signatures, and DRY compliance.
* **Citation:** Checked by [scripts/agent_quality_check.py](file:///Users/rmcdonald/Repos/agy-cli-projects/capability-arbitrator/scripts/agent_quality_check.py) during pre-push git hooks.

### 🥒 BDD Gherkin Testing
* **What:** Plain-English behavior specs mapping the user experience.
* **Citation:** Scenarios defined in [tests/integration/features/routing.feature](file:///Users/rmcdonald/Repos/agy-cli-projects/capability-arbitrator/tests/integration/features/routing.feature) and implemented in [tests/integration/test_routing_bdd.py](file:///Users/rmcdonald/Repos/agy-cli-projects/capability-arbitrator/tests/integration/test_routing_bdd.py).

### 🧪 Unit & Integration Testing
* **What:** Assertions for individual code helper files.
* **Citation:** Located in [tests/unit/](file:///Users/rmcdonald/Repos/agy-cli-projects/capability-arbitrator/tests/unit/) and [tests/integration/](file:///Users/rmcdonald/Repos/agy-cli-projects/capability-arbitrator/tests/integration/).

---

## 3. Runtime Evaluation (Validation Scorecard)

Offline validation tools utilized to run dynamic scorecards against the routing agent.

### 📊 LLM-as-a-Judge Scorecard
* **What:** Autonomous scorecard grading metrics like Token Saturation Rate (TSR) and Cost reduction efficiency (CpE) using dynamic scenarios.
* **Citation:** Implemented in [tests/scripts/phase6-deep-testing/test_deep_testing.py](file:///Users/rmcdonald/Repos/agy-cli-projects/capability-arbitrator/tests/scripts/phase6-deep-testing/test_deep_testing.py).

### 🛡️ STRIDE Threat Modeling Skill
* **What:** Progressively disclosed security model used to audit architecture for security threats.
* **Citation:** Located in [app/skills/stride/SKILL.md](file:///Users/rmcdonald/Repos/agy-cli-projects/capability-arbitrator/app/skills/stride/SKILL.md) and bound to `stride_node` in [app/agent.py:L155](file:///Users/rmcdonald/Repos/agy-cli-projects/capability-arbitrator/app/agent.py#L155).

---

## 4. Development & Dashboard (Monitoring)

### 📈 FastAPI Telemetry Dashboard
* **What:** Graphical web UI displaying active cost and latency charts, plus a task review interface.
* **Citation:** Implemented in [app/fast_api_app.py](file:///Users/rmcdonald/Repos/agy-cli-projects/capability-arbitrator/app/fast_api_app.py) and served locally or via Google Cloud Run at `/dashboard`.

### 🔌 Model Context Protocol (MCP) filesystem integration
* **What:** Real-time data anchoring via external server configurations.
* **Citation:** Declared in [app/agent.py:L157-164](file:///Users/rmcdonald/Repos/agy-cli-projects/capability-arbitrator/app/agent.py#L157-164).

### 💡 Few-Shot Skill grounding
* **What:** Sample inputs/outputs used to guide model generation.
* **Citation:** Defined in [app/skills/researcher/few_shots.json](file:///Users/rmcdonald/Repos/agy-cli-projects/capability-arbitrator/app/skills/researcher/few_shots.json).
