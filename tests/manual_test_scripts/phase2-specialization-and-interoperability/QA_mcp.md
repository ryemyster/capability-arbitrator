# Phase 2 Manual QA Tests (MCP Node)

## Objective
Verify that the `mcp_node` is selectively engaged and successfully connects to the local filesystem MCP server when requested.

## How to Test
1. Run the Capability Arbitrator from the CLI:
   ```bash
   uv run agents-cli run "mcp: list the files in the current directory"
   ```
2. Verify the output.

## Validation Sign-off
- [ ] Scout successfully routes to `mcp_node`.
- [ ] `mcp_node` uses the `list_directory` tool from the local filesystem MCP.
- [ ] The response contains the local file structure.

---
*Created: 2026-06-23T12:35:00-06:00*
