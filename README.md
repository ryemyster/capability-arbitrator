# Capability Arbitrator (Kaggle AI Agents Capstone)

## 1. Overview
The Capability Arbitrator is a "capability-first traffic controller" for AI agent ecosystems. Instead of loading every available tool into a single bloated agent, it dynamically decides whether a task should use a specific Model, an MCP server, an Agent Skill, deterministic code, or a Human-in-the-loop reviewer.

## 2. Why It Exists (The Problem)
**Context Rot & Prompt Bloat:** Traditional agent systems degrade in reasoning quality because they attempt to load every available tool, instruction, and context into the prompt window for every request. This leads to hallucinations, slow response times, and poor decision-making.

**The Solution:** This project solves context saturation by asking *"What capability is needed?"* before asking *"Which model should answer?"*. By decoupling intent classification from execution, the reasoning budget is preserved for the actual task.

## 3. How It Works (The Architecture)
The architecture follows a precise 4-step pipeline:
1. **Scout:** Uses a lightweight, fast model (`gemini-3.5-flash`) to classify the user's intent.
2. **Capability Discovery:** Maps the intent to a specific capability tag (e.g., `math`, `coding`, `research`, `approval`).
3. **Progressive Disclosure:** Dynamically loads only the necessary Agent Skills or MCP tools based on the assigned tag, strictly preserving the reasoning budget.
4. **Execution:** Routes the task to the optimal execution target (e.g., a deterministic Python script for math, Gemini 3.1 Pro for deep research, or a RequestInput node for human approval).

## 4. Getting Started

Before you begin, ensure you have:
- **uv**: Python package manager - [Install](https://docs.astral.sh/uv/getting-started/installation/)
- **agents-cli**: Agents CLI - Install with `uv tool install google-agents-cli`

### Installation
Install required packages using the CLI:
```bash
cd capability-arbitrator
agents-cli install
```

### Running Locally
To test the classification routing and interact with the agent locally, use the playground:
```bash
agents-cli playground
```
The playground automatically reloads on save, allowing you to iterate quickly on the Scout node's routing logic in `app/agent.py`.

---

### Additional Commands & Development
| Command              | Description                                                                                 |
| -------------------- | ------------------------------------------------------------------------------------------- |
| `agents-cli install` | Install dependencies using uv                                                         |
| `agents-cli playground` | Launch local development environment                                                  |
| `agents-cli lint`    | Run code quality checks                                                               |
| `agents-cli eval`    | Evaluate agent behavior (generate, grade, analyze, and more) |
| `uv run pytest tests/unit tests/integration` | Run unit and integration tests                                                        |
| `agents-cli deploy`  | Deploy agent to Agent Runtime                                                                |
| `agents-cli scaffold enhance` | Add CI/CD pipelines and Terraform infrastructure |

> 💡 **Tip:** Use [Gemini CLI](https://github.com/google-gemini/gemini-cli) for AI-assisted development - project context is pre-configured in `GEMINI.md`.
