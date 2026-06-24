---
name: agy-cli-enforcer
description: Mandatory local workflow skill for executing agent and evaluation operations using antigravity and agents-cli only.
---

# Antigravity CLI Enforcer

**Trigger:** Activate this skill whenever you need to run, evaluate, test, or deploy agent code in this project, or when handling any Google Cloud / Vertex AI authentication issues.

## Mandatory Rules

1. **No GCP CLI Fallbacks**: NEVER use `gcloud` commands to configure projects, check quotas, or authenticate (e.g., `gcloud config set project`, `gcloud auth login`). The user's AGY account is linked to `ryan.mcdonald.us@gmail.com`, and `ascendvent` is a legacy/unrelated default context.
2. **Use `agents-cli` exclusively**: All vibe coding, testing, and evaluation MUST be executed through `agents-cli` (or the underlying Antigravity `agy` commands). 
3. **Eval Configuration**: If `agents-cli eval grade` throws a `403 PERMISSION_DENIED` related to Vertex AI or GCP projects, **do not attempt to fix it with `gcloud`**. Instead, recognize that the LLM-as-a-judge requires explicit Gemini API configurations in `eval_config.yaml` or `.env` rather than defaulting to Vertex AI Application Default Credentials (ADC).
4. **Interactive Testing**: When writing test scripts, do not build custom `InMemoryRunner` loops unless explicitly requested. Always instruct the user to run the standard ADK tool:
   ```bash
   uv run agents-cli run "Test message"
   ```

Always prioritize the Antigravity ecosystem over raw Google Cloud Platform interactions.
