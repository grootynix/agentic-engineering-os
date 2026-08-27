"""Deterministic hook policy. Catalog YAML is data; regexes are compiled, never eval'd."""

from __future__ import annotations

import json
import re
from enum import StrEnum
from pathlib import Path
from typing import Any

import yaml
from pydantic import BaseModel, Field, field_validator

from agentic_sdlc.core.models import catalog_root
from agentic_sdlc.errors import CatalogError, HookPayloadError

_ACTION_RANK = {"block": 3, "ask": 2, "warn": 1, "allow": 0}


class PolicyAction(StrEnum):
    ALLOW = "allow"
    WARN = "warn"
    ASK = "ask"
    BLOCK = "block"


class Decision(BaseModel):
    action: PolicyAction
    policy_id: str
    what: str
    why: str
    proceed: str

    def message(self) -> str:
        return (
            f"[{self.policy_id}] {self.what}. {self.why}. "
            f"Legitimate path: {self.proceed}"
        )


class CommandRule(BaseModel):
    id: str
    action: PolicyAction
    regex: str
    what: str
    why: str
    proceed: str

    @field_validator("regex")
    @classmethod
    def compile_regex(cls, value: str) -> str:
        try:
            re.compile(value)
        except re.error as exc:
            raise ValueError(f"invalid regex: {exc}") from exc
        return value


class PathRule(BaseModel):
    id: str
    prefix: str
    what: str
    why: str
    proceed: str


class SecretRule(BaseModel):
    id: str
    regex: str
    what: str
    why: str
    proceed: str

    @field_validator("regex")
    @classmethod
    def compile_regex(cls, value: str) -> str:
        try:
            re.compile(value)
        except re.error as exc:
            raise ValueError(f"invalid regex: {exc}") from exc
        return value


class HookPolicy(BaseModel):
    dangerous_commands: list[CommandRule] = Field(default_factory=list)
    protected_paths: list[PathRule] = Field(default_factory=list)
    secret_patterns: list[SecretRule] = Field(default_factory=list)
    test_globs: list[str] = Field(default_factory=list)
    test_markers: list[str] = Field(default_factory=list)


class HookRequest(BaseModel):
    event: str
    command: str | None = None
    cwd: str | None = None
    file_path: str | None = None
    content: str | None = None
    paths: list[str] = Field(default_factory=list)
    edits: list[dict[str, Any]] = Field(default_factory=list)


def load_hook_policy() -> HookPolicy:
    path = catalog_root() / "policies" / "hooks.yaml"
    if not path.is_file():
        raise CatalogError(f"missing policy file: {path}")
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise CatalogError("hooks policy must be a mapping")
    try:
        return HookPolicy.model_validate(data)
    except Exception as exc:
        raise CatalogError(f"invalid hooks policy: {exc}") from exc


def _worse(left: Decision, right: Decision) -> Decision:
    if _ACTION_RANK[right.action.value] > _ACTION_RANK[left.action.value]:
        return right
    return left


def _allow() -> Decision:
    return Decision(
        action=PolicyAction.ALLOW,
        policy_id="audit.pass",
        what="No blocking policy matched",
        why="Fast-path checks passed",
        proceed="Continue",
    )


def _workspace(request: HookRequest) -> Path:
    if request.cwd:
        return Path(request.cwd).expanduser().resolve()
    return Path.cwd().resolve()


def _repo_root(start: Path) -> Path:
    for path in [start, *start.parents]:
        if (path / ".git").exists() or (path / ".agentic" / "manifest.yaml").is_file():
            return path
    return start


def _relposix(root: Path, raw: str) -> str | None:
    path = Path(raw)
    if not path.is_absolute():
        path = root / path
    try:
        resolved = path.resolve()
        return resolved.relative_to(root.resolve()).as_posix()
    except ValueError:
        return None


