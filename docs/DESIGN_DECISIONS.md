# Design Decisions: Execution Targets

This document outlines the "why, what, how, and when" behind the core execution targets in the Capability Arbitrator architecture.

## 1. Deterministic Execution (e.g., "Math" Node)
**What:** A pure Python function designed to execute tasks mathematically or procedurally without an LLM.
**Why:** Large Language Models excel at abstract reasoning but struggle with raw arithmetic and procedural generation due to tokenization constraints, often leading to hallucinations. 
**When:** Used whenever an incoming request can be solved via closed-form logic, strict algorithms, or direct system calls (e.g., calculating distance, basic data transformations).
**How:** The Scout node classifies the intent as `math` (or similar), and the ADK Graph conditionally routes the workflow to a `FunctionNode` that executes Python code and returns the precise result, bypassing the LLM entirely and saving the reasoning budget.

## 2. Human-in-the-Loop (HITL) Execution
**What:** A designated pause in the agentic workflow that awaits explicit human authorization.
**Why:** Autonomous agents should not have unilateral authority over high-risk, irreversible, or commercially sensitive actions (e.g., production deployments, financial transactions).
**When:** Triggered when the Scout node detects an `approval` intent or a sensitive operational command.
**How:** Implemented using ADK's `RequestInput` node. The system pauses execution, surfaces the context to the human manager, and resumes only when explicit approval is injected back into the state.

## 3. Specialized Model Execution (e.g., "Research" Node)
**What:** An LLM node configured with a heavier, more capable model (e.g., Gemini 3.1 Pro) and connected to specific MCP (Model Context Protocol) servers or Agent Skills.
**Why:** Broad, generalist prompts cause "Context Rot." By specializing the node, we can load deep, niche context (like a research skill or a web-search MCP) without bloating the root agent's context window.
**When:** Used for tasks requiring deep reasoning, synthesis, or external data retrieval.
**How:** The Scout node routes `research` queries to an `LlmAgent` node equipped with the precise tools and instructions needed for that domain.
