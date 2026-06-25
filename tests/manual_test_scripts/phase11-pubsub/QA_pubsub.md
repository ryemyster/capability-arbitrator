# QA Manual Verification: GCP Pub/Sub Webhook Integration

This document outlines the steps to verify the GCP Pub/Sub push notification endpoint `/pubsub` both locally and in production.

## Local Webhook Verification

1. Start the FastAPI application server locally:
   ```bash
   uv run uvicorn app.fast_api_app:app --host 127.0.0.1 --port 8000
   ```
2. Trigger a mocked Pub/Sub push message using a local curl command:
   ```bash
   curl -X POST http://127.0.0.1:8000/pubsub \
     -H "Content-Type: application/json" \
     -d '{
       "message": {
         "data": "eyJwcm9tcHQiOiAiV2h5IGlzIHRoZSBza3kgYmx1ZT8ifQ==",
         "messageId": "19907963570384",
         "publishTime": "2026-06-24T17:37:45Z"
       },
       "subscription": "projects/kaggle-capstone-500322/subscriptions/ambient-sub"
     }'
   ```
   *(Note: The `data` field contains the base64-encoded JSON `{"prompt": "Why is the sky blue?"}`)*
3. Verify that the server returns a HTTP 200 response containing the correct prompt and streaming execution output, structured as:
   ```json
   {
     "status": "success",
     "prompt": "Why is the sky blue?",
     "output": "..."
   }
   ```

## Production Deployment Verification

1. Retrieve the deployed Cloud Run service URL (e.g. `https://capability-arbitrator-xyz.a.run.app`).
2. Publish a message to your GCP Pub/Sub topic:
   ```bash
   gcloud pubsub topics publish ambient-topic --message='\''{"prompt": "What is 15 plus 30"}'\''
   ```
3. Check the Cloud Logging console to verify:
   - The `/pubsub` HTTP request is received with a 200 OK status code.
   - The agent executes routing and returns the correct payload response.

*Created: 2026-06-24T17:37:45-06:00*
