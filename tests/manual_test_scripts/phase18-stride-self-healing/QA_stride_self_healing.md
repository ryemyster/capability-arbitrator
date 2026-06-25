# Phase 18 — Manual QA Checklist: STRIDE Self-Healing

## Prerequisites

- `GOOGLE_GENAI_USE_VERTEXAI=True` and a working Vertex AI project in your environment.
- `gh` CLI authenticated (`gh auth status`).
- A clean git working tree on a feature branch.

---

## Seeding a Vulnerable Test File

Create a throwaway file with an obvious security issue:

```bash
cat > /tmp/vuln_test.py << 'EOF'
import subprocess

SECRET_KEY = "super-secret-hardcoded-value"

def run_command(user_input):
    # Unsafe: shell=True with user-controlled input
    subprocess.run(user_input, shell=True)
EOF
```

---

## Test Cases

| # | Command | Expected Behaviour | Pass? |
|---|---------|-------------------|-------|
| 1 | `uv run arbitrator stride-heal --help` | Prints usage, exits 0 | |
| 2 | `uv run arbitrator stride-heal /tmp/vuln_test.py --dry-run` | Prints STRIDE report, prints "DRY RUN" line, no file changes | |
| 3 | `SELF_HEALING_MODE=propose_patch uv run arbitrator stride-heal /tmp/vuln_test.py --dry-run` | Shows top finding + what patch would be attempted, no writes | |
| 4 | `SELF_HEALING_MODE=audit_only uv run arbitrator stride-heal /tmp/vuln_test.py` | Prints full STRIDE report, exits 0, no file writes | |
| 5 | `SELF_HEALING_MODE=apply_patch uv run arbitrator stride-heal /tmp/vuln_test.py` | Generates patch, writes to file, runs `uv run pytest tests/unit/ -x -q`, passes or reverts | |
| 6 | Config `enabled: false` + no env override | Any command prints report only (audit_only forced) | |
| 7 | Provide a non-existent target path | Exits non-zero with a clear error message | |
| 8 | `SELF_HEALING_ENABLED=true SELF_HEALING_MODE=open_pr uv run arbitrator stride-heal /tmp/vuln_test.py` | Full pipeline: patch → verify → git branch → PR opened to develop | |

---

## Acceptance Criteria

- `audit_only` mode never writes any files.
- `apply_patch` mode reverts the file when pytest fails.
- `open_pr` mode requires `GITHUB_INTEGRATION_ENABLED=true` or `SELF_HEALING_MODE=open_pr` explicitly — does NOT create a PR silently.
- All modes respect `--dry-run` (no file writes, no git operations).
- Config env vars (`SELF_HEALING_ENABLED`, `SELF_HEALING_MODE`) override `stride_self_healing.yaml`.
- No `.env` file contents are read, logged, or exposed in any output.
