# Created: 2026-06-23T20:49:50-06:00
import asyncio
import os
import sys

# Add project root to python path
sys.path.insert(0, "/Users/rmcdonald/Repos/agy-cli-projects/capability-arbitrator")

from app.agent import app
from google.adk.runners import InMemoryRunner
from google.genai import types


async def run_stride_test():
    print("============================================================")
    print("PHASE 10: STRIDE THREAT MODELING NODE VALIDATION")
    print("============================================================")
    
    # Set required environment variables for local testing
    os.environ["GOOGLE_GENAI_USE_VERTEXAI"] = "True"
    os.environ["GOOGLE_CLOUD_PROJECT"] = "kaggle-capstone-500322"
    os.environ["GOOGLE_CLOUD_LOCATION"] = "global"

    prompt = "Audit the security of this backend function: def load_user_config(path): return open(path).read()"
    print(f"Sending prompt: '{prompt}'")
    print("-" * 60)

    try:
        runner = InMemoryRunner(app=app)
        session = await runner.session_service.create_session(
            app_name=app.name, user_id="test_user"
        )

        final_output_parts = []
        routes = []
        async for event in runner.run_async(
            user_id="test_user",
            session_id=session.id,
            new_message=types.Content(
                role="user", parts=[types.Part.from_text(text=prompt)]
            ),
        ):
            if hasattr(event, "route") and event.route:
                routes.append(event.route)
            if hasattr(event, "actions") and event.actions and getattr(event.actions, "route", None):
                routes.append(event.actions.route)
            
            # Accumulate text content
            if event.content and event.content.parts:
                for part in event.content.parts:
                    if part.text:
                        final_output_parts.append(part.text)

        final_output = "".join(final_output_parts)
        print("-" * 60)
        print(f"Routes traversed: {routes}")
        print(f"Final output:\n{final_output}")
        print("-" * 60)

        # Assertions to verify correctness
        assert "stride" in routes, "Error: Prompt was not routed to 'stride' capability."
        assert len(final_output) > 0, "Error: Node execution did not produce user-facing content."
        
        assert any(x in final_output for x in ["STRIDE", "Vulnerability", "Mitigation", "SEC-", "Security Summary"]), (
            "Error: Final output does not contain expected STRIDE threat table sections."
        )

        print("[PASS] STRIDE Threat Modeling node validated successfully.")

    except Exception as e:
        print(f"[FAIL] STRIDE Threat Modeling node validation failed. Error: {e}")
        sys.exit(1)
        
    print("============================================================")


if __name__ == "__main__":
    asyncio.run(run_stride_test())
