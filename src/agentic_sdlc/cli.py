"""Typer CLI: init, doctor, graph, hook, verify, and update stub."""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Annotated

import typer
from pydantic import BaseModel

from agentic_sdlc import __version__
from agentic_sdlc.adapters import ADAPTERS
from agentic_sdlc.core.detect import detect_stack
from agentic_sdlc.core.doctor import run_doctor
from agentic_sdlc.core.graph import walk_graph
from agentic_sdlc.core.manifest import load_manifest, now_utc, write_manifest
from agentic_sdlc.core.models import (
    DesiredState,
    FrameworkInfo,
    InitReport,
    Manifest,
    ManifestFile,
    OverallStatus,
)
from agentic_sdlc.core.ownership import content_sha256, file_sha256, should_write
from agentic_sdlc.core.policy import (
    Decision,
    PolicyAction,
    claude_response,
    cursor_response,
    evaluate,
    infer_host,
    parse_hook_payload,
)
from agentic_sdlc.core.resolve import load_graph, resolve_desired_state
from agentic_sdlc.core.verify import CheckStatus, run_verify
from agentic_sdlc.errors import (
    AdapterConflictError,
    AgenticError,
    HookPayloadError,
    NotGitRepoError,
    NotImplementedFeature,
    UsageError,
)

app = typer.Typer(
    name="agentic-sdlc",
    help="Agentic Engineering OS — catalog-driven agent harness bootstrap.",
    no_args_is_help=True,
    pretty_exceptions_enable=False,
    add_completion=False,
)


def _version_callback(value: bool) -> None:
    if value:
        typer.echo(__version__)
        raise typer.Exit(0)


@app.callback()
def _root(
    version: Annotated[
        bool,
        typer.Option("--version", callback=_version_callback, is_eager=True, help="Print version"),
    ] = False,
) -> None:
    return


def _dump(model: BaseModel) -> str:
    return json.dumps(model.model_dump(mode="json", by_alias=True), indent=2)


def _print_error(exc: AgenticError, *, as_json: bool) -> None:
    if as_json:
        typer.echo(
            json.dumps({"ok": False, "error": str(exc), "code": exc.code}, indent=2)
        )
    else:
        typer.echo(f"error: {exc}", err=True)


def _require_git(root: Path, force: bool) -> None:
    if force:
        return
    if not (root / ".git").exists():
        raise NotGitRepoError(
            f"{root} is not a git repository (missing .git). Re-run with --force to override."
        )


def _default_profile(explicit: str | None) -> str:
    if explicit:
        return explicit
    return "standard"


def _project(
    root: Path,
    desired: DesiredState,
    *,
    force: bool,
) -> tuple[list[str], list[str]]:
    dests: dict[str, str] = {}
    for item in desired.files:
        if item.dest in dests and dests[item.dest] != item.adapter:
            raise AdapterConflictError(
                f"two adapters claim dest {item.dest}: {dests[item.dest]} and {item.adapter}"
            )
        if item.dest in dests:
            raise AdapterConflictError(f"duplicate dest {item.dest}")
        dests[item.dest] = item.adapter
        adapter = ADAPTERS.get(item.adapter)
        if adapter is None:
            raise AdapterConflictError(f"unknown adapter: {item.adapter}")
        if not adapter.accepts(item.dest):
            raise AdapterConflictError(
                f"adapter {item.adapter} does not accept dest {item.dest}"
            )

    prev = load_manifest(root)
    written: list[str] = []
    skipped: list[str] = []
    for item in desired.files:
        write, reason = should_write(item, root, manifest=prev, force=force)
        adapter = ADAPTERS[item.adapter]
        if write:
            adapter.write(root, item)
            written.append(item.dest)
        else:
            skipped.append(item.dest)
            _ = reason
    return written, skipped


def _build_manifest(root: Path, desired: DesiredState) -> Manifest:
    files: list[ManifestFile] = []
    for item in desired.files:
        path = root / item.dest
        digest = file_sha256(path) if path.is_file() else content_sha256(item.content)
        files.append(
            ManifestFile(
                path=item.dest,
                classification=item.classification,
                sha256=digest,
                source=item.source,
            )
        )
    return Manifest(
        framework=FrameworkInfo(name="agentic-sdlc", version=__version__),
        profile=desired.profile,
        stack=desired.stack,
        files=files,
        created_at=now_utc(),
    )


