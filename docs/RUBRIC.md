# The Master Rubric for a "Gold-Standard" Submission

Use this checklist to ensure you have covered the high-leverage technical points.

## Requirements & Best Practices

### Architecture (ADK)
- [x] Uses ADK 2.0 Graph (Workflow) with clearly defined nodes and edges.
- [x] Implements conditional branching (e.g., routing based on intent).
- [x] Includes a Human-in-the-Loop (HITL) node for high-risk actions.

### Specialization (Skills)
- [x] Features at least one custom Agent Skill in `.agents/skills/`.
- [x] Skill utilizes Progressive Disclosure (loads only when relevant).
- [x] Includes few-shot examples or a script in the skill folder.

### Interoperability (MCP)
- [x] Connects to at least one MCP Server (Local or Remote).
- [x] Agent uses MCP tools to ground responses in real-time data.

### Security & Safety
- [x] Implements a Security Screen (PII redaction or injection defense).
- [x] Uses a Persistent Context file (`CONTEXT.md`) for guardrails.
- [x] (Optional) Implements a STRIDE Threat Modeling skill.

### Quality & Eval
- [x] Uses Gherkin syntax for behavior-driven specifications.
- [x] Provides evidence of an Evaluation Scorecard (LLM-as-judge).
- [x] Code passes Automated Linting (`agents-cli lint`).

### Deployment
- [x] Successfully deployed to Agent Runtime or Cloud Run.
- [ ] (Optional) Uses a FastAPI Manager Dashboard for the frontend.
- [ ] Uses Pub/Sub for event-driven "Ambient" triggers.
