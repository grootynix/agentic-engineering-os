#!/usr/bin/env python3
"""Build a one-file agentic-sdlc binary with the catalog bundled."""

from __future__ import annotations

import sys
from pathlib import Path

import PyInstaller.__main__

ROOT = Path(__file__).resolve().parent.parent
SEP = ";" if sys.platform == "win32" else ":"
ENTRY = ROOT / "src" / "agentic_sdlc" / "__main__.py"
CATALOG = ROOT / "catalog"


def main() -> None:
    PyInstaller.__main__.run(
        [
            str(ENTRY),
            "--onefile",
            "--name",
            "agentic-sdlc",
            "--noconfirm",
            "--clean",
            f"--add-data={CATALOG}{SEP}catalog",
            "--hidden-import=agentic_sdlc",
            "--hidden-import=agentic_sdlc.cli",
            "--hidden-import=yaml",
            "--hidden-import=typer",
            "--hidden-import=pydantic",
            "--collect-submodules=agentic_sdlc",
        ]
    )


if __name__ == "__main__":
    main()
