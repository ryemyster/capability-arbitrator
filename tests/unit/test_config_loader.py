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
File: test_config_loader.py
Purpose: Unit tests for the generalized configuration loading and skill discovery logic.
Why it exists: Assures the Capability Arbitrator safely discovers local code conventions dynamically.
How it works: Creates isolated, temporary directories and files using pytest fixtures to test config parsing.
"""

import json
from pathlib import Path
import yaml
from app.app_utils.config_loader import (
    load_arbitrator_config,
    load_mcp_configs,
    discover_local_skills,
    CapabilityDefinition
)

def test_load_arbitrator_config_yaml(tmp_path: Path) -> None:
    """Verifies that the YAML configuration loader parses capabilities correctly."""
    # Create a mock arbitrator.yaml file in our temporary folder
    yaml_content = {
        "capabilities": [
            {
                "tag": "custom_tag",
                "description": "Custom tag description",
                "node_type": "skill",
                "target": "custom_target"
            }
        ]
    }
    yaml_file = tmp_path / "arbitrator.yaml"
    with open(yaml_file, "w", encoding="utf-8") as f:
        yaml.dump(yaml_content, f)

    # Load and verify the config matches our written specifications
    caps = load_arbitrator_config(str(tmp_path))
    assert len(caps) == 1
    assert caps[0].tag == "custom_tag"
    assert caps[0].description == "Custom tag description"
    assert caps[0].node_type == "skill"
    assert caps[0].target == "custom_target"

def test_load_arbitrator_config_json(tmp_path: Path) -> None:
    """Verifies that the JSON configuration loader parses capabilities correctly."""
    # Create a mock arbitrator.json file in our temporary folder
    json_content = {
        "capabilities": [
            {
                "tag": "json_tag",
                "description": "JSON tag description",
                "node_type": "coding",
                "target": None
            }
        ]
    }
    json_file = tmp_path / "arbitrator.json"
    with open(json_file, "w", encoding="utf-8") as f:
        json.dump(json_content, f)

    # Load and verify the json configuration is parsed correctly
    caps = load_arbitrator_config(str(tmp_path))
    assert len(caps) == 1
    assert caps[0].tag == "json_tag"
    assert caps[0].node_type == "coding"

def test_load_mcp_configs_parsing(tmp_path: Path) -> None:
    """Verifies that the MCP configurations are read and parsed from JSON files."""
    # Create a mock mcp_config.json file in our temporary folder
    mcp_content = {
        "mcpServers": {
            "filesystem": {
                "command": "npx",
                "args": ["server-filesystem"]
            }
        }
    }
    mcp_file = tmp_path / "mcp_config.json"
    with open(mcp_file, "w", encoding="utf-8") as f:
        json.dump(mcp_content, f)

    # Load and check the command mappings
    mcp_settings = load_mcp_configs(str(tmp_path))
    assert "filesystem" in mcp_settings
    assert mcp_settings["filesystem"]["command"] == "npx"

def test_discover_local_skills_scanner(tmp_path: Path) -> None:
    """Verifies that the local skill directory scanner discovers subdirectories."""
    # Create a dummy .agents/skills folder structure
    skills_dir = tmp_path / ".agents" / "skills"
    skills_dir.mkdir(parents=True)
    
    # Create two dummy skill subfolders
    (skills_dir / "doc-writer").mkdir()
    (skills_dir / "stride").mkdir()

    # Discover and assert both directories were identified
    discovered = discover_local_skills(str(tmp_path))
    assert "doc-writer" in discovered
    assert "stride" in discovered
