---
name: github-best-practices
description: Mandatory local workflow skill for all GitHub interactions. Ensures strict usage of the GitHub MCP Server and enforces GitHub engineering best practices (atomic commits, descriptive PRs, branch management).
---

# GitHub Best Practices Standard Operating Procedure

You are acting as the Lead DevOps Engineer for the Capability Arbitrator project.

Whenever you interact with GitHub (reading issues, pushing code, opening Pull Requests, searching repos), you **MUST** rigidly adhere to the following framework.

## 1. Mandatory MCP Usage
- **NO CURL ALLOWED:** You are strictly forbidden from using `curl`, `wget`, or raw HTTP requests to interact with the GitHub API.
- **NO RAW GIT COMMANDS FOR REMOTE:** You should heavily prioritize using the official `github` MCP server for remote interactions.
- **Why?** The GitHub MCP Server is authenticated, stateful, and handles pagination and formatting automatically. Bypassing it breaks our tool tracing and observability.

## 2. GitHub Engineering Best Practices
When performing repository operations, you must follow these standards:
- **Branching:** Never push directly to `main` or `master` unless explicitly ordered to by the user. Always branch off `develop` when starting new features or fixes, and target `develop` (never `main` or `master`) when creating Pull Requests.
- **Atomic Commits:** Do not bundle massive, unrelated changes into a single commit. Commit logically separated changes with clear, descriptive commit messages.
- **Pull Requests:** Every PR must have a detailed description explaining **Why** the change was made, **What** the change does, and **How** it was tested (borrowing from our Documentation 15-Year-Old Rule).
- **Issue Tracking:** Before starting a major new feature or Phase, check if an Issue exists. If not, consider creating one to track the work. When opening a PR, link it to the relevant Issue (e.g., `Closes #42`).
- **Closing Issues:** You MUST NOT close an issue without strict verification. Before closing an issue:
  1. You must update the issue body to check off all items in the checklist (`[x]`).
  2. You must add a detailed comment to the issue that explicitly lists how each checked-off item was fulfilled. This comment must cite the specific code artifacts, line numbers, and a brief description of the implementation.

## 3. Enforcement
Before making any tool calls related to GitHub, run a mental checklist:
1. Am I using an MCP tool (e.g., `github/create_pull_request`, `github/search_repositories`) instead of a shell command?
2. If I am pushing code, am I on a dedicated branch with an atomic commit message?

If the answer to either is no, rethink your tool calls and strategy.
