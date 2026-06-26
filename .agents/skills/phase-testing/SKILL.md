---
name: phase-testing
description: Mandatory local workflow skill. Automatically triggers when completing any development phase. Enforces the creation of a QA markdown script and an automated Python test script, along with a timestamp.
---

# Mandatory Phase Testing Rules

You are acting as an Assistant on the Capability Arbitrator project.

Whenever the USER indicates that a "Phase" is complete (e.g., "Phase 3 is good", "Phase 6 done"), or whenever you finalize the core implementation of a specific Phase, you **MUST rigidly adhere** to the following protocol before moving on:

## 1. Automated Python Test Script
Create a Python script in a dedicated subfolder under the `tests/scripts/` directory that programmatically tests the code written during the Phase.
- **Naming convention:** `tests/scripts/phase<NUMBER>-<name>/test_<name>.py`
- **Content requirement:** It must run cleanly from the CLI (`uv run python tests/scripts/...`) and output clear `[PASS]` or `[FAIL]` indicators.

## 2. Manual QA Markdown Script
Create a Markdown file in a dedicated subfolder under the `tests/manual_test_scripts/` directory that provides exact, foolproof instructions for a human to verify the Phase via the UI or terminal.
- **Naming convention:** `tests/manual_test_scripts/phase<NUMBER>-<name>/QA_<name>.md`
- **Content requirement:** Must include specific prompts to test, the expected routing/behavior, and what the user will visually see in the UI/terminal. Must include a checkbox list `[ ]` for sign-off.

## 3. Timestamping
- **Python Scripts:** You must append `# Created: <CURRENT_LOCAL_TIME>` to the very top (Line 1) of the `test_phase...py` script.
- **Markdown Scripts:** You must append `*Created: <CURRENT_LOCAL_TIME>*` to the very bottom of the `QA_phase...md` file.

### Enforcement
Do not ask the user for permission to create these files. Create them proactively the moment a Phase is deemed complete, and then notify the user that the mandatory QA and automated testing scaffolding has been generated according to the `phase-testing` skill.
