"""Discover and run native format/lint/type/test commands. Missing tools skip."""

from __future__ import annotations

import os
import shutil
import subprocess
from enum import StrEnum
from pathlib import Path

import yaml
from pydantic import BaseModel, Field

from agentic_sdlc.core.detect import detect_stack
from agentic_sdlc.core.models import OverallStatus, catalog_root

_OUTPUT_CAP = 2000
_TIMEOUT = 180


class CheckStatus(StrEnum):
    PASS = "pass"
    FAIL = "fail"
    SKIP = "skip"


class CheckSpec(BaseModel):
    id: str
    stacks: list[str]
    kind: str
    bin: str
    argv: list[str]
    need_any: list[str] = Field(default_factory=list)
    require_config: str | None = None


class CheckResult(BaseModel):
    id: str
    kind: str
    status: CheckStatus
    command: list[str] = Field(default_factory=list)
    detail: str = ""
    action: str = ""


class VerifyReport(BaseModel):
    overall: OverallStatus
    path: str
    stack: str
    checks: list[CheckResult] = Field(default_factory=list)

    @property
    def ok(self) -> bool:
        return self.overall != OverallStatus.FAIL


def load_check_specs() -> list[CheckSpec]:
    path = catalog_root() / "verify" / "checks.yaml"
    data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    return [CheckSpec.model_validate(item) for item in data.get("checks", [])]


def _env(root: Path) -> dict[str, str]:
    env = os.environ.copy()
    extras = [
        str(root / ".venv" / "bin"),
        str(root / "node_modules" / ".bin"),
        os.path.expanduser("~/.local/bin"),
    ]
    env["PATH"] = os.pathsep.join([*extras, env.get("PATH", "")])
    return env


def _has_uv(root: Path, env: dict[str, str]) -> bool:
    return (root / "uv.lock").is_file() and shutil.which("uv", path=env.get("PATH")) is not None


def _has_mypy_config(root: Path) -> bool:
    if (root / "mypy.ini").is_file() or (root / ".mypy.ini").is_file():
        return True
    pyproject = root / "pyproject.toml"
    if not pyproject.is_file():
        return False
    text = pyproject.read_text(encoding="utf-8")
    return "[tool.mypy]" in text


def _has_npm_test(root: Path) -> bool:
    import json

    pkg = root / "package.json"
    if not pkg.is_file():
        return False
    try:
        data = json.loads(pkg.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return False
    scripts = data.get("scripts") or {}
    return isinstance(scripts, dict) and "test" in scripts


def _need_any(root: Path, names: list[str]) -> bool:
    if not names:
        return True
    return any((root / name).exists() for name in names)


def _config_ok(root: Path, kind: str | None) -> bool:
    if kind == "mypy":
        return _has_mypy_config(root)
    if kind == "npm-test":
        return _has_npm_test(root)
    return True


def _argv(root: Path, spec: CheckSpec, env: dict[str, str]) -> list[str]:
    parts: list[str] = []
    for part in spec.argv:
        if part in {"src", "tests"} and not (root / part).exists():
            continue
        parts.append(part)
    if spec.bin in {"ruff", "pytest", "mypy"} and _has_uv(root, env):
        return ["uv", "run", *parts]
    return parts


def _bin_ok(root: Path, spec: CheckSpec, env: dict[str, str]) -> bool:
    if spec.bin in {"ruff", "pytest", "mypy"} and _has_uv(root, env):
        return True
    path = env.get("PATH")
    if shutil.which(spec.bin, path=path):
        return True
    if spec.bin == "npx" or spec.argv[:1] == ["npx"]:
        return shutil.which("npx", path=path) is not None
    return False


def _clip(text: str) -> str:
    text = text.strip()
    if len(text) <= _OUTPUT_CAP:
        return text
    return text[:_OUTPUT_CAP] + "\n…(truncated)"


def _run(root: Path, argv: list[str], env: dict[str, str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        argv,
        cwd=root,
        env=env,
        capture_output=True,
        text=True,
        timeout=_TIMEOUT,
        check=False,
        shell=False,
    )


def _skip(spec: CheckSpec, reason: str, action: str) -> CheckResult:
    return CheckResult(
        id=spec.id,
        kind=spec.kind,
        status=CheckStatus.SKIP,
        detail=reason,
        action=action,
    )


def run_verify(root: Path) -> VerifyReport:
    root = root.resolve()
    stack = detect_stack(root)
    env = _env(root)
    results: list[CheckResult] = []
    for spec in load_check_specs():
        if stack.primary not in spec.stacks and stack.primary != "unknown":
            continue
        if stack.primary == "unknown":
            continue
        if not _need_any(root, spec.need_any):
            results.append(
                _skip(
                    spec,
                    f"no {', '.join(spec.need_any)} in the tree",
                    f"Add {spec.need_any[0]} if this {spec.kind} check should run",
                )
            )
            continue
        if not _config_ok(root, spec.require_config):
            results.append(
                _skip(
                    spec,
                    f"{spec.require_config} config not found",
                    f"Add {spec.require_config} config if you want this check",
                )
            )
            continue
        if not _bin_ok(root, spec, env):
            results.append(
                _skip(
                    spec,
                    f"{spec.bin} not on PATH",
                    f"Install {spec.bin} (or uv extra) to enable {spec.id}",
                )
            )
            continue
        argv = _argv(root, spec, env)
        try:
            proc = _run(root, argv, env)
        except FileNotFoundError:
            results.append(
                _skip(
                    spec,
                    f"executable missing: {argv[0]}",
                    f"Install {argv[0]} and re-run agentic-sdlc verify",
                )
            )
            continue
        except subprocess.TimeoutExpired:
            results.append(
                CheckResult(
                    id=spec.id,
                    kind=spec.kind,
                    status=CheckStatus.FAIL,
                    command=argv,
                    detail=f"timed out after {_TIMEOUT}s",
                    action=f"Run locally: {' '.join(argv)}",
                )
            )
            continue
        blob = _clip((proc.stdout or "") + "\n" + (proc.stderr or ""))
        if proc.returncode == 0:
            results.append(
                CheckResult(
                    id=spec.id,
                    kind=spec.kind,
                    status=CheckStatus.PASS,
                    command=argv,
                    detail=blob,
                )
            )
        else:
            results.append(
                CheckResult(
                    id=spec.id,
                    kind=spec.kind,
                    status=CheckStatus.FAIL,
                    command=argv,
                    detail=blob or f"exit {proc.returncode}",
                    action=f"Fix {spec.id}, then re-run: {' '.join(argv)}",
                )
            )

    fails = [c for c in results if c.status is CheckStatus.FAIL]
    passes = [c for c in results if c.status is CheckStatus.PASS]
    if fails:
        overall = OverallStatus.FAIL
    elif passes:
        overall = OverallStatus.OK
    else:
        overall = OverallStatus.DEGRADED
    return VerifyReport(
        overall=overall,
        path=str(root),
        stack=stack.primary,
        checks=results,
    )
