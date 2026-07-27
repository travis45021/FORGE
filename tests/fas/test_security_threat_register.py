"""Integrity checks for the fail-closed FORGE v1 threat register."""

import json
from pathlib import Path

from jsonschema import Draft202012Validator

ROOT = Path(__file__).resolve().parents[2]
REGISTER_PATH = ROOT / "docs" / "security" / "v1-threat-register.json"
SCHEMA_PATH = ROOT / "schemas" / "fas" / "security-threat-register.schema.json"


def load(path: Path) -> dict:
    value = json.loads(path.read_text(encoding="utf-8"))
    assert isinstance(value, dict)
    return value


def test_register_matches_strict_schema_and_has_unique_threats() -> None:
    schema = load(SCHEMA_PATH)
    register = load(REGISTER_PATH)
    Draft202012Validator.check_schema(schema)
    Draft202012Validator(schema).validate(register)

    threat_ids = [threat["threat_id"] for threat in register["threats"]]
    assert len(threat_ids) == len(set(threat_ids))


def test_every_controlled_threat_has_existing_evidence() -> None:
    register = load(REGISTER_PATH)
    for threat in register["threats"]:
        if threat["status"] == "controlled":
            assert threat["evidence_refs"]
        for reference in threat["evidence_refs"]:
            assert (ROOT / reference).is_file(), (
                f"{threat['threat_id']} references missing evidence: {reference}"
            )


def test_open_release_blockers_keep_security_gate_false() -> None:
    register = load(REGISTER_PATH)
    blockers = [
        threat
        for threat in register["threats"]
        if threat["release_blocking"] is True and threat["status"] != "controlled"
    ]
    assert blockers
    assert register["status"] == "incomplete"
    assert register["security_gate_passed"] is False
    assert register["release_authorized"] is False
