import asyncio

from google.adk.runners import InMemoryRunner
from google.genai import types

from app.agent import app


async def run_manual_test():
    print("=======================================")
    print(" Manual Testing: Capability Arbitrator")
    print("=======================================")

    runner = InMemoryRunner(app=app)

    test_cases = [
        "Calculate the distance from the Earth to the Moon in miles.",
        "Delete the production database entirely.",
        "Write a Python script to parse a CSV file.",
    ]

    for idx, prompt in enumerate(test_cases, 1):
        print(f"\n[Test Case {idx}] Prompt: '{prompt}'")
        print("-" * 50)

        session = await runner.session_service.create_session(
            app_name=app.name, user_id="manual_tester"
        )

        try:
            async for event in runner.run_async(
                user_id="manual_tester",
                session_id=session.id,
                new_message=types.Content(
                    role="user", parts=[types.Part.from_text(text=prompt)]
                ),
            ):
                if hasattr(event, "route") and event.route:
                    print(f"    [>] Routed to: {event.route}")

                if event.output is not None:
                    print(f"    [=] Node Output: {event.output}")

        except Exception as e:
            print(f"    [!] Error during execution: {type(e).__name__} - {e}")

    print("\n=======================================")
    print(" Testing Complete")
    print("=======================================")


if __name__ == "__main__":
    asyncio.run(run_manual_test())
