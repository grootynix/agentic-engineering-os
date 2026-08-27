from __future__ import annotations

import json
from pathlib import Path

from typer.testing import CliRunner

from agentic_sdlc.cli import app

runner = CliRunner()


def test_graph_json_actionables(tmp_path: Path) -> None:
    result = runner.invoke(app, ["graph", "--path", str(tmp_path), "--json"])
    assert result.exit_code == 0, result.output
    payload = json.loads(result.stdout)
    assert payload["name"] == "sdlc"
    assert payload["next_ids"] == ["intent"]
    intent = next(n for n in payload["nodes"] if n["id"] == "intent")
    assert intent["status"] == "ready"
    assert intent["action"]


def test_graph_human_actionables(tmp_path: Path) -> None:
    result = runner.invoke(app, ["graph", "--path", str(tmp_path)])
    assert result.exit_code == 0
    assert "Actionables:" in result.output
    assert "intent" in result.output


def test_graph_unknown_name(tmp_path: Path) -> None:
    result = runner.invoke(app, ["graph", "--path", str(tmp_path), "--name", "nope"])
    assert result.exit_code == 1
    err = (result.output + (result.stderr or "")).lower()
    assert "unknown graph" in err
