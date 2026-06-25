# Copyright 2026 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""
File: config_loader.py
Purpose: Dynamically loads capability arbitrator configurations and discovers local skills/MCP servers.
Why it exists: To generalize the orchestrator for arbitrary codebases without hardcoded paths or tools.
How it works: Resolves target workspace directory, scans for arbitrator.yaml/json and mcp_config.json,
              auto-discovers local .agents/skills, and exposes capability mappings.
"""

import json
import os
from typing import Any, Dict, List, Optional
import yaml

class CapabilityDefinition:
    """Represents a capability tag routing definition."""
    def __init__(self, tag: str, description: str, node_type: str, target: Optional[str] = None):
        self.tag: str = tag
        self.description: str = description
        self.node_type: str = node_type
        self.target: Optional[str] = target

    def to_dict(self) -> Dict[str, Any]:
        return {
            "tag": self.tag,
            "description": self.description,
            "node_type": self.node_type,
            "target": self.target,
        }

def get_target_dir() -> str:
    """Returns the active target directory for execution."""
    return os.path.abspath(os.environ.get("ARBITRATOR_CWD", os.getcwd()))

def load_mcp_configs(target_dir: str) -> Dict[str, Dict[str, Any]]:
    """Scans target_dir for mcp_config.json or .agents-cli and returns MCP configurations."""
    # Search paths for MCP configuration files
    search_files = [
        os.path.join(target_dir, "mcp_config.json"),
        os.path.join(target_dir, ".agents-cli"),
        os.path.join(target_dir, ".mcp_config.json"),
    ]
    for file_path in search_files:
        if os.path.exists(file_path):
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    # Support standard schema {"mcpServers": {...}} or flat dictionary
                    return data.get("mcpServers", data)
            except Exception:
                pass
    return {}

def discover_local_skills(target_dir: str) -> List[str]:
    """Scans target_dir/.agents/skills/ for custom agent skills directories."""
    skills_dir = os.path.join(target_dir, ".agents", "skills")
    if not os.path.exists(skills_dir):
        skills_dir = os.path.join(target_dir, "app", "skills")
    
    if os.path.isdir(skills_dir):
        try:
            return [
                name for name in os.listdir(skills_dir)
                if os.path.isdir(os.path.join(skills_dir, name)) and not name.startswith(".")
            ]
        except Exception:
            pass
    return []

def _discover_default_caps(target_dir: str) -> List[CapabilityDefinition]:
    """Helper to dynamically auto-discover capabilities in target_dir."""
    discovered_skills = discover_local_skills(target_dir)
    default_caps = [
        CapabilityDefinition("coding", "writing, modifying, implementing files", "coding"),
        CapabilityDefinition("devops", "executing pytest, lint, code checks, format", "devops"),
        CapabilityDefinition("mcp", "viewing files, indexing, listing files", "mcp"),
    ]

    # Map discovered local skills into the routing engine
    for skill in discovered_skills:
        if skill in ["researcher", "stride"]:
            tag = "research" if skill == "researcher" else "stride"
            desc = "literature/paper search" if skill == "researcher" else "security audit, threat model, vulnerabilities"
            default_caps.append(CapabilityDefinition(tag, desc, "skill", skill))
        elif skill not in [c.tag for c in default_caps]:
            default_caps.append(CapabilityDefinition(skill, f"Apply capability-{skill} skill", "skill", skill))
            
    tags = [c.tag for c in default_caps]
    if "research" not in tags:
        default_caps.append(CapabilityDefinition("research", "literature/paper search", "skill", "researcher"))
    if "stride" not in tags:
        default_caps.append(CapabilityDefinition("stride", "security audit, threat model, vulnerabilities", "skill", "stride"))

    return default_caps

def load_arbitrator_config(target_dir: str) -> List[CapabilityDefinition]:
    """Loads capability rules and tag routes from arbitrator.yaml/json or auto-discovers them."""
    yaml_path = os.path.join(target_dir, "arbitrator.yaml")
    json_path = os.path.join(target_dir, "arbitrator.json")
    
    config_data: Optional[Dict[str, Any]] = None
    if os.path.exists(yaml_path):
        try:
            with open(yaml_path, "r", encoding="utf-8") as f:
                config_data = yaml.safe_load(f)
        except Exception:
            pass
    elif os.path.exists(json_path):
        try:
            with open(json_path, "r", encoding="utf-8") as f:
                config_data = json.load(f)
        except Exception:
            pass

    if config_data and "capabilities" in config_data:
        caps = []
        for cap in config_data["capabilities"]:
            caps.append(
                CapabilityDefinition(
                    tag=cap["tag"],
                    description=cap["description"],
                    node_type=cap["node_type"],
                    target=cap.get("target"),
                )
            )
        return caps

    return _discover_default_caps(target_dir)
