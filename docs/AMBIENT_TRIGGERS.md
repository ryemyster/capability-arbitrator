# GCP Pub/Sub Ambient Event Triggers
### Event-Driven Orchestration for Background Triage

This guide explains how the Capability Arbitrator listens for and processes background events using Google Cloud Pub/Sub push notifications.

---

## 💡 The Motion-Sensor Light Analogy (Why & What)

### Why does this exist?
Flipping a light switch manually every time you walk into a room is fine, but it gets annoying if you do it fifty times a day. A motion-sensor light solves this by automatically turning on when it detects movement.
In software development, running a security audit manually on every minor code change is like flipping that switch manually. It is slow, expensive, and easy to forget.
**Ambient Triggers** act like motion sensors. When a developer opens a Pull Request on GitHub, GitHub detects the "movement," sends a message down a highway (GCP Pub/Sub), and our agent wakes up in the background to automatically audit the code!

### What is it?
It is a background messaging pipeline:
1. **GitHub Webhook** fires when a PR is updated.
2. **GCP Pub/Sub Topic** receives the webhook data.
3. **Pub/Sub Push Subscription** POSTs a base64-encoded message to our `/pubsub` API endpoint.
4. **FastAPI Webhook Handler** decodes the prompt and runs the arbitrator agent graph.

---

## 🛠️ How to Configure and Test (How)

> [!IMPORTANT]
> **Agent operation rule:** Coding agents working in this repository must not use raw
> `gcloud` commands for project setup, authentication, quota checks, Pub/Sub
> provisioning, or deployment. Use the approved `agents-cli` workflow for
> deployment work, and use the Google Cloud Console or a human-owned
> infrastructure process for Pub/Sub resources that are not yet covered by
> `agents-cli`.

### 1. Trigger the Webhook Locally
You can test the ambient trigger locally without setting up Google Cloud services by sending a mock Pub/Sub envelope using `curl`:

```bash
curl -X POST http://127.0.0.1:8000/pubsub \
  -H "Content-Type: application/json" \
  -d '{
    "message": {
      "data": "eyJwcm9tcHQiOiAiQ29uZHVjdCBhY2FkZW1pYyByZXNlYXJjaCBvbiBxdWFudHVtIGNvbXB1dGluZyBicmVha3Rocm91Z2hzLiJ9",
      "messageId": "pubsub-test-12345",
      "attributes": {}
    },
    "subscription": "projects/kaggle-capstone-500322/subscriptions/ambient-sub"
  }'
```
*Note: The `data` string above is the base64-encoded JSON `{"prompt": "Conduct academic research on quantum computing breakthroughs."}`.*

### 2. Configure the Production Pub/Sub Push Subscription
To wire this up in production on Google Cloud:

1. **Deploy the FastAPI service** through the project-approved deployment path:
   ```bash
   agents-cli deploy
   ```
   This produces the Cloud Run service URL, such as
   `https://capability-arbitrator-xyz.a.run.app`.
2. **Create or verify the Pub/Sub topic** using the Google Cloud Console or your
   team's approved infrastructure workflow.
   - Topic example: `ambient-topic`
   - Purpose: receives webhook events from GitHub or another event source.
3. **Create or verify a push subscription** using the Google Cloud Console or the
   approved infrastructure workflow.
   - Subscription example: `ambient-sub`
   - Push endpoint: `https://capability-arbitrator-xyz.a.run.app/pubsub`
   - Ack deadline: `60` seconds
4. **Connect the event source** so GitHub or another system publishes the PR
   event payload into the Pub/Sub topic.

These setup steps are human/operator infrastructure work. They should not be
performed by a coding agent through raw cloud CLI commands.

---

## 🎯 When to Use This Feature (When)

| Reach for Ambient Triggers | Reach for Manual Run / CLI |
| :--- | :--- |
| **Continuous Integration (CI/CD):** Waking up the agent to automatically scan code diffs during active GitHub Pull Requests. | **Interactive Debugging:** Developing and testing new skills locally using the `agents-cli playground` REPL. |
| **Background Triage:** Routing low-risk edits (e.g. documentation updates) away from heavy computation to optimize token budgets. | **One-off Audits:** Running a STRIDE threat modeling analysis manually on a specific local function or script. |

---
*Created: 2026-06-24T17:45:35-06:00*
