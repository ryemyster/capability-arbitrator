# Manual QA Test Script - Phase 9 Telemetry Dashboard

## Purpose
This document provides the manual QA steps to verify that the FastAPI-based Telemetry Dashboard, routing playground, and "Stats for Nerds" HUD operate successfully.

## Prerequisites
1. Ensure dependencies are installed: `uv sync`.
2. Ensure you are on the branch being verified.

## QA Execution Steps

### 1. Launch the Unified Server
Run the FastAPI server locally:
```bash
uv run uvicorn app.fast_api_app:app --host 127.0.0.1 --port 8000
```
*Expected Output:* The console prints: `INFO:     Started server process [pid]` and `INFO:     Uvicorn running on http://127.0.0.1:8000`

### 2. Verify Initial Dashboard Layout
1. Open your web browser and navigate to `http://127.0.0.1:8000/dashboard`.
2. Verify that:
   - The header displays **Capability Arbitrator** with the subtitle **Outcome Governance & Live Telemetry Console**.
   - The **Cumulative Efficiency Gains** card displays initial values (e.g., token savings rate, cost savings, TTFT).
   - The **Stats for Nerds HUD** is visible on the right sidebar.
   - The **Execution History Log** table is rendered.

### 3. Test Routing Playground & SSE Streaming
1. In the **Interactive Routing Playground**, enter a math prompt:
   ```text
   Solve (45 * 2) - 10
   ```
2. Click **Execute Prompt**.
3. Verify that:
   - The response streams live inside the terminal block.
   - The final output includes `Math Engine result: 80`.
4. Enter a research prompt:
   ```text
   Conduct academic research on quantum computing breakthroughs.
   ```
5. Click **Execute Prompt**.
6. Verify that:
   - The response streams live, adhering to the structured researcher skill (e.g., Executive Summary & Methodology).

### 4. Verify "Stats for Nerds" HUD Update
After running a prompt, look at the **Stats for Nerds HUD** sidebar and confirm:
- **Scout Model:** Shows `gemini-3.5-flash-lite` (or the active model name).
- **Run Source:** Shows where the row came from, such as `dashboard_local_runner`, `pubsub_integration`, or `agent_runtime`.
- **Scout Latency (TTFT):** Shows a valid positive decimal (e.g. `0.85s`).
- **Active Exec Node:** Shows the correct active routing tag (e.g. `MATH` or `RESEARCH`).
- **Token Saturation Profile:** Shows the tokens consumed by the Scout and active execution nodes.
- **Scout Token Source / Exec Token Source:** Shows whether the token values are `actual`, `deterministic_zero`, or `estimated`.
- **Context Window Reduction:** Visualizes the progressive disclosure percentage gains with a filled progress bar.

### 5. Check History Logs
Verify that the **Execution History Log** at the bottom of the page has appended a new row for each execution showing:
- Correct timestamp.
- The prompt text.
- The route tag badge (e.g., green `math` or blue `research`).
- The run source (for example, `dashboard_local_runner` for dashboard playground executions).
- Arbitrator and Monolithic input token footprints.
- Token source labels. Scout tokens should be `actual` when the GenAI SDK reports usage. Math and DevOps execution tokens should show `deterministic_zero`. LLM execution-node tokens may show `estimated` when ADK does not expose downstream usage.
- Precise cost savings in USD.

*Created: 2026-06-24T06:32:00-06:00*
