from __future__ import annotations

from pathlib import Path

from agentic_sdlc.core.policy import (
    HookRequest,
    PolicyAction,
    evaluate,
    load_hook_policy,
)


def test_policy_yaml_loads() -> None:
    policy = load_hook_policy()
    assert policy.dangerous_commands
    assert policy.secret_patterns


def test_blocks_rm_rf_root() -> None:
    decision = evaluate(
        HookRequest(event="beforeShellExecution", command="rm -rf /", cwd=".")
    )
    assert decision.action is PolicyAction.BLOCK
    assert "rm-rf" in decision.policy_id


def test_asks_force_push_main() -> None:
    decision = evaluate(
        HookRequest(
            event="beforeShellExecution",
            command="git push --force origin main",
            cwd=".",
        )
    )
    assert decision.action is PolicyAction.ASK


def test_precommit_promotes_ask_to_block() -> None:
    decision = evaluate(
        HookRequest(
            event="precommit",
            command="git push --force origin main",
            cwd=".",
        )
    )
    assert decision.action is PolicyAction.BLOCK


def test_blocks_protected_manifest(tmp_path: Path) -> None:
    (tmp_path / ".git").mkdir()
    decision = evaluate(
        HookRequest(
            event="afterFileEdit",
            cwd=str(tmp_path),
            file_path=str(tmp_path / ".agentic" / "manifest.yaml"),
        )
    )
    assert decision.action is PolicyAction.BLOCK
    assert "manifest" in decision.policy_id


def test_blocks_path_escape(tmp_path: Path) -> None:
    (tmp_path / ".git").mkdir()
    decision = evaluate(
        HookRequest(
            event="afterFileEdit",
            cwd=str(tmp_path),
            file_path="/etc/passwd",
        )
    )
    assert decision.action is PolicyAction.BLOCK
    assert decision.policy_id == "protected-path.escape"


def test_blocks_aws_key_in_edit() -> None:
    decision = evaluate(
        HookRequest(
            event="afterFileEdit",
            file_path="src/app.py",
            edits=[{"new_string": "key = AKIAIOSFODNN7EXAMPLE\n"}],
        )
    )
    assert decision.action is PolicyAction.BLOCK
    assert "aws" in decision.policy_id


def test_blocks_deleted_test(tmp_path: Path) -> None:
    (tmp_path / ".git").mkdir()
    decision = evaluate(
        HookRequest(
            event="precommit",
            cwd=str(tmp_path),
            paths=["tests/test_gone.py"],
        )
    )
    assert decision.action is PolicyAction.BLOCK
    assert "deleted" in decision.policy_id


def test_warns_empty_test(tmp_path: Path) -> None:
    (tmp_path / ".git").mkdir()
    path = tmp_path / "tests" / "test_empty.py"
    path.parent.mkdir()
    path.write_text("# nothing\n", encoding="utf-8")
    decision = evaluate(
        HookRequest(
            event="precommit",
            cwd=str(tmp_path),
            paths=[str(path)],
        )
    )
    assert decision.action is PolicyAction.WARN
    assert "weakened" in decision.policy_id


def test_allows_safe_command() -> None:
    decision = evaluate(
        HookRequest(event="beforeShellExecution", command="pytest -q", cwd=".")
    )
    assert decision.action is PolicyAction.ALLOW
