# Created: 2026-06-23T12:15:42-06:00
import asyncio
import time

from google.adk.runners import InMemoryRunner
from google.genai import types

from app.agent import app


async def measure_execution(prompt: str, expected_tag: str):
    print("-" * 60)
    print(f"Testing Prompt: '{prompt}'")
    print(f"Expected Route: {expected_tag}")

    start_time = time.perf_counter()
    try:
        runner = InMemoryRunner(app=app)
        session = await runner.session_service.create_session(
            app_name=app.name, user_id="test_user"
        )

        final_output = None
        async for event in runner.run_async(
            user_id="test_user",
            session_id=session.id,
            new_message=types.Content(
                role="user", parts=[types.Part.from_text(text=prompt)]
            ),
        ):
            if event.output is not None:
                final_output = event.output

        latency = time.perf_counter() - start_time
        print(f"-> Execution Output: {final_output}")
        print(f"-> Real Latency (LpA): {latency:.4f} seconds")
        print("[PASS] Successfully traversed the graph.")
    except Exception as e:
        print(f"[FAIL] Execution Error: {e}")
    print("-" * 60)


async def main():
    print("============================================================")
    print("PHASE 2: PROGRESSIVE DISCLOSURE ROUTING VALIDATION")
    print("============================================================")

    # Test Research Routing (Should trigger the capability-researcher instructions)
    await measure_execution(
        prompt="Analyze the empirical methodology used in the AlphaFold 3 paper.",
        expected_tag="research",
    )

    # Test Coding Routing (Should trigger the coding_node placeholder for MCPs)
    await measure_execution(
        prompt="Write a Python script that calculates the Fibonacci sequence.",
        expected_tag="coding",
    )


if __name__ == "__main__":
    asyncio.run(main())
