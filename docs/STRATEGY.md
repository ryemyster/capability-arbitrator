# Capability Arbitrator - Strategy Overview

## 1. The Core Innovation: "Capability Before Implementation"
The project shifts the fundamental question from "Which model should answer?" to "What capability is required to solve this problem?". The true "whitespace" in the current open-source landscape isn't model selection, but Capability Resolution—deciding whether a task needs a Model, an MCP server, a specialized Skill, a deterministic script, or a Human-in-the-Loop.

## 2. Solving the "Context Rot" Crisis
This design directly targets "Context Rot" and "Prompt Bloat"—the phenomenon where loading an agent with too many instructions and tools saturates the context window and degrades reasoning. By using Progressive Disclosure, the system keeps the agent "lean" by exposing it only to minimal metadata until a specific intent triggers the activation of heavy procedural knowledge.

## 3. The "Scout and Execute" Workflow
A high-efficiency pipeline using ADK 2.0 Graph primitives:
- **The Scout:** Uses Gemini 3.5 Flash for low-latency classification of the required capability.
- **The Registry:** A mapping layer that links capability tags (e.g., math, research) to specific execution targets.
- **Dynamic Routing:** Utilizing conditional edges to route the flow, ensuring that "math" goes to a deterministic Python script while "research" might load a specialized Gemini 3.1 Pro node with an MCP server.

## 4. The Value Proposition
Focus on demonstrating measurable benefits rather than just architectural theory. Compare a "Naive Agent" (loading 15+ skills and hitting 250k tokens) against the "Capability Arbitrator" (loading 3 skills and using only 42k tokens). This proves that the approach optimizes the "reasoning budget," making the agent faster, cheaper, and more accurate.

## 5. Alignment with Previous Projects
This architecture is the culmination of a pattern built across several projects:
- **Context Engine:** The focus on retrieving only what is absolutely necessary.
- **Checkin:** Prioritizing capability identification before choosing an implementation.
- **Signal HoriZon:** Applying systems thinking to agentic infrastructure.
- **ADK Intensive:** Mastering the Skills + Workflows + MCP stack to package this pattern into a portable, production-grade container.
