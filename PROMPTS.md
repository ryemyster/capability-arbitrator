h1. Day 1 Prompt to Configure the Repository

```
Please help me set up a new ADK 2.0 agent project called "capability-arbitrator".

Step 1: Scaffolding
Run the command `agents-cli scaffold create capability-arbitrator --adk` in the terminal. Once created, please cd into the directory.

Step 2: Establish the Rules (CONTEXT.md)
Create a file at `.agents/CONTEXT.md` and define the following project-specific rules:
- Architecture: This agent is a "Capability Arbitrator". It must always ask "What capability is required?" before assigning a resource.
- Progressive Disclosure: Do not load all tools into the context window at once.
- Fast Scouting: Always use `gemini-3.5-flash` for the initial intent classification (the Scout node) to preserve the reasoning budget.

Step 3: Build the Scout Node (app/agent.py)
Overwrite the scaffolded `app/agent.py` to implement the first phase of our workflow:
- Create an ADK 2.0 `Workflow` graph.
- Create an `llm_scout` node powered by `gemini-3.5-flash`.
- The `llm_scout` should take the user's prompt and output a structured JSON response (using a Pydantic schema) that assigns one of the following capability tags: ["coding", "research", "math", "document", "approval"].
- For now, route the output of the `llm_scout` directly to the END of the graph so we can test the classification logic.

Please present the implementation plan for my approval before writing the code.
Once Antigravity finishes generating the code, you can quickly test it in your terminal by running agents-cli run "Calculate the distance to the moon" to ensure it successfully classifies the intent and outputs the math tag
```
