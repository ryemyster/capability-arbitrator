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


def _run_flywheel(window: int, threshold: int, dry_run: bool) -> None:
    """Execute the Quality Flywheel optimization pipeline."""
    import pathlib
    from app.app_utils.flywheel_utils import generate_few_shot
    from app.app_utils.kpi_config_loader import load_kpi_config

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


def main(argv: list[str] | None = None) -> None:
    """Standard CLI entrypoint handler."""
    parser = argparse.ArgumentParser(
        description="Capability Arbitrator: General-purpose developer agent orchestrator."
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    # Subcommand: run
    run_parser = subparsers.add_parser("run", help="Run the arbitrator on a prompt.")
    run_parser.add_argument("prompt", type=str, help="The prompt to evaluate and execute.")

    # Subcommand: dashboard
    subparsers.add_parser("dashboard", help="Start the local telemetry dashboard.")

    # Subcommand: flywheel
    flywheel_parser = subparsers.add_parser(
        "flywheel",
        help="Run the Quality Flywheel offline optimizer (detects violations, generates few-shots, opens PR).",
    )
    flywheel_parser.add_argument(
        "--window", type=int, default=20, metavar="N",
        help="Number of telemetry rows to inspect (default: 20).",
    )
    flywheel_parser.add_argument(
        "--threshold", type=int, default=3, metavar="N",
        help="Violations in window before triggering (default: 3).",
    )
    flywheel_parser.add_argument(
        "--dry-run", action="store_true",
        help="Print what would change without writing files or opening a PR.",
    )

    args = parser.parse_args(argv)

    if args.command == "run":
        run_prompt_sync(args.prompt)
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
