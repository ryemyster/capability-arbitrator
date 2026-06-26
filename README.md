# Capability Arbitrator 
[Created By: Ryan K McDonald](https://ryanmcdonald.ai)

## Capability-Scoped Execution With Measurable Governance

[![Status: Evaluation-Ready Prototype](https://img.shields.io/badge/Status-Evaluation--Ready%20Prototype-blue.svg)](#)
[![Stack: ADK 2.0 + MCP](https://img.shields.io/badge/Stack-ADK%202.0%20%2B%20MCP-blue.svg)](#)
[![Telemetry: Estimated + Measured](https://img.shields.io/badge/Telemetry-Estimated%20%2B%20Measured-orange.svg)](#)

Today’s agent systems become increasingly difficult to operate as they gain more tools, skills and workflows. Even when routing exists, execution logic, governance and telemetry are often tightly coupled, making it difficult to understand why an agent chose a capability, how much context it consumed or whether the routing decision was actually beneficial.

As these systems grow, developers frequently compensate by expanding prompts and attaching more tools to every request. The result is larger context windows, higher inference costs and reduced observability into the decisions the system is making.

## Our Approach

Capability Arbitrator separates **understanding** from **execution**.

A lightweight Scout first determines what capability a request requires. The graph then executes the matching branch: deterministic tasks use code, LLM tasks use a scoped skill or toolset, and risky or uncertain tasks pause for human approval.

This keeps execution focused while adding a governance layer around routing, safety, telemetry and outcome checks.

## What Makes It Different
Capability Arbitrator is not simply another multi-agent framework.

It combines:
* capability-based routing
* deterministic execution
* governance checkpoints
* telemetry provenance
* runtime outcome validation
* controlled optimization through offline learning loops

into a single execution architecture.

The goal is to make AI workflows measurable, governable and continuously improvable.

## Outcome Signals

The project tracks a mix of measured runtime values, deterministic checks and baseline estimates. The telemetry code labels token and cost comparisons as estimates when ADK or Gemini does not expose exact downstream token usage.

| Signal | Current Evidence | Confidence |
| :--- | :--- | :--- |
| **Capability routing** | Scout emits a capability tag and confidence score before the Router selects an execution branch. | Implemented |
| **Deterministic offload** | Math and DevOps paths run through Python/subprocess helpers and record `deterministic_zero` execution tokens. | Implemented |
| **PII handling** | Regex-based PII detection routes matching prompts to HITL approval before Scout execution. | Implemented detection and escalation |
| **Token/cost savings** | Runtime telemetry compares arbitrator token footprint against a monolithic baseline estimate. | Estimated |
| **Routing quality** | BDD tests, eval scorecards and the Quality Flywheel inspect routing behavior. | Test/eval-backed target |
| **Self-healing security** | STRIDE Self-Healing CLI can audit, patch, verify and open a PR when explicitly enabled. | Experimental / opt-in |

See [docs/OUTCOMES.md](docs/OUTCOMES.md) for the full KPI definitions, evidence boundaries and dashboard metric map.

---

## Core Value Proposition

* **Capability-Scoped Execution:** Route each request to the smallest suitable execution branch.
* **Decision Visibility:** Record the Scout tag, confidence, token source and run source for each execution.
* **Hybrid Routing Engine:** Instantly route deterministic queries (like math or linting) to native code, bypassing expensive LLM calls entirely.
* **Prototype Guardrails:** Built-in regex PII detection, confidence-based human-in-the-loop (HITL) escalation, runtime output compliance checks and KPI auditing.

---

## Core Architecture

The runtime graph follows this lifecycle:

```text
Security Screen -> Scout -> Scout Supervisor -> Router -> Execution Node
  -> Compliance Judge -> Product KPI Auditor -> Telemetry Watchdog
```

This is the central idea: **Scout decides, gates govern, nodes execute, telemetry proves or challenges the decision.**


## Product Documentation Suite

Explore our guides to understand, develop, and deploy the Capability Arbitrator:

| Document | Purpose | Key Highlights |
| :--- | :--- | :--- |
| [System Architecture](docs/ARCHITECTURE.md) | Architecture map and system boundaries | Runtime graph, improvement surfaces, deployment boundaries |
| [Core Runtime Graph](docs/CORE_RUNTIME_GRAPH.md) | Detailed live graph behavior | Security screen, Scout, router, compliance judge, KPI auditor, watchdog |
| [Improvement Surfaces](docs/IMPROVEMENT_SURFACES.md) | STRIDE/Flywheel operating model | Command mode, ambient mode, enablement flags, current limitations |
| [Developer Portal](docs/DEVELOPMENT.md) | Local setup, skills development, and MCP configuration | Filesystem MCP servers, AST quality checker, git hooks |
| [Verification and Testing](docs/TESTING.md) | Quality assurance and evaluation scorecards | BDD Gherkin specs, manual QA script checklists, LLM-as-a-Judge |
| [Security & Privacy](docs/SECURITY.md) | GDPR PII filtration and STRIDE audits | Regex filtration screen, HITL escalation, threat modeling reports |
| [Deployment Guide](docs/DEPLOYMENT.md) | Manual ADK deployment | Agent Runtime, GitHub validation, production deploy gates |
| [Rubric & Compliance](docs/RUBRIC.md) | Kaggle Capstone alignment and validations | Clickable file/line citations mapping requirements to the codebase |

---

## Opt-In Self-Healing Security

When explicitly enabled, the system can audit its own codebase for vulnerabilities using the STRIDE threat model, generate a targeted security patch, run the test suite to verify it, and open a pull request — all from a single command. See [`docs/STRATEGY.md`](docs/STRATEGY.md) for the full escalating-autonomy design and safety gates.

```bash
uv run arbitrator stride-heal app/agent.py --mode audit_only   # print STRIDE report
uv run arbitrator stride-heal app/agent.py --mode apply_patch  # write + verify locally
```

Both improvement features (STRIDE Self-Healing and Quality Flywheel) support a three-layer runtime surface control:

| Layer | Toggle | Behavior when disabled |
| :--- | :--- | :--- |
| **Master** | `enabled: false` in YAML | Complete no-op — no LLM calls, no file writes |
| **Arbitrator** | `arbitrator.enabled: false` | CLI returns a clear "disabled" message |
| **Ambient** *(experimental)* | `ambient.enabled: false` | Background observer stays silent |

The **[EXPERIMENTAL] ambient supervisor** is a telemetry hook that observes saved runs when enabled. In the current implementation it logs Flywheel and STRIDE signals; patching and PR creation remain CLI-controlled. Enable per-feature via `config/quality_flywheel.yaml` or `config/stride_self_healing.yaml`. See [`docs/IMPROVEMENT_SURFACES.md`](docs/IMPROVEMENT_SURFACES.md) for design details.

---

## Quick Start

### 1. Install CLI
Install the project dependencies using the package manager:
```bash
agents-cli install
```

### 2. Launch The ADK Playground
Start the ADK development UI:
```bash
agents-cli playground
```
Open `http://127.0.0.1:8080/dev-ui`.

### 3. Launch The Standalone Telemetry Dashboard
Run the custom telemetry dashboard:
```bash
uv run arbitrator dashboard
```
Open `http://127.0.0.1:8000/`.

### 4. Launch The Unified FastAPI Service
Run the combined ADK API, Pub/Sub endpoint and telemetry dashboard:
```bash
uv run uvicorn app.fast_api_app:app --host 127.0.0.1 --port 8000
```

| URL | What It Serves |
| :--- | :--- |
| `http://127.0.0.1:8000/` | ADK web UI root |
| `http://127.0.0.1:8000/dashboard` | Custom telemetry dashboard |
| `http://127.0.0.1:8000/api/run` | Streaming dashboard execution endpoint |
| `http://127.0.0.1:8000/api/metrics` | Local telemetry history |

### 5. View The Dashboard In The Cloud
The unified FastAPI service (including `/dashboard`) can be deployed to Cloud Run. Once deployed, the dashboard lives at `/dashboard` on the service URL printed by the deploy command:
```text
https://<service-url>/dashboard
```
Retrieve the URL anytime with `uv run python scripts/deploy_agent.py status --target cloud_run`. See [docs/DEPLOYMENT.md](docs/DEPLOYMENT.md#finding-the-deployed-dashboard-url) for the full Cloud Run workflow.
