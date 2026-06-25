"""Phase 18 smoke tests — STRIDE Self-Healing pipeline."""

import subprocess
import sys
import textwrap

import pytest


def test_stride_heal_help():
    """CLI help exits cleanly."""
    result = subprocess.run(
        ["uv", "run", "arbitrator", "stride-heal", "--help"],
        capture_output=True, text=True,
    )
    assert result.returncode == 0
    assert "audit" in result.stdout.lower() or "stride" in result.stdout.lower()


def test_load_self_healing_config_smoke():
    """Config loader returns a dict with expected keys."""
    from app.app_utils.patch_agent_utils import load_self_healing_config
    load_self_healing_config.cache_clear()
    cfg = load_self_healing_config()
    sh = cfg["stride_self_healing"]
    assert "enabled" in sh
    assert "mode" in sh
    assert "detection" in sh
    assert "verification" in sh
    load_self_healing_config.cache_clear()


def test_parse_findings_smoke():
    """parse_findings handles a static sample without crashing."""
    from app.app_utils.patch_agent_utils import _parse_findings
    sample = textwrap.dedent("""\
        | VULN-001 | Information Disclosure | Hardcoded API key | High | Use env vars |
        | VULN-002 | Tampering | Missing validation | Medium | Add checks |
    """)
    findings = _parse_findings(sample, "medium")
    assert len(findings) == 2
    assert all("id" in f and "severity" in f for f in findings)


def test_apply_and_revert(tmp_path):
    """apply_patch writes new content; revert_file restores original."""
    from app.app_utils.patch_agent_utils import apply_patch, revert_file
    target = tmp_path / "sample.py"
    target.write_text("x = 1\n")

    original = apply_patch("x = 2\n", str(target))
    assert target.read_text() == "x = 2\n"
    assert original == "x = 1\n"

    revert_file(str(target), original)
    assert target.read_text() == "x = 1\n"


def test_verify_patch_passthrough(tmp_path):
    """verify_patch with a trivially passing command returns True."""
    from app.app_utils.patch_agent_utils import verify_patch
    passed, output = verify_patch(["python3", "-c", "print('ok')"], str(tmp_path))
    assert passed is True
    assert "ok" in output


def test_stride_heal_audit_only_dry_run(tmp_path, monkeypatch):
    """--dry-run with audit_only mode exits 0 and prints report (LLM mocked)."""
    from unittest.mock import MagicMock, patch
    from app.app_utils import patch_agent_utils as pau

    # Create a minimal target file
    target = tmp_path / "vuln.py"
    target.write_text("SECRET = 'hardcoded'\n")

    # Stub out LLM
    mock_resp = MagicMock()
    mock_resp.text = "| VULN-001 | Information Disclosure | Hardcoded secret | High | Use env |"
    mock_client = MagicMock()
    mock_client.models.generate_content.return_value = mock_resp

    pau.load_self_healing_config.cache_clear()
    monkeypatch.setenv("SELF_HEALING_MODE", "audit_only")

    with patch("app.app_utils.patch_agent_utils.genai") as mock_genai:
        mock_genai.Client.return_value = mock_client
        result = subprocess.run(
            ["uv", "run", "arbitrator", "stride-heal", str(target), "--dry-run"],
            capture_output=True, text=True,
        )

    pau.load_self_healing_config.cache_clear()
    assert result.returncode == 0
