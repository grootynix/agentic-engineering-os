from __future__ import annotations

import json
from pathlib import Path

from typer.testing import CliRunner

from agentic_sdlc.cli import app

runner = CliRunner()


def test_verify_json_degraded(tmp_path: Path, monkeypatch) -> None:
    bindir = tmp_path / "bin"
    bindir.mkdir()
    monkeypatch.setenv("PATH", str(bindir))
    (tmp_path / "pyproject.toml").write_text("[project]\nname='demo'\n", encoding="utf-8")
    (tmp_path / "src").mkdir()
    result = runner.invoke(app, ["verify", "--path", str(tmp_path), "--json"])
    assert result.exit_code == 0, result.output
    payload = json.loads(result.stdout)
    assert payload["overall"] == "DEGRADED"
    assert payload["stack"] == "python"


def test_verify_help() -> None:
    result = runner.invoke(app, ["verify", "--help"])
    assert result.exit_code == 0
    assert "skip" in result.output.lower() or "discover" in result.output.lower()
