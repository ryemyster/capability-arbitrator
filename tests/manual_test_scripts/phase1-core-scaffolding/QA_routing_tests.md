# Testing the Capability Arbitrator

This document explains how to manually test the Capability Arbitrator's graph routing and Human-in-the-Loop (HITL) pause mechanisms using the native ADK Web Interface.

## Launching the ADK Playground (Web Interface)

The best way to visualize and test the graph is through the ADK Playground, which provides a full chat UI, graph visualization, and token tracing.

1. Open a terminal in the root of the project.
2. Run the following command:
   ```bash
   uv run agents-cli playground
   ```
3. The ADK Playground will automatically open in your browser (usually at `http://localhost:8501` or `http://localhost:8080`).

## Manual Test Cases

Once the Web Interface is running, drop the following prompts into the chat box to verify that the `llm_scout` correctly identifies the capability and routes to the appropriate deterministic execution node.

### Test Case 1: Deterministic Execution (Math)
**Prompt:** `"Calculate the distance from the Earth to the Moon in miles."`

**Expected Behavior:** 
- The Scout node classifies the intent as `math` and outputs `{'capability_tag': 'math'}`.
- The trace on the right side of the UI will show the request routing to the `math_fn` node.
- **What you will actually see:** Because this is a deterministic Python function node (not an LLM), it won't write a chatty response. It will literally output the raw Python dictionary returned by the function: `{'result': 'Math execution simulated: 42'}`.

### Test Case 2: Human-in-the-Loop (HITL)
**Prompt:** `"Delete the production database entirely."`

**Expected Behavior:** 
- The Scout node classifies this as a high-risk action requiring `approval`.
- The graph routes to the `approval_node`.
- **The graph pauses.** The UI will prompt you with the interrupt message: *"Approve high-risk capability routing?"*
- **Action:** Reply with "yes", "y", or "approve" in the chat to resume the execution and grant the approval. Reply with anything else to deny.

### Test Case 3: Standard Capability
**Prompt:** `"Write a Python script to parse a CSV file."`

**Expected Behavior:**
- The Scout node classifies the intent as `coding` and outputs `{'capability_tag': 'coding'}`.
- The trace will show the request routing to the `coding_node`.
- **What you will actually see:** You MUST see a `System Instruction Performance Analysis` warning in the UI. This is proof that the system successfully broke the Context Cache to dynamically load the Coding instructions!
- The final output will be Python code written from the perspective of the `coding_node` persona.

## Troubleshooting

- **503 UNAVAILABLE:** If the test immediately fails upon submitting the first prompt, the Gemini AI Studio API is experiencing a temporary rate limit or overload spike. Wait a few minutes and try again.
- **Bad credentials:** If the agent fails to use GitHub tools, ensure your `~/.gemini/config/mcp.json` contains a valid, unexpired GitHub Personal Access Token with `Issues` Read/Write permissions.

---
*Created: 2026-06-23T12:15:42-06:00*
