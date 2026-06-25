# GitHub Agent Flows and Manual Cloud Setup
### Local Validation, Runtime Smoke Tests, and Optional Google Cloud Deployment

This guide explains this repository's GitHub Actions model. The default workflows are **agent validation flows** that run locally on GitHub-hosted runners. They do not deploy to Google Cloud when they finish.

Google Cloud setup is still documented here because the repository keeps a manual production deployment workflow. That deployment must be triggered intentionally.

After setup:

- Pull requests to `develop` run **Agent Validation**.
- Pushes to `develop` run **Agent Validation**.
- Operators can manually run **Local Runtime Smoke** to start the dashboard, check local routes, run CLI commands, and tear everything down.
- Operators can manually run **Manual Cloud Production Deploy** when cloud deployment is intentionally needed.
- No workflow automatically deploys after validation completes.

---

## Why This Exists

GitHub should first prove that the agent works locally: dependencies install, tests pass, CLI commands run, and the dashboard can start. Those checks should not require cloud credentials.

Cloud deployment is a separate operator action. When the manual production deployment workflow runs, it needs permission to deploy to Google Cloud. The unsafe way to do that is to store a long-lived Google Cloud key in GitHub.

This repository uses **Workload Identity Federation (WIF)** for that manual deployment path. In plain English, WIF lets GitHub Actions prove its identity to Google Cloud at runtime. Google Cloud then issues a short-lived token for that one workflow run.

This reduces credential risk because there is no permanent Google Cloud service account key sitting in GitHub secrets.

---

## What This Sets Up

The GitHub Actions workflows are:

| Workflow | File | Trigger | Cloud Access? | Purpose |
| :--- | :--- | :--- | :--- | :--- |
| Agent Validation | [`.github/workflows/pr_checks.yaml`](../.github/workflows/pr_checks.yaml) | Pull request, push to `develop`, or manual run | No | Runs `uv sync --locked`, `uv run pytest`, and safe CLI smoke commands. Pytest is configured to collect stable unit and integration tests by default. The `arbitrator run` smoke prompt intentionally uses the PII route so it stays local and does not call the Scout model. |
| Local Runtime Smoke | [`.github/workflows/local-runtime-smoke.yaml`](../.github/workflows/local-runtime-smoke.yaml) | Manual run only | No | Starts `uv run python app/dashboard.py`, checks local routes, runs local-safe CLI commands, then tears down the process. |
| Manual Cloud Production Deploy | [`.github/workflows/deploy-to-prod.yaml`](../.github/workflows/deploy-to-prod.yaml) | Manual run only | Yes | Deploys to production when an operator explicitly starts it. |

The Terraform configuration in [`deployment/terraform/cicd`](../deployment/terraform/cicd) creates and wires the cloud resources needed by the manual deployment path:

| Area | What Gets Created |
| :--- | :--- |
| Google Cloud identity | Workload Identity Pool, OIDC provider, CI/CD runner service account, app service accounts. |
| Google Cloud access | IAM bindings for staging and production deployment. |
| Storage and telemetry | Logs buckets and telemetry resources. |
| GitHub Actions settings | Repository variables, repository secrets, and the `production` environment. |

---

## When To Use This Guide

Use this guide when:

- You are setting up GitHub agent validation flows for a fresh fork.
- GitHub Actions fails at `Authenticate to Google Cloud`.
- You changed the Google Cloud project IDs, region, repository owner, or repository name.
- You need to verify that manual production deployment uses the right service account.

Do not use this guide for local development. Local setup is covered in [Development](DEVELOPMENT.md).

---

## Prerequisites

You need these before running Terraform.

| Requirement | Why It Matters |
| :--- | :--- |
| Three Google Cloud projects | Keeps CI/CD infrastructure, staging, and production isolated. |
| Google Cloud permissions | Your account must be able to enable APIs, create service accounts, assign IAM roles, and create storage/telemetry resources. |
| GitHub repository admin access | Terraform creates repository Actions variables, secrets, and the `production` environment. |
| `gcloud` CLI | Authenticates your terminal to Google Cloud. |
| `terraform` | Provisions the Google Cloud and GitHub resources from code. |
| GitHub token for Terraform | The GitHub Terraform provider needs permission to manage repository settings. |

Install links:

