"""
File: conftest.py
Purpose: Configures pytest hooks to optimize run speed (such as skipping slow integration tests when only documentation changed).
Why it exists: Speeds up development feedback loops by preventing full regressions on minor documentation edits.
How it works: Runs git diff to inspect changes, and filters collected tests if changes are limited to docs/markdown files.
"""

import subprocess

def pytest_collection_modifyitems(config, items) -> None:
    try:
        # Run git diff against develop to get changed files
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
                    # Keep only unit tests
                    path_str = str(item.fspath)
                    if "tests/integration" in path_str or "tests/scripts" in path_str:
                        continue
                    keep.append(item)
                items[:] = keep
    except Exception:
        # Fallback gracefully
        pass
