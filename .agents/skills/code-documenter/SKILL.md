---
name: code-documenter
description: Mandatory local workflow skill for code files. Ensures every source code file has a plain-English header block and that all inline comments adhere to the 15-year-old accessibility rule.
---

# Code Documentation Standard Operating Procedure

You are acting as the Lead Code Reviewer for the Capability Arbitrator project.

Whenever you create a new source code file (e.g., `.py`, `.js`, `.ts`) or significantly refactor an existing one, you **MUST** strictly adhere to the following code documentation framework.

## 1. The Header Comment Block
Every single source code file must begin with a clear, standardized header comment block that explains the file's purpose before any imports or logic.

The header block must include:
- **File Purpose:** A one-sentence summary of what the file does.
- **Why it exists:** What larger architectural role does it play?
- **How it works:** A very brief summary of the primary functions or classes inside.

Example Python Header:
```python
\"\"\"
File: example.py
Purpose: Handles the routing of user requests to the correct execution node.
Why it exists: We need a centralized traffic controller so that we don't load every tool at once.
How it works: It takes the intent tag from the Scout and uses a dictionary to trigger the corresponding function.
\"\"\"
```

## 2. The "15-Year-Old" Accessibility Rule for Inline Comments
All docstrings and inline comments must be written so clearly and intuitively that a 15-year-old with basic programming interest can fully understand what the code is doing.
- **Avoid dense jargon:** Do not use complex computer science terms where a simple analogy will do.
- **Explain the "Why", not just the "What":** Instead of writing `# Adds 1 to x` (which is obvious from `x += 1`), write `# We increment the counter so we don't infinitely loop through the graph.`
- **Keep it conversational:** Write comments as if you are pair-programming with a junior developer and explaining your thought process out loud.

## 3. Enforcement
Before saving any code file edits, run a mental checklist:
1. Does this file have the required header block explaining Purpose, Why, and How?
2. Are the inline comments simple enough for a 15-year-old to follow the logic?

If the answer to either is no, update the comments before saving the file.
