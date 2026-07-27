"""Verify that a FORGE wheel contains the exact published Python source."""

from __future__ import annotations

import argparse
import json
from hashlib import sha256
from pathlib import Path
from zipfile import BadZipFile, ZipFile


class WheelSourceVerificationError(ValueError):
    """Raised when packaged Python differs from the source tree."""


def verify_wheel_source(wheel: Path, source_root: Path) -> dict:
    """Compare every packaged FORGE Python file byte-for-byte with source."""
    wheel = wheel.resolve()
    source_root = source_root.resolve()
    if wheel.suffix != ".whl" or not wheel.is_file():
        raise WheelSourceVerificationError("wheel path must name an existing .whl")
    if not source_root.is_dir():
        raise WheelSourceVerificationError("source root must be a directory")

    expected = {
        f"{source_root.name}/{path.relative_to(source_root).as_posix()}": path.read_bytes()
        for path in sorted(source_root.rglob("*.py"))
        if path.is_file()
    }
    if not expected:
        raise WheelSourceVerificationError("source root contains no Python files")

    try:
        with ZipFile(wheel) as archive:
            packaged_names = sorted(
                name
                for name in archive.namelist()
                if name.startswith("forge/") and name.endswith(".py")
            )
            packaged = {name: archive.read(name) for name in packaged_names}
    except (BadZipFile, KeyError) as exc:
        raise WheelSourceVerificationError("wheel archive is invalid") from exc

    missing = sorted(set(expected) - set(packaged))
    extra = sorted(set(packaged) - set(expected))
    mismatched = sorted(
        name
        for name in set(expected) & set(packaged)
        if expected[name] != packaged[name]
    )
    if missing or extra or mismatched:
        details = []
        if missing:
            details.append(f"missing: {', '.join(missing)}")
        if extra:
            details.append(f"extra: {', '.join(extra)}")
        if mismatched:
            details.append(f"mismatched: {', '.join(mismatched)}")
        raise WheelSourceVerificationError("; ".join(details))

    files = [
        {
            "path": name,
            "sha256": sha256(expected[name]).hexdigest(),
            "size_bytes": len(expected[name]),
        }
        for name in sorted(expected)
    ]
    canonical = json.dumps(
        files,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return {
        "schema_version": "1.0.0",
        "wheel": wheel.name,
        "source_root": source_root.name,
        "python_file_count": len(files),
        "files": files,
        "source_manifest_digest": sha256(canonical).hexdigest(),
        "all_python_sources_match": True,
        "proves_complete_release_source": False,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("wheel", type=Path)
    parser.add_argument("--source-root", type=Path, default=Path("src/forge"))
    arguments = parser.parse_args()
    try:
        evidence = verify_wheel_source(arguments.wheel, arguments.source_root)
    except WheelSourceVerificationError as exc:
        parser.error(str(exc))
    print(json.dumps(evidence, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
