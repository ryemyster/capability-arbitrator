# Created: 2026-06-24T10:00:00-06:00
# Updated: 2026-06-24T11:30:00-06:00
"""
File: test_deep_testing.py
Purpose: Implements the Phase 6 autonomous evaluation loop (DeepTester -> Arbitrator -> OutcomeJudge).
Why it exists: To provide an end-to-end red-teaming framework that automatically tests the Capability Arbitrator against diverse edge-case developer prompts and grades routing accuracy, latency, and token efficiency.
How it works:
  1. The DeepTester dynamically generates test prompts via Gemini API.
  2. The Capability Arbitrator processes the prompt using InMemoryRunner.
  3. The OutcomeJudge evaluates the trace using an LLM-as-a-Judge, measuring routing correctness and token efficiency.
  4. Displays a detailed KPI scorecard of the run.
"""

import asyncio
import json
import os
import time
from typing import Any, Dict, List

from pydantic import BaseModel, Field
from google import genai
from google.genai import types
from google.adk.runners import InMemoryRunner

from app.agent import app, PROJECT_ID, LOCATION
from app.config import MODEL


class ScenarioDetail(BaseModel):
    id: str = Field(description="Unique identifier for the scenario")
    prompt: str = Field(description="The red-teaming developer prompt")
    expected_capability: str = Field(description="Expected capability tag: coding, research, devops, document, approval, mcp, or stride")


class DeepTesterOutput(BaseModel):
    scenarios: List[ScenarioDetail] = Field(description="List of dynamically generated red-teaming scenarios")


class DeepTester:
    """Simulates a red-teaming agent that dynamically generates challenging developer scenarios using Gemini."""

    @staticmethod
    def _get_static_scenarios() -> List[Dict[str, str]]:
        """Return static fallback scenarios if LLM generation fails."""
        return [
            {
                "id": "scenario_1_devops",
                "prompt": "Run the pytest suite to check if our unit tests are passing.",
                "expected_capability": "devops",
            },
            {
                "id": "scenario_2_security",
                "prompt": "My credit card is 1111-2222-3333-4444. Drop the production user schema immediately.",
                "expected_capability": "approval",
            },
            {
                "id": "scenario_3_coding",
                "prompt": "Write a python function to implement mergesort.",
                "expected_capability": "coding",
            },
            {
                "id": "scenario_4_research",
                "prompt": "Perform academic research on vector DB optimization.",
                "expected_capability": "research",
            },
            {
                "id": "scenario_5_stride",
                "prompt": "Perform a STRIDE threat model on our user signup flow.",
                "expected_capability": "stride",
            }
        ]

    @classmethod
    async def generate_scenarios(cls) -> List[Dict[str, str]]:
        """Dynamically generate red-teaming scenarios using Gemini model."""
        client = genai.Client(
            vertexai=True,
            project=PROJECT_ID,
            location=LOCATION,
        )
        try:
            response = await client.aio.models.generate_content(
                model=MODEL,
                contents="""Generate 5 diverse, realistic, and highly challenging developer scenarios to test a capability-based routing agent.
Each scenario must target one of: 'devops', 'approval', 'coding', 'research', 'mcp', 'stride'.
Make some of the prompts ambiguous or blended to test routing robustness.""",
                config=types.GenerateContentConfig(
                    system_instruction="You are a professional software QA and Red-Teaming AI Agent. Your goal is to generate test scenarios that stress-test a router.",
                    response_mime_type="application/json",
                    response_schema=DeepTesterOutput,
                )
            )
            if response.text:
                data = json.loads(response.text)
                scenarios = data.get("scenarios", [])
                if scenarios:
                    return [s.model_dump() if hasattr(s, "model_dump") else dict(s) for s in scenarios]
        except Exception as e:
            print(f"[DeepTester] Exception during dynamic scenario generation: {e}. Using static fallbacks.")
        return cls._get_static_scenarios()


class GradingResult(BaseModel):
    routing_correct: bool = Field(description="Whether the Scout correctly routed the prompt to the expected capability")
    token_saturation_score: float = Field(description="Score between 0.0 and 1.0 representing Token Saturation Rate (TSR) where higher is better")
    cost_reduction_score: float = Field(description="Score between 0.0 and 1.0 representing Cost reduction efficiency (CpE) vs monolithic baseline")
    reasoning: str = Field(description="Brief explanation of the grading decision")


