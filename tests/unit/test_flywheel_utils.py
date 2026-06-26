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

"""Unit tests for flywheel_utils.py — Quality Flywheel pipeline stages."""

import json
import os
import textwrap
from unittest.mock import MagicMock, patch

import pytest

from app.app_utils.flywheel_utils import (
    detect_violations,
    generate_few_shot,
    revert_few_shot,
    validate_routing,
    write_few_shot,
)


# ---------------------------------------------------------------------------
# detect_violations
# ---------------------------------------------------------------------------

def test_detect_violations_returns_empty_when_no_db(tmp_path):
    result = detect_violations(str(tmp_path / "missing.json"))
    assert result == []


def test_detect_violations_returns_empty_when_no_violations(tmp_path):
    db = [{"scout_tag": "stride", "outcome_violations": []} for _ in range(5)]
    db_path = str(tmp_path / "telemetry_db.json")
    with open(db_path, "w") as f:
        json.dump(db, f)
    result = detect_violations(db_path, window=20, threshold=3)
    assert result == []


def test_detect_violations_triggers_above_threshold(tmp_path):
    db = [
        {"scout_tag": "stride", "outcome_violations": ["routing_confidence"]}
        for _ in range(4)
    ]
    db_path = str(tmp_path / "telemetry_db.json")
    with open(db_path, "w") as f:
        json.dump(db, f)
    result = detect_violations(db_path, window=20, threshold=3)
    assert "stride" in result


def test_detect_violations_does_not_trigger_below_threshold(tmp_path):
    db = [
        {"scout_tag": "stride", "outcome_violations": ["routing_confidence"]}
        for _ in range(2)
    ]
    db_path = str(tmp_path / "telemetry_db.json")
    with open(db_path, "w") as f:
        json.dump(db, f)
    result = detect_violations(db_path, window=20, threshold=3)
    assert result == []


def test_detect_violations_excludes_non_optimizable_tags(tmp_path):
    db = [
        {"scout_tag": "math", "outcome_violations": ["routing_confidence"]}
        for _ in range(5)
    ]
    db_path = str(tmp_path / "telemetry_db.json")
    with open(db_path, "w") as f:
        json.dump(db, f)
    result = detect_violations(db_path, window=20, threshold=3)
    assert result == []


def test_detect_violations_respects_window(tmp_path):
    # 4 violations but outside the window=2 look-back
    db = [
        {"scout_tag": "stride", "outcome_violations": ["routing_confidence"]}
        for _ in range(4)
    ] + [{"scout_tag": "stride", "outcome_violations": []}] * 2
    db_path = str(tmp_path / "telemetry_db.json")
    with open(db_path, "w") as f:
        json.dump(db, f)
    result = detect_violations(db_path, window=2, threshold=3)
    assert result == []


# ---------------------------------------------------------------------------
# write_few_shot / revert_few_shot
# ---------------------------------------------------------------------------

def test_write_few_shot_appends_example(tmp_path):
    few_shots_path = str(tmp_path / "few_shots.json")
    with open(few_shots_path, "w") as f:
        json.dump({"examples": [{"input": "a", "output": "b"}]}, f)

    original = write_few_shot(few_shots_path, {"input": "c", "output": "d"})

    with open(few_shots_path) as f:
        data = json.load(f)

    assert len(data["examples"]) == 2
    assert data["examples"][-1] == {"input": "c", "output": "d"}
    assert original == [{"input": "a", "output": "b"}]


def test_write_few_shot_creates_file_if_missing(tmp_path):
    few_shots_path = str(tmp_path / "few_shots.json")
    write_few_shot(few_shots_path, {"input": "x", "output": "y"})

    with open(few_shots_path) as f:
        data = json.load(f)
    assert data["examples"] == [{"input": "x", "output": "y"}]


def test_revert_few_shot_restores_original(tmp_path):
    few_shots_path = str(tmp_path / "few_shots.json")
    original = [{"input": "orig", "output": "orig_out"}]
    revert_few_shot(few_shots_path, original)

    with open(few_shots_path) as f:
        data = json.load(f)
    assert data["examples"] == original


