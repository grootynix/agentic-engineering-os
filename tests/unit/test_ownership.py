from __future__ import annotations

from pathlib import Path

from agentic_sdlc.core.manifest import now_utc
from agentic_sdlc.core.models import (
    DesiredFile,
    FileClass,
    FrameworkInfo,
    Manifest,
    ManifestFile,
    StackReport,
)
from agentic_sdlc.core.ownership import content_sha256, should_write


def _item(dest: str, content: str, classification: FileClass) -> DesiredFile:
    return DesiredFile(
        dest=dest,
        content=content,
        classification=classification,
        adapter="shared",
        source="templates/x",
    )


def _manifest(path: str, content: str, classification: FileClass) -> Manifest:
    return Manifest(
        framework=FrameworkInfo(name="agentic-sdlc", version="0.1.0"),
        profile="standard",
        stack=StackReport(primary="python", language="python", confidence="high"),
        files=[
            ManifestFile(
                path=path,
                classification=classification,
                sha256=content_sha256(content),
                source="templates/x",
            )
        ],
        created_at=now_utc(),
    )


def test_managed_writes_when_missing(tmp_path: Path) -> None:
    item = _item("AGENTS.md", "hello", FileClass.MANAGED)
    write, reason = should_write(item, tmp_path, manifest=None, force=False)
    assert write is True
    assert reason is None


def test_managed_skips_on_hash_drift(tmp_path: Path) -> None:
    original = "hello"
    (tmp_path / "AGENTS.md").write_text("mutated", encoding="utf-8")
    item = _item("AGENTS.md", original, FileClass.MANAGED)
    manifest = _manifest("AGENTS.md", original, FileClass.MANAGED)
    write, reason = should_write(item, tmp_path, manifest=manifest, force=False)
    assert write is False
    assert reason == "hash_drift"


def test_managed_force_overwrites_drift(tmp_path: Path) -> None:
    original = "hello"
    (tmp_path / "AGENTS.md").write_text("mutated", encoding="utf-8")
    item = _item("AGENTS.md", original, FileClass.MANAGED)
    manifest = _manifest("AGENTS.md", original, FileClass.MANAGED)
    write, reason = should_write(item, tmp_path, manifest=manifest, force=True)
    assert write is True
    assert reason is None


def test_generated_always_writes(tmp_path: Path) -> None:
    (tmp_path / ".agentic").mkdir()
    (tmp_path / ".agentic" / "INDEX.md").write_text("old", encoding="utf-8")
    item = _item(".agentic/INDEX.md", "new", FileClass.GENERATED)
    write, _ = should_write(item, tmp_path, manifest=None, force=False)
    assert write is True


def test_owned_skips_if_exists(tmp_path: Path) -> None:
    (tmp_path / ".agentic").mkdir()
    (tmp_path / ".agentic" / "config.yaml").write_text("user: true\n", encoding="utf-8")
    item = _item(".agentic/config.yaml", "profile: standard\n", FileClass.OWNED)
    write, reason = should_write(item, tmp_path, manifest=None, force=True)
    assert write is False
    assert reason == "owned_exists"
