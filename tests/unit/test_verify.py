from __future__ import annotations

from pathlib import Path

from agentic_sdlc.core.models import OverallStatus
from agentic_sdlc.core.verify import CheckStatus, load_check_specs, run_verify


def _path(tmp_path: Path, monkeypatch) -> Path:
    bindir = tmp_path / "bin"
    bindir.mkdir()
    monkeypatch.setenv("PATH", str(bindir))
    monkeypatch.delenv("VIRTUAL_ENV", raising=False)
    return bindir


def _script(path: Path, body: str) -> None:
    path.write_text(f"#!/bin/sh\n{body}\n", encoding="utf-8")
    path.chmod(0o755)


def test_check_catalog_loads() -> None:
    specs = load_check_specs()
    ids = [s.id for s in specs]
    assert "python.ruff-lint" in ids
    assert "python.pytest" in ids


def test_unknown_stack_degraded(tmp_path: Path, monkeypatch) -> None:
    _path(tmp_path, monkeypatch)
    report = run_verify(tmp_path)
    assert report.stack == "unknown"
    assert report.overall is OverallStatus.DEGRADED
    assert report.checks == []


def test_python_skips_missing_tools(tmp_path: Path, monkeypatch) -> None:
    _path(tmp_path, monkeypatch)
    (tmp_path / "pyproject.toml").write_text("[project]\nname='demo'\n", encoding="utf-8")
    (tmp_path / "src").mkdir()
    (tmp_path / "tests").mkdir()
    report = run_verify(tmp_path)
    assert report.stack == "python"
    assert report.overall is OverallStatus.DEGRADED
    by_id = {c.id: c for c in report.checks}
    assert by_id["python.ruff-lint"].status is CheckStatus.SKIP
    assert by_id["python.pytest"].status is CheckStatus.SKIP
    assert by_id["python.mypy"].status is CheckStatus.SKIP


def test_python_ruff_and_pytest_pass(tmp_path: Path, monkeypatch) -> None:
    bindir = _path(tmp_path, monkeypatch)
    _script(bindir / "ruff", "exit 0")
    _script(bindir / "pytest", "exit 0")
    (tmp_path / "pyproject.toml").write_text("[project]\nname='demo'\n", encoding="utf-8")
    (tmp_path / "src").mkdir()
    (tmp_path / "tests").mkdir()
    report = run_verify(tmp_path)
    by_id = {c.id: c for c in report.checks}
    assert by_id["python.ruff-lint"].status is CheckStatus.PASS
    assert by_id["python.pytest"].status is CheckStatus.PASS
    assert report.overall is OverallStatus.OK


def test_python_ruff_fail(tmp_path: Path, monkeypatch) -> None:
    bindir = _path(tmp_path, monkeypatch)
    _script(bindir / "ruff", "echo lint; exit 1")
    _script(bindir / "pytest", "exit 0")
    (tmp_path / "pyproject.toml").write_text("[project]\nname='demo'\n", encoding="utf-8")
    (tmp_path / "src").mkdir()
    (tmp_path / "tests").mkdir()
    report = run_verify(tmp_path)
    assert report.overall is OverallStatus.FAIL
    assert not report.ok
    lint = next(c for c in report.checks if c.id == "python.ruff-lint")
    assert lint.status is CheckStatus.FAIL
    assert lint.action
