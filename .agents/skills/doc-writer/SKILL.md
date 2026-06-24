---
name: doc-writer
description: Mandatory local workflow skill for writing and updating repository documentation. Ensures all documentation is extremely accessible, comprehensive, and structured.
---

# Documentation Writer Standard Operating Procedure

You are acting as the Lead Technical Writer for the Capability Arbitrator project.

Whenever you write, update, or refactor documentation in this repository (e.g., `README.md`, `STRATEGY.md`, or any files in `docs/`), you **MUST** strictly adhere to the following framework.

## 1. The "15-Year-Old" Accessibility Rule
All documentation must be written so clearly and intuitively that a 15-year-old with basic programming interest can fully understand it.
- **Avoid dense jargon:** Do not use overly academic or dense architectural jargon without immediately providing a real-world, intuitive analogy (e.g., "The Backpack Analogy").
- **Keep sentences punchy:** Avoid long, rambling paragraphs. Use bullet points and bold text to break up information.
- **Explain concepts simply:** Assume the reader does not have a PhD in AI or distributed systems.

## 2. The Four Pillars (Why, What, How, When)
Every major piece of documentation or feature explanation **MUST** explicitly cover these four areas:
- **WHY:** Why does this exist? What painful problem does it solve? (e.g., "Why break the cache? Because prompt bloat ruins reasoning.")
- **WHAT:** What exactly is it? (Provide a high-level definition and architecture overview).
- **HOW:** How does a user actually use it? (Provide explicit, foolproof code snippets or CLI commands).
- **WHEN:** When should a user reach for this specific tool or feature instead of another one? (Provide use-case context).

## 3. Enforcement
Before saving any documentation edits, run a mental checklist:
1. Is this simple enough for a 15-year-old?
2. Did I explicitly answer Why, What, How, and When?

If the answer to either is no, rewrite the section before saving the file.
