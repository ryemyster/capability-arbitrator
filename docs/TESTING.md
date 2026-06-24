# Verification & QA Suite
### Testing Non-Deterministic Agent workflows

Because Large Language Models generate text non-deterministically, standard unit tests (expecting exact string matches) are insufficient for agent verification. 

The Capability Arbitrator implements a **multi-tiered testing framework** that ranges from static code constraints to automated red-teaming eval scorecards.

---

## 📐 The Verification Hierarchy

Our verification strategy spans four distinct layers, moving from local code validations to cloud-based runtime evaluations:

| Test Layer | Focus | Scope | How It Runs |
| :--- | :--- | :--- | :--- |
| **1. Runtime Evaluation** | System KPIs | Measures routing accuracy, latency, and token cost savings under load | `test_deep_testing.py` |
| **2. BDD Gherkin Specs** | Integration | Validates logical routing rules and edge cases in plain English | `pytest-bdd` |
| **3. Unit & Integration** | Code Quality | Tests utility functions, config validation, and database records | `pytest` |
| **4. Manual QA Scripts** | User Experience | Guides human testing of dashboard UI overlays and HITL portals | Markdown sign-off checklists |

---

## 🛠️ Execution Guides

### 1. Fast Local Unit Testing
Unit tests run locally to check utilities like math algorithms, prompt parsers, and telemetry logging databases.
```bash
uv run pytest
```

### 2. Behavior-Driven Development (BDD)
We use natural-language Gherkin specifications to map functional requirements.
*   **Gherkin File:** [tests/integration/features/routing.feature](file:///Users/rmcdonald/Repos/agy-cli-projects/capability-arbitrator/tests/integration/features/routing.feature)
*   **Step Implementations:** [tests/integration/test_routing_bdd.py](file:///Users/rmcdonald/Repos/agy-cli-projects/capability-arbitrator/tests/integration/test_routing_bdd.py)

#### Gherkin Scenario Example:
```gherkin
Scenario: Routing of a DevOps task to verification engine
  Given a user prompt requesting "Run the pytest suite on unit tests"
  When the Capability Arbitrator processes the request
  Then the Scout node should classify the intent as "devops"
  And the workflow should route execution to the DevOps node
```

### 3. Manual QA Sign-offs
We maintain checklist files under `tests/manual_test_scripts/` to ensure developers manually verify visual UI panels and HITL pause/resume logic before checking in code.
*   *Example:* [QA_deep_testing.md](file:///Users/rmcdonald/Repos/agy-cli-projects/capability-arbitrator/tests/manual_test_scripts/phase6-deep-testing/QA_deep_testing.md) contains verification guidelines for red-teaming.

---

## 🧠 Dynamic Evaluation & Scorecards (LLM-as-a-Judge)

To evaluate routing accuracy, latency, and token efficiency, we run an automated evaluation loop using two specialized agents:
*   **`DeepTester`:** An agent that dynamically generates diverse, highly ambiguous developer scenarios designed to stress-test intent classification.
*   **`OutcomeJudge`:** An LLM-as-a-judge that evaluates the arbitrator's execution traces, calculating Token Saturation (TSR) and Cost reduction efficiency (CpE) against a monolithic baseline.

```bash
uv run python tests/scripts/phase6-deep-testing/test_deep_testing.py
```

> [!TIP]
> **Performance Optimization:** During evaluation runs, the system automatically swaps out heavy downstream nodes with fast, safe stub nodes (`mock_app`). This prevents sub-agents from mutating files in your workspace, avoids infinite search loops, and cuts API costs.

### Evaluation Scorecard Example:
```
======================================================================
 AGGREGATE EVALUATION SCORECARD SUMMARY
======================================================================
  ● Routing Accuracy:        3/5 (60.0%)
  ● Average Latency (LpA):   1.4710 seconds
  ● Avg Token Saturation:    65.0%
  * Avg Cost Reduction:      58.0% vs. Monolithic Agent
======================================================================
```
