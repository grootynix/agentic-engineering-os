"""Read/write `.agentic/manifest.yaml`."""

from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path

import yaml

from agentic_sdlc.core.models import Manifest

MANIFEST_REL = ".agentic/manifest.yaml"


def manifest_path(root: Path) -> Path:
    return root / MANIFEST_REL


def load_manifest(root: Path) -> Manifest | None:
    path = manifest_path(root)
    if not path.is_file():
        return None
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    return Manifest.model_validate(data)


def write_manifest(root: Path, manifest: Manifest) -> Path:
    path = manifest_path(root)
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = manifest.model_dump(mode="json", by_alias=True)
    path.write_text(
        yaml.safe_dump(payload, sort_keys=False, allow_unicode=True),
        encoding="utf-8",
    )
    return path


def now_utc() -> datetime:
    return datetime.now(UTC)
