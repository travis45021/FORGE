"""Local-first STEP/3MF quarantine assessment."""

from __future__ import annotations

import stat
from hashlib import sha256
from pathlib import Path, PurePosixPath
from typing import Any
from xml.etree import ElementTree
from zipfile import BadZipFile, ZipFile


class ImportAssessmentError(ValueError):
    """Raised when an input cannot be safely assessed."""


class ImportQuarantine:
    """Assess supported files without extracting them or granting authority."""

    MAX_ARCHIVE_MEMBERS = 10_000
    MAX_MEMBER_BYTES = 128 * 1024 * 1024
    MAX_TOTAL_BYTES = 512 * 1024 * 1024
    MAX_COMPRESSION_RATIO = 200
    MAX_STEP_BYTES = 64 * 1024 * 1024
    MAX_STEP_LINE_BYTES = 1024 * 1024

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
                    members = archive.infolist()
                    names = [member.filename for member in members]
                    if not names:
                        raise ImportAssessmentError("3MF archive is empty")
                    if len(members) > self.MAX_ARCHIVE_MEMBERS:
                        raise ImportAssessmentError("3MF archive has too many members")
                    if len(names) != len(set(names)):
                        raise ImportAssessmentError("3MF archive has duplicate members")
                    unsafe = [name for name in names if self._unsafe_member(name)]
                    if unsafe:
                        raise ImportAssessmentError("3MF archive contains unsafe paths")
                    if any(member.flag_bits & 0x1 for member in members):
                        raise ImportAssessmentError(
                            "encrypted 3MF members are not accepted"
                        )
                    if any(
                        stat.S_ISLNK(member.external_attr >> 16) for member in members
                    ):
                        raise ImportAssessmentError(
                            "3MF archive contains symbolic links"
                        )
                    if any(
                        member.file_size > self.MAX_MEMBER_BYTES for member in members
                    ):
                        raise ImportAssessmentError("3MF member exceeds size limit")
                    if (
                        sum(member.file_size for member in members)
                        > self.MAX_TOTAL_BYTES
                    ):
                        raise ImportAssessmentError("3MF archive exceeds size limit")
                    if any(
                        member.file_size > 1_000_000
                        and member.file_size
                        > max(member.compress_size, 1) * self.MAX_COMPRESSION_RATIO
                        for member in members
                    ):
                        raise ImportAssessmentError(
                            "3MF archive has an unsafe compression ratio"
                        )
                    if "3D/3dmodel.model" not in names:
                        ambiguities.append("standard 3MF model part is missing")
                        decision = "needs_user_resolution"
                        normalized_digest = None
                    else:
                        normalized_digest, model_ambiguities = (
                            self._normalize_3mf_model(archive.read("3D/3dmodel.model"))
                        )
                        ambiguities.extend(model_ambiguities)
                        if model_ambiguities:
                            decision = "needs_user_resolution"
            except BadZipFile as exc:
                raise ImportAssessmentError("3MF input is not a valid archive") from exc
        else:
            hostile_checked = True
            if path.stat().st_size > self.MAX_STEP_BYTES:
                raise ImportAssessmentError("STEP input exceeds size limit")
            raw = path.read_bytes()
            header = raw[:4096].upper()
            if b"ISO-10303-21" not in header:
                raise ImportAssessmentError("STEP header is missing or malformed")
            normalized_digest, step_ambiguities = self._normalize_step(raw)
            ambiguities.extend(step_ambiguities)
            if step_ambiguities:
                decision = "needs_user_resolution"

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
            "normalized_digest": normalized_digest,
            "normalization_version": "forge-import-v1",
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

    @staticmethod
    def _normalize_step(raw: bytes) -> tuple[str, list[str]]:
        if b"\x00" in raw:
            raise ImportAssessmentError("STEP input contains binary NUL data")
        if any(
            len(line) > ImportQuarantine.MAX_STEP_LINE_BYTES
            for line in raw.splitlines()
        ):
            raise ImportAssessmentError("STEP input contains an oversized line")
        try:
            text = raw.decode("utf-8-sig")
        except UnicodeDecodeError as exc:
            raise ImportAssessmentError("STEP input must be UTF-8 compatible") from exc
        canonical = (
            "\n".join(
                line.rstrip()
                for line in text.replace("\r\n", "\n").replace("\r", "\n").split("\n")
            ).strip()
            + "\n"
        )
        upper = canonical.upper()
        ambiguities = []
        if "HEADER;" not in upper:
            ambiguities.append("STEP HEADER section is missing")
        if "DATA;" not in upper:
            ambiguities.append("STEP DATA section is missing")
        if "END-ISO-10303-21;" not in upper:
            ambiguities.append("STEP end marker is missing")
        return sha256(canonical.encode("utf-8")).hexdigest(), ambiguities

    @staticmethod
    def _normalize_3mf_model(raw: bytes) -> tuple[str, list[str]]:
        upper = raw.upper()
        if b"<!DOCTYPE" in upper or b"<!ENTITY" in upper:
            raise ImportAssessmentError("3MF model contains forbidden XML declarations")
        try:
            root = ElementTree.fromstring(raw)
        except ElementTree.ParseError as exc:
            raise ImportAssessmentError("3MF model XML is malformed") from exc
        local_name = root.tag.rsplit("}", 1)[-1]
        if local_name != "model":
            raise ImportAssessmentError("3MF model root element is invalid")
        canonical = ElementTree.canonicalize(
            xml_data=raw.decode("utf-8-sig"), strip_text=True
        )
        child_names = {child.tag.rsplit("}", 1)[-1] for child in root}
        ambiguities = []
        if "resources" not in child_names:
            ambiguities.append("3MF model resources are missing")
        if "build" not in child_names:
            ambiguities.append("3MF build instructions are missing")
        return sha256(canonical.encode("utf-8")).hexdigest(), ambiguities
