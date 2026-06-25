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
File: devops_utils.py
Purpose: DevOps toolchain detection and execution logic for the Capability Arbitrator.
Why it exists: Separates execution concerns and reduces size of core agent module.
How it works: Scans the target workspace file structure, determines relevant test commands,
              and executes them deterministically inside the workflow graph.
"""

import os
import time
import subprocess
from typing import Any, AsyncGenerator

from google.adk.agents.context import Context
from google.adk.events.event import Event
from google.adk.workflow import FunctionNode
from google.genai import types

from app.app_utils.routing_utils import get_prompt_text
from app.app_utils.telemetry import record_node_execution
from app.app_utils.config_loader import get_target_dir

def _detect_devops_command(prompt: str, t_dir: str) -> list[str]:
    """Helper to detect language/framework and return the correct test/lint command."""
    prompt_lower = prompt.lower()
    is_test = any(w in prompt_lower for w in ["test", "pytest", "run tests", "check tests"])
    
    # 1. Node.js project
    if os.path.exists(os.path.join(t_dir, "package.json")):
        return ["npm", "test"] if is_test else ["npm", "run", "lint"]
    # 2. Go project
    elif os.path.exists(os.path.join(t_dir, "go.mod")):
        return ["go", "test", "./..."] if is_test else ["go", "vet", "./..."]
    # 3. Python project (default)
    else:
        if is_test:
            if os.path.exists(os.path.join(t_dir, "tests", "unit")):
                return ["uv", "run", "pytest", "tests/unit"]
            elif os.path.exists(os.path.join(t_dir, "tests")):
                if "PYTEST_CURRENT_TEST" in os.environ:
                    # Avoid running integration/BDD tests recursively
                    return ["uv", "run", "pytest", "tests", "-k", "unit"]
                return ["uv", "run", "pytest", "tests"]
            return ["uv", "run", "pytest"]
        verify_script = os.path.join(t_dir, "verify_code.py")
        if os.path.exists(verify_script):
            return ["uv", "run", "python", "verify_code.py"]
        quality_script = os.path.join(t_dir, "scripts", "agent_quality_check.py")
        if os.path.exists(quality_script):
            return ["uv", "run", "python", quality_script]
        return ["uv", "run", "ruff", "check", "."]

async def devops_node(ctx: Context, node_input: Any) -> AsyncGenerator[Event, None]:
    """DevOps execution node using pytest/subprocess verification."""
    prompt = get_prompt_text(ctx) or (str(node_input) if node_input else "")
    start_time = time.time()
    target_dir = get_target_dir()
    cmd = _detect_devops_command(prompt, target_dir)
    desc = f"Running: {' '.join(cmd)}"
    
    yield Event(content=types.Content(role="model", parts=[types.Part.from_text(text=f"⚙️ DevOps Engine: {desc}\n")]))
    try:
        res = subprocess.run(cmd, capture_output=True, text=True)
        latency = time.time() - start_time
        record_node_execution("devops", latency, 0, 0)
        output_text = f"STDOUT:\n{res.stdout}\nSTDERR:\n{res.stderr}\n"
        yield Event(content=types.Content(role="model", parts=[types.Part.from_text(text=output_text)]))
        yield Event(output={"result": output_text, "exit_code": res.returncode})
    except Exception as e:
        latency = time.time() - start_time
        record_node_execution("devops", latency, 0, 0)
        err = f"Error executing DevOps tool: {e}"
        yield Event(content=types.Content(role="model", parts=[types.Part.from_text(text=err)]))
        yield Event(output={"result": err, "exit_code": -1})

devops_fn = FunctionNode(name="devops", func=devops_node)
