# Created: 2026-06-23T12:22:49-06:00
import os


def test_deploy_env():
    print("============================================================")
    print("PHASE 5: DEPLOYMENT VALIDATION")
    print("============================================================")

    project_id = os.getenv("GOOGLE_CLOUD_PROJECT")

    if not project_id:
        print("[FAIL] GOOGLE_CLOUD_PROJECT environment variable is not set.")
        print("To run Phase 5, you must set your GCP project ID.")
        return

    print(f"[PASS] GCP Project identified: {project_id}")
    print("Run the following command to deploy the Agent to Vertex AI Agent Runtime:")
    print(f"  uv run agents-cli deploy --project {project_id}")
    print("============================================================")


if __name__ == "__main__":
    test_deploy_env()
