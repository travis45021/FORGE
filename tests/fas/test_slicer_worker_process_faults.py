"""Process-level slicer worker lifecycle evidence without an Orca engine."""

import subprocess
import sys
from pathlib import Path

import pytest

from forge.fas.process_supervision import LocalProcessSupervisor
from forge.fas.slicer_worker import REQUIRED_FORBIDDEN, SlicerWorkerSupervisor


def manifest() -> dict:
    return {
        "worker_id": "worker-process-fixture",
        "context": "production",
        "workspace": {
            "input": "work/process-fixture/input",
            "output": "work/process-fixture/output",
            "logs": "work/process-fixture/logs",
        },
        "limits": {
            "timeout_seconds": 1,
            "memory_bytes": 10_000_000,
            "disk_bytes": 10_000_000,
        },
        "forbidden_capabilities": sorted(REQUIRED_FORBIDDEN),
    }


def assess(tmp_path: Path, outcome: str, artifact_digest: str | None = None) -> dict:
    return SlicerWorkerSupervisor().assess_outcome(
        manifest(),
        outcome=outcome,
        context_id="context:process-fixture",
        current_context_id="context:process-fixture",
        peak_memory_bytes=0,
        disk_written_bytes=0,
        artifact_digest=artifact_digest,
    )


def isolated_python(source: str) -> list[str]:
    return [sys.executable, "-I", "-c", source]


def test_real_process_completion_produces_non_authoritative_evidence(
    tmp_path: Path,
) -> None:
    completed = subprocess.run(
        isolated_python("raise SystemExit(0)"),
        check=False,
        capture_output=True,
        stdin=subprocess.DEVNULL,
        timeout=1,
    )
    outcome = "completed" if completed.returncode == 0 else "crashed"

    result = assess(tmp_path, outcome, "a" * 64)

    assert result["status"] == "succeeded"
    assert result["artifact_accepted"] is True
    assert result["can_upload"] is False
    assert result["can_start_print"] is False


def test_real_process_crash_fails_closed(tmp_path: Path) -> None:
    completed = subprocess.run(
        isolated_python("raise SystemExit(23)"),
        check=False,
        capture_output=True,
        stdin=subprocess.DEVNULL,
        timeout=1,
    )
    outcome = "completed" if completed.returncode == 0 else "crashed"

    result = assess(tmp_path, outcome)

    assert completed.returncode == 23
    assert result["status"] == "failed_closed"
    assert result["reason"] == "worker_crashed"
    assert result["artifact_accepted"] is False


def test_real_process_timeout_fails_closed(tmp_path: Path) -> None:
    try:
        subprocess.run(
            isolated_python("import time; time.sleep(10)"),
            check=False,
            capture_output=True,
            stdin=subprocess.DEVNULL,
            timeout=0.1,
        )
    except subprocess.TimeoutExpired:
        outcome = "timed_out"
    else:
        outcome = "completed"

    result = assess(tmp_path, outcome)

    assert result["status"] == "failed_closed"
    assert result["reason"] == "worker_timed_out"
    assert result["retry_requires_fresh_context"] is True


def test_real_process_cancellation_fails_closed(tmp_path: Path) -> None:
    process = subprocess.Popen(
        isolated_python("import time; time.sleep(10)"),
        stdin=subprocess.DEVNULL,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    try:
        process.terminate()
        process.wait(timeout=1)
    finally:
        if process.poll() is None:
            process.kill()
            process.wait(timeout=1)

    result = assess(tmp_path, "cancelled")

    assert process.returncode != 0
    assert result["status"] == "failed_closed"
    assert result["reason"] == "worker_cancelled"
    assert result["worker_reuse_allowed"] is False


def test_supervisor_evidence_is_validated_before_worker_acceptance(
    tmp_path: Path,
) -> None:
    evidence = LocalProcessSupervisor().run(
        isolated_python("raise SystemExit(0)"),
        cwd=tmp_path,
        timeout_seconds=1,
    )

    result = SlicerWorkerSupervisor().assess_process_evidence(
        manifest(),
        evidence,
        context_id="context:process-fixture",
        current_context_id="context:process-fixture",
        peak_memory_bytes=0,
        disk_written_bytes=0,
        artifact_digest="a" * 64,
    )

    assert result["status"] == "succeeded"
    assert result["artifact_accepted"] is True
    assert result["can_upload"] is False


def test_supervisor_rejects_authoritative_process_evidence(tmp_path: Path) -> None:
    evidence = LocalProcessSupervisor().run(
        isolated_python("raise SystemExit(0)"),
        cwd=tmp_path,
        timeout_seconds=1,
    )
    evidence["release_authority_granted"] = True

    with pytest.raises(ValueError, match="unsafe authority"):
        SlicerWorkerSupervisor().assess_process_evidence(
            manifest(),
            evidence,
            context_id="context:process-fixture",
            current_context_id="context:process-fixture",
            peak_memory_bytes=0,
            disk_written_bytes=0,
            artifact_digest="a" * 64,
        )
