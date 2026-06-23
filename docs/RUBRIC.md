# The Master Rubric for a "Gold-Standard" Submission

Use this checklist to ensure you have covered the high-leverage technical points.

## Requirements & Best Practices

### Architecture (ADK)
- [ ] Uses ADK 2.0 Graph (Workflow) with clearly defined nodes and edges.
- [ ] Implements conditional branching (e.g., routing based on intent).
- [ ] Includes a Human-in-the-Loop (HITL) node for high-risk actions.

### Specialization (Skills)
- [ ] Features at least one custom Agent Skill in `.agents/skills/`.
- [ ] Skill utilizes Progressive Disclosure (loads only when relevant).
- [ ] Includes few-shot examples or a script in the skill folder.

### Interoperability (MCP)
- [ ] Connects to at least one MCP Server (Local or Remote).
- [ ] Agent uses MCP tools to ground responses in real-time data.

### Security & Safety
- [ ] Implements a Security Screen (PII redaction or injection defense).
- [x] Uses a Persistent Context file (`CONTEXT.md`) for guardrails.
- [ ] (Optional) Implements a STRIDE Threat Modeling skill.

### Quality & Eval
- [ ] Uses Gherkin syntax for behavior-driven specifications.
- [ ] Provides evidence of an Evaluation Scorecard (LLM-as-judge).
- [ ] Code passes Automated Linting (`agents-cli lint`).

### Deployment
- [ ] Successfully deployed to Agent Runtime or Cloud Run.
- [ ] (Optional) Uses a FastAPI Manager Dashboard for the frontend.
- [ ] Uses Pub/Sub for event-driven "Ambient" triggers.
