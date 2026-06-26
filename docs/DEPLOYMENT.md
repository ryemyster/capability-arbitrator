# Deployment Guide
### Two Deployment Targets

This project supports two cloud deployment targets. Use the one that matches your need:

| Target | Command | When to use |
| :--- | :--- | :--- |
| **Agent Runtime** | `deploy_agent.py deploy` | Agent query API only — no custom HTTP routes needed |
| **Cloud Run** | `deploy_agent.py deploy --target cloud_run` | Full HTTP surface including `/dashboard`, `/api/run`, `/api/metrics` |

Neither target deploys automatically. Production deployment is always manual — operator-triggered from the terminal or the Antigravity IDE.

---

## Why This Exists

The project needs a deployment path that keeps `main` deployable without making every development push deploy to cloud. Unit tests, integration tests, and local smoke checks should catch regressions early. Cloud deployment should happen only when an operator starts it.

This keeps the default developer loop fast and keeps cloud credentials out of normal PR validation.

---

## What Gets Deployed

### Agent Runtime

The agent query API is deployed via the ADK agent wrapped by [`app/agent_runtime_app.py`](../app/agent_runtime_app.py):

| Setting | Value |
| :--- | :--- |
| Entrypoint module | `app.agent_runtime_app` |
| Entrypoint object | `agent_runtime` |
| Runtime framework | Google ADK |
| Requirements file | `app/app_utils/.requirements.txt` |

Agent Runtime only exposes the agent query API. It does **not** serve custom HTTP routes.

### Cloud Run

The full FastAPI surface is deployed via [`app/fast_api_app.py`](../app/fast_api_app.py) using Google Cloud Buildpacks (no Dockerfile needed — the [`Procfile`](../Procfile) specifies the start command):

| Setting | Value |
| :--- | :--- |
| Entrypoint | `app.fast_api_app:app` (uvicorn via Procfile) |
| Routes served | `/dashboard`, `/api/run`, `/api/metrics`, `/feedback`, `/pubsub`, + ADK base routes |
| Port | `$PORT` (Cloud Run injects 8080) |

> **Note on `/pubsub`:** On Cloud Run, the `/pubsub` route proxies to a remote Agent Runtime instance. It requires a companion Agent Runtime deployment to be running. All other routes (`/dashboard`, `/api/run`, `/api/metrics`, `/feedback`) work standalone.

### Local-only surfaces

| Surface | Command | URL |
| :--- | :--- | :--- |
| Standalone dashboard | `uv run arbitrator dashboard` | `http://127.0.0.1:8000/` |
| Unified FastAPI service | `uv run uvicorn app.fast_api_app:app --host 127.0.0.1 --port 8000` | `http://127.0.0.1:8000` |

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

| Environment | Auth Method | How It Works |
| :--- | :--- | :--- |
| **Local development** | `.env` file | `GOOGLE_GENAI_USE_VERTEXAI=False` + `GOOGLE_API_KEY` loaded via `python-dotenv`. |
| **Agent Runtime (production)** | Application Default Credentials (ADC) | `GOOGLE_GENAI_USE_VERTEXAI=True`. ADC handles auth automatically — the deploy script excludes `GOOGLE_API_KEY` from its env var allow-list. |
| **Cloud Run (production)** | Secret Manager | `GOOGLE_GENAI_USE_VERTEXAI=False`. `GOOGLE_API_KEY` is stored in Secret Manager and injected at container startup via `--set-secrets`. Never set as a plain env var. |

> [!IMPORTANT]
> `GOOGLE_API_KEY` is **never hard-coded or committed**. On Agent Runtime, ADC removes the need for it entirely. On Cloud Run, Secret Manager provides it at runtime with audit logging and independent rotation.

---

## Deployment Script

[`scripts/deploy_agent.py`](../scripts/deploy_agent.py) handles both targets. It reads non-sensitive config flags from your `.env` file and builds the deploy command automatically.

> [!IMPORTANT]
> The `.env` file is **not sent to the cloud**. All env vars are passed explicitly at deploy time — the script handles this for you.

### Agent Runtime

```bash
# Deploy / redeploy (idempotent — updates the existing instance in-place)
uv run python scripts/deploy_agent.py deploy

# Deploy without waiting for completion
uv run python scripts/deploy_agent.py deploy --no-wait

# Check deployment status
uv run python scripts/deploy_agent.py status

# List existing deployments in the project/region
uv run python scripts/deploy_agent.py list

# Delete the deployed agent (reads ID from deployment_metadata.json, prompts for confirmation)
uv run python scripts/deploy_agent.py undeploy
```

> [!NOTE]
> `agents-cli` has no built-in delete command. `undeploy` uses the Vertex AI Python SDK (`vertexai.agent_engines`) and reads the resource ID from `deployment_metadata.json`.

### Cloud Run

```bash
# One-time setup: enable APIs, create GOOGLE_API_KEY secret, grant IAM
# Set CLOUD_RUN_SERVICE_ACCOUNT in .env before running
uv run python scripts/deploy_agent.py init --target cloud_run

# Deploy (or redeploy) — idempotent, works for first deploy and updates
uv run python scripts/deploy_agent.py deploy --target cloud_run

# Check service status and URL
uv run python scripts/deploy_agent.py status --target cloud_run

# Delete — use the existing delete_runtime.sh script
```

