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

"""Unit tests for flywheel_config_loader.py — three-layer surface control."""

import os
import tempfile

import pytest
import yaml

from app.app_utils.flywheel_config_loader import (
    _apply_env_overrides,
    _DEFAULTS,
    load_flywheel_config,
)


@pytest.fixture(autouse=True)
def clear_cache():
    load_flywheel_config.cache_clear()
    yield
    load_flywheel_config.cache_clear()


@pytest.fixture(autouse=True)
def clean_env(monkeypatch):
    for key in (
        "QUALITY_FLYWHEEL_ENABLED",
        "QUALITY_FLYWHEEL_ARBITRATOR_ENABLED",
        "QUALITY_FLYWHEEL_AMBIENT_ENABLED",
        "QUALITY_FLYWHEEL_MODE",
    ):
        monkeypatch.delenv(key, raising=False)


def test_defaults_when_no_file():
    cfg = load_flywheel_config(path="/nonexistent/quality_flywheel.yaml")
    fw = cfg["quality_flywheel"]
    assert fw["enabled"] is False
    assert fw["arbitrator"]["enabled"] is True
    assert fw["ambient"]["enabled"] is False
    assert fw["mode"] == "observe_only"
    assert fw["require_manual_review"] is True


def test_yaml_overrides_defaults(tmp_path):
    yaml_file = tmp_path / "quality_flywheel.yaml"
    yaml_file.write_text(yaml.dump({
        "quality_flywheel": {
            "enabled": True,
            "mode": "optimize",
            "arbitrator": {"enabled": True},
            "ambient": {"enabled": True},
        }
    }))
    cfg = load_flywheel_config(path=str(yaml_file))
    fw = cfg["quality_flywheel"]
    assert fw["enabled"] is True
    assert fw["mode"] == "optimize"
    assert fw["ambient"]["enabled"] is True


def test_env_master_enabled(monkeypatch):
    monkeypatch.setenv("QUALITY_FLYWHEEL_ENABLED", "true")
    cfg = load_flywheel_config(path="/nonexistent/quality_flywheel.yaml")
    assert cfg["quality_flywheel"]["enabled"] is True


def test_env_master_disabled(monkeypatch):
    monkeypatch.setenv("QUALITY_FLYWHEEL_ENABLED", "false")
    cfg = load_flywheel_config(path="/nonexistent/quality_flywheel.yaml")
    assert cfg["quality_flywheel"]["enabled"] is False


def test_env_arbitrator_disabled(monkeypatch):
    monkeypatch.setenv("QUALITY_FLYWHEEL_ARBITRATOR_ENABLED", "false")
    cfg = load_flywheel_config(path="/nonexistent/quality_flywheel.yaml")
    assert cfg["quality_flywheel"]["arbitrator"]["enabled"] is False


def test_env_ambient_enabled(monkeypatch):
    monkeypatch.setenv("QUALITY_FLYWHEEL_AMBIENT_ENABLED", "true")
    cfg = load_flywheel_config(path="/nonexistent/quality_flywheel.yaml")
    assert cfg["quality_flywheel"]["ambient"]["enabled"] is True


def test_env_mode_override(monkeypatch):
    monkeypatch.setenv("QUALITY_FLYWHEEL_MODE", "open_pr")
    cfg = load_flywheel_config(path="/nonexistent/quality_flywheel.yaml")
    assert cfg["quality_flywheel"]["mode"] == "open_pr"


def test_env_overrides_yaml(tmp_path, monkeypatch):
    yaml_file = tmp_path / "quality_flywheel.yaml"
    yaml_file.write_text(yaml.dump({"quality_flywheel": {"enabled": True}}))
    monkeypatch.setenv("QUALITY_FLYWHEEL_ENABLED", "false")
    cfg = load_flywheel_config(path=str(yaml_file))
    assert cfg["quality_flywheel"]["enabled"] is False


def test_corrupt_yaml_falls_back_to_defaults(tmp_path):
    bad_file = tmp_path / "quality_flywheel.yaml"
    bad_file.write_text(": : bad yaml : :")
    cfg = load_flywheel_config(path=str(bad_file))
    assert cfg["quality_flywheel"]["enabled"] is False


def test_require_manual_review_preserved(tmp_path):
    yaml_file = tmp_path / "quality_flywheel.yaml"
    yaml_file.write_text(yaml.dump({"quality_flywheel": {"enabled": True}}))
    cfg = load_flywheel_config(path=str(yaml_file))
    assert cfg["quality_flywheel"]["require_manual_review"] is True
