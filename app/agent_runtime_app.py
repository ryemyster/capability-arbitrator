"""
File: agent_runtime_app.py
Purpose: Wraps the ADK agent workflow in a production-ready Vertex AI Agent Engine App.
Why it exists: To support production deployment, feedback registration, and cloud-logging capabilities.
How it works: Subclasses AdkApp, initializes Vertex AI and Cloud Logging clients at set_up, and registers feedback endpoints.
Updated: 2026-06-23T13:17:56-06:00
"""

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
import logging
import os
from typing import Any, AsyncGenerator

import vertexai
from dotenv import load_dotenv
from google.adk.artifacts import GcsArtifactService, InMemoryArtifactService
from google.cloud import logging as google_cloud_logging
from vertexai.agent_engines.templates.adk import AdkApp

from app.agent import app as adk_app
from app.app_utils.telemetry import setup_telemetry
from app.app_utils.typing import Feedback

# Load environment variables from .env file at runtime
load_dotenv()


class AgentEngineApp(AdkApp):
    def set_up(self) -> None:
        """Initialize the agent engine app with logging and telemetry.
        If we are running integration tests, we bypass external GCP client initialization.
        """
        if os.environ.get("INTEGRATION_TEST") == "TRUE":
            self.logger = logging.getLogger(__name__)
            # Mock log_struct to capture structured logging without calling Cloud Logging API
            self.logger.log_struct = lambda data, severity: logging.info(
                f"Feedback (mock): {data}"
            )
            return

        vertexai.init()
        setup_telemetry()
        super().set_up()
        logging.basicConfig(level=logging.INFO)
        logging_client = google_cloud_logging.Client()
        self.logger = logging_client.logger(__name__)
        if gemini_location:
            os.environ["GOOGLE_CLOUD_LOCATION"] = gemini_location

    def register_feedback(self, feedback: dict[str, Any]) -> None:
        """Collect and log feedback."""
        feedback_obj = Feedback.model_validate(feedback)
        if hasattr(self.logger, "log_struct"):
            self.logger.log_struct(feedback_obj.model_dump(), severity="INFO")  # type: ignore
        else:
            self.logger.info(f"Feedback: {feedback_obj.model_dump()}")

    def _save_query_metadata(
        self,
        user_id: str,
        session_id: str | None,
        run_source: str,
    ) -> None:
        """Persist query metadata after the graph has recorded telemetry."""
        from app.app_utils.telemetry import save_run, update_telemetry

        update_telemetry({
            "user_id": user_id,
            "session_id": session_id or "agent-runtime-session",
            "run_source": run_source,
        })
        save_run()

    async def _stream_local_query(
        self,
        message: str | dict[str, Any],
        user_id: str,
        session_id: str | None,
        run_source: str,
    ) -> AsyncGenerator[Any, None]:
        """Run the graph through an in-memory ADK runner and save telemetry."""
        from google.adk.runners import InMemoryRunner
        from google.genai import types

        runner = InMemoryRunner(app=adk_app)
        session = await runner.session_service.create_session(
            app_name=adk_app.name,
            user_id=user_id,
            session_id=session_id,
        )
        msg_str = message if isinstance(message, str) else str(message)
        try:
            async for event in runner.run_async(
                user_id=user_id,
                session_id=session.id,
                new_message=types.Content(
                    role="user", parts=[types.Part.from_text(text=msg_str)]
                ),
            ):
                yield event
        finally:
            self._save_query_metadata(user_id, session.id, run_source)

    async def _stream_remote_query(
        self,
        query_args: dict[str, Any],
        user_id: str,
        session_id: str | None,
        run_source: str,
    ) -> AsyncGenerator[Any, None]:
        """Run the deployed Agent Runtime path and save telemetry."""
        try:
            async for event in super().async_stream_query(**query_args):
                yield event
        finally:
            self._save_query_metadata(user_id, session_id, run_source)

    async def async_stream_query(
        self,
        *,
        message: str | dict[str, Any],
        user_id: str,
        session_id: str | None = None,
        session_events: list[dict[str, Any]] | None = None,
        run_config: dict[str, Any] | None = None,
        **kwargs,
    ) -> AsyncGenerator[Any, None]:
        """Intercepts streaming query to run locally in integration tests."""
        from app.app_utils.telemetry import classify_run_source

        force_local = bool((run_config or {}).get("force_local"))
        use_local_runner = force_local or os.environ.get("INTEGRATION_TEST") == "TRUE"
        run_source = classify_run_source(user_id, session_id, force_local)

        if use_local_runner:
            async for event in self._stream_local_query(
                message, user_id, session_id, run_source
            ):
                yield event
            return

        query_args = {
            "message": message,
            "user_id": user_id,
            "session_id": session_id,
            "session_events": session_events,
            "run_config": run_config,
            **kwargs,
        }
        async for event in self._stream_remote_query(
            query_args, user_id, session_id, run_source
        ):
            yield event

    def register_operations(self) -> dict[str, list[str]]:
        """Registers the operations of the Agent."""
        operations = super().register_operations()
        operations[""] = [*operations.get("", []), "register_feedback"]
        return operations

    def clone(self) -> "AgentEngineApp":
        """Returns a clone of the Agent Runtime application."""
        return self


gemini_location = os.environ.get("GOOGLE_CLOUD_LOCATION")
logs_bucket_name = os.environ.get("LOGS_BUCKET_NAME")
try:
    agent_runtime = AgentEngineApp(
        app=adk_app,
        artifact_service_builder=lambda: (
            GcsArtifactService(bucket_name=logs_bucket_name)
            if logs_bucket_name
            else InMemoryArtifactService()
        ),
    )
except Exception as e:
    print(f"⚠️ [WARNING] Failed to initialize AgentEngineApp: {e}")
    agent_runtime = None  # type: ignore