def _print_init_human(report: InitReport) -> None:
    status = "ok" if report.ok else "failed"
    typer.echo(f"init {status}")
    typer.echo(f"  path:    {report.path}")
    if report.profile:
        typer.echo(f"  profile: {report.profile}")
    if report.stack:
        typer.echo(
            f"  stack:   {report.stack.primary} "
            f"(language={report.stack.language}, confidence={report.stack.confidence})"
        )
    if report.files_written:
        typer.echo("  wrote:")
        for path in report.files_written:
            typer.echo(f"    + {path}")
    if report.files_skipped:
        typer.echo("  skipped:")
        for path in report.files_skipped:
            typer.echo(f"    ~ {path}")
    if report.doctor:
        typer.echo(f"  doctor:  {report.doctor.overall.value}")
        _print_actionables(report.doctor.issues)
    if report.error:
        typer.echo(f"  error:   {report.error}")


def _print_actionables(issues) -> None:
    if not issues:
        typer.echo("Actionables: none")
        return
    typer.echo("Actionables:")
    for i, issue in enumerate(issues, start=1):
        typer.echo(f"  {i}. [{issue.code}] {issue.action}")


def _print_doctor_human(report) -> None:
    typer.echo(f"doctor {report.overall.value}")
    typer.echo(f"  path: {report.path}")
    if report.profile:
        typer.echo(f"  profile: {report.profile}")
    if report.stack:
        typer.echo(
            f"  stack: {report.stack.primary} (confidence={report.stack.confidence})"
        )
    if not report.issues:
        typer.echo("  issues: none")
        _print_actionables([])
        return
    typer.echo("  issues:")
    for issue in report.issues:
        loc = f" {issue.path}" if issue.path else ""
        typer.echo(f"    [{issue.severity.value}] {issue.code}{loc}: {issue.message}")
    _print_actionables(report.issues)


@app.command()
def init(
    path: Annotated[
        Path | None,
        typer.Option("--path", help="Project root (default: cwd)"),
    ] = None,
    profile: Annotated[
        str | None,
        typer.Option("--profile", help="Catalog profile name"),
    ] = None,
    as_json: Annotated[bool, typer.Option("--json", help="Print JSON report")] = False,
    force: Annotated[
        bool,
        typer.Option("--force", help="Skip .git check; overwrite drifted managed files"),
    ] = False,
) -> None:
    """Detect stack, render catalog, project files, write manifest, doctor."""
    root = (path or Path.cwd()).resolve()
    try:
        if not sys.stdin.isatty() and profile is None:
            chosen = "standard"
        else:
            chosen = _default_profile(profile)
        _require_git(root, force)
        load_graph("sdlc")
        stack = detect_stack(root)
        desired = resolve_desired_state(
            profile_name=chosen,
            stack=stack,
            version=__version__,
        )
        written, skipped = _project(root, desired, force=force)
        write_manifest(root, _build_manifest(root, desired))
        doctor = run_doctor(root)
        report = InitReport(
            ok=doctor.overall is not OverallStatus.FAIL,
            path=str(root),
            profile=desired.profile,
            stack=stack,
            files_written=written,
            files_skipped=skipped,
            doctor=doctor,
        )
    except AgenticError as exc:
        _print_error(exc, as_json=as_json)
        raise typer.Exit(exc.exit_code) from exc

    if as_json:
        typer.echo(_dump(report))
    else:
        _print_init_human(report)
    raise typer.Exit(0 if report.ok else 1)


@app.command()
def doctor(
    path: Annotated[
        Path | None,
        typer.Option("--path", help="Project root (default: cwd)"),
    ] = None,
    as_json: Annotated[bool, typer.Option("--json", help="Print JSON report")] = False,
) -> None:
    """Validate manifest, hashes, profile, and stack."""
    root = (path or Path.cwd()).resolve()
    try:
        report = run_doctor(root)
    except AgenticError as exc:
        _print_error(exc, as_json=as_json)
        raise typer.Exit(exc.exit_code) from exc
    if as_json:
        typer.echo(_dump(report))
    else:
        _print_doctor_human(report)
    raise typer.Exit(0 if report.ok else 1)


