"""
File: test_telemetry.py
Purpose: Verifies durable telemetry storage and HITL resume updates.
Why it exists: Interrupted agent runs must remain visible without losing earlier or later sessions.
How it works: Uses a temporary JSON database and exercises save, merge, and path resolution behavior.
"""

from contextvars import Context
import json
from pathlib import Path
from types import SimpleNamespace

import pytest

from app.app_utils import telemetry
from app.app_utils.telemetry_store import resolve_db_file


PROMPT = (
    "Update the customer record for John Smith, SSN 123-45-6789, "
    "to reflect the new billing address."
)


@pytest.fixture
def telemetry_store(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> Path:
    """Point telemetry writes at a clean file for each test."""
    db_path = tmp_path / "telemetry_db.json"
    monkeypatch.setattr(telemetry, "DB_FILE", str(db_path))
    telemetry.reset_telemetry()
    return db_path


def _save_hitl_run(
    session_id: str,
    invocation_id: str,
    approved: bool,
    telemetry_run_id: str | None = None,
) -> dict:
    """Create one completed HITL record with stable execution identifiers."""
    telemetry.init_telemetry(PROMPT)
    telemetry.record_security_screen(True, ["Social Security Number"])
    telemetry.record_hitl(escalated=True, approved=approved, latency=1.0)
    telemetry.update_telemetry(
        {
            "user_id": "manual_tester",
            "session_id": session_id,
            "invocation_id": invocation_id,
            "run_source": "local_test_runner",
            **(
                {"telemetry_run_id": telemetry_run_id}
                if telemetry_run_id is not None
                else {}
            ),
        }
    )
    saved = telemetry.save_run()
    assert saved is not None
    return saved


def test_separate_hitl_sessions_are_both_persisted(telemetry_store: Path) -> None:
    """An approval and a denial from different sessions remain separate rows."""
    _save_hitl_run("deny-session", "deny-invocation", approved=False)
    _save_hitl_run("approve-session", "approve-invocation", approved=True)

    history = json.loads(telemetry_store.read_text())

    assert len(history) == 2
    assert [run["hitl_approved"] for run in history] == [False, True]
    assert [run["hitl_status"] for run in history] == ["denied", "approved"]
    assert all(run["hitl_escalated"] for run in history)
    assert all(run["prompt"] == PROMPT for run in history)


def test_resumed_invocation_replaces_interrupted_phase(telemetry_store: Path) -> None:
    """The resumed decision updates its interrupt row instead of adding a duplicate."""
    run_id = "stable-workflow-run"
    _save_hitl_run(
        "shared-session", "shared-invocation", approved=False, telemetry_run_id=run_id
    )
    _save_hitl_run(
        "shared-session", "shared-invocation", approved=True, telemetry_run_id=run_id
    )

    history = json.loads(telemetry_store.read_text())

    assert len(history) == 1
    assert history[0]["hitl_approved"] is True
    assert history[0]["hitl_status"] == "approved"
    assert history[0]["invocation_id"] == "shared-invocation"
    assert history[0]["telemetry_run_id"] == run_id


def test_interrupt_is_pending_until_operator_decides(telemetry_store: Path) -> None:
    """A newly paused run is not mislabeled as an operator denial."""
    telemetry.init_telemetry(PROMPT)
    telemetry.record_hitl(escalated=True, approved=None, latency=0.0)

    current = telemetry.get_current_telemetry()

    assert current is not None
    assert current["hitl_escalated"] is True
    assert current["hitl_approved"] is False
    assert current["hitl_status"] == "pending"


def test_node_checkpoint_and_cloud_callback_converge(
    telemetry_store: Path,
) -> None:
    """A later Agent Runtime callback enriches the node row without duplicating it."""
    run = telemetry.init_telemetry(PROMPT)
    context = SimpleNamespace(
        session=SimpleNamespace(id="cloud-session", user_id="cloud-user"),
        state={"telemetry_run_id": run["telemetry_run_id"]},
    )
    telemetry.record_hitl(escalated=True, approved=True, latency=1.0)
    telemetry.checkpoint_telemetry(context, "workflow_node_checkpoint")
    telemetry.update_telemetry(
        {"invocation_id": "cloud-invocation", "run_source": "agent_runtime"}
    )
    telemetry.save_run()

    history = json.loads(telemetry_store.read_text())

    assert len(history) == 1
    assert history[0]["telemetry_run_id"] == run["telemetry_run_id"]
    assert history[0]["invocation_id"] == "cloud-invocation"
    assert history[0]["run_source"] == "agent_runtime"


def test_resume_restores_task_local_run_from_workflow_state(
    telemetry_store: Path,
) -> None:
    """A resumed request can recover its pending row in a fresh async context."""
    run = telemetry.init_telemetry(PROMPT)
    context = SimpleNamespace(
        session=SimpleNamespace(id="resume-session", user_id="resume-user"),
        state={"telemetry_run_id": run["telemetry_run_id"]},
    )
    telemetry.record_hitl(escalated=True, approved=None, latency=0.0)
    telemetry.checkpoint_telemetry(context, "workflow_node_checkpoint")
    telemetry.reset_telemetry()

    restored = telemetry.restore_telemetry(context)

    assert restored is not None
    assert restored["telemetry_run_id"] == run["telemetry_run_id"]
    assert restored["hitl_status"] == "pending"


def test_concurrent_contexts_keep_active_runs_isolated(
    telemetry_store: Path,
) -> None:
    """Cloud requests running in separate async contexts do not share prompts."""
    first = telemetry.init_telemetry("first prompt")
    second = Context().run(telemetry.init_telemetry, "second prompt")

    assert telemetry.get_current_telemetry()["prompt"] == "first prompt"
    assert first["telemetry_run_id"] != second["telemetry_run_id"]


def test_repository_working_directory_is_preferred(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Generated runners use the repository database when launched from its root."""
    (tmp_path / "agents-cli-manifest.yaml").write_text("name: test\n")
    monkeypatch.chdir(tmp_path)
    monkeypatch.delenv("ARBITRATOR_CWD", raising=False)
    monkeypatch.delenv("K_SERVICE", raising=False)

    assert resolve_db_file() == str(tmp_path / "telemetry_db.json")


def test_cloud_run_uses_writable_tmp_storage(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Cloud Run keeps checkpoint writes away from its read-only source tree."""
    monkeypatch.setenv("K_SERVICE", "capability-arbitrator")

    assert resolve_db_file() == "/tmp/telemetry_db.json"
