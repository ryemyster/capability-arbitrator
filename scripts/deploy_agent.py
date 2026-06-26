"""
File: deploy_agent.py
Purpose: Manage capability-arbitrator deployments on Vertex AI Agent Runtime
         or Cloud Run.
Why exists: Env vars must be passed explicitly at deploy time because the .env
            file is not sent to the cloud. This script reads non-sensitive env
            vars from .env and builds the deploy command automatically.
How: --target agent_runtime (default) uses agents-cli + vertexai SDK.
     --target cloud_run uses gcloud run deploy --source . (no Dockerfile needed;
     Buildpacks auto-build from pyproject.toml + Procfile). GOOGLE_API_KEY is
     injected via Secret Manager, not plain env vars.
     Auth: Agent Runtime uses ADC. Cloud Run uses GOOGLE_GENAI_USE_VERTEXAI=False
     + GOOGLE_API_KEY from Secret Manager.

Usage:
    # Agent Runtime (existing behavior, unchanged)
    uv run python scripts/deploy_agent.py deploy
    uv run python scripts/deploy_agent.py deploy --no-wait
    uv run python scripts/deploy_agent.py status
    uv run python scripts/deploy_agent.py redeploy
    uv run python scripts/deploy_agent.py list
    uv run python scripts/deploy_agent.py undeploy

    # Cloud Run
    uv run python scripts/deploy_agent.py init --target cloud_run
    uv run python scripts/deploy_agent.py deploy --target cloud_run
    uv run python scripts/deploy_agent.py status --target cloud_run
"""

import argparse
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

# --- Agent Runtime ---
# Only non-sensitive config flags are deployed as env vars.
# GOOGLE_API_KEY is intentionally excluded — Agent Runtime uses ADC
# (Application Default Credentials) when GOOGLE_GENAI_USE_VERTEXAI=True.
ENV_VARS_TO_DEPLOY = [
    "GOOGLE_GENAI_USE_VERTEXAI",
    "LOGS_BUCKET_NAME",
    "STRIDE_SELF_HEALING_ENABLED",
    "STRIDE_SELF_HEALING_ARBITRATOR_ENABLED",
    "STRIDE_SELF_HEALING_AMBIENT_ENABLED",
    "STRIDE_SELF_HEALING_MODE",
    "QUALITY_FLYWHEEL_ENABLED",
    "QUALITY_FLYWHEEL_ARBITRATOR_ENABLED",
    "QUALITY_FLYWHEEL_AMBIENT_ENABLED",
    "QUALITY_FLYWHEEL_MODE",
    "GITHUB_INTEGRATION_ENABLED",
]

# --- Cloud Run ---
CR_SERVICE_NAME = "capability-arbitrator"
# GOOGLE_API_KEY is excluded — injected at runtime via Secret Manager
# CLOUD_RUN_SERVICE_ACCOUNT is excluded — it's deploy config, not an app env var
CR_ENV_VARS_TO_DEPLOY = [
    "GOOGLE_GENAI_USE_VERTEXAI",
    "LOGS_BUCKET_NAME",
    "GOOGLE_CLOUD_PROJECT",
    "GOOGLE_CLOUD_LOCATION",
    "STRIDE_SELF_HEALING_ENABLED",
    "STRIDE_SELF_HEALING_ARBITRATOR_ENABLED",
    "STRIDE_SELF_HEALING_AMBIENT_ENABLED",
    "STRIDE_SELF_HEALING_MODE",
    "QUALITY_FLYWHEEL_ENABLED",
    "QUALITY_FLYWHEEL_ARBITRATOR_ENABLED",
    "QUALITY_FLYWHEEL_AMBIENT_ENABLED",
    "QUALITY_FLYWHEEL_MODE",
    "GITHUB_INTEGRATION_ENABLED",
]


def _load_env() -> dict[str, str]:
    """Load .env file and return non-empty key-value pairs."""
    from dotenv import dotenv_values

    env = dotenv_values(ROOT / ".env")
    return {k: v for k, v in env.items() if v is not None and v.strip()}


def _build_env_vars_string(env: dict[str, str]) -> str:
    """Build comma-separated KEY=VALUE string for --update-env-vars."""
    pairs = [f"{k}={env[k]}" for k in ENV_VARS_TO_DEPLOY if k in env]
    return ",".join(pairs)


def _gcp_config(env: dict[str, str] | None = None) -> tuple[str, str]:
    """Return (project, location) from .env, exiting with a clear message if unset."""
    if env is None:
        env = _load_env()
    project = env.get("GOOGLE_CLOUD_PROJECT", "").strip()
    location = env.get("GOOGLE_CLOUD_LOCATION", "").strip()
    if not project:
        sys.exit("Error: GOOGLE_CLOUD_PROJECT is not set in .env")
    if not location:
        sys.exit("Error: GOOGLE_CLOUD_LOCATION is not set in .env")
    return project, location