# ---------------------------------------------------------------------------
# generate_few_shot (LLM mocked)
# ---------------------------------------------------------------------------

def _mock_genai(response_text: str):
    """Return a context manager that patches the lazy genai import in generate_few_shot."""
    mock_response = MagicMock()
    mock_response.text = response_text
    mock_client = MagicMock()
    mock_client.models.generate_content.return_value = mock_response
    mock_genai_module = MagicMock()
    mock_genai_module.Client.return_value = mock_client
    return patch("google.genai", mock_genai_module, create=True), mock_genai_module


def test_generate_few_shot_returns_valid_example(tmp_path):
    skill_dir = str(tmp_path)
    with open(os.path.join(skill_dir, "SKILL.md"), "w") as f:
        f.write("# STRIDE skill instructions\nAnalyse security threats.")
    with open(os.path.join(skill_dir, "few_shots.json"), "w") as f:
        json.dump({"examples": [{"input": "old", "output": "old_out"}]}, f)

    mock_response = MagicMock()
    mock_response.text = json.dumps({"input": "new test prompt", "output": "new detailed output"})
    mock_client = MagicMock()
    mock_client.models.generate_content.return_value = mock_response

    with patch("app.app_utils.flywheel_utils.genai") as mock_genai_mod:
        mock_genai_mod.Client.return_value = mock_client
        result = generate_few_shot("stride", skill_dir, violation_count=4)

    assert result["input"] == "new test prompt"
    assert result["output"] == "new detailed output"


def test_generate_few_shot_strips_markdown_fences(tmp_path):
    skill_dir = str(tmp_path)

    mock_response = MagicMock()
    mock_response.text = '```json\n{"input": "q", "output": "a"}\n```'
    mock_client = MagicMock()
    mock_client.models.generate_content.return_value = mock_response

    with patch("app.app_utils.flywheel_utils.genai") as mock_genai_mod:
        mock_genai_mod.Client.return_value = mock_client
        result = generate_few_shot("stride", skill_dir, violation_count=3)

    assert result["input"] == "q"
    assert result["output"] == "a"


def test_generate_few_shot_raises_on_bad_schema(tmp_path):
    skill_dir = str(tmp_path)

    mock_response = MagicMock()
    mock_response.text = '{"wrong_key": "no"}'
    mock_client = MagicMock()
    mock_client.models.generate_content.return_value = mock_response

    with patch("app.app_utils.flywheel_utils.genai") as mock_genai_mod:
        mock_genai_mod.Client.return_value = mock_client
        with pytest.raises(ValueError):
            generate_few_shot("stride", skill_dir, violation_count=3)


# ---------------------------------------------------------------------------
# validate_routing
# ---------------------------------------------------------------------------

def test_validate_routing_returns_false_when_script_missing(tmp_path):
    passed, accuracy = validate_routing(str(tmp_path))
    assert passed is False
    assert accuracy == 0.0


def test_validate_routing_parses_accuracy_and_passes(tmp_path):
    script_dir = tmp_path / "tests" / "scripts" / "phase6-deep-testing"
    script_dir.mkdir(parents=True)
    script_path = script_dir / "test_deep_testing.py"
    script_path.write_text(
        textwrap.dedent("""\
            print("  Routing Accuracy:        4/5 (80.0%)")
        """)
    )
    passed, accuracy = validate_routing(str(tmp_path), min_accuracy=0.60)
    assert passed is True
    assert abs(accuracy - 0.8) < 0.01


def test_validate_routing_fails_when_accuracy_below_threshold(tmp_path):
    script_dir = tmp_path / "tests" / "scripts" / "phase6-deep-testing"
    script_dir.mkdir(parents=True)
    script_path = script_dir / "test_deep_testing.py"
    script_path.write_text(
        textwrap.dedent("""\
            print("  Routing Accuracy:        2/5 (40.0%)")
        """)
    )
    passed, accuracy = validate_routing(str(tmp_path), min_accuracy=0.60)
    assert passed is False
    assert abs(accuracy - 0.4) < 0.01
