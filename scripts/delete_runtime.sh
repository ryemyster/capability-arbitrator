PROJECT="906183434819"
LOCATION="us-west1"
ENGINE="94056622686470144"

ACCESS_TOKEN=$(gcloud auth print-access-token)

curl -X DELETE \
  -H "Authorization: Bearer ${ACCESS_TOKEN}" \
  "https://${LOCATION}-aiplatform.googleapis.com/v1/projects/${PROJECT}/locations/${LOCATION}/reasoningEngines/${ENGINE}?force=true"