def cmd_status() -> None:
    """Check deployment status via agents-cli."""
    _, location = _gcp_config()
    subprocess.run(
        [
            "agents-cli",
            "deploy",
            "--status",
            "--region",
            location,
            "--no-confirm-project",
        ],
        check=False,  # Don't raise if no pending deploy
    )


def cmd_list() -> None:
    """List all Agent Runtime deployments in the project/region."""
    _, location = _gcp_config()
    subprocess.run(
        [
            "agents-cli",
            "deploy",
            "--list",
            "--region",
            location,
            "--no-confirm-project",
        ],
        check=False,
    )


def _get_runtime_id() -> str | None:
    """Read the deployed runtime ID from deployment_metadata.json."""
    meta_path = ROOT / "deployment_metadata.json"
    if not meta_path.exists():
        print("No deployment_metadata.json found — nothing to undeploy.")
        return None
    with open(meta_path) as f:
        meta = json.load(f)
    runtime_id = meta.get("remote_agent_runtime_id")
    if not runtime_id:
        print("No remote_agent_runtime_id in deployment_metadata.json.")
        return None
    return runtime_id


def cmd_undeploy() -> None:
    """Delete the deployed Agent Runtime instance using the Vertex AI SDK."""
    runtime_id = _get_runtime_id()
    if not runtime_id:
        return

    print(f"Undeploying: {runtime_id}")
    confirm = input("Are you sure? This will delete the deployed agent. (y/N): ")
    if confirm.lower() not in ("y", "yes"):
        print("Cancelled.")
        return

    import vertexai
    from vertexai import agent_engines

    project, location = _gcp_config()
    vertexai.init(project=project, location=location)
    try:
        agent_engines.AgentEngine(runtime_id).delete(force=True)
        print("✅ Agent Runtime deleted successfully.")
        # Clean up local metadata
        meta_path = ROOT / "deployment_metadata.json"
        if meta_path.exists():
            meta_path.unlink()
            print("Removed deployment_metadata.json.")
    except Exception as e:
        print(f"❌ Failed to delete: {e}")


def cmd_deploy(no_wait: bool = False) -> None:
    """Deploy the agent to Agent Runtime with env vars from .env."""
    env = _load_env()
    project, location = _gcp_config(env)
    env_str = _build_env_vars_string(env)

    print(f"Deploying to {project} / {location}")
    print(f"Env vars: {env_str}\n")

    cmd = [
        "agents-cli",
        "deploy",
        "--no-confirm-project",
        "--region",
        location,
    ]
    # Only add --update-env-vars if we have values to send
    if env_str:
        cmd.extend(["--update-env-vars", env_str])
    if no_wait:
        cmd.append("--no-wait")

    subprocess.run(cmd, check=True)


def cmd_redeploy(no_wait: bool = False) -> None:
    """Redeploy by running a fresh deploy (Agent Runtime updates in-place)."""
    # Agent Runtime deploy is idempotent — it updates the existing
    # deployment if one exists with the same display name. No need
    # to delete first.
    print("=== Redeploying (Agent Runtime updates in-place) ===")
    cmd_deploy(no_wait=no_wait)


# ---------------------------------------------------------------------------
# Cloud Run commands
# ---------------------------------------------------------------------------


def _cr_env_vars_string(env: dict[str, str]) -> str:
    pairs = [
        f"{k}={env[k]}" for k in CR_ENV_VARS_TO_DEPLOY if k in env and env[k].strip()
    ]
    return ",".join(pairs)


