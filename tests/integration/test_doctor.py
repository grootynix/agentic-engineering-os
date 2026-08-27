from __future__ import annotations

import json
import shutil
from pathlib import Path

from tests.conftest import FIXTURES
from typer.testing import CliRunner

from agentic_sdlc.cli import app

runner = CliRunner()


def test_doctor_ok(tmp_path: Path) -> None:
    shutil.copytree(FIXTURES / "python-uv", tmp_path, dirs_exist_ok=True)
    (tmp_path / ".git").mkdir()
    init = runner.invoke(app, ["init", "--path", str(tmp_path)])
    assert init.exit_code == 0, init.output
    result = runner.invoke(app, ["doctor", "--path", str(tmp_path), "--json"])
    assert result.exit_code == 0, result.output
    payload = json.loads(result.stdout)
    assert payload["overall"] == "OK"
    assert payload["issues"] == []


def test_mutate_managed_degraded(tmp_path: Path) -> None:
    shutil.copytree(FIXTURES / "python-uv", tmp_path, dirs_exist_ok=True)
    (tmp_path / ".git").mkdir()
    init = runner.invoke(app, ["init", "--path", str(tmp_path)])
    assert init.exit_code == 0, init.output
    agents = tmp_path / "AGENTS.md"
    agents.write_text(agents.read_text(encoding="utf-8") + "\nuser edit\n", encoding="utf-8")
    result = runner.invoke(app, ["doctor", "--path", str(tmp_path), "--json"])
    assert result.exit_code == 0, result.output
    payload = json.loads(result.stdout)
    assert payload["overall"] == "DEGRADED"
    codes = [i["code"] for i in payload["issues"]]
    assert "HASH_DRIFT" in codes


def test_doctor_fail_without_manifest(tmp_path: Path) -> None:
    result = runner.invoke(app, ["doctor", "--path", str(tmp_path), "--json"])
    assert result.exit_code == 1
    payload = json.loads(result.stdout)
    assert payload["overall"] == "FAIL"
    assert any(i["code"] == "MANIFEST_MISSING" for i in payload["issues"])


def test_doctor_stack_ambiguous(tmp_path: Path) -> None:
    shutil.copytree(FIXTURES / "mixed", tmp_path, dirs_exist_ok=True)
    (tmp_path / ".git").mkdir()
    init = runner.invoke(app, ["init", "--path", str(tmp_path)])
    assert init.exit_code == 0, init.output
    result = runner.invoke(app, ["doctor", "--path", str(tmp_path), "--json"])
    assert result.exit_code == 0, result.output
    payload = json.loads(result.stdout)
    codes = [i["code"] for i in payload["issues"]]
    assert "STACK_AMBIGUOUS" in codes
    assert payload["overall"] == "DEGRADED"
