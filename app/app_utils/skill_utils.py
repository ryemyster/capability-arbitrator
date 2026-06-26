"""
File: skill_utils.py
Purpose: Consolidates instructions and few-shots loading logic for custom agent skills.
Why it exists: Prevents duplication of instructions loaders across different capability nodes, satisfying DRY standards.
How it works: Searches a skill's directory for SKILL.md and few_shots.json, formats and combines them, and returns a single instruction string.
"""

import json
import os

def load_skill_instructions(skill_name: str, target_dir: str = None) -> str:
    """Reads the instructions from the local skill SKILL.md file and
    dynamically appends the few-shot examples from few_shots.json at startup.
    This ensures our system instruction always aligns dynamically with the skill definitions.
    """
    if not target_dir:
        target_dir = os.environ.get("ARBITRATOR_CWD", os.getcwd())

    # Try local .agents/skills/<skill_name>
    skill_dir = os.path.join(target_dir, ".agents", "skills", skill_name)
    if not os.path.exists(skill_dir):
        # Try local app/skills/<skill_name>
        skill_dir = os.path.join(target_dir, "app", "skills", skill_name)
    if not os.path.exists(skill_dir):
        # Fallback to internal packaged skills
        base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        skill_dir = os.path.join(base_dir, "app", "skills", skill_name)

    # Load system instructions from SKILL.md
    instructions = ""
    try:
        with open(os.path.join(skill_dir, "SKILL.md"), "r", encoding="utf-8") as f:
            content = f.read()
            if content.startswith("---"):
                parts = content.split("---", 2)
                if len(parts) >= 3:
                    instructions = parts[2].strip()
            else:
                instructions = content.strip()
    except Exception:
        instructions = f"You are the dedicated {skill_name} node. Apply capability-{skill_name} skill."

    # Load few-shot examples from few_shots.json
    try:
        with open(os.path.join(skill_dir, "few_shots.json"), "r", encoding="utf-8") as f:
            data = json.load(f)
            examples = data.get("examples", [])
            if examples:
                instructions += "\n\n## Few-Shot Examples of Expected Output Format\n"
                for idx, eg in enumerate(examples, 1):
                    instructions += f"\n### Example {idx}\n**Input:** {eg['input']}\n**Output:**\n{eg['output']}\n"
    except Exception:
        # If few-shots fail to load, proceed with just instructions
        pass

    return instructions
