from __future__ import annotations

import json

from typer.testing import CliRunner

from agentic_sdlc.cli import app

runner = CliRunner()


def test_hook_blocks_rm_json() -> None:
    payload = json.dumps({"command": "rm -rf /", "cwd": "."})
    result = runner.invoke(app, ["hook", "beforeShellExecution"], input=payload)
    assert result.exit_code == 0, result.output
    body = json.loads(result.stdout)
    assert body["permission"] == "deny"
    assert "rm-rf" in body["agent_message"]


def test_hook_precommit_exit_1(tmp_path) -> None:
    (tmp_path / ".git").mkdir()
    payload = json.dumps({"cwd": str(tmp_path)})
    result = runner.invoke(
        app,
        ["hook", "precommit", "tests/test_missing.py"],
        input=payload,
    )
    assert result.exit_code == 1
    assert "deleted" in result.output.lower()


def test_hook_claude_pretooluse() -> None:
    payload = json.dumps({"tool_name": "Bash", "tool_input": {"command": "pytest"}})
    result = runner.invoke(app, ["hook", "PreToolUse"], input=payload)
    assert result.exit_code == 0
    body = json.loads(result.stdout)
    assert body["hookSpecificOutput"]["permissionDecision"] == "allow"


def test_hook_invalid_json_fail_closed() -> None:
    result = runner.invoke(app, ["hook", "beforeShellExecution"], input="not-json")
    assert result.exit_code == 0
    body = json.loads(result.stdout)
    assert body["permission"] == "deny"
    assert "invalid-payload" in body["user_message"]
