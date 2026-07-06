"""
File: telemetry_store.py
Purpose: Resolves, reads, and safely updates the local telemetry JSON database.
Why it exists: CLI, dashboard, and Agent Runtime processes must share data without overwriting each other.
How it works: Chooses one path, locks updates, and atomically replaces the JSON file.
"""

import fcntl
import json
import os
import pathlib
import tempfile
from typing import Any


def resolve_db_file() -> str:
    """Choose one telemetry file for every local execution surface."""
    if os.environ.get("K_SERVICE"):
        return "/tmp/telemetry_db.json"
    if configured_root := os.environ.get("ARBITRATOR_CWD"):
        return os.path.join(configured_root, "telemetry_db.json")
    working_root = pathlib.Path.cwd()
    if (working_root / "agents-cli-manifest.yaml").exists():
        return str(working_root / "telemetry_db.json")
    project_root = pathlib.Path(__file__).resolve().parent.parent.parent
    return str(project_root / "telemetry_db.json")


def load_history(db_file: str) -> list[dict[str, Any]]:
    """Read saved runs, returning an empty list for a missing or invalid file."""
    if not os.path.exists(db_file):
        return []
    try:
        with open(db_file) as history_file:
            return json.load(history_file)
    except Exception:
        return []


def _merge_run(
    history: list[dict[str, Any]], run: dict[str, Any]
) -> list[dict[str, Any]]:
    """Add a run or replace the earlier phase of the same invocation."""
    telemetry_run_id = run.get("telemetry_run_id")
    invocation_id = run.get("invocation_id")
    session_id = run.get("session_id")
    identity = ("telemetry_run_id", telemetry_run_id)
    if not telemetry_run_id or telemetry_run_id == "unknown":
        identity = ("invocation_id", invocation_id)
    if identity[1] in (None, "unknown"):
        identity = ("session_id", session_id)
    key, value = identity
    if value and value != "unknown":
        for index, saved_run in enumerate(history):
            if saved_run.get(key) == value:
                history[index] = run
                return history[-1000:]
    history.append(run)
    return history[-1000:]


def persist_run(db_file: str, run: dict[str, Any]) -> None:
    """Lock, merge, and atomically replace the telemetry database."""
    db_path = pathlib.Path(db_file)
    db_path.parent.mkdir(parents=True, exist_ok=True)
    try:
        with open(f"{db_file}.lock", "a+") as lock_file:
            fcntl.flock(lock_file.fileno(), fcntl.LOCK_EX)
            history = _merge_run(load_history(db_file), dict(run))
            with tempfile.NamedTemporaryFile(
                "w", dir=db_path.parent, delete=False, prefix=".telemetry-", suffix=".tmp"
            ) as temp_file:
                json.dump(history, temp_file, indent=2)
                temp_name = temp_file.name
            os.replace(temp_name, db_file)
    except Exception as error:
        print(f"Error saving telemetry: {error}")
