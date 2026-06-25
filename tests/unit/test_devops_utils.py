# Copyright 2026 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""
File: test_devops_utils.py
Purpose: Unit tests for the generalized DevOps command detection logic.
Why it exists: Assures the devops node selects the appropriate linting and testing tooling.
How it works: Creates mock project boundary files (package.json, go.mod, python scripts) in tmp directories.
"""

import os
from pathlib import Path
from app.app_utils.devops_utils import _detect_devops_command

def test_detect_node_commands(tmp_path: Path) -> None:
    """Verifies that Node.js projects trigger npm test or lint commands."""
    # Write package.json to the temporary folder
    (tmp_path / "package.json").write_text("{}", encoding="utf-8")

    # Run checks for tests prompt
    test_cmd = _detect_devops_command("Run npm test suite", str(tmp_path))
    assert test_cmd == ["npm", "test"]

    # Run checks for lint prompt
    lint_cmd = _detect_devops_command("Format codebase and run linter", str(tmp_path))
    assert lint_cmd == ["npm", "run", "lint"]

def test_detect_go_commands(tmp_path: Path) -> None:
    """Verifies that Go projects trigger go test or vet commands."""
    # Write go.mod to the temporary folder
    (tmp_path / "go.mod").write_text("module test", encoding="utf-8")

    # Run checks for tests prompt
    test_cmd = _detect_devops_command("execute tests", str(tmp_path))
    assert test_cmd == ["go", "test", "./..."]

    # Run checks for lint prompt
    lint_cmd = _detect_devops_command("lint go code", str(tmp_path))
    assert lint_cmd == ["go", "vet", "./..."]

def test_detect_python_commands(tmp_path: Path) -> None:
    """Verifies that Python projects trigger appropriate pytest or script commands."""
    # By default, without any special files, a python test prompt triggers uv pytest
    test_cmd = _detect_devops_command("run tests", str(tmp_path))
    assert test_cmd == ["uv", "run", "pytest"]

    # If verification script verify_code.py exists, it is triggered for lint/check prompts
    (tmp_path / "verify_code.py").write_text("print('ok')", encoding="utf-8")
    lint_cmd = _detect_devops_command("check python style", str(tmp_path))
    assert lint_cmd == ["uv", "run", "python", "verify_code.py"]

def test_detect_python_recursion_skip(tmp_path: Path, monkeypatch: any) -> None:
    """Verifies that nested pytest executions check for recursion via PYTEST_CURRENT_TEST."""
    # Setup directories
    tests_dir = tmp_path / "tests"
    tests_dir.mkdir()
    
    # Simulate being inside an active pytest execution thread
    monkeypatch.setenv("PYTEST_CURRENT_TEST", "test_file.py::test_case (call)")

    # The command detected should append -k unit to avoid integration test loops
    test_cmd = _detect_devops_command("run pytest suite", str(tmp_path))
    assert "-k" in test_cmd
    assert "unit" in test_cmd
