# QA Manual Verification: STRIDE Threat Modeling Security Node

This document outlines the steps to verify the functionality of the STRIDE security audit node on both the local playground and the remote deployed Reasoning Engine.

## Local Playground Verification

1. Start the local agent playground:
   ```bash
   uv run agents-cli playground
   ```
2. In the playground chat box, input a security audit request, for example:
   > Audit the security of this backend function: def load_user_config(path): return open(path).read()
3. Verify that the routing console output indicates the prompt is routed to the `stride` capability.
4. Verify that the agent response matches the STRIDE Threat Modeling SOP, displaying:
   - An **Executive Security Summary**
   - **Data Flow & Trust Boundaries**
   - A **Threat Modeling Table** outlining vulnerabilities, severity levels, and concrete mitigations.

## Remote Deployment Verification

1. Run the remote command to query the deployed agent on Vertex AI:
   ```bash
   uv run agents-cli run --url https://us-east1-aiplatform.googleapis.com/v1/projects/kaggle-capstone-500322/locations/us-east1/reasoningEngines/5281702016115015680 --mode adk "Audit the security of this backend function: def load_user_config(path): return open(path).read()"
   ```
2. Verify that the output streams successfully and displays the full threat modeling report.

*Created: 2026-06-23T20:51:30-06:00*
