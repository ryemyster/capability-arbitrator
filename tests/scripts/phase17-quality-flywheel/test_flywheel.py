"""
Phase 17 smoke tests — Quality Flywheel offline optimizer.
# Created: 2026-06-25 MDT
"""

import json
import os
from unittest.mock import MagicMock, patch

from app.app_utils.flywheel_utils import (
    detect_violations,
    revert_few_shot,
    write_few_shot,
)
from app.app_utils.kpi_config_loader import load_kpi_config

PASS = "[PASS]"
FAIL = "[FAIL]"


def run(label: str, condition: bool) -> bool:
    print(f"  {PASS if condition else FAIL} {label}")
    return condition


def test_kpi_config_loads_without_error() -> bool:
    cfg = load_kpi_config()
    ok = (
        "product_agent" in cfg
        and "flywheel" in cfg
        and cfg["product_agent"]["routing_confidence_threshold"] == 75.0
        and cfg["flywheel"]["threshold"] == 3
    )
    return run("kpi_config.yaml loads with correct defaults", ok)


def test_detect_violations_triggers_for_stride(tmp_path) -> bool:
    db = [
        {"scout_tag": "stride", "outcome_violations": ["routing_confidence"]}
        for _ in range(4)
    ]
    db_path = str(tmp_path / "telemetry_db.json")
    with open(db_path, "w") as f:
        json.dump(db, f)
    result = detect_violations(db_path, window=20, threshold=3)
    return run("detect_violations triggers for stride with 4 violations", "stride" in result)


def test_detect_violations_skips_math(tmp_path) -> bool:
    db = [
        {"scout_tag": "math", "outcome_violations": ["routing_confidence"]}
        for _ in range(5)
    ]
    db_path = str(tmp_path / "telemetry_db.json")
    with open(db_path, "w") as f:
        json.dump(db, f)
    result = detect_violations(db_path, window=20, threshold=3)
    return run("detect_violations ignores math tag (no few_shots to optimize)", result == [])


def test_write_and_revert_roundtrip(tmp_path) -> bool:
    few_shots_path = str(tmp_path / "few_shots.json")
    original = [{"input": "original", "output": "original_out"}]
    with open(few_shots_path, "w") as f:
        json.dump({"examples": original}, f)

    original_back = write_few_shot(few_shots_path, {"input": "new", "output": "new_out"})
    with open(few_shots_path) as f:
        after_write = json.load(f)

    revert_few_shot(few_shots_path, original_back)
    with open(few_shots_path) as f:
        after_revert = json.load(f)

    ok = (
        len(after_write["examples"]) == 2
        and after_revert["examples"] == original
    )
    return run("write_few_shot + revert_few_shot roundtrip is correct", ok)


def test_generate_few_shot_calls_llm_with_skill_context(tmp_path) -> bool:
    from app.app_utils.flywheel_utils import generate_few_shot

    skill_dir = str(tmp_path)
    with open(os.path.join(skill_dir, "SKILL.md"), "w") as f:
        f.write("# Test skill")

    mock_response = MagicMock()
    mock_response.text = json.dumps({"input": "test q", "output": "test a"})
    mock_client = MagicMock()
    mock_client.models.generate_content.return_value = mock_response

    with patch("app.app_utils.flywheel_utils.genai") as mock_genai:
        mock_genai.Client.return_value = mock_client
        result = generate_few_shot("stride", skill_dir, violation_count=3)

    ok = result == {"input": "test q", "output": "test a"}
    return run("generate_few_shot calls LLM and parses JSON response", ok)


def test_flywheel_cli_subcommand_is_registered() -> bool:
    import subprocess
    result = subprocess.run(
        ["uv", "run", "arbitrator", "flywheel", "--help"],
        capture_output=True, text=True, timeout=15,
        cwd=os.path.join(os.path.dirname(__file__), "..", "..", ".."),
    )
    ok = "--dry-run" in result.stdout and "--window" in result.stdout
    return run("arbitrator flywheel --help shows --dry-run and --window flags", ok)


if __name__ == "__main__":
    import tempfile

    print("\n=== Phase 17: Quality Flywheel Smoke Tests ===\n")
    with tempfile.TemporaryDirectory() as tmp:
        from pathlib import Path
        tmp_path = Path(tmp)
        for sub in ("detect1", "detect2", "roundtrip", "gen"):
            (tmp_path / sub).mkdir(parents=True, exist_ok=True)
        results = [
            test_kpi_config_loads_without_error(),
            test_detect_violations_triggers_for_stride(tmp_path / "detect1"),
            test_detect_violations_skips_math(tmp_path / "detect2"),
            test_write_and_revert_roundtrip(tmp_path / "roundtrip"),
            test_generate_few_shot_calls_llm_with_skill_context(tmp_path / "gen"),
            test_flywheel_cli_subcommand_is_registered(),
        ]
    passed = sum(results)
    total = len(results)
    print(f"\n{'=' * 50}")
    print(f"Results: {passed}/{total} passed")
    if passed < total:
        raise SystemExit(1)