| Tool | Install |
| :--- | :--- |
| `gcloud` CLI | [Install gcloud](https://cloud.google.com/sdk/docs/install) |
| `terraform` | [Install Terraform](https://developer.hashicorp.com/terraform/install) |

Authenticate to Google Cloud:

```bash
gcloud auth login
gcloud auth application-default login
```

Set a GitHub token for Terraform. Use a token that can manage repository Actions secrets, Actions variables, and environments.

```bash
export GITHUB_TOKEN="YOUR_GITHUB_TOKEN"
```

---

## Step 1: Create Three Google Cloud Projects

Create three separate projects in [Google Cloud Console](https://console.cloud.google.com).

| Purpose | Suggested Display Name | Example Project ID |
| :--- | :--- | :--- |
| CI/CD infrastructure | `capability-arbitrator-cicd` | `my-company-ca-cicd` |
| Staging environment | `capability-arbitrator-staging` | `my-company-ca-staging` |
| Production environment | `capability-arbitrator-prod` | `my-company-ca-prod` |

Use the **Project ID**, not the display name, in Terraform. The Project ID is the unique string Google Cloud shows under the display name. It cannot be changed after project creation.

---

## Step 2: Configure Terraform Variables

Open [`deployment/terraform/cicd/vars/env.tfvars`](../deployment/terraform/cicd/vars/env.tfvars) and replace the placeholders.

```hcl
project_name           = "capability-arbitrator"
prod_project_id        = "my-company-ca-prod"
staging_project_id     = "my-company-ca-staging"
cicd_runner_project_id = "my-company-ca-cicd"
repository_owner       = "ryemyster"
repository_name        = "capability-arbitrator"
region                 = "us-east1"
```

Keep `project_name = "capability-arbitrator"` unless you also want different WIF resource names.

The generated WIF names are:

| Resource | Generated Name |
| :--- | :--- |
| Workload Identity Pool | `capability-arbitrator-pool` |
| Workload Identity Provider | `capability-arbitrator-oidc` |

---

## Step 3: Run Terraform

Run Terraform from the CI/CD Terraform directory.

```bash
cd deployment/terraform/cicd
terraform init
terraform apply -var-file=vars/env.tfvars
```

Terraform prints a plan. Review it, then type `yes` to apply.

Expected output includes values like these:

```text
app_service_account_emails = {
  "prod"    = "ca-app-prod@my-company-ca-cicd.iam.gserviceaccount.com"
  "staging" = "ca-app-staging@my-company-ca-cicd.iam.gserviceaccount.com"
}
cicd_runner_service_account_email = "ca-cicd-runner@my-company-ca-cicd.iam.gserviceaccount.com"
logs_bucket_names = {
  "prod"    = "ca-logs-prod-abc123"
  "staging" = "ca-logs-staging-abc123"
}
```

Terraform should also create the GitHub Actions settings defined in [`deployment/terraform/cicd/github.tf`](../deployment/terraform/cicd/github.tf).

---

## Step 4: Verify GitHub Actions Settings

In GitHub, open:

`Settings` -> `Secrets and variables` -> `Actions`

Terraform should create these repository secrets:

| Secret | Expected Source |
| :--- | :--- |
| `WIF_POOL_ID` | Terraform WIF pool ID, usually `capability-arbitrator-pool`. |
| `WIF_PROVIDER_ID` | Terraform WIF provider ID, usually `capability-arbitrator-oidc`. |
| `GCP_SERVICE_ACCOUNT` | CI/CD runner service account email. |

Terraform should create these repository variables:

| Variable | Expected Source |
| :--- | :--- |
| `GCP_PROJECT_NUMBER` | Numeric project number for the CI/CD project. |
| `CICD_PROJECT_ID` | CI/CD project ID. |
| `STAGING_PROJECT_ID` | Staging project ID. |
| `PROD_PROJECT_ID` | Production project ID. |
| `REGION` | Deployment region, usually `us-east1`. |
| `APP_SERVICE_ACCOUNT_STAGING` | Staging app service account email. |
| `APP_SERVICE_ACCOUNT_PROD` | Production app service account email. |
| `LOGS_BUCKET_NAME_STAGING` | Staging logs bucket name. |
| `LOGS_BUCKET_NAME_PROD` | Production logs bucket name. |

If Terraform did not create these values because the GitHub token was missing or under-scoped, create them manually in GitHub using the Terraform outputs.

---

## Step 5: Configure Production Approval

Terraform creates a GitHub environment named `production`. To require manual approval before production deployment:

1. Open the repository in GitHub.
2. Go to `Settings` -> `Environments`.
3. Select `production`.
4. Under protection rules, enable `Required reviewers`.
5. Add the users or teams who can approve production deployments.

Without this protection rule, the production workflow can run without a manual approval pause.

---

## Step 6: Verify the GitHub Agent Flows

Push a small change to a branch with a pull request into `develop`, or run the workflow manually.

Then verify:

1. Open the repository `Actions` tab.
2. Select `Agent Validation`.
3. Confirm dependencies install with `uv sync --locked`.
4. Confirm `uv run pytest` passes.
5. Confirm the CLI smoke step runs `arbitrator run`, `stride-heal --help`, and `flywheel --help`.

To verify the manual runtime smoke flow:

1. Open the repository `Actions` tab.
2. Select `Local Runtime Smoke`.
3. Click `Run workflow`.
4. Confirm the job starts `uv run python app/dashboard.py`.
5. Confirm the job checks `/` and `/api/metrics`.
6. Confirm the job runs local arbitrator commands.
7. Confirm the dashboard process is stopped when the job exits.

Neither flow deploys to Google Cloud.

---

## Manual Fallback Values

Use this section only if Terraform could not write GitHub settings.

Find the CI/CD project number:

```bash
gcloud projects describe YOUR_CICD_PROJECT_ID --format="value(projectNumber)"
```

Then create the same secrets and variables listed in [Step 4](#step-4-verify-github-actions-settings).

The WIF provider path used by the workflows is built from these values:

```text
projects/${GCP_PROJECT_NUMBER}/locations/global/workloadIdentityPools/${WIF_POOL_ID}/providers/${WIF_PROVIDER_ID}
```

---

## Troubleshooting

### `Invalid value for "audience"`

Example error:

```text
Error: google-github-actions/auth failed with: failed to generate Google Cloud federated token for
//iam.googleapis.com/projects//locations/global/workloadIdentityPools//providers/
```

The empty sections in the provider path usually mean one or more GitHub values are missing.

Check:

- `GCP_PROJECT_NUMBER` exists under repository variables.
- `WIF_POOL_ID` exists under repository secrets.
- `WIF_PROVIDER_ID` exists under repository secrets.
- The values are repository-level values available to the workflow.

### `Failed to compute a project ID`

This usually appears after authentication fails or when `CICD_PROJECT_ID` is missing.

Fix the authentication variables first. Then confirm `CICD_PROJECT_ID` exists under repository variables.

### Terraform Cannot Manage GitHub Settings

If Terraform fails while creating GitHub Actions secrets or variables:

- Confirm `GITHUB_TOKEN` is set in your shell.
- Confirm the token has repository administration access.
- Confirm `repository_owner` and `repository_name` in `env.tfvars` match the GitHub repository.
- Use the manual fallback section if you cannot grant Terraform GitHub access.

### Terraform Permission Error

If Terraform reports that your user does not have permission, your Google account needs stronger access on the relevant projects.

At minimum, the setup account must be able to:

- Enable Google Cloud APIs.
- Create service accounts.
- Assign IAM roles.
- Create storage buckets and telemetry resources.
- Read project metadata.

Grant the needed permissions in [IAM & Admin](https://console.cloud.google.com/iam-admin), then rerun:

```bash
terraform apply -var-file=vars/env.tfvars
```

### Terraform Project Not Found

The project ID in `env.tfvars` does not match an existing Google Cloud project.

Check available projects:

```bash
gcloud projects list
```

Then correct `prod_project_id`, `staging_project_id`, or `cicd_runner_project_id`.

---

## Operator Checklist

Before considering GitHub agent flows ready, confirm:

- Terraform apply completed without errors.
- GitHub Actions secrets and variables exist.
- The `production` GitHub environment exists.
- Required reviewers are configured if production needs manual approval.
- `Agent Validation` passes on pull requests.
- `Agent Validation` passes on pushes to `develop`.
- `Local Runtime Smoke` passes when manually triggered.
- `Manual Cloud Production Deploy` runs only when manually triggered.
- Production deployment uses the approval behavior you expect.