def cmd_cr_init() -> None:
    """One-time Cloud Run setup: enable APIs, store API key in Secret Manager, grant IAM."""
    env = _load_env()
    project, _ = _gcp_config(env)
    sa = env.get("CLOUD_RUN_SERVICE_ACCOUNT", "").strip()

    print(f"=== Cloud Run init — project: {project} ===\n")

    # 1. Enable required GCP APIs
    print("Enabling Cloud Run, Cloud Build, and Secret Manager APIs...")
    subprocess.run(
        [
            "gcloud",
            "services",
            "enable",
            "run.googleapis.com",
            "cloudbuild.googleapis.com",
            "secretmanager.googleapis.com",
            f"--project={project}",
        ],
        check=True,
    )

    # 2. Create GOOGLE_API_KEY secret (idempotent)
    api_key = env.get("GOOGLE_API_KEY", "").strip()
    if not api_key:
        print("GOOGLE_API_KEY not found in .env — skipping secret creation.")
    else:
        result = subprocess.run(
            [
                "gcloud",
                "secrets",
                "describe",
                "GOOGLE_API_KEY",
                f"--project={project}",
            ],
            capture_output=True,
        )
        if result.returncode == 0:
            print("Secret GOOGLE_API_KEY already exists — skipping creation.")
        else:
            print("Creating GOOGLE_API_KEY secret...")
            subprocess.run(
                [
                    "gcloud",
                    "secrets",
                    "create",
                    "GOOGLE_API_KEY",
                    f"--project={project}",
                    "--replication-policy=automatic",
                ],
                check=True,
            )
        print("Adding secret version from .env value...")
        subprocess.run(
            [
                "gcloud",
                "secrets",
                "versions",
                "add",
                "GOOGLE_API_KEY",
                f"--project={project}",
                "--data-file=-",
            ],
            input=api_key.encode(),
            check=True,
        )

    # 3. Grant service account access to the secret
    if sa:
        if not sa.endswith(".gserviceaccount.com"):
            print(
                f"⚠️  CLOUD_RUN_SERVICE_ACCOUNT={sa!r} does not look like a service "
                "account (expected *.gserviceaccount.com). Cloud Run runs as a "
                "service account, not a user. Skipping IAM grant — fix .env and re-run init."
            )
        else:
            print(f"Granting {sa} secretAccessor on GOOGLE_API_KEY...")
            result = subprocess.run(
                [
                    "gcloud",
                    "secrets",
                    "add-iam-policy-binding",
                    "GOOGLE_API_KEY",
                    f"--project={project}",
                    f"--member=serviceAccount:{sa}",
                    "--role=roles/secretmanager.secretAccessor",
                ],
                check=False,
            )
            if result.returncode != 0:
                print(
                    "⚠️  IAM grant failed (see error above). The secret was still "
                    "created; fix the binding and re-run init before deploying."
                )
    else:
        print("CLOUD_RUN_SERVICE_ACCOUNT not set in .env — skipping IAM grant.")
        print("Add CLOUD_RUN_SERVICE_ACCOUNT=<email> to .env and re-run init.")

    print("\n✅ Cloud Run init complete.")


def cmd_cr_deploy() -> None:
    """Deploy (or redeploy) the Cloud Run service from source. Idempotent."""
    env = _load_env()
    project, location = _gcp_config(env)
    sa = env.get("CLOUD_RUN_SERVICE_ACCOUNT", "").strip()
    env_str = _cr_env_vars_string(env)

    print(
        f"=== Cloud Run deploy — {CR_SERVICE_NAME} in {project}/{location} ==="
    )
    if env_str:
        print(f"Env vars: {env_str}\n")

    cmd = [
        "gcloud",
        "run",
        "deploy",
        CR_SERVICE_NAME,
        "--source",
        str(ROOT),
        f"--project={project}",
        f"--region={location}",
        "--set-secrets=GOOGLE_API_KEY=GOOGLE_API_KEY:latest",
        "--port=8080",
        "--allow-unauthenticated",
    ]
    if sa:
        cmd.append(f"--service-account={sa}")
    if env_str:
        cmd.append(f"--set-env-vars={env_str}")

    subprocess.run(cmd, check=True)
    print("\n✅ Cloud Run deploy complete.")


def cmd_cr_status() -> None:
    """Describe the Cloud Run service."""
    project, location = _gcp_config()
    subprocess.run(
        [
            "gcloud",
            "run",
            "services",
            "describe",
            CR_SERVICE_NAME,
            f"--project={project}",
            f"--region={location}",
        ],
        check=False,
    )


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Manage capability-arbitrator deployments (Agent Runtime or Cloud Run).",
    )
    parser.add_argument(
        "command",
        choices=["init", "deploy", "status", "redeploy", "list", "undeploy"],
    )
    parser.add_argument(
        "--target",
        choices=["agent_runtime", "cloud_run"],
        default="agent_runtime",
        help="Deployment target (default: agent_runtime).",
    )
    parser.add_argument(
        "--no-wait",
        action="store_true",
        help="Agent Runtime only: start deployment and return immediately.",
    )
    args = parser.parse_args()

    if args.target == "cloud_run":
        cr_commands = {
            "init": cmd_cr_init,
            "deploy": cmd_cr_deploy,
            "status": cmd_cr_status,
        }
        if args.command not in cr_commands:
            parser.error(
                f"'{args.command}' is not supported for --target cloud_run. "
                f"Use: {', '.join(cr_commands)}"
            )
        cr_commands[args.command]()
    else:
        ar_commands = {
            "deploy": lambda: cmd_deploy(no_wait=args.no_wait),
            "status": cmd_status,
            "redeploy": lambda: cmd_redeploy(no_wait=args.no_wait),
            "list": cmd_list,
            "undeploy": cmd_undeploy,
        }
        if args.command not in ar_commands:
            parser.error(
                f"'{args.command}' is not supported for --target agent_runtime. "
                f"Use: {', '.join(ar_commands)}"
            )
        ar_commands[args.command]()


if __name__ == "__main__":
    main()
