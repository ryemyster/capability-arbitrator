# Phase 5 Manual QA Tests (Observability & Telemetry)

## Objective
Verify that the `LoggingPlugin` and `DebugLoggingPlugin` are correctly tracing the execution path, capturing prompt payloads, identifying system instruction swaps, and tracking token counts. (BigQuery Analytics testing is deferred since Terraform provisioning is not available).

## Test 1: Verifying Console Telemetry
1. Open a terminal in the project root.
2. Run the Phase 5 test script:
   ```bash
   uv run python tests/scripts/phase5-enterprise-telemetry-and-logging/test_telemetry.py
   ```
3. **Expected Behavior:**
   - The terminal should output an extremely detailed execution trace prefixed with `[logging_plugin]`.
   - You MUST see `🧠 LLM REQUEST` blocks that explicitly print out the `System Instruction` that was loaded for that specific node.
   - You MUST see `Token Usage - Input: X, Output: Y` printed after every LLM hop.
4. **Validation Check:** 
   - Verify that the `System Instruction` for the `llm_scout` node is entirely different from the `System Instruction` for the `research_node`. This telemetry proves the Progressive Disclosure architecture is active.

## Validation Sign-off
- [ ] Detailed plugin logs are visible in the console
- [ ] System Instruction swaps are captured in the trace
- [ ] Token Usage counts are accurately logged for each hop

---
*Created: 2026-06-23T12:15:42-06:00*
