# Capability Arbitrator (Kaggle AI Agents Capstone)

> **Vision:** Today when AI developers and enterprise engineering teams want to build capable autonomous agents to solve complex workflows, they have to dump every conceivable tool, API, and procedural instruction into a single, massive system prompt for every request.
> 
> This is unacceptable because it causes **"Context Rot"** and **"Prompt Bloat,"** forcing the model to burn its expensive reasoning budget just parsing irrelevant instructions, which leads to high latency, hallucinations, and degraded decision-making.
> 
> We envision a world where managing an AI ecosystem is like a highly efficient traffic control system—a **"lean orchestration engine for AI"** where models only hold the exact knowledge they need in their active memory. We are bringing this world about through the **Capability Arbitrator**, an architecture that uses a high-speed Scout node to classify a user's intent first, and then uses **Progressive Disclosure** to dynamically load only the specific Agent Skills, MCP tools, deterministic scripts, or human reviewers required at the exact moment of execution.

---

## 1. The Capability-First Manifesto: The End of the "Everything Agent"

For the past two years, the industry has been obsessed with building the ultimate "everything agent." We have treated LLMs like digital hoarders, dumping every conceivable tool, API, and instruction into a single, monolithic system prompt. The result is **Context Rot**: our agents are drowning in irrelevant data, burning their reasoning budgets just to parse their own bloated instructions, leading to high latency and degraded decision-making. 

The era of the bloated, "everything agent" is dead. The next massive leap in AI is not a larger context window or a smarter foundation model—it is **infrastructure discipline**. 

The **Capability Arbitrator** represents this radical paradigm shift. We are fundamentally changing the core question of agent orchestration. We must stop asking, *"Which model should answer this?"* and start asking, ***"What capability is required to solve this problem?"*** 

This vision is built on three uncompromising pillars:

1.  **Capability Before Implementation:** An agent's intent must be classified before a single heavy-duty tool is loaded. By deploying a high-speed, low-latency "Scout" node (like Gemini 3.5 Flash), we intercept the user's intent and assign a precise capability tag—be it math, deep research, or human approval. We separate the *understanding* of the task from the *execution* of the task.
2.  **Radical Progressive Disclosure:** We must eradicate "Prompt Bloat." The Arbitrator embraces **Progressive Disclosure**, exposing the system to a lightweight menu of metadata and only loading the heavy procedural knowledge—a specific Agent Skill, a deterministic Python script, or an MCP server—at the exact moment it is triggered. 
3.  **Preserving the Reasoning Budget:** By keeping the agent lean and strictly gating what enters the context window, we preserve the model's "cognitive overhead" entirely for solving the actual problem. We route deterministic tasks (like math) to deterministic code, and high-risk tasks to human-in-the-loop reviewers, ensuring that expensive LLM reasoning is only spent where it is actually needed.

**The Vision:** We are moving from casual "vibe coding" into true **agentic engineering**. The Capability Arbitrator transforms fragile, isolated "custom machines" into a modular, highly interoperable traffic-control ecosystem. 

We are no longer just building chatbots; we are orchestrating a lean, secure, and dynamic AI workforce where every resource—whether an LLM, a script, or a human—is deployed with surgical precision.

---

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

## 4. Outcomes & Key Performance Indicators (KPIs)
To measure and prove that a capability-first architecture outperforms a monolithic agent layout, the system evaluates three core outcomes:
1. **Eradicating Context Rot & Maximizing Reasoning Budget:** (Context window efficiency, Scout time-to-first-token, overall task latency).
2. **High-Fidelity Task Execution:** (Scout routing precision, deterministic offloading rate, output reliability score).
3. **Secure & Gated Enterprise Operations:** (Pre-LLM PII/SSN redaction, STRIDE coverage, human-in-the-loop escalation accuracy).

Detailed metric definitions, value dimensions, and evaluation scorecards are documented in [OUTCOMES.md](file:///Users/rmcdonald/Repos/agy-cli-projects/capability-arbitrator/docs/OUTCOMES.md).

## 5. Getting Started

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
