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
File: flywheel_config_loader.py
Purpose: Loads and caches the Quality Flywheel three-layer surface config.
Why it exists: Keeps flywheel surface control (enabled/arbitrator/ambient) in its own
               YAML file, separate from kpi_config.yaml which owns operational thresholds.
How it works: YAML → defaults → QUALITY_FLYWHEEL_* env overrides; cached with lru_cache.
"""

import copy
import os
import pathlib
from functools import lru_cache
from typing import Any

_FLYWHEEL_CONFIG_PATH = (
    pathlib.Path(__file__).parent.parent.parent / "config" / "quality_flywheel.yaml"
)

_DEFAULTS: dict[str, Any] = {
    "quality_flywheel": {
        "enabled": False,
        "arbitrator": {"enabled": True},
        "ambient": {"enabled": False},
        "mode": "observe_only",
        "require_manual_review": True,
    }
}


def _apply_env_overrides(config: dict[str, Any]) -> dict[str, Any]:
    """Apply QUALITY_FLYWHEEL_* env vars over config dict values."""
    fw = dict(config.get("quality_flywheel", {}))
    enabled_env = os.getenv("QUALITY_FLYWHEEL_ENABLED", "").lower()
    if enabled_env in ("true", "1", "yes"):
        fw["enabled"] = True
    elif enabled_env in ("false", "0", "no"):
        fw["enabled"] = False
    if mode_env := os.getenv("QUALITY_FLYWHEEL_MODE"):
        fw["mode"] = mode_env
    arb = dict(fw.get("arbitrator", {"enabled": True}))
    arb_env = os.getenv("QUALITY_FLYWHEEL_ARBITRATOR_ENABLED", "").lower()
    if arb_env in ("true", "1", "yes"):
        arb["enabled"] = True
    elif arb_env in ("false", "0", "no"):
        arb["enabled"] = False
    fw["arbitrator"] = arb
    amb = dict(fw.get("ambient", {"enabled": False}))
    amb_env = os.getenv("QUALITY_FLYWHEEL_AMBIENT_ENABLED", "").lower()
    if amb_env in ("true", "1", "yes"):
        amb["enabled"] = True
    elif amb_env in ("false", "0", "no"):
        amb["enabled"] = False
    fw["ambient"] = amb
    return {**config, "quality_flywheel": fw}


@lru_cache(maxsize=1)
def load_flywheel_config(path: str | None = None) -> dict[str, Any]:
    """Return merged flywheel surface config (YAML → defaults → env overrides)."""
    config = copy.deepcopy(_DEFAULTS)
    cfg_path = pathlib.Path(path) if path else _FLYWHEEL_CONFIG_PATH
    if not cfg_path.exists():
        return _apply_env_overrides(config)
    try:
        import yaml  # type: ignore[import-not-found]
        with open(cfg_path) as f:
            raw = yaml.safe_load(f) or {}
    except Exception:
        return _apply_env_overrides(config)
    fw_raw = raw.get("quality_flywheel", {})
    fw = config["quality_flywheel"]
    fw.update({k: v for k, v in fw_raw.items() if not isinstance(v, dict)})
    for sub in ("arbitrator", "ambient"):
        if isinstance(fw_raw.get(sub), dict):
            fw[sub] = {**fw[sub], **fw_raw[sub]}
    return _apply_env_overrides(config)