#### Finding the deployed dashboard URL

A successful `deploy --target cloud_run` prints the service URL on the last line, e.g.:

```text
Service URL: https://capability-arbitrator-906183434819.us-west1.run.app
```

The dashboard lives at `/dashboard` on that URL:

```text
https://capability-arbitrator-906183434819.us-west1.run.app/dashboard
```

To retrieve the URL again later without redeploying, use either the script or `gcloud`:

```bash
# Via the deploy script (full service description)
uv run python scripts/deploy_agent.py status --target cloud_run

# Just the URL
gcloud run services describe capability-arbitrator \
  --project=YOUR_PROJECT_ID --region=YOUR_REGION \
  --format="value(status.url)"
```

| Route | Full URL (example) |
| :--- | :--- |
| Dashboard | `https://<service-url>/dashboard` |
| Run agent (SSE) | `https://<service-url>/api/run` |
| Metrics | `https://<service-url>/api/metrics` |

> [!NOTE]
> The URL host is stable across redeploys — only the revision changes. The example host above (`capability-arbitrator-906183434819.us-west1.run.app`) is specific to the `kaggle-capstone-500322` project; yours will differ by project number.

Cloud Run deployments use `gcloud run deploy --source .` — Google Cloud Buildpacks automatically build a container from `pyproject.toml` and [`Procfile`](../Procfile). No Dockerfile required.

> [!IMPORTANT]
> **The `Procfile` is required — do not delete it.** It is a committed source file, **not** a build artifact: nothing autogenerates it (not Buildpacks, `gcloud`, `uv`, or the deploy script), so if you delete it, it stays gone. It maps the container's web process to the app's real entrypoint:
> ```
> web: uvicorn app.fast_api_app:app --host 0.0.0.0 --port $PORT
> ```
> Without it, the Python buildpack falls back to its default entrypoint (`main:app`), fails to find `app.fast_api_app:app`, and the service either fails to build or boots the wrong module — `/dashboard` would not serve. The only equivalent without a Procfile is passing `--set-build-env-vars=GOOGLE_ENTRYPOINT="uvicorn app.fast_api_app:app --host 0.0.0.0 --port $PORT"` on every deploy, which is more fragile. Keep the Procfile.

> [!IMPORTANT]
> **Memory:** The service is deployed with `--memory=2Gi` (set via `CR_MEMORY` in [`scripts/deploy_agent.py`](../scripts/deploy_agent.py)). Cloud Run's default of 512 MiB is **not enough** — the FastAPI + ADK + `vertexai` + `google-cloud` import stack OOMs at startup with `Memory limit of 512 MiB exceeded with 512 MiB used`, and the revision silently fails to serve. Do not lower this below ~1Gi.

> [!IMPORTANT]
> **Python version pin:** [`.python-version`](../.python-version) pins the build to Python `3.13`. Without it, Buildpacks default to the newest available interpreter (3.14+), which `uv sync` rejects because `pyproject.toml` requires `>=3.11,<3.14`. The `us-west1` builder only stocks the `3.13.x` and `3.14.x` series, so `3.13` is the only in-range option — do not change this to `3.12` even though that matches some local environments.

---

## Required GCP APIs

The following APIs must be enabled in your GCP project before deployment. Missing any of these will cause silent failures or empty agent responses.

**Agent Runtime:**

```bash
gcloud services enable cloudresourcemanager.googleapis.com --project=YOUR_PROJECT_ID
gcloud services enable aiplatform.googleapis.com --project=YOUR_PROJECT_ID
gcloud services enable logging.googleapis.com --project=YOUR_PROJECT_ID
```

`cloudresourcemanager.googleapis.com` is required by `vertexai.init()` at runtime to resolve the project ID. If it is not enabled, the agent will start but return empty responses with no visible error in the console.

**Cloud Run (additional):**

```bash
gcloud services enable run.googleapis.com --project=YOUR_PROJECT_ID
gcloud services enable cloudbuild.googleapis.com --project=YOUR_PROJECT_ID
gcloud services enable secretmanager.googleapis.com --project=YOUR_PROJECT_ID
```

Run `deploy_agent.py init --target cloud_run` to enable these and perform the one-time Secret Manager setup automatically.

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
| Deploy agent query API to Google Cloud | `deploy_agent.py deploy` (Agent Runtime). |
| Deploy `/dashboard` + full HTTP surface to Google Cloud | `deploy_agent.py deploy --target cloud_run` (Cloud Run). |
| Query the deployed agent from CLI | `agents-cli run --url <runtime-url> --mode adk "your prompt"`. |
| Run the dashboard locally | `uv run arbitrator dashboard`. |
| Run the full FastAPI surface locally | `uv run uvicorn app.fast_api_app:app --host 127.0.0.1 --port 8000`. |

---

## Current Boundary

Two cloud deployment targets are supported:

- **Agent Runtime** — agent query API; managed by `agents-cli`; no custom HTTP routes.
- **Cloud Run** — full HTTP surface including `/dashboard`; source-based deployment via Buildpacks; `GOOGLE_API_KEY` via Secret Manager.

Production deployment for both is manual only — operator-triggered from the terminal or Antigravity IDE. There is no automatic deployment on merge or test pass.
