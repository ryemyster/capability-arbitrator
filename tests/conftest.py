"""
File: conftest.py
Purpose: Configures pytest hooks, mocks out external GCP and GenAI dependencies, and manages test suites.
Why it exists: Enables fast, deterministic, offline-first testing of agent routing and logic without network calls or credential requirements.
How it works: intercept and mock `google.genai.Client` and `google.auth.default` at start-up, and filters tests in `pytest_collection_modifyitems`.
"""

import os
import sys
import json
import subprocess
import google.auth
import google.genai

# Define Mock objects for Google GenAI SDK to enable offline execution
class MockUsageMetadata:
    def __init__(self) -> None:
        self.prompt_token_count = 100
        self.candidates_token_count = 50

class MockPart:
    def __init__(self, text: str) -> None:
        self.text = text

class MockContent:
    def __init__(self, text: str) -> None:
        self.parts = [MockPart(text)]

class MockCandidate:
    def __init__(self, text: str) -> None:
        self.content = MockContent(text)
        self.grounding_metadata = None
        self.finish_reason = None
        self.safety_ratings = None
        self.citation_metadata = None
        self.avg_logprobs = None

    def __getattr__(self, name: str) -> any:
        return None

class MockResponse:
    def __init__(self, text: str, usage_metadata: MockUsageMetadata | None = None) -> None:
        self.text = text
        self.candidates = [MockCandidate(text)]
        self.usage_metadata = usage_metadata or MockUsageMetadata()

    def __getattr__(self, name: str) -> any:
        return None

class MockModelsService:
    def __init__(self, mock_client: "MockGenAIClient", is_async: bool = False) -> None:
        self.mock_client = mock_client
        self.is_async = is_async

    def _get_mock_response_text(self, contents: any, config: any) -> str:
        prompt = ""
        # 1. Extract prompt text from various formats
        if isinstance(contents, str):
            prompt = contents
        elif hasattr(contents, "parts"):
            prompt = "".join(part.text for part in contents.parts if hasattr(part, "text") and part.text)
        elif isinstance(contents, list):
            prompt_parts = []
            for item in contents:
                if isinstance(item, str):
                    prompt_parts.append(item)
                elif hasattr(item, "parts"):
                    prompt_parts.extend(p.text for p in item.parts if hasattr(p, "text") and p.text)
                elif isinstance(item, dict):
                    if "parts" in item:
                        for p in item["parts"]:
                            if isinstance(p, dict) and "text" in p:
                                prompt_parts.append(p["text"])
                            elif hasattr(p, "text"):
                                prompt_parts.append(p.text)
                    elif "text" in item:
                        prompt_parts.append(item["text"])
            prompt = "".join(prompt_parts)

        # 2. Check if this is the Scout node request (application/json response_mime_type)
        is_scout = False
        if config:
            mime_type = getattr(config, "response_mime_type", None) or (config.get("response_mime_type") if isinstance(config, dict) else None)
            if mime_type == "application/json":
                is_scout = True

        if is_scout:
            tag = "coding"
            prompt_lower = prompt.lower()
            if "pytest" in prompt_lower or "test" in prompt_lower:
                tag = "devops"
            elif "database" in prompt_lower or "delete" in prompt_lower:
                tag = "approval"
            elif "academic research" in prompt_lower or "quantum" in prompt_lower:
                tag = "research"
            elif "prime factors" in prompt_lower or "python function" in prompt_lower:
                tag = "coding"
            elif "workspace" in prompt_lower or "find files" in prompt_lower:
                tag = "mcp"
            elif "stride" in prompt_lower:
                tag = "stride"
            return json.dumps({"capability_tag": tag, "confidence_score": 95.0})

        # 3. Non-scout, standard execution node instructions
        system_instruction = ""
        if config:
            sys_instr = getattr(config, "system_instruction", "") or (config.get("system_instruction") if isinstance(config, dict) else "")
            if isinstance(sys_instr, list):
                system_instruction = "".join(p.text for p in sys_instr if hasattr(p, "text") and p.text)
            elif isinstance(sys_instr, str):
                system_instruction = sys_instr
            else:
                system_instruction = str(sys_instr)

        syst_lower = system_instruction.lower()
        prompt_lower = prompt.lower()

        if "researcher" in syst_lower or "research" in prompt_lower:
            return "### Executive Summary\nQuantum computing breakthroughs are real.\n### Methodology\nWe researched papers."
        elif "coding" in syst_lower or "prime factors" in prompt_lower:
            return "Here is the python function:\n```python\ndef get_prime_factors(n):\n    return []\n```"
        else:
            return "Mock response for prompt: " + prompt

    async def generate_content_async(self, model: str, contents: any, config: any = None, **kwargs: any) -> MockResponse:
        text = self._get_mock_response_text(contents, config)
        return MockResponse(text)

    async def generate_content_stream_async(self, model: str, contents: any, config: any = None, **kwargs: any) -> any:
        text = self._get_mock_response_text(contents, config)
        
        class AsyncIteratorWrapper:
            def __init__(self, response: MockResponse) -> None:
                self.response = response
                self.done = False

            def __aiter__(self) -> "AsyncIteratorWrapper":
                return self

            async def __anext__(self) -> MockResponse:
                if self.done:
                    raise StopAsyncIteration
                self.done = True
                return self.response

            async def aclose(self) -> None:
                pass

        return AsyncIteratorWrapper(MockResponse(text))

    def generate_content_sync(self, model: str, contents: any, config: any = None, **kwargs: any) -> MockResponse:
        text = self._get_mock_response_text(contents, config)
        return MockResponse(text)

    def generate_content_stream_sync(self, model: str, contents: any, config: any = None, **kwargs: any) -> any:
        text = self._get_mock_response_text(contents, config)
        yield MockResponse(text)

    def generate_content(self, model: str, contents: any, config: any = None, **kwargs: any) -> any:
        if self.is_async:
            return self.generate_content_async(model, contents, config, **kwargs)
        return self.generate_content_sync(model, contents, config, **kwargs)

    def generate_content_stream(self, model: str, contents: any, config: any = None, **kwargs: any) -> any:
        if self.is_async:
            return self.generate_content_stream_async(model, contents, config, **kwargs)
        return self.generate_content_stream_sync(model, contents, config, **kwargs)

