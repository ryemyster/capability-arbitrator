# Capability Arbitrator Customizations & Agent Guidelines

This file outlines the rules, skills, and workflows that govern agent operations in this workspace.

---

## 1. Rules (Always follow these constraints)

These constraints are mandatory and must be strictly followed for all operations.

### Sandbox & Code Isolation
- **Workspace & Core Code Isolation Guardrail (CRITICAL)**:
  - You must ONLY read and modify files inside the current project directory (`/Users/rmcdonald/Repos/agy-cli-projects/capability-arbitrator`).
  - You are STRICTLY FORBIDDEN from navigating into or reading files from Antigravity system directories, such as `/Users/rmcdonald/.gemini/` or `/Users/rmcdonald/.gemini/antigravity-cli/brain/` (except the conversation's own artifacts folder if writing/updating artifacts).
  - You are STRICTLY FORBIDDEN from reading or modifying generated Python files (e.g., those under `app/.adk/` or any `__pycache__/` directories).
  - ONLY read/modify core source code files in the project workspace (e.g., `app/`, `tests/`, `scripts/`, `docs/`, `pyproject.toml`, or `agents-cli-manifest.yaml`).

### Security Gates
- **Secret Zero-Trust**: NEVER read the contents of `.env` files using `view_file` or any terminal command.
- **No Leakage**: NEVER output API keys, environment variables, or sensitive credentials in the response.

### GitHub Interactions
- **Mandatory MCP usage**: ALWAYS use the `github` MCP server for ALL GitHub interactions. Do not fall back to curl or other tools when interacting with GitHub; use the provided MCP tools.
- **No Direct Remote Git Commands**: Prioritize remote interactions through the official `github` MCP server.

### Development Environment & Commands
- **No GCP CLI Fallbacks**: NEVER use `gcloud` commands to configure projects, check quotas, or authenticate.
- **Use `agents-cli` exclusively**: All vibe coding, testing, and evaluation MUST be executed through `agents-cli` (or the underlying Antigravity `agy` commands).
- **Run Python with `uv`**: Always execute Python scripts using `uv run python script.py`. Ensure `agents-cli install` is run first.
- **Stop on repeated errors**: If the same error appears 3+ times, fix the root cause instead of retrying.
- **Terraform conflicts**: For Error 409 (resource conflicts), use `terraform import` instead of retrying creation.

### Code & Model Integrity
- **Code preservation**: Only modify code directly targeted by the user's request. Preserve all surrounding code, config values, comments, and formatting.
- **Model Integrity**: NEVER change the model unless explicitly asked. Fix `GOOGLE_CLOUD_LOCATION` (e.g., `global` instead of `us-east1`) for 404 errors, not the model name.
- **ADK tool imports**: Import the tool instance, not the module (e.g., `from google.adk.tools.load_web_page import load_web_page`).
- **AI Agent Coding Quality Rules**:
  - Keep functions/nodes below 50 lines and files below 300 lines of executable code.
  - Follow the DRY (Don't Repeat Yourself) principle. Do not duplicate loading or logic code (e.g. loader/prompt logic).
  - Provide explicit python type annotations on all helper/utility functions.
  - Provide a standard Header Block (Purpose, Why, How) on all newly created modules.

---

## 2. Skills (Reusable capabilities invoked when relevant)

Skills are specialized capabilities residing under `.agents/skills/`. Each skill contains specific rule components:

- **agy-cli-enforcer** ([agy-cli-enforcer](file:///Users/rmcdonald/Repos/agy-cli-projects/capability-arbitrator/.agents/skills/agy-cli-enforcer/SKILL.md)):
  - *Trigger*: Invoked when running, evaluating, testing, or deploying agent code, or handling auth issues.
  - *Rule Component*: Enforces exclusive use of `agents-cli`, forbids `gcloud` fallbacks, and guides Vertex AI API configurations for evaluation.
- **code-documenter** ([code-documenter](file:///Users/rmcdonald/Repos/agy-cli-projects/capability-arbitrator/.agents/skills/code-documenter/SKILL.md)):
  - *Trigger*: Invoked when creating new source files or refactoring existing ones.
  - *Rule Component*: Requires a standard Header Block (Purpose, Why, How) and inline comments simple enough for a 15-year-old.
- **doc-writer** ([doc-writer](file:///Users/rmcdonald/Repos/agy-cli-projects/capability-arbitrator/.agents/skills/doc-writer/SKILL.md)):
  - *Trigger*: Invoked when writing/updating repository documentation.
  - *Rule Component*: Enforces the 15-year-old readability rule and the Four Pillars (Why, What, How, When).
- **github-best-practices** ([github-best-practices](file:///Users/rmcdonald/Repos/agy-cli-projects/capability-arbitrator/.agents/skills/github-best-practices/SKILL.md)):
  - *Trigger*: Invoked during git branching, commits, PRs, or issue closing.
  - *Rule Component*: Enforces branch-naming standards, atomic commits, detailed PR descriptions, and issue checklist/closing verification comments.
- **researcher** ([researcher](file:///Users/rmcdonald/Repos/agy-cli-projects/capability-arbitrator/app/skills/researcher/SKILL.md)):
  - *Trigger*: Loaded dynamically by `research_node` at runtime during literature parsing or document summarization.
  - *Rule Component*: Strict boundaries (no coding, no math), IEEE citation format, and structured summaries (Executive Summary and Methodology).
- **rubric-tracker** ([rubric-tracker](file:///Users/rmcdonald/Repos/agy-cli-projects/capability-arbitrator/.agents/skills/rubric-tracker/SKILL.md)):
  - *Trigger*: Invoked when features or phases are completed.
  - *Rule Component*: Requires updating `kaggle_objectives.md` with citations and reviewing outstanding rubric items at the end of the turn.
- **phase-testing** ([phase-testing](file:///Users/rmcdonald/Repos/agy-cli-projects/capability-arbitrator/.agents/skills/phase-testing/SKILL.md)):
  - *Trigger*: Programmatically invoked when completing any development phase.
  - *Rule Component*: Proactively creates automated python test scripts and manual QA markdown scripts with timestamps.

---

## 3. Workflows (Multi-step procedures)

These procedures define structured, multi-step workflows that must be executed in sequence.

### Development Lifecycle Workflow
Follow the 7 development phases sequentially:
1. **Understand Requirements**: Clarify requirements, constraints, and success criteria.
2. **Build and Implement**: Write agent logic in `app/`. Use `agents-cli playground` to test interactively.
3. **The Evaluation Loop (Main Iteration Phase)**: Synthesize dataset (`agents-cli eval dataset synthesize`), run agent on dataset (`agents-cli eval generate`), grade traces (`agents-cli eval grade`), analyze failure modes (`agents-cli eval analyze`), compare results (`agents-cli eval compare`), and auto-tune prompts (`agents-cli eval optimize`).
4. **Pre-Deployment Tests**: Execute `uv run pytest tests/unit tests/integration` to verify unit and integration tests.
5. **Deploy to Dev**: Propose deployment and obtain explicit user approval, then run `agents-cli deploy`.
6. **Production Deployment**: Consult the user to choose Option A (simple project) or Option B (CI/CD pipeline with `agents-cli infra cicd`).
7. **Daily Use and Production Integration**: Configure the arbitrator as a daemon for everyday developer tasks (automated reviews, ticket triage, and regression testing).

### Phase Completion Verification Workflow
When a development phase is finalized or the user indicates a phase is complete:
1. Create an automated test folder and script: `tests/scripts/phase<NUMBER>-<name>/test_<name>.py`. Prepend the `# Created: <CURRENT_LOCAL_TIME>` timestamp to line 1.
2. Create a manual QA markdown file: `tests/manual_test_scripts/phase<NUMBER>-<name>/QA_<name>.md`. Append the `*Created: <CURRENT_LOCAL_TIME>*` timestamp to the end.
3. Run the automated script using `uv run python tests/scripts/...` and ensure it outputs clean `[PASS]` or `[FAIL]` indicators.
4. Notify the user of the generated testing scaffolding.

### Kaggle Rubric Tracking Workflow
When completing any new feature:
1. Open and review `docs/RUBRIC.md`.
2. Update `docs/kaggle_objectives.md` by checking off fulfilled objectives and appending an italicized citation: `*(Completed: Phase X [description] in [filepath])*`.
3. In the final response of the turn, list the objectives just completed and outline the outstanding items.

### GitHub Issue Resolution Workflow
To resolve and close a GitHub issue:
1. Perform development on a feature branch (`feature/description` or `fix/description`).
2. Commit logically separated changes atomically with clear commit messages.
3. Open a detailed PR referencing the issue (e.g., `Closes #42`).
4. Update the issue body to check off all items (`[x]`).
5. Add a comment to the issue listing how each checked-off item was fulfilled, citing code artifacts and line numbers. Do NOT close the issue without this comment.
