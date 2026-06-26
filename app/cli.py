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
File: cli.py
Purpose: Exposes the command-line interface (CLI) entrypoint for the Capability Arbitrator.
Why it exists: Allows developers to run the arbitrator on any codebase as a global tool or via uvx.
How it works: Parses commands for 'run' and 'dashboard', setting up execution context and runners.
"""

import argparse
import asyncio
import os
import subprocess
import sys

def run_prompt_sync(prompt: str) -> None:
    """Run the arbitrator agent locally on the prompt and stream responses."""
    # Ensure integration test mode or similar mocks aren't overriding real run unless requested
    if os.environ.get("RUN_REAL_LLM") != "true" and "INTEGRATION_TEST" not in os.environ:
        os.environ["INTEGRATION_TEST"] = "TRUE"

    async def _run() -> None:
        from google.adk.runners import InMemoryRunner
        from google.genai import types
        from app.agent import app as adk_app

        runner = InMemoryRunner(app=adk_app)
        session = await runner.session_service.create_session(
            app_name=adk_app.name, user_id="cli_user"
        )

        async for event in runner.run_async(
            user_id="cli_user",
            session_id=session.id,
            new_message=types.Content(
                role="user", parts=[types.Part.from_text(text=prompt)]
            ),
        ):
            if event.content and event.content.parts:
                for part in event.content.parts:
                    if part.text:
                        print(part.text, end="", flush=True)
            elif event.output:
                if isinstance(event.output, dict) and "capability_tag" in event.output:
                    continue
                print(f"\n[Output]: {event.output}")

    asyncio.run(_run())
    print()

def _flywheel_detect(db_path: str, window: int, threshold: int) -> tuple[list[str], str | None, str | None]:
    """Return (triggered_tags, tag, few_shots_path) or ([], None, None) when nothing to do."""
    from app.app_utils.flywheel_utils import detect_violations
    import pathlib

    triggered = detect_violations(db_path, window=window, threshold=threshold)
    if not triggered:
        return [], None, None

    tag = triggered[0]
    project_root = str(pathlib.Path(__file__).parent.parent)
    few_shots_path = os.path.join(project_root, "app", "skills", tag, "few_shots.json")
    return triggered, tag, few_shots_path


def _flywheel_write_validate_pr(
    tag: str, few_shots_path: str, example: dict, project_root: str, min_accuracy: float
) -> None:
    """Write, validate, revert-on-failure, or open PR."""
    from app.app_utils.flywheel_utils import (
        write_few_shot, validate_routing, revert_few_shot, create_pr,
    )

    original_examples = write_few_shot(few_shots_path, example)
    print(f"[Flywheel] Wrote new example to {few_shots_path}. Validating...")

    passed, accuracy = validate_routing(project_root, min_accuracy=min_accuracy)
    print(f"[Flywheel] Routing accuracy: {accuracy:.1%} (required: {min_accuracy:.0%})")

    if not passed:
        revert_few_shot(few_shots_path, original_examples)
        print(f"[Flywheel] VALIDATION FAILED — reverted {few_shots_path}. No PR opened.")
        sys.exit(1)

    print("[Flywheel] Validation passed. Opening PR...")
    try:
        pr_url = create_pr(tag, [few_shots_path], project_root)
        print(f"[Flywheel] PR opened: {pr_url}")
    except subprocess.CalledProcessError as e:
        print(f"[Flywheel] ERROR opening PR: {e}")
        sys.exit(1)


def _stride_heal_audit(
    target: str, config: dict, project_root: str
) -> tuple[list[dict], str]:
    """Run STRIDE audit on target; return (findings, raw_report)."""
    from app.app_utils.patch_agent_utils import run_stride_audit, _parse_findings
    stride_skill = os.path.join(project_root, "app", "skills", "stride")
    threshold = config["stride_self_healing"]["detection"]["severity_threshold"]
    report = run_stride_audit(target, stride_skill)
    return _parse_findings(report, threshold), report


def _stride_heal_patch_loop(
    finding: dict, target: str, config: dict, project_root: str
) -> tuple[bool, str]:
    """Patch-and-verify loop up to max_attempts; return (success, last_output)."""
    from app.app_utils.patch_agent_utils import generate_patch, apply_patch, verify_patch, revert_file
    patch_skill = os.path.join(project_root, "app", "skills", "patch_agent")
    cfg = config["stride_self_healing"]["verification"]
    commands, max_attempts = cfg["commands"], cfg["max_attempts"]
    last_out = ""
    for attempt in range(1, max_attempts + 1):
        print(f"[StrideHeal] Attempt {attempt}/{max_attempts}...")
        patch = generate_patch(finding, target, patch_skill)
        original = apply_patch(patch, target)
        passed, last_out = verify_patch(commands, project_root)
        if passed:
            return True, last_out
        print("[StrideHeal] Verification failed — reverting.")
        revert_file(target, original)
    return False, last_out


def _run_stride_heal(target: str, mode: str, dry_run: bool) -> None:
    """Execute the STRIDE self-healing pipeline."""
    import pathlib
    from app.app_utils.patch_agent_utils import load_self_healing_config, create_heal_pr

    project_root = str(pathlib.Path(__file__).parent.parent)
    config = load_self_healing_config()
    cfg = config["stride_self_healing"]

    if not cfg.get("enabled", False):
        print("[StrideHeal] Disabled (master flag). Set STRIDE_SELF_HEALING_ENABLED=true to activate.")
        return
    if not cfg.get("arbitrator", {}).get("enabled", True):
        print("[StrideHeal] Arbitrator surface disabled. Set STRIDE_SELF_HEALING_ARBITRATOR_ENABLED=true.")
        return

    print(f"\n=== STRIDE Self-Heal {'[DRY RUN] ' if dry_run else ''}(mode: {mode}) ===\n")
    findings, report = _stride_heal_audit(target, config, project_root)
    print(f"[StrideHeal] Found {len(findings)} actionable finding(s).")

    if not findings or mode == "audit_only":
        print(report)
        print("[StrideHeal] Mode=audit_only or no findings. Done.")
        return

    finding = findings[0]
    desc_preview = finding["description"][:80]
    print(f"[StrideHeal] Top: [{finding['severity'].upper()}] {finding['id']} — {desc_preview}")

    if dry_run:
        cmds = cfg["verification"]["commands"]
        print(f"\n[DRY RUN] Would patch {finding['id']} and run: {cmds}")
        return

    if mode in ("propose_patch", "apply_patch", "open_pr"):
        passed, _ = _stride_heal_patch_loop(finding, target, config, project_root)
        if not passed:
            print("[StrideHeal] All attempts failed. No PR opened.")
            sys.exit(1)
        print("[StrideHeal] Patch verified.")

    if mode == "open_pr":
        pr_url = create_heal_pr(finding, target, project_root)
        print(f"[StrideHeal] PR opened: {pr_url}")


def _run_flywheel(window: int, threshold: int, dry_run: bool) -> None:
    """Execute the Quality Flywheel optimization pipeline."""
    import pathlib
    from app.app_utils.flywheel_utils import generate_few_shot
    from app.app_utils.flywheel_config_loader import load_flywheel_config
    from app.app_utils.kpi_config_loader import load_kpi_config

    fw_cfg = load_flywheel_config()["quality_flywheel"]
    if not fw_cfg.get("enabled", False):
        print("[Flywheel] Disabled (master flag). Set QUALITY_FLYWHEEL_ENABLED=true to activate.")
        return
    if not fw_cfg.get("arbitrator", {}).get("enabled", True):
        print("[Flywheel] Arbitrator surface disabled. Set QUALITY_FLYWHEEL_ARBITRATOR_ENABLED=true.")
        return

    project_root = str(pathlib.Path(__file__).parent.parent)
    db_path = os.path.join(project_root, "telemetry_db.json")
    skill_base = os.path.join(project_root, "app", "skills")
    min_accuracy = load_kpi_config()["flywheel"]["min_routing_accuracy"]

    print(f"\n=== Quality Flywheel {'[DRY RUN] ' if dry_run else ''}===")
    print(f"Window: last {window} rows | Threshold: {threshold} violations\n")

    triggered, tag, few_shots_path = _flywheel_detect(db_path, window, threshold)
    if not triggered:
        print("[Flywheel] No violations above threshold. Nothing to do.")
        return

    print(f"[Flywheel] Triggered for tags: {triggered}")
    print(f"[Flywheel] Generating few-shot for skill: {tag}")
    try:
        example = generate_few_shot(tag, os.path.join(skill_base, tag), violation_count=threshold)
    except Exception as e:
        print(f"[Flywheel] ERROR: LLM generation failed: {e}")
        sys.exit(1)

    print(f"[Flywheel] Generated example input: {example['input'][:80]}...")
    if dry_run:
        print("\n[DRY RUN] Would append this example to:", few_shots_path)
        print("[DRY RUN] Would then run validation and open a PR. Exiting.")
        return

    _flywheel_write_validate_pr(tag, few_shots_path, example, project_root, min_accuracy)


def _build_parser() -> argparse.ArgumentParser:
    """Build and return the CLI argument parser."""
    parser = argparse.ArgumentParser(
        description="Capability Arbitrator: General-purpose developer agent orchestrator."
    )
    sub = parser.add_subparsers(dest="command", required=True)

    run_p = sub.add_parser("run", help="Run the arbitrator on a prompt.")
    run_p.add_argument("prompt", type=str, help="The prompt to evaluate and execute.")

    sub.add_parser("dashboard", help="Start the local telemetry dashboard.")

    heal_p = sub.add_parser(
        "stride-heal",
        help="STRIDE Self-Healing optimizer (audit → patch → verify → PR).",
    )
    heal_p.add_argument("target", type=str, help="Python file to audit and (optionally) patch.")
    heal_p.add_argument(
        "--mode", type=str,
        choices=["audit_only", "propose_patch", "apply_patch", "open_pr"],
        default=None,
        help="Override mode from config (default: read from stride_self_healing.yaml).",
    )
    heal_p.add_argument("--dry-run", action="store_true",
                        help="Print plan without writing files or opening a PR.")

    fly_p = sub.add_parser(
        "flywheel",
        help="Quality Flywheel optimizer (detects violations, generates few-shots, opens PR).",
    )
    fly_p.add_argument("--window", type=int, default=20, metavar="N",
                       help="Telemetry rows to inspect (default: 20).")
    fly_p.add_argument("--threshold", type=int, default=3, metavar="N",
                       help="Violations in window before triggering (default: 3).")
    fly_p.add_argument("--dry-run", action="store_true",
                       help="Print what would change without writing files or opening a PR.")

    return parser


def main(argv: list[str] | None = None) -> None:
    """Standard CLI entrypoint handler."""
    args = _build_parser().parse_args(argv)

    if args.command == "run":
        run_prompt_sync(args.prompt)
    elif args.command == "stride-heal":
        from app.app_utils.patch_agent_utils import load_self_healing_config
        cfg = load_self_healing_config()
        mode = args.mode or cfg["stride_self_healing"]["mode"]
        _run_stride_heal(target=args.target, mode=mode, dry_run=args.dry_run)
    elif args.command == "dashboard":
        from app.dashboard import main as start_dashboard
        start_dashboard()
    elif args.command == "flywheel":
        _run_flywheel(
            window=args.window,
            threshold=args.threshold,
            dry_run=args.dry_run,
        )

if __name__ == "__main__":
    main()
