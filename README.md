# Capability Arbitrator (Kaggle AI Agents Capstone)

## 1. Overview
The Capability Arbitrator is a "capability-first traffic controller" for AI agent ecosystems. Instead of loading every available tool into a single bloated agent, it dynamically decides whether a task should use a specific Model, an MCP server, an Agent Skill, deterministic code, or a Human-in-the-loop reviewer.

## 2. Why It Exists (The Backpack Analogy)
Imagine you are carrying a massive backpack filled with thick textbooks for every subject (Math, Coding, History, etc.). If a teacher asks you a simple math question, you don't dump every single textbook on your desk and try to read them all at once. That would be chaotic, slow, and you'd probably get confused.

But that is exactly how most AI agents work today! They suffer from **"Prompt Bloat."** They try to load *every* tool and *every* instruction into their memory (the context window) all at once.

**The Solution:** The Capability Arbitrator keeps the desk completely empty. 
1. First, a fast "Scout" AI looks at the question and says, *"Ah, this is a Math question."*
2. Then, it specifically hands the question off to a specialized "Math" worker who *only* has the Math textbook.

## 3. The "Cache Break" Trade-off (Why it's a feature, not a bug)
When you test this project in the ADK Playground, you might see a warning that says:
`Performance Alert: System instructions were modified... This breaks context cache alignment.`

This is our secret weapon! It means we are intentionally clearing the AI's memory (breaking the cache) when we hand the task from the Scout to the specialized worker. 
*   **The downside:** It takes an extra second to load the new instructions (like unzipping your backpack).
*   **The massive upside:** The AI becomes hyper-focused, stops hallucinating, and uses way fewer tokens because it isn't distracted by irrelevant instructions.
*   **Phase 7 (The End Goal):** Moving beyond a proof-of-concept, the Arbitrator is designed to be wired into real-world software projects. It will act as a headless daemon for daily developer workflows—automatically triaging GitHub tickets, conducting automated PR reviews, and executing codebase regressions via CI/CD.

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
To test the classification routing and interact with the agent locally, use either the terminal playground or the browser dev UI:

**Terminal Playground:**
```bash
agents-cli playground
```
The playground automatically reloads on save, allowing you to iterate quickly on the Scout node's routing logic in `app/agent.py`.

**Browser Dev UI (Option A):**
```bash
uv run agents-cli dev
```
Navigate to `http://127.0.0.1:8080/dev-ui` to interact with the arbitrator visually and test the expanded GDPR-scoped security screen (which screens SSNs, Emails, Phone Numbers, Credit Cards, and IP Addresses).

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
