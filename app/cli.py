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

    args = parser.parse_args(argv)

    if args.command == "run":
        run_prompt_sync(args.prompt)
    elif args.command == "dashboard":
        from app.dashboard import main as start_dashboard
        start_dashboard()

if __name__ == "__main__":
    main()