def _is_test_path(rel: str, policy: HookPolicy) -> bool:
    posix = rel.replace("\\", "/")
    name = Path(posix).name
    if posix.startswith("tests/") or posix.startswith("test/"):
        return True
    if name.startswith("test_") and name.endswith(".py"):
        return True
    if name.endswith("_test.py"):
        return True
    if ".test." in name or ".spec." in name:
        return True
    for glob in policy.test_globs:
        stripped = glob.replace("**/", "").rstrip("/")
        if glob.endswith("/") and (posix == stripped or posix.startswith(f"{stripped}/")):
            return True
    return False


def _text_from_request(request: HookRequest) -> str:
    parts: list[str] = []
    if request.content:
        parts.append(request.content)
    if request.command:
        parts.append(request.command)
    for edit in request.edits:
        new = edit.get("new_string")
        if isinstance(new, str):
            parts.append(new)
    return "\n".join(parts)


def _check_command(command: str, policy: HookPolicy) -> Decision | None:
    for rule in policy.dangerous_commands:
        if re.search(rule.regex, command, flags=re.IGNORECASE):
            return Decision(
                action=rule.action,
                policy_id=rule.id,
                what=rule.what,
                why=rule.why,
                proceed=rule.proceed,
            )
    return None


def _check_path(rel: str | None, policy: HookPolicy) -> Decision | None:
    if rel is None:
        return Decision(
            action=PolicyAction.BLOCK,
            policy_id="protected-path.escape",
            what="Path is outside the workspace",
            why="Resolved path escaped the intended tree",
            proceed="Operate on files inside the repository",
        )
    posix = rel.replace("\\", "/")
    for rule in policy.protected_paths:
        prefix = rule.prefix.replace("\\", "/")
        if prefix.startswith("./"):
            prefix = prefix[2:]
        if posix == prefix.rstrip("/") or posix.startswith(prefix):
            return Decision(
                action=PolicyAction.BLOCK,
                policy_id=rule.id,
                what=rule.what,
                why=rule.why,
                proceed=rule.proceed,
            )
    return None


def _check_secrets(text: str, policy: HookPolicy) -> Decision | None:
    if not text:
        return None
    for rule in policy.secret_patterns:
        if re.search(rule.regex, text):
            return Decision(
                action=PolicyAction.BLOCK,
                policy_id=rule.id,
                what=rule.what,
                why=rule.why,
                proceed=rule.proceed,
            )
    return None


def _check_tests(
    rel: str, content: str | None, missing: bool, policy: HookPolicy
) -> Decision | None:
    if not _is_test_path(rel, policy):
        return None
    if missing:
        return Decision(
            action=PolicyAction.BLOCK,
            policy_id="test-protection.deleted",
            what=f"Test file removed: {rel}",
            why="Deleting tests is not an allowed way to go green",
            proceed="Fix the code or skip with an explicit tracked reason; do not delete the test",
        )
    if content is None:
        return None
    if not any(marker in content for marker in policy.test_markers):
        return Decision(
            action=PolicyAction.WARN,
            policy_id="test-protection.weakened",
            what=f"Test file has no assertions: {rel}",
            why="Empty or assertion-free tests do not protect behavior",
            proceed="Keep or add real assertions; do not gut the file",
        )
    return None


def _format_hint(request: HookRequest) -> Decision | None:
    if request.event not in {"afterFileEdit", "PostToolUse"}:
        return None
    path = request.file_path or ""
    if path.endswith(".py"):
        return Decision(
            action=PolicyAction.WARN,
            policy_id="format-on-edit.python",
            what="Python file edited",
            why="Format is advisory on the edit fast-path",
            proceed="Run ruff format on the file before commit",
        )
    return None


