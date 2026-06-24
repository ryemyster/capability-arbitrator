# Created: 2026-06-23T12:22:49-06:00
import os


def test_terraform_env():
    print("============================================================")
    print("PHASE 4: INFRASTRUCTURE (TERRAFORM) VALIDATION")
    print("============================================================")

    project_id = os.getenv("GOOGLE_CLOUD_PROJECT")

    if not project_id:
        print("[FAIL] GOOGLE_CLOUD_PROJECT environment variable is not set.")
        print("To run Phase 4, you must set your GCP project ID.")
        return

    print(f"[PASS] GCP Project identified: {project_id}")
    print(
        "Run the following command to provision BigQuery and Agent Runtime infrastructure:"
    )
    print(f"  uv run agents-cli infra single-project --project {project_id}")
    print("============================================================")


if __name__ == "__main__":
    test_terraform_env()
