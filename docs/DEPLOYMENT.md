# Deployment Guide
### ADK CLI and Agent Runtime Deployment

This project does not use a custom container build as the supported deployment path. The supported path is:

1. Validate locally.
2. Provision Google Cloud identity and Agent Runtime infrastructure when needed.
3. Deploy intentionally with the ADK / Agents CLI workflow.

GitHub Actions do not deploy automatically after tests pass. Production deployment is manual.

---

## Why This Exists

The project needs a deployment path that keeps `main` deployable without making every development push deploy to cloud. Unit tests, integration tests, and local smoke checks should catch regressions early. Cloud deployment should happen only when an operator starts it.

This keeps the default developer loop fast and keeps cloud credentials out of normal PR validation.

---

## What Gets Deployed

The deployable runtime is the ADK agent wrapped by [`app/agent_runtime_app.py`](../app/agent_runtime_app.py). Terraform provisions Vertex AI Agent Runtime / Reasoning Engine resources with:

| Setting | Value |
| :--- | :--- |
| Entrypoint module | `app.agent_runtime_app` |
| Entrypoint object | `agent_runtime` |
| Runtime framework | Google ADK |
| Requirements file | `app/app_utils/.requirements.txt` |

The local dashboard and unified FastAPI app are **local-only development surfaces** — they are not deployed to Agent Runtime:

| Surface | Command | URL |
| :--- | :--- | :--- |
| Standalone dashboard | `uv run arbitrator dashboard` | `http://127.0.0.1:8000/` |
| Unified FastAPI service | `uv run uvicorn app.fast_api_app:app --host 127.0.0.1 --port 8000` | `/`, `/dashboard`, `/api/run`, `/api/metrics`, `/pubsub` |

> [!WARNING]
> **The dashboard is not available on Agent Runtime.** Agent Runtime only exposes the agent's query API (used by the GCP Console Playground and `agents-cli run --url`). It does not serve custom HTTP routes like `/dashboard`. To use the dashboard, run it locally.

---

## How To Validate Before Deployment

Run the same default test command used by GitHub Actions:

```bash
uv run pytest
```

The default pytest configuration collects only stable unit and integration tests:

```text
tests/unit
tests/integration
```

Legacy phase scripts under `tests/scripts` are opt-in manual checks and are not part of default pytest collection.

For a local dashboard check:

```bash
uv run arbitrator dashboard
```

Open:

```text
http://127.0.0.1:8000/
```

---

## Authentication

This project does **not** use Google Cloud Secret Manager for API key storage.

| Environment | Auth Method | How It Works |
| :--- | :--- | :--- |
| **Local development** | `.env` file | Set `GOOGLE_GENAI_USE_VERTEXAI=True` and `GOOGLE_API_KEY` in `.env`. The ADK loads these via `python-dotenv` at startup. |
| **Agent Runtime (production)** | Application Default Credentials (ADC) | Set `GOOGLE_GENAI_USE_VERTEXAI=True` as a deployed env var. The Agent Runtime infrastructure handles authentication automatically — no raw API keys are sent to the cloud. |

> [!IMPORTANT]
> `GOOGLE_API_KEY` is **never deployed** to Agent Runtime. With `GOOGLE_GENAI_USE_VERTEXAI=True`, ADC provides secure, managed authentication. The deploy script intentionally excludes it from the env var allow-list.

---

## Local Deployment Script

Use [`scripts/deploy_agent.py`](../scripts/deploy_agent.py) for local operator deployments. It reads non-sensitive config flags from your `.env` file and passes them to `agents-cli deploy` automatically.

> [!IMPORTANT]
> The `.env` file is **not sent to the cloud**. `load_dotenv()` only works locally. All env vars must be passed explicitly at deploy time via `--update-env-vars` — the script handles this for you.

```bash
# Deploy (reads env vars from .env, passes to agents-cli)
uv run python scripts/deploy_agent.py deploy

# Deploy without waiting (check status later)
uv run python scripts/deploy_agent.py deploy --no-wait

# Check deployment status
uv run python scripts/deploy_agent.py status

# Redeploy (Agent Runtime updates in-place, no delete needed)
uv run python scripts/deploy_agent.py redeploy

# List existing deployments in the project/region
uv run python scripts/deploy_agent.py list

# Delete the deployed agent (reads ID from deployment_metadata.json)
uv run python scripts/deploy_agent.py undeploy
```

