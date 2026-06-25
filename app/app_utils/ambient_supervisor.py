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
File: ambient_supervisor.py
Purpose: [EXPERIMENTAL] Event-driven background observers for Quality Flywheel and STRIDE Self-Healing.
Why it exists: Implements the "ambient agent" pattern — continuously monitoring data streams
               and acting autonomously when conditions are met, without waiting for human prompts.
How it works: on_run_saved() is called from save_run() after each telemetry write. It checks
              each feature's ambient surface flag and dispatches to the appropriate observer.
              All errors are caught and logged; the main agent flow is never blocked.
"""

import logging
import os
from typing import Any

logger = logging.getLogger(__name__)

_AMBIENT_STRIDE_TAGS = {"coding", "stride"}


def _load_stride_config() -> dict[str, Any]:
    from app.app_utils.patch_agent_utils import load_self_healing_config
    return load_self_healing_config()


def _load_flywheel_config() -> dict[str, Any]:
    from app.app_utils.flywheel_config_loader import load_flywheel_config
    return load_flywheel_config()


def _stride_should_intervene(run_record: dict[str, Any], cfg: dict[str, Any]) -> bool:
    """Return True when the ambient STRIDE surface is active and this run is relevant."""
    heal = cfg.get("stride_self_healing", {})
    if not heal.get("enabled", False):
        return False
    if not heal.get("ambient", {}).get("enabled", False):
        return False
    return run_record.get("scout_tag") in _AMBIENT_STRIDE_TAGS


def _flywheel_should_intervene(fw_cfg: dict[str, Any]) -> bool:
    """Return True when the ambient Flywheel surface is active."""
    fw = fw_cfg.get("quality_flywheel", {})
    if not fw.get("enabled", False):
        return False
    return fw.get("ambient", {}).get("enabled", False)


def _observe_flywheel(project_root: str) -> None:
    """Ambient Flywheel observer: scan telemetry for violations and log findings."""
    from app.app_utils.flywheel_utils import detect_violations
    from app.app_utils.kpi_config_loader import load_kpi_config
    db_path = os.path.join(project_root, "telemetry_db.json")
    kpi = load_kpi_config().get("flywheel", {})
    triggered = detect_violations(
        db_path, window=kpi.get("window", 20), threshold=kpi.get("threshold", 3)
    )
    if triggered:
        logger.info("[AmbientFlywheel] Violations detected for: %s", triggered)
    else:
        logger.debug("[AmbientFlywheel] No violations above threshold.")


def _observe_stride(
    run_record: dict[str, Any], stride_cfg: dict[str, Any], project_root: str
) -> None:
    """Ambient STRIDE observer: audit the file from this run and log findings."""
    from app.app_utils.patch_agent_utils import run_stride_audit, _parse_findings
    target = run_record.get("target_file")
    if not target or not os.path.isfile(target):
        logger.debug("[AmbientSTRIDE] No target_file in run record — skipping.")
        return
    heal = stride_cfg["stride_self_healing"]
    skill_dir = os.path.join(project_root, "app", "skills", "stride")
    threshold = heal.get("detection", {}).get("severity_threshold", "medium")
    report = run_stride_audit(target, skill_dir)
    findings = _parse_findings(report, threshold)
    logger.info(
        "[AmbientSTRIDE] %d finding(s) in %s (mode=%s)",
        len(findings), target, heal.get("mode", "audit_only"),
    )


def on_run_saved(run_record: dict[str, Any], project_root: str) -> None:
    """[EXPERIMENTAL] Event hook: called after each save_run(). Never blocks the agent."""
    try:
        stride_cfg = _load_stride_config()
    except Exception as exc:
        logger.warning("[AmbientSupervisor] STRIDE config load failed: %s", exc)
        stride_cfg = {}
    try:
        fw_cfg = _load_flywheel_config()
    except Exception as exc:
        logger.warning("[AmbientSupervisor] Flywheel config load failed: %s", exc)
        fw_cfg = {}
    if _flywheel_should_intervene(fw_cfg):
        try:
            _observe_flywheel(project_root)
        except Exception as exc:
            logger.warning("[AmbientFlywheel] Observer error: %s", exc)
    if _stride_should_intervene(run_record, stride_cfg):
        try:
            _observe_stride(run_record, stride_cfg, project_root)
        except Exception as exc:
            logger.warning("[AmbientSTRIDE] Observer error: %s", exc)
