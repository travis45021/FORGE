"""Hostile 3MF fixture tests for pre-slicer quarantine."""

import stat
from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile, ZipInfo

import pytest

from forge.fas.imports import ImportAssessmentError, ImportQuarantine


def assess_archive(path: Path, members: dict[str, str]) -> dict:
    with ZipFile(path, "w") as archive:
        for name, content in members.items():
            archive.writestr(name, content)
    return ImportQuarantine().assess(path)


@pytest.mark.parametrize(
    "unsafe_name",
    [
        "/absolute.txt",
        "C:/drive-path.txt",
        "3D/../../outside.txt",
        r"3D\..\outside.txt",
    ],
)
def test_rejects_unsafe_member_path(tmp_path: Path, unsafe_name: str) -> None:
    with pytest.raises(ImportAssessmentError, match="unsafe paths"):
        assess_archive(
            tmp_path / "unsafe.3mf",
            {
                "3D/3dmodel.model": "<model><resources/><build/></model>",
                unsafe_name: "hostile",
            },
        )


def test_rejects_symbolic_link_member(tmp_path: Path) -> None:
    path = tmp_path / "symlink.3mf"
    with ZipFile(path, "w") as archive:
        archive.writestr("3D/3dmodel.model", "<model><resources/><build/></model>")
        link = ZipInfo("3D/link")
        link.create_system = 3
        link.external_attr = (stat.S_IFLNK | 0o777) << 16
        archive.writestr(link, "../outside")

    with pytest.raises(ImportAssessmentError, match="symbolic links"):
        ImportQuarantine().assess(path)


def test_rejects_high_compression_ratio(tmp_path: Path) -> None:
    path = tmp_path / "compression-bomb.3mf"
    with ZipFile(path, "w", compression=ZIP_DEFLATED) as archive:
        archive.writestr("3D/3dmodel.model", b" " * 2_000_000)

    with pytest.raises(ImportAssessmentError, match="compression ratio"):
        ImportQuarantine().assess(path)


@pytest.mark.parametrize(
    "declaration",
    [
        '<!DOCTYPE model SYSTEM "file:///etc/passwd"><model/>',
        (
            '<!DOCTYPE model [<!ENTITY xxe SYSTEM "file:///etc/passwd">]>'
            "<model>&xxe;</model>"
        ),
    ],
)
def test_rejects_xml_doctype_and_entities(tmp_path: Path, declaration: str) -> None:
    with pytest.raises(ImportAssessmentError, match="forbidden XML"):
        assess_archive(
            tmp_path / "xml-attack.3mf",
            {"3D/3dmodel.model": declaration},
        )