Agent Runtime deployments are **idempotent** — deploying again updates the existing instance in-place. There is no separate stop/delete step required.

> [!NOTE]
> `agents-cli` does not have a built-in delete/undeploy command. The `undeploy` command uses the Vertex AI Python SDK (`vertexai.agent_engines`) to delete the Agent Runtime instance. It reads the resource ID from `deployment_metadata.json` and prompts for confirmation before deleting.

---

## How To Deploy (GitHub Actions)

Use the manual GitHub workflow when deploying from GitHub:

1. Open the repository in GitHub.
2. Go to `Actions`.
3. Select `Manual Cloud Production Deploy`.
4. Click `Run workflow`.
5. Approve the `production` environment gate if required.

The workflow uses:

```bash
uvx google-agents-cli deploy
```

with the configured Google Cloud project, region, service account, and environment variables.

For local operator deployment, use the same ADK / Agents CLI deployment flow after authenticating to Google Cloud:

```bash
agents-cli deploy
```

---

## Required GCP APIs

The following APIs must be enabled in your GCP project before deployment. Missing any of these will cause silent failures or empty agent responses.

```bash
gcloud services enable cloudresourcemanager.googleapis.com --project=YOUR_PROJECT_ID
gcloud services enable aiplatform.googleapis.com --project=YOUR_PROJECT_ID
gcloud services enable logging.googleapis.com --project=YOUR_PROJECT_ID
```

`cloudresourcemanager.googleapis.com` is required by `vertexai.init()` at runtime to resolve the project ID. If it is not enabled, the agent will start but return empty responses with no visible error in the console.

> [!CAUTION]
> **Model availability:** Not all Gemini models are available in all regions. `us-west1` only supports `gemini-2.5-flash` and `gemini-2.5-flash-lite`. If you change the deployment region, verify the model in `app/config.py` is available there before deploying.

---

## Required Configuration

The manual deployment workflow expects GitHub Actions variables and secrets created by the Terraform setup in [`deployment/terraform/cicd`](../deployment/terraform/cicd).

| Name | Type | Purpose |
| :--- | :--- | :--- |
| `GCP_PROJECT_NUMBER` | Variable | Builds the Workload Identity Provider path. |
| `CICD_PROJECT_ID` | Variable | Project used for deployment authentication. |
| `PROD_PROJECT_ID` | Variable | Production deploy target. |
| `REGION` | Variable | Google Cloud deployment region. |
| `APP_SERVICE_ACCOUNT_PROD` | Variable | Runtime service account for production. |
| `LOGS_BUCKET_NAME_PROD` | Variable | Artifact/log storage used by the runtime. |
| `WIF_POOL_ID` | Secret | Workload Identity Pool ID. |
| `WIF_PROVIDER_ID` | Secret | Workload Identity Provider ID. |
| `GCP_SERVICE_ACCOUNT` | Secret | CI/CD runner service account email. |

See [GitHub Agent Flows and Manual Cloud Setup](CICD_SETUP.md) for the full setup process.

---

## Deployment Metadata

`deployment_metadata.json` is a generated local artifact, not source-controlled configuration. It stores the deployed Reasoning Engine resource ID used by optional load tests.

Use the template when you need to run load tests against a deployed runtime:

```bash
cp deployment_metadata.example.json deployment_metadata.json
```

Then replace `remote_agent_runtime_id` with the real resource ID from the deployment output.

The real `deployment_metadata.json` file is ignored by git and removed by the generated-artifact cleanup script.

---

## When To Use Each Surface

| Need | Use |
| :--- | :--- |
| Catch regressions during development | `uv run pytest` or the `Agent Validation` workflow. |
| Check dashboard startup and local CLI commands | `Local Runtime Smoke` workflow. |
| Deploy the ADK agent to Google Cloud | `Manual Cloud Production Deploy` workflow or `agents-cli deploy`. |
| Query the deployed agent from CLI | `agents-cli run --url <runtime-url> --mode adk "your prompt"`. |
| Work on the local dashboard only | `uv run arbitrator dashboard` (local only — not available on Agent Runtime). |
| Work on the unified local FastAPI app | `uv run uvicorn app.fast_api_app:app --host 127.0.0.1 --port 8000` (local only). |

---

## Current Boundary

There is intentionally no supported custom container path in this repository. If a future team wants a separate container deployment, it should be added as a new, tested deployment surface with its own workflow and documentation.
