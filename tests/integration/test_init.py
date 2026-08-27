from __future__ import annotations

import json
import shutil
from pathlib import Path

from tests.conftest import FIXTURES
from typer.testing import CliRunner

from agentic_sdlc.cli import app

runner = CliRunner()


def _stage(name: str, tmp_path: Path) -> Path:
    src = FIXTURES / name
    shutil.copytree(src, tmp_path, dirs_exist_ok=True)
    (tmp_path / ".git").mkdir(exist_ok=True)
    return tmp_path


def test_init_tmp_path(tmp_path: Path) -> None:
    _stage("python-uv", tmp_path)
    result = runner.invoke(app, ["init", "--path", str(tmp_path), "--json"])
    assert result.exit_code == 0, result.output
    payload = json.loads(result.stdout)
    assert payload["ok"] is True
    assert payload["profile"] == "standard"
    assert payload["stack"]["primary"] == "python"
    assert payload["doctor"]["overall"] == "OK"
    assert (tmp_path / "AGENTS.md").is_file()
    assert (tmp_path / "CLAUDE.md").is_file()
    assert (tmp_path / ".agentic" / "INDEX.md").is_file()
    assert (tmp_path / ".agentic" / "config.yaml").is_file()
    assert (tmp_path / ".agentic" / "manifest.yaml").is_file()
    assert (tmp_path / ".cursor" / "rules" / "agentic-os.mdc").is_file()
    assert (tmp_path / ".cursor" / "skills" / "using-agentic-sdlc" / "SKILL.md").is_file()
    assert (tmp_path / ".claude" / "skills" / "using-agentic-sdlc" / "SKILL.md").is_file()
    assert (tmp_path / ".cursor" / "rules" / "testing.mdc").is_file()
    assert (tmp_path / ".cursor" / "rules" / "engineering.mdc").is_file()
    assert (tmp_path / ".cursor" / "rules" / "documentation.mdc").is_file()
    assert (tmp_path / ".cursor" / "rules" / "python.mdc").is_file()
    assert (tmp_path / ".cursor" / "rules" / "typescript.mdc").is_file()
    assert (tmp_path / ".cursor" / "rules" / "release.mdc").is_file()
    assert (tmp_path / ".cursor" / "skills" / "cut-release" / "SKILL.md").is_file()
    assert (tmp_path / ".agentic" / "templates" / "Dockerfile").is_file()
    assert (tmp_path / ".cursor" / "skills" / "threat-model" / "SKILL.md").is_file()
    assert (tmp_path / ".cursor" / "agents" / "verifier.md").is_file()
    assert (tmp_path / ".claude" / "agents" / "architecture-reviewer.md").is_file()
    assert (tmp_path / ".cursor" / "hooks.json").is_file()
    assert (tmp_path / ".claude" / "settings.json").is_file()
    assert (tmp_path / ".pre-commit-config.yaml").is_file()
    assert (tmp_path / ".agentic" / "templates" / "ci-verify.yml").is_file()
    hooks = (tmp_path / ".cursor" / "hooks.json").read_text(encoding="utf-8")
    assert "agentic-sdlc hook" in hooks
    assert "failClosed" in hooks
    assert "scripts/" not in hooks
    assert ".venv/bin" in hooks
    mdc = (tmp_path / ".cursor" / "rules" / "agentic-os.mdc").read_text(encoding="utf-8")
    assert "alwaysApply: true" in mdc


def test_init_requires_git(tmp_path: Path) -> None:
    result = runner.invoke(app, ["init", "--path", str(tmp_path)])
    assert result.exit_code == 1
    assert "git" in result.output.lower() or "git" in (result.stderr or "").lower()


def test_init_force_without_git(tmp_path: Path) -> None:
    result = runner.invoke(app, ["init", "--path", str(tmp_path), "--force", "--json"])
    assert result.exit_code == 0, result.output
    payload = json.loads(result.stdout)
    assert payload["ok"] is True


def test_init_idempotent(tmp_path: Path) -> None:
    _stage("python-uv", tmp_path)
    first = runner.invoke(app, ["init", "--path", str(tmp_path), "--json"])
    assert first.exit_code == 0, first.output
    second = runner.invoke(app, ["init", "--path", str(tmp_path), "--json"])
    assert second.exit_code == 0, second.output
    payload = json.loads(second.stdout)
    assert "AGENTS.md" in payload["files_skipped"]
    assert ".agentic/INDEX.md" in payload["files_written"]


def test_owned_not_overwritten(tmp_path: Path) -> None:
    _stage("python-uv", tmp_path)
    runner.invoke(app, ["init", "--path", str(tmp_path)])
    config = tmp_path / ".agentic" / "config.yaml"
    config.write_text("profile: custom\n", encoding="utf-8")
    runner.invoke(app, ["init", "--path", str(tmp_path), "--force"])
    assert config.read_text(encoding="utf-8") == "profile: custom\n"
