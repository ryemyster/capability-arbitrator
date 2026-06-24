"""
File: test_agent_quality.py
Purpose: Integrates agent quality checks into the pytest suite.
Why it exists: Enforces static code quality limits automatically during local test runs to prevent regressions.
How it works: Executes scripts/agent_quality_check.py check_file logic on all app files and asserts no errors.
"""

import os
from scripts.agent_quality_check import check_file

def test_app_code_quality() -> None:
    """Ensures all python source files in app/ meet AI Agent quality standards."""
    base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    app_dir = os.path.join(base_dir, "app")
    
    all_errors = {}
    for root, _, files in os.walk(app_dir):
        if "__pycache__" in root or ".adk" in root:
            continue
        for file in files:
            if file.endswith(".py"):
                filepath = os.path.join(root, file)
                rel_path = os.path.relpath(filepath, base_dir)
                errors = check_file(filepath)
                if errors:
                    all_errors[rel_path] = errors
                    
    assert not all_errors, f"Code quality checks failed:\n" + "\n".join(
        f"❌ {path}:\n" + "\n".join(f"  - {e}" for e in errs)
        for path, errs in all_errors.items()
    )
