"""Local-first STEP/3MF quarantine assessment."""

from __future__ import annotations

from hashlib import sha256
from pathlib import Path, PurePosixPath
from typing import Any
from zipfile import BadZipFile, ZipFile


class ImportAssessmentError(ValueError):
    """Raised when an input cannot be safely assessed."""


class ImportQuarantine:
    """Assess supported files without extracting them or granting authority."""

    def assess(self, source: str | Path) -> dict[str, Any]:
        path = Path(source)
        if not path.is_file():
            raise ImportAssessmentError("input file does not exist")
        format_name = path.suffix.lower().lstrip(".")
        if format_name not in {"step", "stp", "3mf"}:
            raise ImportAssessmentError("only STEP/STP and 3MF are supported")

        digest = sha256(path.read_bytes()).hexdigest()
        ambiguities: list[str] = []
        hostile_checked = False
        traversal_checked = False
        decision = "accepted"

        if format_name == "3mf":
            hostile_checked = True
            traversal_checked = True
            try:
                with ZipFile(path) as archive:
                    names = archive.namelist()
                    if not names:
                        raise ImportAssessmentError("3MF archive is empty")
                    unsafe = [name for name in names if self._unsafe_member(name)]
                    if unsafe:
                        raise ImportAssessmentError("3MF archive contains unsafe paths")
                    if "3D/3dmodel.model" not in names:
                        ambiguities.append("standard 3MF model part is missing")
                        decision = "needs_user_resolution"
            except BadZipFile as exc:
                raise ImportAssessmentError("3MF input is not a valid archive") from exc
        else:
            hostile_checked = True
            header = path.read_bytes()[:4096].upper()
            if b"ISO-10303-21" not in header:
                raise ImportAssessmentError("STEP header is missing or malformed")

        return {
            "assessment_id": f"sha256:{digest}",
            "format": format_name,
            "source_digest": digest,
            "quarantine": {
                "isolated": True,
                "hostile_content_checked": hostile_checked,
                "path_traversal_checked": traversal_checked,
            },
            "decision": decision,
            "ambiguities": ambiguities,
            "normalized_digest": None,
            "can_authorize_production": False,
        }

    @staticmethod
    def _unsafe_member(name: str) -> bool:
        normalized = name.replace("\\", "/")
        member = PurePosixPath(normalized)
        return (
            member.is_absolute()
            or ".." in member.parts
            or (len(normalized) >= 2 and normalized[1] == ":")
        )
