"""Minimal local Forge bootstrap smoke entry point."""

from __future__ import annotations

import argparse


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="python -m forge")
    parser.add_argument(
        "--once",
        action="store_true",
        help="validate the local contract bootstrap without starting services",
    )
    args = parser.parse_args(argv)
    if not args.once:
        parser.error("--once is required for the contract-only bootstrap")
    print("FORGE local bootstrap ready; physical dispatch remains disabled")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
