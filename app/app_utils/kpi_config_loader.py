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
File: kpi_config_loader.py
Purpose: Loads KPI thresholds and flywheel tuning knobs from config/kpi_config.yaml.
Why it exists: Centralises all threshold values so changes propagate to both the live
               Product Agent KPI gate and the offline Quality Flywheel without touching
               source code.
How it works: Reads config/kpi_config.yaml relative to the project root, falls back to
              hardcoded defaults so unit tests work without the file on disk.
"""

import os
from functools import lru_cache
from typing import Any

_DEFAULTS: dict[str, Any] = {
    "product_agent": {
        "routing_confidence_threshold": 75.0,
        "latency_threshold_seconds": 30.0,
        "token_savings_threshold": 0.80,
    },
    "flywheel": {
        "window": 20,
        "threshold": 3,
        "min_routing_accuracy": 0.60,
    },
}

_CONFIG_PATH = os.path.join(
    os.path.dirname(__file__), "..", "..", "config", "kpi_config.yaml"
)


@lru_cache(maxsize=1)
def load_kpi_config(path: str | None = None) -> dict[str, Any]:
    """Return the merged KPI config dict (file values override defaults)."""
    resolved = os.path.abspath(path or _CONFIG_PATH)
    if not os.path.exists(resolved):
        return _DEFAULTS

    try:
        import yaml  # type: ignore[import-not-found]
        with open(resolved) as f:
            raw = yaml.safe_load(f) or {}
    except Exception:
        return _DEFAULTS

    merged: dict[str, Any] = {}
    for section, defaults in _DEFAULTS.items():
        merged[section] = {**defaults, **(raw.get(section) or {})}
    return merged
