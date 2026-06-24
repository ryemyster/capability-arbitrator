# Phase 2 Manual QA Tests (Progressive Disclosure)

## Objective
Verify that the Capability Arbitrator successfully routes tasks to specialized `LlmAgent` nodes and that those nodes apply their specific "Progressive Disclosure" instructions (like the researcher skill), rather than responding with generic text.

## Test 1: Testing the Research Node
1. Open the ADK Playground:
   ```bash
   uv run agents-cli playground
   ```
2. Enter the prompt:
   `Analyze the empirical methodology used in the AlphaFold 3 paper.`
3. **Expected Behavior:**
   - The Scout node should classify the intent and route to the `research_node`.
   - You MUST see the `System Instruction Performance Analysis` warning. This proves the system intentionally broke the Context Cache to load new instructions!
   - The response should be a highly structured **"Extraction & Synthesis Protocol"** directly from the `researcher` persona. It will introduce itself as the "dedicated Research Node" and outline its "Methodological Extraction Schema." This proves the Progressive Disclosure instructions were successfully injected!

## Test 2: Testing the Coding Node
1. In the same Playground session, enter the prompt:
   `Write a Python script that calculates the Fibonacci sequence.`
2. **Expected Behavior:**
   - The Scout node should classify the intent as `coding`.
   - You MUST see another `Performance Alert` cache break warning as the graph unloads the Researcher instructions and loads the Coding instructions.
   - The final output should contain the Python code from the perspective of the Coding Node.

## Validation Sign-off
- [ ] Research formatting rules applied successfully
- [ ] Cache break telemetry verified in the UI
- [ ] Coding placeholder responded successfully
