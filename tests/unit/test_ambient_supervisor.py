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

"""Unit tests for ambient_supervisor.py — three-layer surface gating behavior."""

from unittest.mock import MagicMock, patch

import pytest

from app.app_utils.ambient_supervisor import (
    _flywheel_should_intervene,
    _stride_should_intervene,
    on_run_saved,
)


def _stride_cfg(enabled=True, ambient=True):
    return {"stride_self_healing": {"enabled": enabled, "ambient": {"enabled": ambient}}}


def _fw_cfg(enabled=True, ambient=True):
    return {"quality_flywheel": {"enabled": enabled, "ambient": {"enabled": ambient}}}


# --- _stride_should_intervene ---

def test_stride_no_intervene_master_off():
    assert _stride_should_intervene({"scout_tag": "coding"}, _stride_cfg(enabled=False)) is False


def test_stride_no_intervene_ambient_off():
    assert _stride_should_intervene({"scout_tag": "coding"}, _stride_cfg(ambient=False)) is False


def test_stride_no_intervene_wrong_tag():
    assert _stride_should_intervene({"scout_tag": "math"}, _stride_cfg()) is False


def test_stride_intervenes_coding_tag():
    assert _stride_should_intervene({"scout_tag": "coding"}, _stride_cfg()) is True


def test_stride_intervenes_stride_tag():
    assert _stride_should_intervene({"scout_tag": "stride"}, _stride_cfg()) is True


# --- _flywheel_should_intervene ---

def test_flywheel_no_intervene_master_off():
    assert _flywheel_should_intervene(_fw_cfg(enabled=False)) is False


def test_flywheel_no_intervene_ambient_off():
    assert _flywheel_should_intervene(_fw_cfg(ambient=False)) is False


def test_flywheel_intervenes_when_both_on():
    assert _flywheel_should_intervene(_fw_cfg()) is True


# --- on_run_saved ---

def test_on_run_saved_master_off_is_noop():
    """Master disabled → complete no-op; neither observer fires."""
    with (
        patch("app.app_utils.ambient_supervisor._load_stride_config",
              return_value=_stride_cfg(enabled=False)),
        patch("app.app_utils.ambient_supervisor._load_flywheel_config",
              return_value=_fw_cfg(enabled=False)),
        patch("app.app_utils.ambient_supervisor._observe_flywheel") as mock_fw,
        patch("app.app_utils.ambient_supervisor._observe_stride") as mock_st,
    ):
        on_run_saved({"scout_tag": "coding"}, "/fake/root")
        mock_fw.assert_not_called()
        mock_st.assert_not_called()


def test_on_run_saved_ambient_off_is_noop():
    """Ambient disabled → neither observer fires even with master enabled."""
    with (
        patch("app.app_utils.ambient_supervisor._load_stride_config",
              return_value=_stride_cfg(ambient=False)),
        patch("app.app_utils.ambient_supervisor._load_flywheel_config",
              return_value=_fw_cfg(ambient=False)),
        patch("app.app_utils.ambient_supervisor._observe_flywheel") as mock_fw,
        patch("app.app_utils.ambient_supervisor._observe_stride") as mock_st,
    ):
        on_run_saved({"scout_tag": "coding"}, "/fake/root")
        mock_fw.assert_not_called()
        mock_st.assert_not_called()


def test_on_run_saved_both_surfaces_fire():
    """Both ambient surfaces enabled → both observers called."""
    with (
        patch("app.app_utils.ambient_supervisor._load_stride_config",
              return_value=_stride_cfg()),
        patch("app.app_utils.ambient_supervisor._load_flywheel_config",
              return_value=_fw_cfg()),
        patch("app.app_utils.ambient_supervisor._observe_flywheel") as mock_fw,
        patch("app.app_utils.ambient_supervisor._observe_stride") as mock_st,
    ):
        on_run_saved({"scout_tag": "coding"}, "/fake/root")
        mock_fw.assert_called_once_with("/fake/root")
        mock_st.assert_called_once()


def test_on_run_saved_observer_error_does_not_raise():
    """Observer errors are swallowed — main agent flow is never blocked."""
    with (
        patch("app.app_utils.ambient_supervisor._load_stride_config",
              return_value=_stride_cfg()),
        patch("app.app_utils.ambient_supervisor._load_flywheel_config",
              return_value=_fw_cfg()),
        patch("app.app_utils.ambient_supervisor._observe_flywheel",
              side_effect=RuntimeError("boom")),
        patch("app.app_utils.ambient_supervisor._observe_stride",
              side_effect=RuntimeError("boom")),
    ):
        on_run_saved({"scout_tag": "coding"}, "/fake/root")  # must not raise


def test_on_run_saved_config_error_does_not_raise():
    """Config load failure is swallowed — main agent flow is never blocked."""
    with (
        patch("app.app_utils.ambient_supervisor._load_stride_config",
              side_effect=FileNotFoundError("no config")),
        patch("app.app_utils.ambient_supervisor._load_flywheel_config",
              side_effect=FileNotFoundError("no config")),
    ):
        on_run_saved({"scout_tag": "coding"}, "/fake/root")  # must not raise
