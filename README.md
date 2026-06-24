# Capability Arbitrator
### The High-Performance Orchestration Gateway for AI Agent Infrastructure

[![Status: Production-Ready](https://img.shields.io/badge/Status-Production--Ready-success.svg)](#)
[![Stack: ADK 2.0 + MCP](https://img.shields.io/badge/Stack-ADK%202.0%20%2B%20MCP-blue.svg)](#)
[![Performance: Optimized](https://img.shields.io/badge/Performance-Optimized-orange.svg)](#)

Traditional AI frameworks load every tool, instruction, and dependency into a single monolithic prompt. This anti-pattern leads to **Context Rot**—overloading LLM context windows, degrading decision accuracy, and burning reasoning budgets.

The **Capability Arbitrator** is a lightweight, low-latency traffic-control router for agentic systems. By separating *intent classification* from *execution*, it uses **Progressive Disclosure** to dynamically stream only the specific skills and tools needed at the exact millisecond of execution.

---

## ⚡ Core Value Proposition

* **Zero-Waste Context Windows:** Prevent prompt bloat by loading tools and instructions on-demand.
* **Cognitive Budget Preservation:** Maximize model accuracy by keeping active memory hyper-focused on the task.
* **Hybrid Routing Engine:** Instantly route deterministic queries (like math or linting) to native code, bypassing expensive LLM calls entirely.
* **Production-Grade Guardrails:** Built-in GDPR security screening, confidence-based human-in-the-loop (HITL) escalations, and runtime compliance auditing.

---

## 🎒 The Backpack Analogy
> [!TIP]
> Think of a traditional agent like a student carrying a massive backpack filled with textbooks for every subject. When asked a simple math question, the student dumps *every single textbook* onto their desk and tries to read them all at once.
>
> The **Capability Arbitrator** keeps the desk completely empty. When a query arrives:
> 1. A lightweight **Scout** identifies the query's domain: *"This requires Math."*
> 2. It reaches into the backpack, retrieves *only* the Math textbook, and hands it to the execution worker.

---

## 📚 Product Documentation Suite

Explore our guides to understand, develop, and deploy the Capability Arbitrator:

| Document | Purpose | Key Highlights |
| :--- | :--- | :--- |
| [📐 System Architecture](file:///Users/rmcdonald/Repos/agy-cli-projects/capability-arbitrator/docs/ARCHITECTURE.md) | Technical blueprint and workflow topology | Scout-and-Execute pattern, Mermaid flowcharts, supervisor nodes |
| [🛠️ Developer Portal](file:///Users/rmcdonald/Repos/agy-cli-projects/capability-arbitrator/docs/DEVELOPMENT.md) | Local setup, skills development, and MCP configuration | Filesystem MCP servers, AST quality checker, git hooks |
| [🧪 Verification & Testing](file:///Users/rmcdonald/Repos/agy-cli-projects/capability-arbitrator/docs/TESTING.md) | Quality assurance and evaluation scorecards | BDD Gherkin specs, manual QA script checklists, LLM-as-a-Judge |
| [🔒 Security & Privacy](file:///Users/rmcdonald/Repos/agy-cli-projects/capability-arbitrator/docs/SECURITY.md) | GDPR PII filtration and STRIDE audits | Regex filtration screen, HITL escalation, threat modeling reports |
| [🚀 Deployment Guide](file:///Users/rmcdonald/Repos/agy-cli-projects/capability-arbitrator/docs/DEPLOYMENT.md) | Cloud scaling and containerization | FastAPI Dashboard, Google Cloud Run, auto-scaling |
| [🏅 Rubric & Compliance](file:///Users/rmcdonald/Repos/agy-cli-projects/capability-arbitrator/docs/RUBRIC.md) | Kaggle Capstone alignment and validations | Clickable file/line citations mapping requirements to the codebase |

---

## 🚀 Quick Start

### 1. Install CLI
Install the project dependencies using the package manager:
```bash
agents-cli install
```

### 2. Launch Local Dev Console
Start the terminal dev console to interact with the arbitrator graph:
```bash
agents-cli playground
```

### 3. Serve the Visual Dashboard
Run the FastAPI server locally to view the telemetry dashboard and live "Stats for Nerds" interface:
```bash
uv run agents-cli dev
```
Open your browser and navigate to `http://127.0.0.1:8080/dev-ui`.
