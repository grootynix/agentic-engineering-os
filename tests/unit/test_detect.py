from __future__ import annotations

from pathlib import Path

from tests.conftest import FIXTURES

from agentic_sdlc.core.detect import detect_stack


def test_detect_python_uv() -> None:
    report = detect_stack(FIXTURES / "python-uv")
    assert report.primary == "python"
    assert report.language == "python"
    assert report.confidence == "high"
    assert report.ambiguous is False
    assert "pyproject.toml" in report.markers


def test_detect_typescript_react_vitest() -> None:
    report = detect_stack(FIXTURES / "typescript-react-vitest")
    assert report.primary == "typescript"
    assert report.confidence == "high"
    assert "package.json" in report.markers
    assert "package.json:react" in report.markers
    assert "package.json:vitest" in report.markers


def test_detect_go() -> None:
    report = detect_stack(FIXTURES / "go")
    assert report.primary == "go"
    assert report.language == "go"
    assert report.confidence == "high"


def test_detect_empty() -> None:
    report = detect_stack(FIXTURES / "empty")
    assert report.primary == "unknown"
    assert report.confidence == "low"
    assert report.ambiguous is False


def test_detect_mixed_ambiguous() -> None:
    report = detect_stack(FIXTURES / "mixed")
    assert report.ambiguous is True
    assert report.confidence == "low"
    assert report.primary in {"python", "typescript"}
    assert "python" in report.scores
    assert "typescript" in report.scores


def test_detect_harness_presence(tmp_path: Path) -> None:
    (tmp_path / ".cursor").mkdir()
    (tmp_path / ".claude").mkdir()
    (tmp_path / "AGENTS.md").write_text("# hi\n", encoding="utf-8")
    (tmp_path / "CLAUDE.md").write_text("# hi\n", encoding="utf-8")
    report = detect_stack(tmp_path)
    assert report.harness.cursor_dir is True
    assert report.harness.claude_dir is True
    assert report.harness.agents_md is True
    assert report.harness.claude_md is True
