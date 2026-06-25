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
File: flywheel_utils.py
Purpose: Five-stage offline optimization loop that reads telemetry violations,
         generates improved few-shot examples for struggling skills, validates that
         routing accuracy doesn't regress, then opens a PR with the new example.
Why it exists: Closes the Product Agent feedback loop — violations written to
               telemetry_db.json now drive autonomous skill improvement rather than
               just surfacing on the dashboard.
How it works: DETECT → GENERATE → WRITE → VALIDATE → PR.
              If validation fails, WRITE is reverted and no PR is opened.
"""

import json
import os
import re
import subprocess
from datetime import datetime
from typing import Any

from google import genai  # type: ignore[import-not-found]

from app.config import MODEL

PROJECT_ID = os.environ.get("GOOGLE_CLOUD_PROJECT", "kaggle-capstone-500322")
LOCATION = os.environ.get("GOOGLE_CLOUD_LOCATION", "us-west1")


# Skills that have few_shots.json files flywheel can improve.
_OPTIMIZABLE_TAGS = {"stride", "researcher"}


def detect_violations(
    db_path: str,
    window: int = 20,
    threshold: int = 3,
) -> list[str]:
    """Return scout_tags with >= threshold routing_confidence violations in last window rows."""
    if not os.path.exists(db_path):
        return []

    with open(db_path) as f:
        try:
            rows: list[dict] = json.load(f)
        except json.JSONDecodeError:
            return []

    recent = rows[-window:] if len(rows) > window else rows

    counts: dict[str, int] = {}
    for row in recent:
        tag = row.get("scout_tag", "")
        violations = row.get("outcome_violations", [])
        if tag and "routing_confidence" in violations and tag in _OPTIMIZABLE_TAGS:
            counts[tag] = counts.get(tag, 0) + 1

    return [tag for tag, count in counts.items() if count >= threshold]


def _build_generation_prompt(skill_dir: str, violation_count: int) -> str:
    """Build the LLM prompt for few-shot generation."""
    skill_md_path = os.path.join(skill_dir, "SKILL.md")
    few_shots_path = os.path.join(skill_dir, "few_shots.json")

    skill_md = ""
    if os.path.exists(skill_md_path):
        with open(skill_md_path) as f:
            skill_md = f.read()

    existing_examples: list[dict] = []
    if os.path.exists(few_shots_path):
        with open(few_shots_path) as f:
            existing_examples = json.load(f).get("examples", [])

    existing_summary = "\n".join(
        f"Example {i + 1} input: {ex['input'][:120]}..."
        for i, ex in enumerate(existing_examples)
    )
    return (
        "You are a prompt engineering expert improving a skill for an AI agent.\n\n"
        f"SKILL INSTRUCTIONS:\n{skill_md[:2000]}\n\n"
        f"EXISTING FEW-SHOT EXAMPLES (summarised):\n{existing_summary}\n\n"
        f"CONTEXT: This skill has had {violation_count} routing_confidence violations in recent "
        "telemetry, meaning the Scout agent is not confidently routing prompts to this skill. "
        "Generate one new, high-quality few-shot example that clearly illustrates when and how "
        "to use this skill.\n\n"
        'Return a JSON object with exactly two keys: "input" and "output".\n'
        '- "input" should be a realistic user prompt that should route to this skill.\n'
        '- "output" should be a complete, well-structured response demonstrating the skill\'s ideal output.\n\n'
        "Respond with ONLY the JSON object, no markdown fences, no explanation."
    )


def _parse_llm_example(raw: str) -> dict[str, str]:
    """Strip markdown fences and parse JSON; raise ValueError on bad schema."""
    raw = re.sub(r"^```(?:json)?\s*", "", raw.strip())
    raw = re.sub(r"\s*```$", "", raw)
    example = json.loads(raw)
    if not isinstance(example, dict) or "input" not in example or "output" not in example:
        raise ValueError(f"LLM returned unexpected schema: {raw[:200]}")
    return {"input": str(example["input"]), "output": str(example["output"])}


def generate_few_shot(
    tag: str,
    skill_dir: str,
    violation_count: int,
    model_name: str = MODEL,
) -> dict[str, str]:
    """Call LLM to produce one new {input, output} few-shot for the named skill."""
    prompt = _build_generation_prompt(skill_dir, violation_count)
    client = genai.Client(vertexai=True, project=PROJECT_ID, location=LOCATION)
    response = client.models.generate_content(model=model_name, contents=prompt)
    return _parse_llm_example(response.text or "")


def write_few_shot(few_shots_path: str, example: dict[str, str]) -> list[dict]:
    """Append example to few_shots.json; return original examples list for potential revert."""
    if os.path.exists(few_shots_path):
        with open(few_shots_path) as f:
            data: dict[str, Any] = json.load(f)
    else:
        data = {"examples": []}

    original_examples: list[dict] = list(data.get("examples", []))
    data["examples"] = original_examples + [example]

    with open(few_shots_path, "w") as f:
        json.dump(data, f, indent=2)

    return original_examples


def validate_routing(
    project_root: str,
    min_accuracy: float = 0.60,
) -> tuple[bool, float]:
    """Run the phase-6 deep-testing script; return (passed, accuracy_ratio)."""
    script = os.path.join(
        project_root,
        "tests",
        "scripts",
        "phase6-deep-testing",
        "test_deep_testing.py",
    )
    if not os.path.exists(script):
        return False, 0.0

    try:
        result = subprocess.run(
            ["uv", "run", "python", script],
            capture_output=True,
            text=True,
            timeout=180,
            cwd=project_root,
        )
        output = result.stdout + result.stderr
    except (subprocess.TimeoutExpired, FileNotFoundError):
        return False, 0.0

    # Parse "Routing Accuracy:        4/5 (80.0%)" or "4/5" patterns
    match = re.search(r"Routing Accuracy[^\d]*(\d+)\s*/\s*(\d+)", output, re.IGNORECASE)
    if match:
        numerator, denominator = int(match.group(1)), int(match.group(2))
        accuracy = numerator / denominator if denominator > 0 else 0.0
        return accuracy >= min_accuracy, accuracy

    return False, 0.0


def revert_few_shot(few_shots_path: str, original_examples: list[dict]) -> None:
    """Restore few_shots.json to original_examples."""
    with open(few_shots_path, "w") as f:
        json.dump({"examples": original_examples}, f, indent=2)


def _git_commit_and_push(branch_name: str, files_changed: list[str], tag: str, project_root: str) -> None:
    """Create branch, stage files, commit, and push."""
    for cmd in [
        ["git", "checkout", "-b", branch_name],
        ["git", "add"] + files_changed,
    ]:
        subprocess.run(cmd, cwd=project_root, check=True, capture_output=True)

    commit_msg = (
        f"feat(flywheel): add optimized few-shot example for {tag} skill\n\n"
        f"Quality Flywheel detected routing_confidence violations for '{tag}' and\n"
        f"generated a new few-shot example. Validation passed with routing accuracy >= 60%.\n\n"
        f"Closes #18"
    )
    subprocess.run(
        ["git", "commit", "-m", commit_msg],
        cwd=project_root, check=True, capture_output=True,
    )
    subprocess.run(
        ["git", "push", "-u", "origin", branch_name],
        cwd=project_root, check=True, capture_output=True,
    )


def create_pr(tag: str, files_changed: list[str], project_root: str) -> str:
    """Create branch flywheel/optimize-<tag>-<date>, commit, open PR to develop. Returns PR URL."""
    date_str = datetime.now().strftime("%Y%m%d")
    branch_name = f"flywheel/optimize-{tag}-{date_str}"
    _git_commit_and_push(branch_name, files_changed, tag, project_root)

    pr_body = (
        f"## Summary\n"
        f"- Quality Flywheel detected `routing_confidence` violations for the `{tag}` skill\n"
        f"- Generated one new few-shot example via `{MODEL}`\n"
        f"- Validated that routing accuracy did not regress below 60%\n\n"
        f"## Files changed\n"
        + "\n".join(f"- `{f}`" for f in files_changed)
        + "\n\nCloses #18"
    )
    pr_result = subprocess.run(
        [
            "gh", "pr", "create",
            "--base", "develop",
            "--title", f"feat(flywheel): optimized few-shot for {tag} skill",
            "--body", pr_body,
        ],
        cwd=project_root, capture_output=True, text=True, check=True,
    )
    return pr_result.stdout.strip()
