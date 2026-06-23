import os
from typing import Literal
import google.auth
from pydantic import BaseModel, Field

from google.adk.workflow import Workflow
from google.adk.agents import LlmAgent
from google.adk.apps import App

_, project_id = google.auth.default()
os.environ["GOOGLE_CLOUD_PROJECT"] = project_id
os.environ["GOOGLE_CLOUD_LOCATION"] = "global"
os.environ["GOOGLE_GENAI_USE_VERTEXAI"] = "True"

class ScoutOutput(BaseModel):
    capability_tag: Literal["coding", "research", "math", "document", "approval"] = Field(
        description="The capability required to handle the user's prompt."
    )

llm_scout = LlmAgent(
    name="llm_scout",
    model="gemini-3.5-flash",
    instruction="""You are the 'Scout' node for a Capability Arbitrator agent.
Your task is to analyze the user's request and ask 'What capability is required?' before assigning a resource.
Return the appropriate capability tag.
""",
    output_schema=ScoutOutput,
    output_key="capability_tag",
)

root_workflow = Workflow(
    name="root_agent",
    edges=[
        ('START', llm_scout),
    ]
)

app = App(
    root_agent=root_workflow,
    name="app",
)
