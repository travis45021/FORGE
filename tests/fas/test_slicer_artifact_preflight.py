"""Deterministic byte-to-contract tests for slicer artifact preflight."""

from hashlib import sha256
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
        max_output_bytes=1_000_000,
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
            max_output_bytes=1_000_000,
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
            max_output_bytes=1_000_000,
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
            max_output_bytes=1_000_000,
        )


def test_malformed_artifact_metadata_becomes_review_findings() -> None:
    result = ArtifactPreflight().inspect(
        {
            "artifact_id": "artifact:malformed",
            "filename": "part.3mf",
            "format": "3mf",
            "digest": 123,
            "size_bytes": "large",
        }
    )

    assert result["status"] == "needs_review"
    assert "artifact size must be positive" in result["findings"]
    assert "artifact digest must be sha256" in result["findings"]


def test_rejects_output_over_explicit_limit(tmp_path: Path) -> None:
    output = tmp_path / "oversized.gcode"
    content = b"G28\n"
    output.write_bytes(content)

    with pytest.raises(PreflightError, match="disk limit"):
        ArtifactPreflight().inspect_slicer_output(
            output,
            result(sha256(content).hexdigest()),
            expected_request_id="request:production",
            expected_context="production",
            max_output_bytes=3,
        )


def test_rejects_output_changed_while_being_read(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    output = tmp_path / "changing.gcode"
    content = b"G28\n"
    output.write_bytes(content)
    original_read = Path.read_bytes

    def read_then_change(path: Path) -> bytes:
        value = original_read(path)
        path.write_bytes(value + b"M84\n")
        return value

    monkeypatch.setattr(Path, "read_bytes", read_then_change)

    with pytest.raises(PreflightError, match="changed during preflight"):
        ArtifactPreflight().inspect_slicer_output(
            output,
            result(sha256(content).hexdigest()),
            expected_request_id="request:production",
            expected_context="production",
            max_output_bytes=1_000_000,
        )
