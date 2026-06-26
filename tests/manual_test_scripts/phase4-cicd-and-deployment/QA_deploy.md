# Phase 4 Manual QA Tests (Cloud Deployment)

## Objective
Verify that the Capability Arbitrator can be successfully deployed as a remote service (Vertex AI Agent Runtime) using the `agents-cli deploy` command.

## Why are we testing this?
A local graph is great for debugging, but for production integration, the agent must run as a headless daemon in the cloud (specifically using Vertex AI Agent Runtime) to handle API requests and scaling.

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

### Deployment Route (Recommended)
This command packages the agent workflow source code, resolves dependencies, and deploys it to Vertex AI Agent Runtime.
```bash
uv run agents-cli deploy --project $GOOGLE_CLOUD_PROJECT
```

> **Note:** Agent Runtime deployments can take 5-10 minutes. If the deployment times out or you want to start it asynchronously, you can run:
> ```bash
> uv run agents-cli deploy --project $GOOGLE_CLOUD_PROJECT --no-wait
> ```
> And check status periodically using:
> ```bash
> uv run agents-cli deploy --status
> ```

### Testing the Deployed Agent
Once deployed, retrieve the Reasoning Engine resource ID from the output. If you need to run load tests, copy `deployment_metadata.example.json` to `deployment_metadata.json` and fill in the real resource ID. The real `deployment_metadata.json` file is generated/local-only and should not be committed.
```bash
# Query the deployed Agent Runtime remotely
uv run agents-cli run --url https://us-east1-aiplatform.googleapis.com/v1/projects/$GOOGLE_CLOUD_PROJECT/locations/us-east1/reasoningEngines/<ENGINE_ID> --mode adk "Calculate 50 * 5"
```

### Tear Down (Cleanup)
To delete the deployed Reasoning Engine and stop any potential billing, delete the service via the Google Cloud Console:
1. Open the [Vertex AI Google Cloud Console](https://console.cloud.google.com/vertex-ai/reasoning-engines).
2. Find the `capability-arbitrator` Reasoning Engine under your project.
3. Select and delete the resource.

## Validation Sign-off
- [ ] Deployment succeeds and provides a real Reasoning Engine resource ID.
- [ ] Local `deployment_metadata.json` is generated or filled from `deployment_metadata.example.json` for load testing only.
- [ ] Remote inference via `agents-cli run` successfully reaches the remote graph and returns an answer.

---
*Created: 2026-06-23T12:22:49-06:00*
