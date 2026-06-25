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

"""Unit tests for patch_agent_utils — all LLM calls mocked."""

import os
import textwrap
from unittest.mock import MagicMock, patch

import pytest

import app.app_utils.patch_agent_utils as pau


# --- Config loading ---

def test_load_defaults_when_no_file(monkeypatch, tmp_path):
    monkeypatch.delenv("STRIDE_SELF_HEALING_ENABLED", raising=False)
    monkeypatch.delenv("STRIDE_SELF_HEALING_MODE", raising=False)
    pau.load_self_healing_config.cache_clear()
    cfg = pau.load_self_healing_config(str(tmp_path / "missing.yaml"))
    assert cfg["stride_self_healing"]["enabled"] is False
    assert cfg["stride_self_healing"]["mode"] == "audit_only"
    pau.load_self_healing_config.cache_clear()


def test_load_merges_yaml_over_defaults(monkeypatch, tmp_path):
    monkeypatch.delenv("STRIDE_SELF_HEALING_ENABLED", raising=False)
    monkeypatch.delenv("STRIDE_SELF_HEALING_MODE", raising=False)
    pau.load_self_healing_config.cache_clear()
    yaml_file = tmp_path / "stride_self_healing.yaml"
    yaml_file.write_text("stride_self_healing:\n  enabled: true\n  mode: apply_patch\n")
    cfg = pau.load_self_healing_config(str(yaml_file))
    assert cfg["stride_self_healing"]["enabled"] is True
    assert cfg["stride_self_healing"]["mode"] == "apply_patch"
    assert cfg["stride_self_healing"]["verification"]["max_attempts"] == 3
    pau.load_self_healing_config.cache_clear()


def test_env_override_enabled(monkeypatch, tmp_path):
    pau.load_self_healing_config.cache_clear()
    monkeypatch.setenv("STRIDE_SELF_HEALING_ENABLED", "true")
    monkeypatch.setenv("STRIDE_SELF_HEALING_MODE", "open_pr")
    cfg = pau.load_self_healing_config(str(tmp_path / "missing.yaml"))
    assert cfg["stride_self_healing"]["enabled"] is True
    assert cfg["stride_self_healing"]["mode"] == "open_pr"
    pau.load_self_healing_config.cache_clear()


def test_env_override_disabled(monkeypatch, tmp_path):
    pau.load_self_healing_config.cache_clear()
    monkeypatch.setenv("STRIDE_SELF_HEALING_ENABLED", "false")
    cfg = pau.load_self_healing_config(str(tmp_path / "missing.yaml"))
    assert cfg["stride_self_healing"]["enabled"] is False
    pau.load_self_healing_config.cache_clear()


# --- _parse_findings ---

_SAMPLE_AUDIT = textwrap.dedent("""\
    | VULN-001 | Information Disclosure | Hardcoded API key detected | High | Use env vars |
    | VULN-002 | Tampering | Missing input validation | Medium | Add sanitisation |
    | VULN-003 | Denial of Service | Unbounded loop | Low | Add rate limit |
""")


def test_parse_findings_high_severity():
    findings = pau._parse_findings(_SAMPLE_AUDIT, "high")
    assert len(findings) == 1
    assert findings[0]["id"] == "VULN-001"
    assert findings[0]["severity"] == "high"


def test_parse_findings_medium_threshold():
    findings = pau._parse_findings(_SAMPLE_AUDIT, "medium")
    assert len(findings) == 2
    severities = {f["severity"] for f in findings}
    assert severities == {"high", "medium"}


def test_parse_findings_filters_low():
    findings = pau._parse_findings(_SAMPLE_AUDIT, "medium")
    ids = [f["id"] for f in findings]
    assert "VULN-003" not in ids


def test_parse_findings_empty():
    findings = pau._parse_findings("No table here.", "medium")
    assert findings == []


# --- run_stride_audit (LLM mocked) ---

def test_run_stride_audit_calls_llm(tmp_path):
    skill_dir = tmp_path / "stride"
    skill_dir.mkdir()
    (skill_dir / "SKILL.md").write_text("STRIDE instructions")
    target = tmp_path / "code.py"
    target.write_text("SECRET = 'abc123'")

    mock_response = MagicMock()
    mock_response.text = "| VULN-001 | Information Disclosure | Hardcoded secret | High | Use env |"
    mock_client = MagicMock()
    mock_client.models.generate_content.return_value = mock_response

    with patch("app.app_utils.patch_agent_utils.genai") as mock_genai:
        mock_genai.Client.return_value = mock_client
        result = pau.run_stride_audit(str(target), str(skill_dir))

    assert "VULN-001" in result
    call_args = mock_client.models.generate_content.call_args
    assert "STRIDE instructions" in call_args.kwargs["contents"]
    assert "SECRET" in call_args.kwargs["contents"]


# --- generate_patch (LLM mocked) ---

def test_generate_patch_calls_llm(tmp_path):
    skill_dir = tmp_path / "patch_agent"
    skill_dir.mkdir()
    (skill_dir / "SKILL.md").write_text("Patch instructions")
    target = tmp_path / "code.py"
    target.write_text("SECRET = 'abc123'")

    finding = {
        "id": "VULN-001", "category": "Information Disclosure",
        "severity": "high", "description": "Hardcoded secret", "mitigation": "Use env",
    }
    mock_response = MagicMock()
    mock_response.text = "SECRET = os.environ.get('SECRET', '')"
    mock_client = MagicMock()
    mock_client.models.generate_content.return_value = mock_response

    with patch("app.app_utils.patch_agent_utils.genai") as mock_genai:
        mock_genai.Client.return_value = mock_client
        result = pau.generate_patch(finding, str(target), str(skill_dir))

    assert "os.environ" in result
    call_contents = mock_client.models.generate_content.call_args.kwargs["contents"]
    assert "VULN-001" in call_contents
    assert "Hardcoded secret" in call_contents


# --- apply_patch / revert_file ---

def test_apply_patch_writes_and_returns_original(tmp_path):
    target = tmp_path / "code.py"
    target.write_text("original content")
    original = pau.apply_patch("patched content", str(target))
    assert original == "original content"
    assert target.read_text() == "patched content"


def test_apply_patch_strips_markdown_fences(tmp_path):
    target = tmp_path / "code.py"
    target.write_text("x = 1")
    pau.apply_patch("```python\nx = 2\n```", str(target))
    assert target.read_text() == "x = 2"


def test_revert_file_restores_content(tmp_path):
    target = tmp_path / "code.py"
    target.write_text("patched")
    pau.revert_file(str(target), "original")
    assert target.read_text() == "original"


# --- verify_patch ---

def test_verify_patch_passes(tmp_path):
    passed, output = pau.verify_patch(["echo ok"], str(tmp_path))
    assert passed is True
    assert "ok" in output


def test_verify_patch_fails(tmp_path):
    passed, output = pau.verify_patch(["false"], str(tmp_path))
    assert passed is False


# --- GitHub integration flag ---

def test_github_not_required_for_audit_only(monkeypatch, tmp_path):
    monkeypatch.delenv("STRIDE_SELF_HEALING_MODE", raising=False)
    pau.load_self_healing_config.cache_clear()
    cfg_file = tmp_path / "stride_self_healing.yaml"
    cfg_file.write_text("stride_self_healing:\n  mode: audit_only\n")
    cfg = pau.load_self_healing_config(str(cfg_file))
    assert cfg["stride_self_healing"]["mode"] == "audit_only"
    pau.load_self_healing_config.cache_clear()
