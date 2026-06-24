# Created: 2026-06-23T12:15:42-06:00
import asyncio
import time

from google.adk.runners import InMemoryRunner
from google.genai import types

from app.agent import app


async def run_observability_test():
    print("============================================================")
    print("PHASE 3: OBSERVABILITY AND TELEMETRY VALIDATION")
    print("============================================================")
    print(
        "Expect to see dense [logging_plugin] and [debug_logging_plugin] outputs below."
    )
    print("Pay close attention to 'Token Usage' and 'System Instruction' blocks.")
    print("-" * 60)

    prompt = "Analyze the empirical methodology used in the AlphaFold 3 paper."
    start_time = time.perf_counter()

    try:
        runner = InMemoryRunner(app=app)
        session = await runner.session_service.create_session(
            app_name=app.name, user_id="test_user"
        )

        final_output = None
        # We run the prompt through the graph. The ADK plugins attached in app/agent.py
        # will automatically intercept all events and print detailed telemetry to stdout.
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
        print("-" * 60)
        print(f"-> Execution Output: {final_output}")
        print(f"-> Total Run Latency: {latency:.4f} seconds")
        print("[PASS] Observability test completed successfully.")

    except Exception as e:
        print(f"[FAIL] Execution Error: {e}")
    print("============================================================")


if __name__ == "__main__":
    asyncio.run(run_observability_test())
