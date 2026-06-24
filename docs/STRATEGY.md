# Capability Arbitrator - Strategy Overview

## 1. The Core Innovation: "Capability Before Implementation"
The project shifts the fundamental question from "Which model should answer?" to "What capability is required to solve this problem?". The true "whitespace" in the current open-source landscape isn't model selection, but Capability Resolution—deciding whether a task needs a Model, an MCP server, a specialized Skill, a deterministic script, or a Human-in-the-Loop.

## 2. Solving the "Context Rot" Crisis (The Backpack Analogy)
Think of an AI agent like a student carrying a giant backpack full of textbooks. If the teacher asks a simple math question, a traditional AI dumps *every single textbook* onto the desk (loading all instructions and tools into the prompt). This is called "Prompt Bloat." It overwhelms the AI, causes hallucinations, and costs a lot of tokens.

By using **Progressive Disclosure**, this project keeps the desk empty. The Scout node identifies the subject ("Math"), and *only* pulls out the Math textbook. 

When you do this, the system breaks the "Context Cache" (clearing the desk). While breaking the cache causes a tiny delay (unzipping the backpack), it guarantees the specialized node is hyper-focused on exactly the right instructions.

## 3. The "Scout and Execute" Workflow
A high-efficiency pipeline using ADK 2.0 Graph primitives:
- **The Scout:** Uses Gemini 3.5 Flash for low-latency classification of the required capability.
- **The Registry:** A mapping layer that links capability tags (e.g., math, research) to specific execution targets.
- **Dynamic Routing:** Utilizing conditional edges to route the flow. For example, "math" goes to a deterministic script, while "research" goes to an isolated agent loaded with deep research instructions.

## 4. The Value Proposition
Focus on demonstrating measurable benefits rather than just architectural theory. Compare a "Naive Agent" (loading 15+ skills and hitting 250k tokens) against the "Capability Arbitrator" (loading 3 skills and using only 42k tokens). This proves that the approach optimizes the "reasoning budget," making the agent faster, cheaper, and more accurate.

## 5. Alignment with Previous Projects
This architecture is the culmination of a pattern built across several projects:
- **Context Engine:** The focus on retrieving only what is absolutely necessary.
- **Check-in:** Prioritizing capability identification before choosing an implementation.
- **Signal HoriZon:** Applying systems thinking to agentic infrastructure.
- **ADK Intensive:** Mastering the Skills + Workflows + MCP stack to package this pattern into a portable, production-grade container.

## 6. Development & Deployment Phases
- **Phases 1-5 (Scaffolding & Proof of Concept):** Prioritize using the native ADK Web Interface (e.g., via the Agent Runtime or Playground) to visually interact with the graph, verify routing logic, and securely handle Human-in-the-Loop (HITL) pause/resume events.
- **Phase 6 (Real-World Deep Testing):** We will build a node that uses the Antigravity Python SDK to programmatically spawn an IDE subagent, scan a local codebase, or trigger a local file system edit. This proves that our Capability Arbitrator can securely orchestrate actual developer tools within the IDE rather than just hallucinating text!
- **Phase 7 (Normal Daily Use & Production Integration):** We transition the Arbitrator from a "cool proof-of-concept" into an actual daily driver. This involves wiring it up to a real-world software project via CI/CD pipelines, mapping everyday developer workflows (e.g., automated PR reviews, ticket triage, and regression testing) to specific capability tags, and deploying it as a headless daemon that runs continuously alongside human developers.
