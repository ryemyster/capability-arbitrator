# Developer Portal
### Setting Up, Developing, and Configuring Local Workflows

Welcome to the Capability Arbitrator developer guide. This document outlines the local environment configuration, tool integration patterns, and code quality controls required to build features.

---

## Environment Prerequisites

Before starting, ensure you have the following installed on your machine:
* **Python Runtime:** Python 3.12 or newer.
* **Package Manager:** [uv](https://docs.astral.sh/uv/) for lightning-fast package syncing.
* **Orchestration CLI:** `google-agents-cli` (installed via `uv tool install google-agents-cli`).

---

## Installation and Setup

1. **Clone the Codebase & Install Dependencies:**
   ```bash
   cd capability-arbitrator
   agents-cli install
   ```

2. **Verify Environment Configuration:**
   Copy the sample environment variables file and configure your credentials:
   ```bash
   cp .env.example .env
   ```

> [!CAUTION]
> **Secret Zero-Trust:** Never commit `.env` files or hardcode API keys. The local quality checking engine scans files for exposed credentials.

---

## Model Context Protocol (MCP) Integration

The Capability Arbitrator utilizes MCP to standardise how sub-agents access system resources. By default, it exposes a local filesystem MCP toolset to the `coding_node` and `mcp_node`.

### Filesystem MCP Setup
In [app/agent.py](../app/agent.py), the toolset is registered via standard node stdio transports:
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

> [!WARNING]
> **Recursive Tree Protection:** To prevent context overload, sub-agents are strictly forbidden from running recursive file tree structures (`directory_tree` on `.`). Direct sub-agents to use `list_directory` or `search_files` instead.

---

## Developing with Agent Skills

Specialized agent workflows are encapsulated as **Skills** under the `.agents/skills/` directory. Each skill must contain:
1. `SKILL.md`: Markdown instructions containing standard YAML frontmatter (`name` and `description`).
2. Optional supporting code examples, prompt templates, or testing scripts.

### Loading Skills Dynamically
Skills are progressively disclosed (loaded into memory only when targeted by the router) using our loader utilities:
```python
from app.app_utils.skill_utils import load_skill_instructions

research_node = LlmAgent(
    name="research_node",
    model=global_model,
    instruction=load_skill_instructions("researcher")
)
```

---

## Git Quality Gates and Verification

We enforce strict codebase formatting and structural constraints via pre-commit and pre-push hooks. 

### Automated AST Quality Auditor
The local auditor [scripts/agent_quality_check.py](../scripts/agent_quality_check.py) parses modifications before they are pushed, enforcing:
* **Function Limits:** No node or helper function may exceed 50 lines.
* **File Limits:** No executable Python file may exceed 300 lines.
* **Typing:** Explicit type signatures are required on all helper functions.
* **Documentation:** A standard header block detailing `Purpose`, `Why`, and `How` is required on all modules.

To execute the code quality scan manually:
```bash
uv run python scripts/agent_quality_check.py
```

---

## Developer Command Reference

| Action | Command | Purpose |
| :--- | :--- | :--- |
| **Sync Packages** | `agents-cli install` | Syncs the virtual environment using `uv` |
| **ADK Playground** | `agents-cli playground` | Starts the ADK development UI at `http://127.0.0.1:8080/dev-ui` |
| **Standalone Dashboard** | `uv run arbitrator dashboard` | Starts the custom telemetry dashboard at `http://127.0.0.1:8000/` |
| **Unified FastAPI Service** | `uv run uvicorn app.fast_api_app:app --host 127.0.0.1 --port 8000` | Starts ADK web UI, custom dashboard, `/api/run`, `/api/metrics`, and `/pubsub` |
| **Verify Tests** | `uv run pytest` | Executes the standard CI verification checks |
| **Check Quality** | `uv run python scripts/agent_quality_check.py` | Runs AST linting rules |
| **Clean Generated Artifacts** | `uv run python scripts/cleanup_generated_artifacts.py` | Removes local telemetry, debug files, test outputs, and Python caches |
| **Cloud Deploy** | `agents-cli deploy` | Manually deploys the ADK agent through the configured Agents CLI path |

## Local Runtime URLs

| URL | Launch Mode | What You Should See |
| :--- | :--- | :--- |
| `http://127.0.0.1:8080/dev-ui` | `agents-cli playground` | ADK development playground |
| `http://127.0.0.1:8000/` | `uv run arbitrator dashboard` | Custom telemetry dashboard |
| `http://127.0.0.1:8000/` | `uv run uvicorn app.fast_api_app:app --host 127.0.0.1 --port 8000` | ADK web UI root |
| `http://127.0.0.1:8000/dashboard` | Unified FastAPI service | Custom telemetry dashboard |
