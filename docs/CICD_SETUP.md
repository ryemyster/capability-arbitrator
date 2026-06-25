# CI/CD Setup
### GitHub Actions, Google Cloud, and Workload Identity Federation

This guide explains how to connect this repository's GitHub Actions workflows to Google Cloud. It is a one-time setup for repository operators.

After setup:

- Pull requests to `develop` run CI checks.
- Pushes to `develop` that touch application, test, deployment, or `uv.lock` paths deploy to staging.
- A successful staging deploy calls the production workflow.
- Production can pause for manual approval if the GitHub `production` environment has required reviewers.

---

## Why This Exists

The deployment workflows need permission to deploy to Google Cloud. The unsafe way to do that is to store a long-lived Google Cloud key in GitHub.

This repository uses **Workload Identity Federation (WIF)** instead. In plain English, WIF lets GitHub Actions prove its identity to Google Cloud at runtime. Google Cloud then issues a short-lived token for that one workflow run.

This reduces credential risk because there is no permanent Google Cloud service account key sitting in GitHub secrets.

---

## What This Sets Up

The Terraform configuration in [`deployment/terraform/cicd`](../deployment/terraform/cicd) creates and wires these resources:

| Area | What Gets Created |
| :--- | :--- |
| Google Cloud identity | Workload Identity Pool, OIDC provider, CI/CD runner service account, app service accounts. |
| Google Cloud access | IAM bindings for staging and production deployment. |
| Storage and telemetry | Logs buckets and telemetry resources used by deploy/load-test workflows. |
| GitHub Actions settings | Repository variables, repository secrets, and the `production` environment. |

The workflows that use this setup are:

| Workflow | File | Trigger |
| :--- | :--- | :--- |
| PR checks | [`.github/workflows/pr_checks.yaml`](../.github/workflows/pr_checks.yaml) | Pull requests into `develop`. |
| Staging deploy | [`.github/workflows/staging.yaml`](../.github/workflows/staging.yaml) | Pushes to `develop` when relevant paths change. |
| Production deploy | [`.github/workflows/deploy-to-prod.yaml`](../.github/workflows/deploy-to-prod.yaml) | Called by staging or run manually with `workflow_dispatch`. |

---

## When To Use This Guide

Use this guide when:

- You are setting up CI/CD for a fresh fork or deployment environment.
- GitHub Actions fails at `Authenticate to Google Cloud`.
- You changed the Google Cloud project IDs, region, repository owner, or repository name.
- You need to verify that staging and production deploys are using the right service accounts.

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

## Step 6: Verify the Pipeline

Push a small relevant change to `develop`, or re-run a failed workflow.

The staging workflow only runs when one of these paths changes:

```text
app/**
data_ingestion/**
tests/**
deployment/**
uv.lock
```

Then verify:

1. Open the repository `Actions` tab.
2. Select `Deploy to Staging`.
3. Confirm `Authenticate to Google Cloud` has a green check.
4. Confirm `Deploy to Staging (Agent Runtime)` succeeds.
5. Confirm the load test runs and writes results to the staging logs bucket.
6. Confirm the production workflow starts after staging succeeds.

If production approval is enabled, the production workflow should pause at the `production` environment gate.

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

Before considering CI/CD ready, confirm:

- Terraform apply completed without errors.
- GitHub Actions secrets and variables exist.
- The `production` GitHub environment exists.
- Required reviewers are configured if production needs manual approval.
- `Deploy to Staging` authenticates to Google Cloud successfully.
- Staging deployment and load test complete.
- Production workflow starts only under the approval behavior you expect.
