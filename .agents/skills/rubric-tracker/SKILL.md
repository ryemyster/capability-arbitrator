---
name: rubric-tracker
description: >
  Mandatory local workflow skill to ensure the project continuously tracks progress against the Kaggle competition rubric.
---
# Rubric Tracker Protocol

## 1. Continuous Tracking
Whenever a new feature is completed, you MUST review `docs/RUBRIC.md` and update `docs/kaggle_objectives.md` to check off any newly fulfilled requirements.

## 2. Citation Requirements
When checking off a box in `docs/kaggle_objectives.md`, you MUST append a short italicized citation explaining exactly where and how it was completed (e.g. `*(Completed: Phase 2 mcp_node in app/agent.py)*`).

## 3. End-of-Turn Review
Before ending a session with the user after completing a major task or Phase, you MUST proactively mention the `kaggle_objectives.md` tracker to show what objectives were just accomplished, and state which rubric items are still outstanding.
