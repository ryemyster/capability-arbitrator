#!/usr/bin/env bash
#
# delete_runtime.sh — Tear down deployed capability-arbitrator surfaces.
#
# Usage:
#   ./scripts/delete_runtime.sh [target]
#
#   target = agent_runtime  (default)  Delete the Vertex AI Agent Runtime (reasoningEngine)
#            cloud_run                  Delete the Cloud Run service
#            all                        Delete both
#
# Notes:
#   - Cloud Run already scales to zero at idle; deleting only matters for a
#     truly zero-footprint teardown.
#   - This does NOT delete the GOOGLE_API_KEY secret, the Artifact Registry
#     repo, or the source bucket (all negligible cost; kept so a redeploy is
#     fast). Remove those manually if you want a fully clean slate.
set -euo pipefail

PROJECT="906183434819"
LOCATION="us-west1"

# --- Agent Runtime ---
ENGINE="94056622686470144"

# --- Cloud Run ---
CR_SERVICE_NAME="capability-arbitrator"

TARGET="${1:-agent_runtime}"

delete_agent_runtime() {
  echo "=== Deleting Agent Runtime (reasoningEngine ${ENGINE}) ==="
  local access_token
  access_token=$(gcloud auth print-access-token)
  curl -X DELETE \
    -H "Authorization: Bearer ${access_token}" \
    "https://${LOCATION}-aiplatform.googleapis.com/v1/projects/${PROJECT}/locations/${LOCATION}/reasoningEngines/${ENGINE}?force=true"
  echo
  echo "Agent Runtime delete request sent."
}

delete_cloud_run() {
  echo "=== Deleting Cloud Run service (${CR_SERVICE_NAME} in ${PROJECT}/${LOCATION}) ==="
  gcloud run services delete "${CR_SERVICE_NAME}" \
    --project="${PROJECT}" \
    --region="${LOCATION}" \
    --quiet
  echo "Cloud Run service deleted."
}

case "${TARGET}" in
  agent_runtime)
    delete_agent_runtime
    ;;
  cloud_run)
    delete_cloud_run
    ;;
  all)
    delete_agent_runtime
    delete_cloud_run
    ;;
  *)
    echo "Unknown target: '${TARGET}'. Use: agent_runtime | cloud_run | all" >&2
    exit 1
    ;;
esac
