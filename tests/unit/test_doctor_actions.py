from __future__ import annotations

import json
from pathlib import Path
from shutil import copytree

import yaml
from tests.conftest import FIXTURES
from typer.testing import CliRunner

from agentic_sdlc.cli import app
from agentic_sdlc.core.doctor import run_doctor
from agentic_sdlc.core.models import Severity

runner = CliRunner()


def test_manifest_missing_has_action(tmp_path: Path) -> None:
    report = run_doctor(tmp_path)
    missing = next(i for i in report.issues if i.code == "MANIFEST_MISSING")
    assert missing.action
    assert "init" in missing.action
    assert missing.severity is Severity.ERROR


def test_doctor_human_actionables(tmp_path: Path) -> None:
    result = runner.invoke(app, ["doctor", "--path", str(tmp_path)])
    assert result.exit_code == 1
    assert "Actionables:" in result.output
    assert "MANIFEST_MISSING" in result.output
    assert "agentic-sdlc init" in result.output


def test_doctor_json_includes_action(tmp_path: Path) -> None:
    result = runner.invoke(app, ["doctor", "--path", str(tmp_path), "--json"])
    payload = json.loads(result.stdout)
    issue = next(i for i in payload["issues"] if i["code"] == "MANIFEST_MISSING")
    assert issue["code"] == "MANIFEST_MISSING"
    assert issue["action"]
    assert "init" in issue["action"]


def test_hash_drift_action(tmp_path: Path) -> None:
    copytree(FIXTURES / "python-uv", tmp_path, dirs_exist_ok=True)
    (tmp_path / ".git").mkdir()
    assert runner.invoke(app, ["init", "--path", str(tmp_path)]).exit_code == 0
    agents = tmp_path / "AGENTS.md"
    agents.write_text(agents.read_text(encoding="utf-8") + "\nedit\n", encoding="utf-8")
    report = run_doctor(tmp_path)
    drift = next(i for i in report.issues if i.code == "HASH_DRIFT")
    assert drift.action
    assert "--force" in drift.action
    assert drift.path == "AGENTS.md"


def test_stack_unknown_action(tmp_path: Path) -> None:
    (tmp_path / ".agentic").mkdir()
    (tmp_path / ".agentic" / "manifest.yaml").write_text(
        "[]\n",
        encoding="utf-8",
    )
    report = run_doctor(tmp_path)
    codes = {i.code for i in report.issues}
    assert "MANIFEST_INVALID" in codes
    invalid = next(i for i in report.issues if i.code == "MANIFEST_INVALID")
    assert invalid.action
    unknown = next(i for i in report.issues if i.code == "STACK_UNKNOWN")
    assert unknown.action


def test_profile_missing_action(tmp_path: Path) -> None:
    copytree(FIXTURES / "python-uv", tmp_path, dirs_exist_ok=True)
    (tmp_path / ".git").mkdir()
    assert runner.invoke(app, ["init", "--path", str(tmp_path)]).exit_code == 0
    man = tmp_path / ".agentic" / "manifest.yaml"
    data = yaml.safe_load(man.read_text(encoding="utf-8"))
    data["profile"] = "does-not-exist"
    man.write_text(yaml.safe_dump(data), encoding="utf-8")
    report = run_doctor(tmp_path)
    missing = next(i for i in report.issues if i.code == "PROFILE_MISSING")
    assert missing.action
    assert "standard" in missing.action


def test_version_mismatch_action(tmp_path: Path) -> None:
    copytree(FIXTURES / "python-uv", tmp_path, dirs_exist_ok=True)
    (tmp_path / ".git").mkdir()
    assert runner.invoke(app, ["init", "--path", str(tmp_path)]).exit_code == 0
    man = tmp_path / ".agentic" / "manifest.yaml"
    data = yaml.safe_load(man.read_text(encoding="utf-8"))
    data["framework"]["version"] = "0.0.0"
    man.write_text(yaml.safe_dump(data), encoding="utf-8")
    report = run_doctor(tmp_path)
    mismatch = next(i for i in report.issues if i.code == "VERSION_MISMATCH")
    assert mismatch.action


def test_path_missing_action(tmp_path: Path) -> None:
    copytree(FIXTURES / "python-uv", tmp_path, dirs_exist_ok=True)
    (tmp_path / ".git").mkdir()
    assert runner.invoke(app, ["init", "--path", str(tmp_path)]).exit_code == 0
    (tmp_path / "AGENTS.md").unlink()
    report = run_doctor(tmp_path)
    missing = next(i for i in report.issues if i.code == "PATH_MISSING")
    assert missing.action
    assert "init" in missing.action


def test_init_prints_actionables_when_degraded(tmp_path: Path) -> None:
    copytree(FIXTURES / "mixed", tmp_path, dirs_exist_ok=True)
    (tmp_path / ".git").mkdir()
    result = runner.invoke(app, ["init", "--path", str(tmp_path)])
    assert "Actionables:" in result.output
    assert "STACK_AMBIGUOUS" in result.output
