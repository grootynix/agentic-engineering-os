from __future__ import annotations

from typer.testing import CliRunner

from agentic_sdlc import __version__
from agentic_sdlc.cli import app

runner = CliRunner()


def test_version() -> None:
    result = runner.invoke(app, ["--version"])
    assert result.exit_code == 0
    assert __version__ in result.stdout


def test_verify_not_implemented() -> None:
    result = runner.invoke(app, ["verify"])
    assert result.exit_code == 2
    assert "not implemented" in result.output.lower()


def test_update_not_implemented() -> None:
    result = runner.invoke(app, ["update"])
    assert result.exit_code == 2


def test_hook_help_exists() -> None:
    result = runner.invoke(app, ["hook", "--help"])
    assert result.exit_code == 0
    assert "policy" in result.output.lower() or "stdin" in result.output.lower()
