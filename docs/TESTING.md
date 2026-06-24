# Testing & Verification Guide

This document explains our testing philosophy, behavior-driven specifications (BDD), manual checks, and automated evaluation loops.

---

## 1. Why: Testing AI Agent Architectures
* **The Problem:** AI agents are non-deterministic. Traditional software testing (asserting exact string matches) fails because LLMs generate text that varies on each run. 
* **The Solution:** We implement a tiered testing hierarchy that combines traditional local unit tests, natural-language Behavior-Driven Development (BDD), manual QA sign-offs, and dynamic LLM-as-a-Judge offline evaluation loops.

---

## 2. What: The Testing Hierarchy

Our testing structure is divided into four main layers:

```
┌─────────────────────────────────────────────────────────┐
│              1. Runtime Evaluation Loop                 │  <-- Dynamic red-teaming (LLM-as-a-Judge)
├─────────────────────────────────────────────────────────┤
│              2. Behavior-Driven (BDD)                   │  <-- Gherkin features & step definitions
├─────────────────────────────────────────────────────────┤
│              3. Unit & Integration                      │  <-- Standard local Pytest validation
├─────────────────────────────────────────────────────────┤
│              4. Manual QA Verification                  │  <-- Checklist-driven human sign-off
└─────────────────────────────────────────────────────────┘
```

---

## 3. How: Step-by-Step Test Guide

### Layer 1: Run Local Unit & Integration Tests
We use `pytest` for fast, local assertions on helper methods, configuration stubs, and telemetry records.
* **Command:**
  ```bash
  uv run pytest
  ```

### Layer 2: Behavior-Driven Development (BDD)
We write behavioral requirements in plain English using Gherkin syntax.
* **Gherkin File:** [tests/integration/features/routing.feature](file:///Users/rmcdonald/Repos/agy-cli-projects/capability-arbitrator/tests/integration/features/routing.feature)
* **Step Definitions:** [tests/integration/test_routing_bdd.py](file:///Users/rmcdonald/Repos/agy-cli-projects/capability-arbitrator/tests/integration/test_routing_bdd.py)

#### Sample Gherkin Test:
```gherkin
Scenario: Correct routing of a DevOps request
  Given a user prompt requesting "Run the pytest suite to verify our unit tests"
  When the Capability Arbitrator processes the request
  Then the Scout node should classify the intent as "devops"
  And the workflow should route execution to the DevOps node
```

### Layer 3: Manual QA Verification Scripts
Every deployment phase generates a corresponding manual QA script with a check-off sign-off sheet.
* **Location:** `tests/manual_test_scripts/`
* **How to run:** Developers execute the steps in the script (e.g. running the playground or opening the browser) and check off validation boxes manually before merging features.
* *Example:* [QA_deep_testing.md](file:///Users/rmcdonald/Repos/agy-cli-projects/capability-arbitrator/tests/manual_test_scripts/phase6-deep-testing/QA_deep_testing.md).

### Layer 4: Runtime Evaluation & Scorecard (LLM-as-a-Judge)
For our non-deterministic routing gates, we run an automated evaluation loop using two specialized agents:
1. **`DeepTester`:** Dynamically generates 5 highly ambiguous red-teaming developer scenarios using the Gemini API.
2. **`OutcomeJudge`:** Inspects the execution traces of the arbitrator, compares the routed destination against the expected tag, and computes metrics like Token Saturation (TSR) and Cost reduction efficiency (CpE) vs a monolithic agent.

* **Run Evaluation:**
  ```bash
  uv run python tests/scripts/phase6-deep-testing/test_deep_testing.py
  ```
* **Scorecard Output:** Prints a detailed dashboard summary of routing precision, average latency, and cost savings in the terminal.

---

## 4. When to Use Which Test
* **Use Pytest/BDD** during continuous integration (CI/CD) to prevent code regressions when adding new nodes or routing edges.
* **Use Manual QA Scripts** when testing human-in-the-loop (HITL) interfaces, dashboard UI components, or browser layouts.
* **Use Runtime Evaluation Scorecards** before major releases to mathematically prove that prompt adjustments or model upgrades have improved system efficiency.
