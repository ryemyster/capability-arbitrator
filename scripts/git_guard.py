#!/usr/bin/env python3
"""
File: git_guard.py
Purpose: Enforces branch safety rules (no main/master pushes, must branch from develop).
Why it exists: Prevents agents or developers from pushing directly to main/master or branching from incorrect base branches.
How it works: Executes git commands to verify that the current branch is not main/master, and that develop is an ancestor of the current branch.
"""

import subprocess
import sys

def run_git_cmd(args: list[str]) -> str:
    res = subprocess.run(["git"] + args, capture_output=True, text=True, check=True)
    return res.stdout.strip()

def main() -> None:
    try:
        current_branch = run_git_cmd(["branch", "--show-current"])
    except Exception as e:
        print(f"Error getting current branch: {e}")
        sys.exit(1)

    # 1. Prevent pushing directly to main/master
    if current_branch in ["main", "master"]:
        print(f"❌ ERROR: Direct pushes to '{current_branch}' are strictly prohibited!")
        print("All development must occur on feature/fix branches targeting 'develop'.")
        sys.exit(1)

    # 2. Ensure current branch is branched from develop
    try:
        # Check if 'develop' is an ancestor of HEAD (exit code 0 if true, 1 if false)
        subprocess.run(["git", "merge-base", "--is-ancestor", "develop", "HEAD"], check=True)
    except subprocess.CalledProcessError:
        print("❌ ERROR: Current branch is not branched off 'develop'!")
        print("Please rebase onto 'develop' or branch from 'develop' directly.")
        sys.exit(1)
    except Exception as e:
        print(f"Error checking ancestor: {e}")
        sys.exit(1)

    print("✅ Git branch validation passed.")
    sys.exit(0)

if __name__ == "__main__":
    main()
