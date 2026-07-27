"""Tests for wheel-to-published-source integrity verification."""

from pathlib import Path
from zipfile import ZipFile

import pytest

from scripts.verify_wheel_source import (
    WheelSourceVerificationError,
    verify_wheel_source,
)


def source(tmp_path: Path) -> Path:
    root = tmp_path / "forge"
    root.mkdir()
    (root / "__init__.py").write_bytes(b'"""FORGE."""\n')
    (root / "runtime.py").write_bytes(b"VALUE = 1\n")
    return root


def wheel(tmp_path: Path, files: dict[str, bytes]) -> Path:
    path = tmp_path / "forge-1.0-py3-none-any.whl"
    with ZipFile(path, "w") as archive:
        for name, content in files.items():
            archive.writestr(name, content)
    return path


def test_exact_wheel_source_match_produces_bounded_evidence(tmp_path: Path) -> None:
    root = source(tmp_path)
    path = wheel(
        tmp_path,
        {
            "forge/__init__.py": (root / "__init__.py").read_bytes(),
            "forge/runtime.py": (root / "runtime.py").read_bytes(),
            "forge-1.0.dist-info/METADATA": b"Name: forge\n",
        },
    )

    evidence = verify_wheel_source(path, root)

    assert evidence["all_python_sources_match"] is True
    assert evidence["python_file_count"] == 2
    assert len(evidence["source_manifest_digest"]) == 64
    assert evidence["proves_complete_release_source"] is False


@pytest.mark.parametrize(
    ("files", "message"),
    [
        (
            {"forge/__init__.py": b'"""FORGE."""\n'},
            "missing: forge/runtime.py",
        ),
        (
            {
                "forge/__init__.py": b'"""FORGE."""\n',
                "forge/runtime.py": b"VALUE = 1\n",
                "forge/hidden.py": b"SECRET = True\n",
            },
            "extra: forge/hidden.py",
        ),
        (
            {
                "forge/__init__.py": b'"""FORGE."""\n',
                "forge/runtime.py": b"VALUE = 2\n",
            },
            "mismatched: forge/runtime.py",
        ),
    ],
)
def test_rejects_missing_extra_or_changed_python(
    tmp_path: Path, files: dict[str, bytes], message: str
) -> None:
    root = source(tmp_path)
    path = wheel(tmp_path, files)

    with pytest.raises(WheelSourceVerificationError, match=message):
        verify_wheel_source(path, root)
