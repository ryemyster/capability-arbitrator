## Context Engine

Use Context Engine for non-trivial repository work. Treat it as a retrieval index: discover references first, read only selected files, and keep responses in `mode=context_safe` unless exact implementation detail is required. If a discovery result is thin, has too few hits, or lacks enough content to choose the next read, make one re-call without the mode flag before broadening reads. Verify source files before editing. Context Engine is read-only; the coding agent owns all repository writes and decisions.

### Workflow: find -> assess -> read -> act -> verify
1. **Discover**: Identify candidate artifacts using the `/find`, `/vector-search`, or `/scan` endpoints. Do not load content yet. Start with `mode=context_safe`.
2. **Assess**: Ensure high confidence before proceeding. High confidence = small scope (<= 3 files), specific matches. Low confidence = re-call without `mode=context_safe`, explore, or ask user.
3. **Read**: Use `/read` to fetch 1-3 artifacts max. Prefer summary mode unless full detail is needed.
4. **Execute**: Perform work using the minimal required context. Verify cited source files.
5. **Verify**: Use `/diff-summary` with `git diff HEAD` after every Write or Edit. Do not skip this step.
6. **Refresh**: If scope shifts, restart from step 1.

## GitHub Interactions
ALWAYS use the `github` MCP server for ALL GitHub interactions. Do not fall back to curl or other tools when interacting with GitHub; use the provided MCP tools.

## Capability Arbitrator Operational Rules
- Architecture: This agent is a "Capability Arbitrator". It must always ask "What capability is required?" before assigning a resource.
- Progressive Disclosure: Do not load all tools into the context window at once.
- Fast Scouting: Always use `gemini-3.5-flash` for the initial intent classification (the Scout node) to preserve the reasoning budget.

## Security Gates
- **Secret Zero-Trust**: NEVER read the contents of `.env` files using `view_file` or any terminal command. 
- **No Leakage**: NEVER output API keys, environment variables, or sensitive credentials into the chat response under any circumstances.
