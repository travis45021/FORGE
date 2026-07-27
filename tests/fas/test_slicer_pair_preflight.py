"""Tests binding production/twin output bytes to one successful worker pair."""

from copy import deepcopy
from hashlib import sha256
from pathlib import Path

import pytest

from forge.fas.preflight import ArtifactPreflight, PreflightError


def result(context: str, digest: str) -> dict:
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


def pair(production_digest: str, twin_digest: str) -> dict:
    outcomes = {}
    for context, digest in (
        ("production", production_digest),
        ("twin", twin_digest),
    ):
        outcomes[context] = {
            "worker_id": f"worker:{context}",
            "request_id": f"request:{context}",
            "context": context,
            "status": "succeeded",
            "artifact_digest": digest,
        }
    return {
        "status": "ready_for_preflight",
        "engine": {
            "name": "reviewed-engine",
            "version": "pinned",
            "source_digest": "c" * 64,
            "build_digest": "d" * 64,
        },
        "input_digest": "a" * 64,
        "profile_digest": "b" * 64,
        "production": outcomes["production"],
        "twin": outcomes["twin"],
        "artifacts_eligible_for_preflight": True,
        "can_compare": True,
        "can_upload": False,
        "can_start_print": False,
        "can_control_hardware": False,
    }


def output(path: Path, content: bytes) -> str:
    path.write_bytes(content)
    return sha256(content).hexdigest()


def test_successful_pair_advances_only_to_comparison(tmp_path: Path) -> None:
    production_path = tmp_path / "production.gcode"
    twin_path = tmp_path / "twin.gcode"
    production_digest = output(production_path, b"G28\nM84\n")
    twin_digest = output(twin_path, b"G28\nM84\n")

    evidence = ArtifactPreflight().inspect_worker_pair_outputs(
        pair(production_digest, twin_digest),
        production_path=production_path,
        production_result=result("production", production_digest),
        twin_path=twin_path,
        twin_result=result("twin", twin_digest),
    )

    assert evidence["status"] == "ready_for_comparison"
    assert evidence["pair_outcome_validated"] is True
    assert evidence["both_output_digests_verified"] is True
    assert evidence["can_upload"] is False
    assert evidence["can_start_print"] is False


def test_rejects_failed_pair_before_reading_outputs(tmp_path: Path) -> None:
    failed = pair("a" * 64, "b" * 64)
    failed["status"] = "failed_closed"
    failed["artifacts_eligible_for_preflight"] = False
    failed["can_compare"] = False

    with pytest.raises(PreflightError, match="not eligible"):
        ArtifactPreflight().inspect_worker_pair_outputs(
            failed,
            production_path=tmp_path / "missing-production",
            production_result={},
            twin_path=tmp_path / "missing-twin",
            twin_result={},
        )


def test_rejects_digest_not_recorded_by_pair(tmp_path: Path) -> None:
    production_path = tmp_path / "production.gcode"
    twin_path = tmp_path / "twin.gcode"
    production_digest = output(production_path, b"G28\n")
    twin_digest = output(twin_path, b"M84\n")
    mismatched = pair("f" * 64, twin_digest)

    with pytest.raises(PreflightError, match="successful worker outcome"):
        ArtifactPreflight().inspect_worker_pair_outputs(
            mismatched,
            production_path=production_path,
            production_result=result("production", production_digest),
            twin_path=twin_path,
            twin_result=result("twin", twin_digest),
        )


def test_rejects_output_from_different_engine(tmp_path: Path) -> None:
    production_path = tmp_path / "production.gcode"
    twin_path = tmp_path / "twin.gcode"
    production_digest = output(production_path, b"G28\n")
    twin_digest = output(twin_path, b"M84\n")
    production_result = result("production", production_digest)
    production_result["engine"]["version"] = "other"

    with pytest.raises(PreflightError, match="different reviewed engine"):
        ArtifactPreflight().inspect_worker_pair_outputs(
            pair(production_digest, twin_digest),
            production_path=production_path,
            production_result=production_result,
            twin_path=twin_path,
            twin_result=result("twin", twin_digest),
        )


def test_rejects_output_from_different_engine_build(tmp_path: Path) -> None:
    production_path = tmp_path / "production.gcode"
    twin_path = tmp_path / "twin.gcode"
    production_digest = output(production_path, b"G28\n")
    twin_digest = output(twin_path, b"M84\n")
    production_result = result("production", production_digest)
    production_result["engine"]["build_digest"] = "e" * 64

    with pytest.raises(PreflightError, match="different reviewed engine"):
        ArtifactPreflight().inspect_worker_pair_outputs(
            pair(production_digest, twin_digest),
            production_path=production_path,
            production_result=production_result,
            twin_path=twin_path,
            twin_result=result("twin", twin_digest),
        )


def test_pair_record_cannot_claim_upload_authority(tmp_path: Path) -> None:
    untrusted = deepcopy(pair("a" * 64, "b" * 64))
    untrusted["can_upload"] = True

    with pytest.raises(PreflightError, match="not eligible"):
        ArtifactPreflight().inspect_worker_pair_outputs(
            untrusted,
            production_path=tmp_path / "missing-production",
            production_result={},
            twin_path=tmp_path / "missing-twin",
            twin_result={},
        )
