"""Deterministic byte-to-contract tests for slicer artifact preflight."""

from pathlib import Path

import pytest

from forge.fas.preflight import ArtifactPreflight, PreflightError


def result(digest: str, *, context: str = "production") -> dict:
    return {
        "contract_version": "1.0",
        "request_id": f"request:{context}",
        "status": "succeeded",
        "context": context,
        "engine": {
            "name": "reviewed-engine",
            "version": "pinned",
            "source_digest": "c" * 64,
            "build_digest": "d" * 64,
        },
        "artifact_digest": digest,
        "warnings": [],
        "authority": {"can_upload": False, "can_start_print": False},
    }


def test_binds_output_bytes_to_result_digest(tmp_path: Path) -> None:
    import hashlib

    output = tmp_path / "production.gcode"
    output.write_bytes(b"G28\nM84\n")
    digest = hashlib.sha256(output.read_bytes()).hexdigest()

    evidence = ArtifactPreflight().inspect_slicer_output(
        output,
        result(digest),
        expected_request_id="request:production",
        expected_context="production",
    )

    assert evidence["status"] == "passed"
    assert evidence["output_digest_verified"] is True
    assert evidence["requires_twin_comparison"] is True
    assert evidence["can_upload"] is False
    assert evidence["can_start_print"] is False


def test_rejects_tampered_output_bytes(tmp_path: Path) -> None:
    output = tmp_path / "tampered.gcode"
    output.write_bytes(b"changed")

    with pytest.raises(PreflightError, match="recorded digest"):
        ArtifactPreflight().inspect_slicer_output(
            output,
            result("a" * 64),
            expected_request_id="request:production",
            expected_context="production",
        )


@pytest.mark.parametrize(
    ("expected_request", "expected_context", "message"),
    [
        ("request:new", "production", "different request"),
        ("request:production", "twin", "stale or wrong context"),
    ],
)
def test_rejects_stale_request_or_context(
    tmp_path: Path,
    expected_request: str,
    expected_context: str,
    message: str,
) -> None:
    import hashlib

    output = tmp_path / "stale.gcode"
    output.write_bytes(b"G28\n")
    digest = hashlib.sha256(output.read_bytes()).hexdigest()

    with pytest.raises(PreflightError, match=message):
        ArtifactPreflight().inspect_slicer_output(
            output,
            result(digest),
            expected_request_id=expected_request,
            expected_context=expected_context,
        )


def test_rejects_empty_output(tmp_path: Path) -> None:
    output = tmp_path / "empty.gcode"
    output.write_bytes(b"")

    with pytest.raises(PreflightError, match="must not be empty"):
        ArtifactPreflight().inspect_slicer_output(
            output,
            result("a" * 64),
            expected_request_id="request:production",
            expected_context="production",
        )
