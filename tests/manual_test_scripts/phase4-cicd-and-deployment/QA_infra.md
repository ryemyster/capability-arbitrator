# Phase 4 Manual QA Tests (Cloud Infrastructure)

## Objective
Verify that the `agents-cli infra single-project` command can successfully provision the necessary Google Cloud infrastructure (BigQuery Datasets for telemetry and Service Accounts) using Terraform.

## Why are we testing this?
Because without Terraform provisioning the BigQuery tables, our `BigQueryAgentAnalyticsPlugin` from Phase 3 will not have anywhere to write its telemetry logs to.

## How to Test
1. Open a terminal in the project root.
2. Authenticate with Google Cloud using the agents CLI:
   ```bash
   uv run agents-cli login
   ```
3. Set your project ID:
   ```bash
   export GOOGLE_CLOUD_PROJECT="your-project-id"
   ```

### Path A: The `agents-cli` Route (Recommended)
This uses the official wrapper to handle state and configuration automatically.
```bash
uv run agents-cli infra single-project --project $GOOGLE_CLOUD_PROJECT
```

### Path B: The Raw Terraform Route
This uses the raw terraform commands directly if you do not want to use the CLI wrapper.
```bash
cd deployment/terraform/single-project/
terraform init
terraform apply -var="project_id=$GOOGLE_CLOUD_PROJECT"
cd ../../../
```

### Tear Down (Cleanup)
Since it is cheap to test and tear down, remember to destroy the resources once you are done validating:
```bash
cd deployment/terraform/single-project/
terraform destroy -var="project_id=$GOOGLE_CLOUD_PROJECT"
```

## Validation Sign-off
- [ ] GCP Project ID is correctly configured.
- [ ] `agents-cli infra single-project` executes without permission errors.
- [ ] BigQuery dataset is visible in the Google Cloud Console.

---
*Created: 2026-06-23T12:22:49-06:00*