@app.command("graph")
def graph_cmd(
    path: Annotated[
        Path | None,
        typer.Option("--path", help="Project root (default: cwd)"),
    ] = None,
    name: Annotated[str, typer.Option("--name", help="Catalog graph id")] = "sdlc",
    as_json: Annotated[bool, typer.Option("--json", help="Print JSON report")] = False,
) -> None:
    """Walk the SDLC artifact graph and print next nodes plus actionables."""
    root = (path or Path.cwd()).resolve()
    try:
        report = walk_graph(root, name=name)
    except AgenticError as exc:
        _print_error(exc, as_json=as_json)
        raise typer.Exit(exc.exit_code) from exc
    if as_json:
        typer.echo(_dump(report))
    else:
        typer.echo(f"graph {report.name}")
        typer.echo(f"  path: {report.path}")
        typer.echo(f"  next: {', '.join(report.next_ids) if report.next_ids else '(none)'}")
        for node in report.nodes:
            art = f" {node.artifact}" if node.artifact else ""
            typer.echo(f"    [{node.status.value}] {node.id}{art}")
        ready = [n for n in report.nodes if n.status.value == "ready"]
        if not ready:
            typer.echo("Actionables: none")
        else:
            typer.echo("Actionables:")
            for i, node in enumerate(ready, start=1):
                typer.echo(f"  {i}. [{node.id}] {node.action}")
    raise typer.Exit(0)


def _not_implemented(name: str) -> None:
    raise NotImplementedFeature(f"{name} is not implemented (no update engine).")


@app.command()
def verify(
    path: Annotated[
        Path | None,
        typer.Option("--path", help="Project root (default: cwd)"),
    ] = None,
    as_json: Annotated[bool, typer.Option("--json", help="Print JSON report")] = False,
) -> None:
    """Run discovered format, lint, type, and test commands. Missing tools skip."""
    root = (path or Path.cwd()).resolve()
    try:
        report = run_verify(root)
    except AgenticError as exc:
        _print_error(exc, as_json=as_json)
        raise typer.Exit(exc.exit_code) from exc
    if as_json:
        typer.echo(_dump(report))
    else:
        typer.echo(f"verify {report.overall.value}")
        typer.echo(f"  path: {report.path}")
        typer.echo(f"  stack: {report.stack}")
        if not report.checks:
            typer.echo("  checks: none")
        for item in report.checks:
            typer.echo(f"    [{item.status.value}] {item.id}")
            if item.status is not CheckStatus.PASS and item.detail:
                first = item.detail.splitlines()[0][:120]
                typer.echo(f"      {first}")
        fails = [c for c in report.checks if c.status.value == "fail"]
        skips = [c for c in report.checks if c.status.value == "skip" and c.action]
        if not fails and not skips:
            typer.echo("Actionables: none")
        else:
            typer.echo("Actionables:")
            n = 1
            for item in fails + skips:
                typer.echo(f"  {n}. [{item.id}] {item.action}")
                n += 1
    raise typer.Exit(0 if report.ok else 1)


@app.command()
def update() -> None:
    """Not implemented (M1)."""
    try:
        _not_implemented("update")
    except AgenticError as exc:
        _print_error(exc, as_json=False)
        raise typer.Exit(exc.exit_code) from exc


@app.command("hook")
def hook_cmd(
    event: Annotated[str, typer.Argument(help="Event id (beforeShellExecution, precommit, …)")],
    files: Annotated[
        list[str] | None,
        typer.Argument(help="Paths from pre-commit (optional)"),
    ] = None,
    host: Annotated[
        str,
        typer.Option("--host", help="cursor | claude | precommit | auto"),
    ] = "auto",
) -> None:
    """Policy engine. Reads JSON on stdin; prints host JSON. Installed CLI only."""
    raw = sys.stdin.read() if not sys.stdin.isatty() else ""
    invalid = Decision(
        action=PolicyAction.BLOCK,
        policy_id="hook.invalid-payload",
        what="Hook payload could not be parsed",
        why="Security events fail closed on invalid input",
        proceed="Fix the host hook JSON; do not bypass the installed CLI",
    )
    try:
        request = parse_hook_payload(event, raw, files or [])
        decision = evaluate(request)
    except HookPayloadError:
        decision = invalid
    except AgenticError as exc:
        _print_error(exc, as_json=False)
        raise typer.Exit(exc.exit_code) from exc

    resolved_host = infer_host(event, host)
    if resolved_host == "precommit":
        if decision.action is PolicyAction.ALLOW:
            raise typer.Exit(0)
        typer.echo(decision.message())
        raise typer.Exit(1 if decision.action is PolicyAction.BLOCK else 0)
    if resolved_host == "claude":
        typer.echo(json.dumps(claude_response(decision, event)))
    else:
        typer.echo(json.dumps(cursor_response(decision)))
    raise typer.Exit(0)


def main() -> None:
    try:
        app()
    except UsageError as exc:
        _print_error(exc, as_json=False)
        raise SystemExit(exc.exit_code) from exc
