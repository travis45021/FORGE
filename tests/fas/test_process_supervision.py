"""Contract-only process supervision evidence tests."""

import sys

import pytest

from forge.fas.process_supervision import (
    LocalProcessSupervisor,
    ProcessSupervisionError,
)


def command(source: str) -> list[str]:
    return [sys.executable, "-I", "-c", source]


def test_completed_process_returns_non_authoritative_digest_evidence(tmp_path):
    result = LocalProcessSupervisor().run(
        command("print('ok')"),
        cwd=tmp_path,
        timeout_seconds=1,
    )

    assert result["outcome"] == "completed"
    assert result["returncode"] == 0
    assert result["stdout_bytes"] > 0
    assert result["shell_used"] is False
    assert result["physical_commands_allowed"] is False
    assert result["release_authority_granted"] is False
    assert result["resource_limits_enforced"] is False


def test_crash_and_timeout_fail_closed(tmp_path):
    crashed = LocalProcessSupervisor().run(
        command("raise SystemExit(23)"), cwd=tmp_path, timeout_seconds=1
    )
    timed_out = LocalProcessSupervisor().run(
        command("import time; time.sleep(10)"), cwd=tmp_path, timeout_seconds=0.05
    )

    assert crashed["outcome"] == "crashed"
    assert crashed["returncode"] == 23
    assert timed_out["outcome"] == "timed_out"
    assert timed_out["returncode"] != 0
    assert timed_out["worker_reuse_allowed"] is False
    assert timed_out["requires_reviewed_resource_supervisor"] is True


def test_cancellation_fails_closed_and_preserves_non_authority(tmp_path):
    calls = iter((False, True))
    result = LocalProcessSupervisor().run(
        command("import time; time.sleep(10)"),
        cwd=tmp_path,
        timeout_seconds=1,
        cancel_requested=lambda: next(calls),
    )

    assert result["outcome"] == "cancelled"
    assert result["worker_reuse_allowed"] is False
    assert result["physical_commands_allowed"] is False
    assert result["release_authority_granted"] is False


@pytest.mark.parametrize(
    "command_value",
    ["not-a-list", [], [sys.executable, "\x00"]],
)
def test_rejects_unsafe_command_shapes(tmp_path, command_value):
    with pytest.raises(ProcessSupervisionError, match="command"):
        LocalProcessSupervisor().run(command_value, cwd=tmp_path, timeout_seconds=1)


def test_rejects_invalid_limits_and_working_directory(tmp_path):
    supervisor = LocalProcessSupervisor()
    with pytest.raises(ProcessSupervisionError, match="timeout"):
        supervisor.run(command("pass"), cwd=tmp_path, timeout_seconds=0)
    with pytest.raises(ProcessSupervisionError, match="working directory"):
        supervisor.run(command("pass"), cwd=tmp_path / "missing", timeout_seconds=1)
