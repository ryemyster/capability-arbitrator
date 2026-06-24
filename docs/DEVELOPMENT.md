# Development Guide: Setting Up and Developing Local Workflows

This document explains how to set up, build, and run the Capability Arbitrator on your local machine.

---

## 1. Why: The Problem & The Vision
* **The Problem:** Setting up multi-agent projects often requires configuring complex environments, registering third-party tools, and running manual lint checks. Without a clear developer workflow, developer speed slows down, and code quality degrades.
* **The Solution:** We implement a standard development environment utilizing the Antigravity `agents-cli` toolset, automated Git hook checks, and pre-configured Model Context Protocol (MCP) integrations to streamline local feature building and testing.

---

## 2. What: Key Components

Our developer ecosystem consists of three main parts:
1. **Model Context Protocol (MCP) Servers:** Provides sub-agents with direct access to local development resources (like the filesystem) in a standardized manner.
2. **Automated Quality Hooks:** Pre-push and pre-commit checks that run code-quality analysis (`agent_quality_check.py`) and pytest suites.
3. **Agent Skills:** Reusable procedural knowledge bases (located in `.agents/skills/`) that are progressively loaded into sub-agents when triggered.

---

## 3. How: Step-by-Step Developer Setup

### Step A: Prerequisites & Installation
Ensure you have [uv](https://docs.astral.sh/uv/) installed. Then run the installation hook to set up the virtual environment and install all packages:
```bash
# Clone the repository and navigate inside
cd capability-arbitrator

# Install dependencies and sync virtual env
agents-cli install
```

### Step B: Working with Model Context Protocol (MCP)
We utilize the `@modelcontextprotocol/server-filesystem` server to allow the `coding_node` and `mcp_node` to interact with our local directory structure safely.

In [app/agent.py](file:///Users/rmcdonald/Repos/agy-cli-projects/capability-arbitrator/app/agent.py), the MCP server is initialized dynamically:
```python
filesystem_mcp = McpToolset(
    connection_params=StdioConnectionParams(
        server_params=StdioServerParameters(
            command="npx",
            args=["-y", "@modelcontextprotocol/server-filesystem", os.getcwd()],
        ),
    ),
)
```
* **Security Guardrail:** The system is explicitly configured to prevent sub-agents from executing recursive directory scans (like `directory_tree` on `.`) to save token costs and prevent context-window crashes.

### Step C: Developing with Agent Skills
Agent Skills reside under the `.agents/skills/` directory. Each skill consists of:
* `SKILL.md`: Main instructions with YAML frontmatter defining name and description.
* Supporting resource scripts or examples.

To load a skill's instructions dynamically in Python, use the `load_skill_instructions` utility:
```python
from app.app_utils.skill_utils import load_skill_instructions

research_node = LlmAgent(
    name="research_node",
    model=global_model,
    instruction=load_skill_instructions("researcher")
)
```

### Step D: Verifying Code Quality via Git Hooks
We enforce strict quality standards before any code is committed or pushed. The pre-push hook runs the quality checker located at [scripts/agent_quality_check.py](file:///Users/rmcdonald/Repos/agy-cli-projects/capability-arbitrator/scripts/agent_quality_check.py).

This quality checker ensures:
* **Function Limits:** No node or helper function exceeds 50 lines.
* **File Limits:** No executable Python file exceeds 300 lines.
* **DRY Rule:** No duplicate prompt or loader logic.
* **Typing:** Explicit type signatures on all helper and node functions.
* **Documentation:** Standard header block (Purpose, Why, How) on all modules.

To run the checks manually:
```bash
uv run python scripts/agent_quality_check.py
```

---

## 4. Useful Developer Commands

| Command | Why Use It | How to Run |
|---|---|---|
| **Install Dependencies** | Set up virtual environment and sync libraries | `agents-cli install` |
| **Interactive Playground** | Test agent routing and responses in terminal | `agents-cli playground` |
| **Browser Dev UI** | Test visual traces, dashboard metrics, and security screen | `uv run agents-cli dev` |
| **Run Unit/Integration Tests** | Execute pytest suite locally | `uv run pytest` |
| **Lint & Quality Checks** | Run AST quality checker | `uv run python scripts/agent_quality_check.py` |
| **Deploy to GCP** | Package and deploy FastAPI dashboard to Cloud Run | `agents-cli deploy` |
