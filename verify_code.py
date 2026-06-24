import subprocess
import sys

# Runs the quality check
# uv run python scripts/agent_quality_check.py

def main():
    result = subprocess.run(["uv", "run", "python", "scripts/agent_quality_check.py"], capture_output=False)
    sys.exit(result.returncode)

if __name__ == "__main__":
    main()
