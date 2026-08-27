"""Doctor: validate manifest, hashes, profile, and stack."""

from __future__ import annotations

from pathlib import Path

import yaml
from pydantic import ValidationError

from agentic_sdlc import __version__
from agentic_sdlc.core.detect import detect_stack
from agentic_sdlc.core.manifest import load_manifest, manifest_path
from agentic_sdlc.core.models import (
    DoctorIssue,
    DoctorReport,
    FileClass,
    OverallStatus,
    Severity,
)
from agentic_sdlc.core.ownership import file_sha256
from agentic_sdlc.core.resolve import list_profiles
from agentic_sdlc.errors import CatalogError


def _issue(
    code: str,
    message: str,
    *,
    severity: Severity,
    action: str,
    path: str | None = None,
) -> DoctorIssue:
    return DoctorIssue(code=code, severity=severity, message=message, action=action, path=path)


def run_doctor(root: Path) -> DoctorReport:
    root = root.resolve()
    root_s = str(root)
    issues: list[DoctorIssue] = []
    stack = detect_stack(root)
    if stack.primary == "unknown":
        issues.append(
            _issue(
                "STACK_UNKNOWN",
                "no language stack markers found",
                severity=Severity.WARN,
                action=(
                    f"Add a stack marker at the repo root (pyproject.toml, package.json, "
                    f"go.mod, pom.xml, or *.tf), or ignore this warn if the tree is empty: {root_s}"
                ),
            )
        )
    if stack.ambiguous:
        issues.append(
            _issue(
                "STACK_AMBIGUOUS",
                "multiple stacks matched; using highest score with low confidence",
                severity=Severity.WARN,
                action=(
                    f"Keep one primary stack at the repo root or remove extra lockfiles; "
                    f"scores={stack.scores}. Re-run: agentic-sdlc doctor --path {root_s}"
                ),
            )
        )

    path = manifest_path(root)
    if not path.is_file():
        issues.append(
            _issue(
                "MANIFEST_MISSING",
                f"missing {path.relative_to(root)} — run `agentic-sdlc init`",
                severity=Severity.ERROR,
                path=".agentic/manifest.yaml",
                action=f"agentic-sdlc init --path {root_s}",
            )
        )
        return _finish(root, issues, stack, present=False, profile=None)

    try:
        manifest = load_manifest(root)
    except (ValidationError, ValueError, TypeError, yaml.YAMLError) as exc:
        issues.append(
            _issue(
                "MANIFEST_INVALID",
                f"manifest is not valid: {exc}",
                severity=Severity.ERROR,
                path=".agentic/manifest.yaml",
                action=(
                    f"Fix .agentic/manifest.yaml or regenerate with "
                    f"agentic-sdlc init --path {root_s} --force"
                ),
            )
        )
        return _finish(root, issues, stack, present=True, profile=None)

    assert manifest is not None
    profile = manifest.profile
    if manifest.framework.version != __version__:
        issues.append(
            _issue(
                "VERSION_MISMATCH",
                f"manifest framework {manifest.framework.version} != package {__version__}",
                severity=Severity.WARN,
                action=(
                    f"Install matching agentic-sdlc {manifest.framework.version} or re-init: "
                    f"agentic-sdlc init --path {root_s}"
                ),
            )
        )

    try:
        known = set(list_profiles())
        if profile not in known:
            issues.append(
                _issue(
                    "PROFILE_MISSING",
                    f"profile {profile!r} is not in the catalog",
                    severity=Severity.ERROR,
                    action=(
                        f"Set profile to one of {sorted(known)} in .agentic/manifest.yaml "
                        f"or run agentic-sdlc init --path {root_s} --profile standard"
                    ),
                )
            )
    except CatalogError as exc:
        issues.append(
            _issue(
                "CATALOG",
                str(exc),
                severity=Severity.ERROR,
                action="Set AGENTIC_SDLC_CATALOG to a valid catalog dir or reinstall",
            )
        )

    for item in manifest.files:
        dest = root / item.path
        if not dest.is_file():
            sev = Severity.ERROR if item.classification is not FileClass.OWNED else Severity.WARN
            issues.append(
                _issue(
                    "PATH_MISSING",
                    f"recorded path does not exist: {item.path}",
                    severity=sev,
                    path=item.path,
                    action=(
                        f"Restore {item.path} or run agentic-sdlc init --path {root_s} "
                        f"{'--force' if item.classification is FileClass.MANAGED else ''}".strip()
                    ),
                )
            )
            continue
        if item.classification is FileClass.MANAGED:
            current = file_sha256(dest)
            if current != item.sha256:
                issues.append(
                    _issue(
                        "HASH_DRIFT",
                        f"managed file changed since last init: {item.path}",
                        severity=Severity.WARN,
                        path=item.path,
                        action=(
                            f"Review {item.path}; restore from catalog or "
                            f"agentic-sdlc init --path {root_s} --force"
                        ),
                    )
                )

    return _finish(root, issues, stack, present=True, profile=profile)


def _finish(
    root: Path,
    issues: list[DoctorIssue],
    stack,
    *,
    present: bool,
    profile: str | None,
) -> DoctorReport:
    if any(i.severity is Severity.ERROR for i in issues):
        overall = OverallStatus.FAIL
    elif issues:
        overall = OverallStatus.DEGRADED
    else:
        overall = OverallStatus.OK
    return DoctorReport(
        overall=overall,
        path=str(root),
        issues=issues,
        manifest_present=present,
        profile=profile,
        stack=stack,
    )