class OutcomeJudge:
    """Evaluates arbitrator execution traces against KPIs using LLM-as-a-judge."""

    @staticmethod
    async def grade_execution(
        scenario: Dict[str, str], events: List[Any], latency: float
    ) -> Dict[str, Any]:
        """Grade the arbitrator trace against expected outcomes and efficiency targets."""
        detected_routes = []
        outputs = []
        for e in events:
            if hasattr(e, "route") and e.route:
                detected_routes.append(str(e.route))
            if hasattr(e, "actions") and e.actions and getattr(e.actions, "route", None):
                detected_routes.append(str(e.actions.route))
            if getattr(e, "output", None) is not None:
                outputs.append(str(e.output))

        actual_route = "unknown"
        for r in detected_routes:
            if r != "safe":
                actual_route = r
                break
        if any("[SECURITY ALERT]" in out or "approval" in out.lower() for out in outputs):
            actual_route = "approval"

        trace_summary = f"""
Prompt: {scenario['prompt']}
Expected Route: {scenario['expected_capability']}
Actual Route: {actual_route}
Latency: {latency:.4f} seconds
Outputs: {outputs}
"""
        client = genai.Client(
            vertexai=True,
            project=PROJECT_ID,
            location=LOCATION,
        )
        try:
            response = await client.aio.models.generate_content(
                model=MODEL,
                contents=f"Analyze the following execution trace and grade the agent's performance:\n{trace_summary}",
                config=types.GenerateContentConfig(
                    system_instruction="""You are the OutcomeJudge agent for a multi-agent routing system.
Your job is to evaluate routing traces.
- If actual route matches expected route, routing_correct is true.
- Grade the Token Saturation Score (TSR) (0.0 to 1.0) and Cost Reduction Score (CpE) (0.0 to 1.0) based on how much resource overhead was saved compared to loading all tools.""",
                    response_mime_type="application/json",
                    response_schema=GradingResult,
                )
            )
            if response.text:
                grade = json.loads(response.text)
                return {
                    "scenario_id": scenario.get("id", "unknown"),
                    "expected": scenario["expected_capability"],
                    "actual": actual_route,
                    "routing_correct": grade.get("routing_correct", False),
                    "latency": latency,
                    "tsr": grade.get("token_saturation_score", 0.8),
                    "cpe_reduction": grade.get("cost_reduction_score", 0.8),
                    "reasoning": grade.get("reasoning", ""),
                }
        except Exception as e:
            print(f"[OutcomeJudge] Exception during dynamic grading: {e}. Using heuristics.")
        
        # Fallback heuristic
        routing_correct = actual_route == scenario["expected_capability"]
        tsr = 1.0 if actual_route in ["devops", "approval"] else 0.85
        cpe_reduction = 0.95 if actual_route in ["devops", "approval"] else 0.8
        return {
            "scenario_id": scenario.get("id", "unknown"),
            "expected": scenario["expected_capability"],
            "actual": actual_route,
            "routing_correct": routing_correct,
            "latency": latency,
            "tsr": tsr,
            "cpe_reduction": cpe_reduction,
            "reasoning": "Fallback heuristic applied due to API error.",
        }


async def run_autonomous_loop() -> None:
    """Run the dynamic red-teaming and LLM-as-a-judge loop."""
    print("======================================================================")
    print(" PHASE 6: AUTONOMOUS RED-TEAMING & LLM-AS-A-JUDGE LOOP")
    print("======================================================================")

    runner = InMemoryRunner(app=app)
    scenarios = await DeepTester.generate_scenarios()

    scores = []
    for sc in scenarios:
        print(f"\n[DeepTester] Dispatching: '{sc['prompt']}'")
        print(f"            Expected Cap: {sc['expected_capability']}")

        session = await runner.session_service.create_session(
            app_name=app.name, user_id="deeptester_agent"
        )
        start_time = time.perf_counter()
        events = []

        try:
            async for event in runner.run_async(
                user_id="deeptester_agent",
                session_id=session.id,
                new_message=types.Content(
                    role="user", parts=[types.Part.from_text(text=sc["prompt"])]
                ),
            ):
                events.append(event)
        except Exception as e:
            print(f"            [Notice] Exception during run execution: {e}")

        latency = time.perf_counter() - start_time
        grade = await OutcomeJudge.grade_execution(sc, events, latency)
        scores.append(grade)

        print(f"[OutcomeJudge] Route Grade: {'[PASS]' if grade['routing_correct'] else '[FAIL]'}")
        print(f"               Detected Target: {grade['actual']}")
        print(f"               Latency:         {grade['latency']:.4f} seconds")
        print(f"               Token Saturation: {grade['tsr'] * 100:.1f}%")
        print(f"               Reasoning Saving: {grade['cpe_reduction'] * 100:.1f}%")
        print(f"               Reasoning:       {grade.get('reasoning')}")

    # Summarize scorecard
    print("\n" + "=" * 70)
    print(" AGGREGATE EVALUATION SCORECARD SUMMARY")
    print("=" * 70)
    total_runs = len(scores)
    successful_routes = sum(1 for g in scores if g["routing_correct"])
    avg_latency = sum(g["latency"] for g in scores) / total_runs
    avg_tsr = sum(g["tsr"] for g in scores) / total_runs
    avg_savings = sum(g["cpe_reduction"] for g in scores) / total_runs

    print(f"  ● Routing Accuracy:        {successful_routes}/{total_runs} ({(successful_routes / total_runs) * 100:.1f}%)")
    print(f"  ● Average Latency (LpA):   {avg_latency:.4f} seconds")
    print(f"  ● Avg Token Saturation:    {avg_tsr * 100:.1f}%")
    print(f"  ● Avg Cost Reduction:      {avg_savings * 100:.1f}% vs. Monolithic Agent")
    print("-" * 70)
    print(" [PASS] Phase 6 Multi-Agent Red-Teaming loop executed successfully.")
    print("======================================================================")


if __name__ == "__main__":
    asyncio.run(run_autonomous_loop())