def evaluate(request: HookRequest, *, policy: HookPolicy | None = None) -> Decision:
    policy = policy or load_hook_policy()
    best = _allow()
    root = _repo_root(_workspace(request))
    ask_to_block = request.event in {"precommit", "pre-commit"}

    if request.command:
        hit = _check_command(request.command, policy)
        if hit:
            best = _worse(best, hit)

    path_strs = list(request.paths)
    if request.file_path:
        path_strs.append(request.file_path)

    for raw in path_strs:
        rel = _relposix(root, raw)
        hit = _check_path(rel, policy)
        if hit:
            best = _worse(best, hit)
        if rel:
            disk = root / rel
            missing = request.event in {"precommit", "pre-commit"} and not disk.is_file()
            content = request.content
            if content is None and disk.is_file() and request.event in {
                "precommit",
                "pre-commit",
            }:
                content = disk.read_text(encoding="utf-8", errors="replace")
            hit = _check_tests(rel, content, missing, policy)
            if hit:
                best = _worse(best, hit)

    text = _text_from_request(request)
    if request.event in {"precommit", "pre-commit"} and not text:
        blobs: list[str] = []
        for raw in path_strs:
            rel = _relposix(root, raw)
            if rel and (root / rel).is_file():
                blobs.append((root / rel).read_text(encoding="utf-8", errors="replace"))
        text = "\n".join(blobs)
    hit = _check_secrets(text, policy)
    if hit:
        best = _worse(best, hit)

    hint = _format_hint(request)
    if hint:
        best = _worse(best, hint)

    if ask_to_block and best.action is PolicyAction.ASK:
        best = best.model_copy(update={"action": PolicyAction.BLOCK})
    return best


def parse_hook_payload(event: str, raw: str, extra_paths: list[str]) -> HookRequest:
    payload: dict[str, Any] = {}
    text = raw.strip()
    if text:
        try:
            loaded = json.loads(text)
        except json.JSONDecodeError as exc:
            raise HookPayloadError(f"invalid hook JSON: {exc}") from exc
        if not isinstance(loaded, dict):
            raise HookPayloadError("hook JSON must be an object")
        payload = loaded

    command = payload.get("command")
    tool_input = payload.get("tool_input")
    if isinstance(tool_input, str):
        try:
            tool_input = json.loads(tool_input)
        except json.JSONDecodeError:
            tool_input = {"raw": tool_input}
    if isinstance(tool_input, dict):
        command = command or tool_input.get("command")
        file_from_tool = tool_input.get("file_path") or tool_input.get("path")
    else:
        file_from_tool = None

    file_path = payload.get("file_path") or file_from_tool
    edits = payload.get("edits") if isinstance(payload.get("edits"), list) else []
    paths = list(extra_paths)
    if file_path:
        paths.append(str(file_path))
    return HookRequest(
        event=event,
        command=str(command) if command else None,
        cwd=str(payload["cwd"]) if payload.get("cwd") else None,
        file_path=str(file_path) if file_path else None,
        content=str(payload["content"]) if payload.get("content") else None,
        paths=paths,
        edits=[e for e in edits if isinstance(e, dict)],
    )


def cursor_response(decision: Decision) -> dict[str, str]:
    permission = {
        PolicyAction.ALLOW: "allow",
        PolicyAction.WARN: "allow",
        PolicyAction.ASK: "ask",
        PolicyAction.BLOCK: "deny",
    }[decision.action]
    body = {
        "permission": permission,
        "user_message": decision.message(),
        "agent_message": decision.message(),
    }
    return body


def claude_response(decision: Decision, event: str) -> dict[str, Any]:
    permission = {
        PolicyAction.ALLOW: "allow",
        PolicyAction.WARN: "allow",
        PolicyAction.ASK: "ask",
        PolicyAction.BLOCK: "deny",
    }[decision.action]
    return {
        "hookSpecificOutput": {
            "hookEventName": event,
            "permissionDecision": permission,
            "permissionDecisionReason": decision.message(),
        }
    }


def infer_host(event: str, explicit: str) -> str:
    if explicit != "auto":
        return explicit
    if event in {"PreToolUse", "PostToolUse", "Stop"}:
        return "claude"
    if event in {"precommit", "pre-commit"}:
        return "precommit"
    return "cursor"
