# The Capability Arbitrator: A Lean Orchestration Engine for AI

> **The Vision:** The era of the bloated, "everything agent" is dead. 
> Dumping every tool, API, and instruction into a single monolithic system prompt causes **Context Rot** and **Prompt Bloat**, forcing the model to burn its cognitive reasoning budget just to parse its own instructions. 
> 
> The **Capability Arbitrator** represents a radical infrastructure shift. Instead of loading everything upfront, we intercept requests using a high-speed **Scout** classifier, then use **Progressive Disclosure** to dynamically load only the specific Skills, MCP tools, and deterministic scripts required at the exact moment of execution.

---

## 1. Executive Summary & Value Proposition

Traditional agents act like digital hoarders, dragging massive system prompts into every interaction. This results in high latency, frequent hallucinations, and wasted token budget. 

The Capability Arbitrator solves this by treating agent orchestration like a traffic-control system:
* **Decoupled Architecture:** We separate *understanding the task* (routing) from *solving the task* (execution).
* **Cognitive Efficiency:** The context window is kept clean, preserving the LLM's reasoning capabilities for the problem at hand.
* **Hybrid Execution:** Deterministic tasks (like math) bypass LLMs entirely and route to pure code, while high-risk tasks are gated by human-in-the-loop approval.

### The Backpack Analogy 🎒
Imagine a student carrying a massive backpack filled with textbooks for every subject (Math, Coding, History, etc.). If a teacher asks a simple math question, a traditional monolithic agent dumps *every single textbook* onto the desk and tries to read them all at once. 

The **Capability Arbitrator** keeps the desk completely empty. When a question is asked:
1. A fast **Scout** looks at the query and says, *"This is a Math question."*
2. It reaches into the backpack, pulls out *only* the Math textbook (Progressive Disclosure), and hands it to the worker.

---

## 2. Navigating the Documentation

To make the codebase accessible and easy to traverse, we have structured our documentation into five dedicated guides:

### 🛠️ [1. Development Guide](file:///Users/rmcdonald/Repos/agy-cli-projects/capability-arbitrator/docs/DEVELOPMENT.md)
* **What:** Local setup, package management, and developer workflow.
* **Highlights:** How to configure Model Context Protocol (MCP) servers, set up Git checks, and work with custom Agent Skills.

### 📐 [2. Architecture & Topology](file:///Users/rmcdonald/Repos/agy-cli-projects/capability-arbitrator/docs/ARCHITECTURE.md)
* **What:** System design, agent nodes, and graph connections.
* **Highlights:** Detail-oriented layout of the Scout-and-Execute pattern, Mermaid flowcharts, and active supervisor nodes.

### 🧪 [3. Testing & Verification](file:///Users/rmcdonald/Repos/agy-cli-projects/capability-arbitrator/docs/TESTING.md)
* **What:** Quality assurance, Gherkin specs, and dynamic eval loops.
* **Highlights:** BDD integration tests, manual QA scripts, and the `DeepTester` / `OutcomeJudge` red-teaming scorecard.

### 🚀 [4. Cloud Deployment](file:///Users/rmcdonald/Repos/agy-cli-projects/capability-arbitrator/docs/DEPLOYMENT.md)
* **What:** Production deployment instructions.
* **Highlights:** Deploying the unified agent API and the visual dashboard container to Google Cloud Run.

### 🏅 [5. Kaggle Rubric Mapping](file:///Users/rmcdonald/Repos/agy-cli-projects/capability-arbitrator/docs/RUBRIC.md)
* **What:** Detailed rubric compliance checklist.
* **Highlights:** Clickable file and line citations mapping our codebase to the Capstone criteria.

---

## 3. Quick Start

### Installation
Ensure you have [uv](https://docs.astral.sh/uv/) installed, then run:
```bash
agents-cli install
```

### Local Dev Modes
* **Terminal Playground:**
  ```bash
  agents-cli playground
  ```
* **Browser Dev UI & Dashboard:**
  ```bash
  uv run agents-cli dev
  ```
  Navigate to `http://127.0.0.1:8080/dev-ui` to interact with the arbitrator visually.
