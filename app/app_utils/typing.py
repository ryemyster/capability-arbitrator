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
File: typing.py
Purpose: Defines Pydantic data schemas and feedback structures.
Why it exists: Standardizes internal data models and logging telemetry records (like customer feedback).
How it works: Subclasses Pydantic BaseModel to expose typed schemas with automatic UUID generation.
"""

import uuid
from typing import (
    Literal,
)

from pydantic import (
    BaseModel,
    Field,
)


class Feedback(BaseModel):
    """Represents feedback for a conversation."""

    score: int | float
    text: str | None = ""
    log_type: Literal["feedback"] = "feedback"
    service_name: Literal["capability-arbitrator"] = "capability-arbitrator"
    user_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    session_id: str = Field(default_factory=lambda: str(uuid.uuid4()))


class PubSubMessage(BaseModel):
    """Pydantic model representing a Pub/Sub message data envelope."""

    data: str
    attributes: dict[str, str] | None = None
    message_id: str | None = Field(default=None, alias="messageId")
    publish_time: str | None = Field(default=None, alias="publishTime")

    model_config = {"populate_by_name": True}


class PubSubEnvelope(BaseModel):
    """Pydantic model representing the overall Pub/Sub push notification envelope."""

    message: PubSubMessage
    subscription: str

