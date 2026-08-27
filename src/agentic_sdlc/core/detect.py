"""Deterministic stack detection from catalog markers. No LLM."""

from __future__ import annotations

import json
from pathlib import Path

import yaml

from agentic_sdlc.core.models import HarnessPresence, StackDef, StackReport, catalog_root


def _load_stacks() -> list[StackDef]:
    stacks_dir = catalog_root() / "stacks"
    stacks: list[StackDef] = []
    if not stacks_dir.is_dir():
        return stacks
    for path in sorted(stacks_dir.glob("*.yaml")):
        data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
        stacks.append(StackDef.model_validate(data))
    return stacks


def _package_json_deps(root: Path) -> set[str]:
    pkg = root / "package.json"
    if not pkg.is_file():
        return set()
    try:
        payload = json.loads(pkg.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return set()
    names: set[str] = set()
    for key in ("dependencies", "devDependencies", "peerDependencies"):
        section = payload.get(key) or {}
        if isinstance(section, dict):
            names.update(section.keys())
    return names


def detect_stack(root: Path) -> StackReport:
    root = root.resolve()
    stacks = _load_stacks()
    scores: dict[str, int] = {}
    markers_by_stack: dict[str, list[str]] = {}
    languages: dict[str, str] = {}
    pkg_deps = _package_json_deps(root)

    for stack in stacks:
        languages[stack.id] = stack.language
        hits: list[str] = []
        for name in stack.files:
            if (root / name).is_file():
                hits.append(name)
        for pattern in stack.globs:
            matched = sorted(p.name for p in root.glob(pattern) if p.is_file())
            if matched:
                hits.append(pattern)
        for dep in stack.package_json_deps:
            if dep in pkg_deps:
                hits.append(f"package.json:{dep}")
        if not hits:
            continue
        score = len(hits) * 10 + stack.priority
        scores[stack.id] = score
        markers_by_stack[stack.id] = hits

    harness = HarnessPresence(
        cursor_dir=(root / ".cursor").is_dir(),
        agents_md=(root / "AGENTS.md").is_file(),
        claude_dir=(root / ".claude").is_dir(),
        claude_md=(root / "CLAUDE.md").is_file(),
    )

    if not scores:
        return StackReport(
            primary="unknown",
            language="unknown",
            confidence="low",
            ambiguous=False,
            markers=[],
            scores={},
            harness=harness,
        )

    ranked = sorted(scores.items(), key=lambda item: (-item[1], item[0]))
    primary, _ = ranked[0]
    ambiguous = len(ranked) > 1
    confidence = "low" if ambiguous else "high"
    all_markers = sorted({m for hits in markers_by_stack.values() for m in hits})
    return StackReport(
        primary=primary,
        language=languages.get(primary, primary),
        confidence=confidence,
        ambiguous=ambiguous,
        markers=all_markers,
        scores=scores,
        harness=harness,
    )
