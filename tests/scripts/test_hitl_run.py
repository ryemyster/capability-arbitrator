# Created: 2026-07-06T10:00:00-06:00
import asyncio
from google.adk.runners import InMemoryRunner
from google.adk.events import RequestInput
from google.genai import types
from app.agent import app

async def main():
    runner = InMemoryRunner(app=app)
    prompt = "Please do some math calculations, or maybe look up code files, or write a summary. I'm not sure which capability we need here."
    print("--- Starting run with prompt ---")
    
    session = await runner.session_service.create_session(
        app_name=app.name, user_id="manual_tester"
    )
    
    last_invocation_id = None
    
    # First run
    async for event in runner.run_async(
        user_id="manual_tester",
        session_id=session.id,
        new_message=types.Content(
            role="user", parts=[types.Part.from_text(text=prompt)]
        )
    ):
        print("YIELDED EVENT:", type(event), getattr(event, "content", None), getattr(event, "output", None), getattr(event, "route", None))
        if hasattr(event, "invocation_id") and event.invocation_id:
            last_invocation_id = event.invocation_id
        if isinstance(event, RequestInput) or (hasattr(event, "content") and event.content and any(p.function_call for p in event.content.parts if p.function_call)):
            print(f"\n[INTERRUPT DETECTED] msg={getattr(event, 'message', 'Function call interrupt')}\n")
    
    if not last_invocation_id:
        print("Error: No invocation ID captured!")
        return

    # Resuming run with approval
    print(f"--- Resuming run with approval 'y' (invocation_id={last_invocation_id}) ---")
    
    resume_msg = types.Content(
        role="user",
        parts=[
            types.Part(
                function_response=types.FunctionResponse(
                    name="adk_request_input",
                    id="approval_req",
                    response={"output": "y"}
                )
            )
        ]
    )
    
    async for event in runner.run_async(
        user_id="manual_tester",
        session_id=session.id,
        invocation_id=last_invocation_id,
        new_message=resume_msg
    ):
        print("YIELDED EVENT (RESUMED):", type(event), getattr(event, "content", None), getattr(event, "output", None), getattr(event, "route", None))

if __name__ == "__main__":
    asyncio.run(main())
