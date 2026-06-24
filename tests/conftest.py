"""
File: conftest.py
Purpose: Configures pytest hooks to optimize run speed and handle unauthenticated CI environments.
Why it exists: Speeds up development feedback loops and allows PR checks to pass in CI without GCP credentials.
How it works: Detects GCP credentials and git diffs to skip integration/scripts tests when appropriate.
"""

import subprocess
import google.auth

def pytest_collection_modifyitems(config, items) -> None:
    # 1. Check for valid GCP authentication
    has_gcp_auth = True
    try:
        google.auth.default()
    except Exception:
        has_gcp_auth = False

    try:
        # If no GCP auth is available, skip integration and script tests
        if not has_gcp_auth:
            print("\n⚡ [WARNING] No GCP credentials detected. Skipping integration and script tests.")
            keep = []
            for item in items:
                path_str = str(item.fspath)
                if "tests/integration" in path_str or "tests/scripts" in path_str:
                    continue
                keep.append(item)
            items[:] = keep
            return

        # 2. Optimize run speed by checking changed files against develop branch
        res = subprocess.run(["git", "diff", "--name-only", "develop"], capture_output=True, text=True)
        changed_files = res.stdout.splitlines()
        
        # If no diff against develop, check local status
        if not changed_files:
            res = subprocess.run(["git", "status", "--porcelain"], capture_output=True, text=True)
            changed_files = [line[3:].strip() for line in res.stdout.splitlines() if line]

        if changed_files:
            # Check if ONLY docs/markdown/txt files changed
            only_docs = all(
                f.endswith(".md") or f.startswith("docs/") or f.endswith(".txt")
                for f in changed_files
            )
            if only_docs:
                print("\n⚡ [INFO] Only documentation changes detected. Skipping integration/scripts test regression.")
                keep = []
                for item in items:
                    path_str = str(item.fspath)
                    if "tests/integration" in path_str or "tests/scripts" in path_str:
                        continue
                    keep.append(item)
                items[:] = keep
    except Exception:
        # Fallback gracefully
        pass
