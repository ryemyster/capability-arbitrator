# Phase 8 Manual QA Tests (Model Agnostic Integration)

## Objective
Verify that the Capability Arbitrator can execute using models from different providers (Gemini, OpenAI, Claude, Ollama, DeepSeek) based on configuration files or environment variables without code modification.

## How to Test
1. Set up a non-Gemini provider key or local model endpoint (e.g. Ollama).
2. Configure the target nodes to use the custom models in the configuration mapping.
3. Run the validation test script:
   ```bash
   uv run python tests/scripts/phase8-model-agnostic/test_model_agnostic.py
   ```
4. Verify that the agent delegates routing actions to the targeted model provider endpoints.

## Validation Sign-off
- [ ] Model abstraction handles non-Gemini APIs correctly.
- [ ] Config correctly overrides specific capability nodes.
- [ ] Agent correctly routes and completes queries using alternative endpoints.

---
*Created: 2026-06-23T13:17:56-06:00*
