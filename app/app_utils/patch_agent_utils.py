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
File: patch_agent_utils.py
Purpose: Core pipeline functions for the STRIDE Self-Healing offline optimizer.
Why it exists: Provides testable, single-responsibility steps for the AUDIT →
               DETECT → PATCH → VERIFY → PR pipeline triggered by `arbitrator stride-heal`.
How it works: Each stage is an importable function; LLM calls use genai at module level
              so tests can patch app.app_utils.patch_agent_utils.genai.
"""

import os
import re
import subprocess
from functools import lru_cache
from typing import Any

from google import genai

_SEVERITY_ORDER: dict[str, int] = {"high": 3, "medium": 2, "low": 1}

_DEFAULTS: dict[str, Any] = {
    "stride_self_healing": {
        "enabled": False,
        "arbitrator": {"enabled": True},
        "ambient": {"enabled": False},
        "mode": "audit_only",
        "detection": {
            "severity_threshold": "medium",
            "checks": ["hardcoded_secrets", "unsafe_shell", "missing_input_validation"],
        },
        "verification": {
            "commands": ["uv run pytest tests/unit/ -x -q"],
            "max_attempts": 3,
        },
        "github": {
            "pr_base": "develop",
            "require_manual_review": True,
        },
    }
}

_HEAL_CONFIG_PATH = os.path.join(
    os.path.dirname(__file__), "..", "..", "config", "stride_self_healing.yaml"
)


def _apply_env_overrides(config: dict[str, Any]) -> dict[str, Any]:
    """Apply STRIDE_SELF_HEALING_* env vars over config values."""
    section = dict(config.get("stride_self_healing", {}))
    enabled_env = os.getenv("STRIDE_SELF_HEALING_ENABLED", "").lower()
    if enabled_env in ("true", "1", "yes"):
        section["enabled"] = True
    elif enabled_env in ("false", "0", "no"):
        section["enabled"] = False
    if mode_env := os.getenv("STRIDE_SELF_HEALING_MODE"):
        section["mode"] = mode_env
    arb = dict(section.get("arbitrator", {"enabled": True}))
    arb_env = os.getenv("STRIDE_SELF_HEALING_ARBITRATOR_ENABLED", "").lower()
    if arb_env in ("true", "1", "yes"):
        arb["enabled"] = True
    elif arb_env in ("false", "0", "no"):
        arb["enabled"] = False
    section["arbitrator"] = arb
    amb = dict(section.get("ambient", {"enabled": False}))
    amb_env = os.getenv("STRIDE_SELF_HEALING_AMBIENT_ENABLED", "").lower()
    if amb_env in ("true", "1", "yes"):
        amb["enabled"] = True
    elif amb_env in ("false", "0", "no"):
        amb["enabled"] = False
    section["ambient"] = amb
    return {**config, "stride_self_healing": section}


@lru_cache(maxsize=1)
def load_self_healing_config(path: str | None = None) -> dict[str, Any]:
    """Return merged self-healing config (YAML → defaults → env overrides)."""
    resolved = os.path.abspath(path or _HEAL_CONFIG_PATH)
    if not os.path.exists(resolved):
        return _apply_env_overrides(_DEFAULTS)
    try:
        import yaml  # type: ignore[import-not-found]
        with open(resolved) as f:
            raw = yaml.safe_load(f) or {}
    except Exception:
        return _apply_env_overrides(_DEFAULTS)
    merged: dict[str, Any] = {}
    for section, defaults in _DEFAULTS.items():
        raw_section = raw.get(section) or {}
        merged_section = {**defaults, **raw_section}
        for key, default_val in defaults.items():
            if isinstance(default_val, dict) and isinstance(raw_section.get(key), dict):
                merged_section[key] = {**default_val, **raw_section[key]}
        merged[section] = merged_section
    return _apply_env_overrides(merged)


def run_stride_audit(
    target_path: str, skill_dir: str, model_name: str = "gemini-2.0-flash"
) -> str:
    """Run STRIDE analysis on target_path, return the full audit report."""
    skill_md = os.path.join(skill_dir, "SKILL.md")
    skill_text = open(skill_md).read() if os.path.exists(skill_md) else ""
    code_text = open(target_path).read() if os.path.exists(target_path) else ""
    prompt = (
        f"{skill_text}\n\n"
        f"## Code to Audit\n\n```python\n{code_text}\n```\n\n"
        "Produce the full STRIDE threat modeling report including the Threat Modeling Table."
    )
    client = genai.Client(vertexai=True)
    response = client.models.generate_content(model=model_name, contents=prompt)
    return response.text or ""


def _parse_findings(audit_output: str, severity_threshold: str) -> list[dict[str, str]]:
    """Extract findings at or above severity_threshold from the STRIDE table."""
    min_level = _SEVERITY_ORDER.get(severity_threshold.lower(), 2)
    findings: list[dict[str, str]] = []
    for line in audit_output.splitlines():
        parts = [p.strip() for p in line.split("|") if p.strip()]
        if len(parts) < 4:
            continue
        severity_cell = parts[3].lower() if len(parts) > 3 else ""
        for sev in ("high", "medium", "low"):
            if sev in severity_cell and _SEVERITY_ORDER.get(sev, 0) >= min_level:
                findings.append({
                    "id": parts[0],
                    "category": parts[1],
                    "description": parts[2],
                    "severity": sev,
                    "mitigation": parts[4] if len(parts) > 4 else "",
                })
                break
    return findings


def generate_patch(
    finding: dict[str, str],
    target_path: str,
    skill_dir: str,
    model_name: str = "gemini-2.0-flash",
) -> str:
    """Call patch_agent LLM with vulnerability context, return patched file content."""
    skill_md = os.path.join(skill_dir, "SKILL.md")
    skill_text = open(skill_md).read() if os.path.exists(skill_md) else ""
    code_text = open(target_path).read() if os.path.exists(target_path) else ""
    prompt = (
        f"{skill_text}\n\n"
        f"## Vulnerability\n"
        f"ID: {finding['id']}\n"
        f"Category: {finding['category']}\n"
        f"Severity: {finding['severity']}\n"
        f"Description: {finding['description']}\n"
        f"Mitigation: {finding['mitigation']}\n\n"
        f"## Original File: {os.path.basename(target_path)}\n\n"
        f"```python\n{code_text}\n```\n\n"
        "Return ONLY the complete patched file content."
    )
    client = genai.Client(vertexai=True)
    response = client.models.generate_content(model=model_name, contents=prompt)
    return response.text or ""


def apply_patch(patch_content: str, target_path: str) -> str:
    """Write patch_content to target_path; return original content for revert."""
    original = open(target_path).read() if os.path.exists(target_path) else ""
    cleaned = re.sub(r"^```[a-z]*\n", "", patch_content, flags=re.MULTILINE)
    cleaned = re.sub(r"^```$", "", cleaned, flags=re.MULTILINE).strip()
    with open(target_path, "w") as f:
        f.write(cleaned)
    return original


def verify_patch(commands: list[str], project_root: str) -> tuple[bool, str]:
    """Run verification commands; return (passed, combined_stdout+stderr)."""
    outputs: list[str] = []
    for cmd in commands:
        result = subprocess.run(
            cmd.split(),
            capture_output=True,
            text=True,
            cwd=project_root,
        )
        outputs.append(result.stdout + result.stderr)
        if result.returncode != 0:
            return False, "\n".join(outputs)
    return True, "\n".join(outputs)


def revert_file(target_path: str, original_content: str) -> None:
    """Restore target_path to original_content."""
    with open(target_path, "w") as f:
        f.write(original_content)


def _git_commit_heal(
    branch_name: str, target_path: str, finding: dict[str, str], project_root: str
) -> None:
    """Create branch, stage the healed file, and commit."""
    subprocess.run(["git", "checkout", "-b", branch_name], check=True, cwd=project_root)
    subprocess.run(["git", "add", target_path], check=True, cwd=project_root)
    msg = f"fix(stride-heal): patch {finding['category']} vulnerability {finding['id']}"
    subprocess.run(["git", "commit", "-m", msg], check=True, cwd=project_root)


def create_heal_pr(
    finding: dict[str, str], target_path: str, project_root: str
) -> str:
    """Commit, push, and open a PR for the healed file; return PR URL."""
    from datetime import date
    branch = f"stride-heal/{finding['id'].lower()}-{date.today().strftime('%Y%m%d')}"
    _git_commit_heal(branch, target_path, finding, project_root)
    subprocess.run(["git", "push", "-u", "origin", branch], check=True, cwd=project_root)
    body = (
        f"Auto-generated security patch.\n\n"
        f"**Vulnerability:** {finding['description']}\n"
        f"**Severity:** {finding['severity']}\n\n"
        f"> Requires manual review before merge."
    )
    result = subprocess.run(
        ["gh", "pr", "create",
         "--title", f"fix(stride-heal): {finding['category']} — {finding['id']}",
         "--body", body,
         "--base", "develop",
         "--head", branch],
        capture_output=True, text=True, check=True, cwd=project_root,
    )
    return result.stdout.strip()
