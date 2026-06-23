import sys
import time
import asyncio
from google.genai import types

# Import the ADK App and Runner
from app.agent import app
from google.adk.runners import InMemoryRunner

async def main(prompt: str):
    print(f"Measuring runtime execution for prompt: '{prompt}'")
    print("-" * 60)
    
    # Initialize the runner
    runner = InMemoryRunner(app=app)
    session = await runner.session_service.create_session(app_name=app.name, user_id="test_user")
    
    start_time = time.perf_counter()
    
    final_output = None
    
    # Execute the workflow
    async for event in runner.run_async(
        user_id="test_user",
        session_id=session.id,
        new_message=types.Content(role="user", parts=[types.Part.from_text(text=prompt)])
    ):
        if event.output is not None:
            final_output = event.output

    end_time = time.perf_counter()
    duration = end_time - start_time
    
    print("EXECUTION COMPLETE")
    print(f"-> Capability Tag Assigned: {final_output}")
    print(f"-> Real Latency (LpA): {duration:.4f} seconds")
    print("-" * 60)
    print("NOTE: Real-time token tracking (CpE) and Token Saturation Ratios (TSR) can be extracted automatically by attaching ADK's `BigQueryAgentAnalyticsPlugin` to the App object in agent.py.")
    print("=" * 60)

if __name__ == "__main__":
    prompt = sys.argv[1] if len(sys.argv) > 1 else "Calculate the distance to the moon"
    asyncio.run(main(prompt))