class MockAioService:
    def __init__(self, mock_client: "MockGenAIClient") -> None:
        self.models = MockModelsService(mock_client, is_async=True)

class MockGenAIClient:
    def __init__(self, *args: any, **kwargs: any) -> None:
        self.models = MockModelsService(self, is_async=False)
        self.aio = MockAioService(self)
        self.vertexai = True

# Mock GCP credentials helper
class MockCredentials:
    def refresh(self, request: any) -> None:
        pass

    def before_request(self, request: any, method: str, url: str, headers: any) -> None:
        pass

    def __getattr__(self, name: str) -> any:
        return None

def mock_default(*args: any, **kwargs: any) -> tuple[MockCredentials, str]:
    return MockCredentials(), "mock-project-id"

# Determine real credentials only if requested
_REAL_GCP_AUTH_AVAILABLE = False
if os.environ.get("RUN_REAL_LLM") == "true":
    try:
        google.auth.default()
        _REAL_GCP_AUTH_AVAILABLE = True
    except Exception:
        pass
else:
    # Apply global mock overrides to ensure offline-first execution
    google.auth.default = mock_default
    google.genai.Client = MockGenAIClient
    _REAL_GCP_AUTH_AVAILABLE = True

def pytest_collection_modifyitems(config: any, items: list[any]) -> None:
    run_e2e = os.environ.get("RUN_E2E") == "true"
    run_scripts = os.environ.get("RUN_SCRIPTS") == "true"

    keep = []
    for item in items:
        path_str = str(item.fspath)

        # 1. Skip E2E server tests by default
        if "test_server_e2e.py" in path_str and not run_e2e:
            continue

        # 2. Skip generated script tests by default
        if "tests/scripts" in path_str and not run_scripts:
            continue

        # 3. If running in real LLM mode, verify GCP credentials
        if os.environ.get("RUN_REAL_LLM") == "true" and not _REAL_GCP_AUTH_AVAILABLE:
            if "tests/integration" in path_str or "tests/scripts" in path_str:
                continue

        keep.append(item)
    items[:] = keep
