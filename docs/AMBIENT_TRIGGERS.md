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

### 2. Configure GCP Pub/Sub Push Subscription
To wire this up in production on Google Cloud:

1. **Create a Pub/Sub Topic:**
   ```bash
   gcloud pubsub topics create ambient-topic
   ```
2. **Deploy the FastAPI service** to Cloud Run to get your service URL (e.g. `https://capability-arbitrator-xyz.a.run.app`).
3. **Create a Push Subscription** pointing to your `/pubsub` endpoint:
   ```bash
   gcloud pubsub subscriptions create ambient-sub \
     --topic=ambient-topic \
     --push-endpoint=https://capability-arbitrator-xyz.a.run.app/pubsub \
     --ack-deadline=60
   ```

---

## 🎯 When to Use This Feature (When)

| Reach for Ambient Triggers | Reach for Manual Run / CLI |
| :--- | :--- |
| **Continuous Integration (CI/CD):** Waking up the agent to automatically scan code diffs during active GitHub Pull Requests. | **Interactive Debugging:** Developing and testing new skills locally using the `agents-cli playground` REPL. |
| **Background Triage:** Routing low-risk edits (e.g. documentation updates) away from heavy computation to optimize token budgets. | **One-off Audits:** Running a STRIDE threat modeling analysis manually on a specific local function or script. |

---
*Created: 2026-06-24T17:45:35-06:00*
