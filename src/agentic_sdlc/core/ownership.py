"""Ownership rules: managed | generated | owned."""

from __future__ import annotations

from hashlib import sha256
from pathlib import Path

from agentic_sdlc.core.models import DesiredFile, FileClass, Manifest


def content_sha256(content: str) -> str:
    return sha256(content.encode("utf-8")).hexdigest()


def file_sha256(path: Path) -> str:
    return sha256(path.read_bytes()).hexdigest()


def should_write(
    item: DesiredFile,
    root: Path,
    *,
    manifest: Manifest | None,
    force: bool,
) -> tuple[bool, str | None]:
    """Return (write, skip_reason)."""
    dest = root / item.dest
    exists = dest.is_file()

    if item.classification is FileClass.GENERATED:
        return True, None

    if item.classification is FileClass.OWNED:
        if exists:
            return False, "owned_exists"
        return True, None

    # managed
    if not exists:
        return True, None
    if force:
        return True, None
    recorded = manifest.file_by_path(item.dest) if manifest else None
    if recorded is None:
        return False, "managed_untracked"
    current = file_sha256(dest)
    if current != recorded.sha256:
        return False, "hash_drift"
    # hash matches last write: refresh if catalog content changed
    desired_hash = content_sha256(item.content)
    if current == desired_hash:
        return False, "unchanged"
    return True, None
