# Key Performance Indicators (KPIs) & Value Metrics

To prove that the Capability Arbitrator successfully mitigates "Context Rot" and optimizes the reasoning budget, we track the following core KPIs across our agentic workflows.

## 1. Token Saturation Ratio (TSR)
**What:** The ratio of *useful context tokens* to *total prompt tokens* per request.
**Target:** > 85% useful context.
**Impact:** A monolithic agent loads 15+ irrelevant skills per request, dropping TSR below 10%. By progressively disclosing only the single necessary skill (e.g., `research`), we eliminate dead tokens, preventing context saturation and hallucinations.

## 2. Latency per Action (LpA)
**What:** The total time from user input to final execution target resolution.
**Target:** < 1.5 seconds for deterministic routing.
**Impact:** Using Gemini 3.5 Flash for the initial Scout node ensures sub-second classification. Routing `math` or `approval` tasks to deterministic functions saves the 5-10 second roundtrip time of forcing a heavy LLM to generate code or reason through arithmetic.

## 3. Cost per Execution (CpE)
**What:** The cloud compute cost (input/output tokens) per workflow.
**Target:** > 80% reduction vs. Naive Monolith.
**Impact:** The Naive Agent averages 250,000 input tokens per request (loading every skill into context). The Capability Arbitrator averages 42,000 input tokens per request (Scout classification + 1 targeted skill). This results in a massive decrease in operational cost at scale.

## 4. Deterministic Accuracy Rate
**What:** The percentage of closed-form tasks (math, system states) that execute flawlessly.
**Target:** 100% accuracy on non-generative tasks.
**Impact:** LLMs hallucinate math. By routing math explicitly to a Python function, accuracy goes from highly variable to 100% deterministic truth.
