# ADR 0001 — Python CLI and catalog/adapters split

**Status:** Accepted

**Date:** 2026-08-27

## Context

The framework must bootstrap into arbitrary repos via `agentic-sdlc init`, support Cursor and Claude Code without coupling the core engine to either, and keep policies/profiles/packs versioned and testable. The product repo started empty. Implementation language was chosen as Python 3.11+.

A naive layout would vendor `.cursor/` and `.claude/` trees as the source of truth, or hard-code profiles in the CLI.

## Decision

1. **Python 3.11+ package** (`agentic_sdlc`), CLI entry `agentic-sdlc`, packaged with `pyproject.toml` (uv preferred). Typer for CLI, Pydantic v2 for schemas, PyYAML for catalog/manifest.

2. **Catalog vs adapters.** Canonical content lives in `catalog/` (YAML, templates, graphs, platform-neutral rule/skill bodies). The core engine resolves a desired state. Thin adapters project into `AGENTS.md`, `.cursor/`, `.claude/`, `.agentic/`. The engine never emits Cursor- or Claude-specific types.

3. **Profiles as data.** `standard`, `secure`, `regulated` are `catalog/profiles/*.yaml` (`extends`, packs, controls), not CLI enums with baked behavior.

## Consequences

- One edit to a rule body can project to both hosts; frontmatter/layout differences stay in adapters.
- Catalog ships as package data so a wheel install can `init` without a git checkout of this repo.
- Python is weaker for a single static binary than Go; acceptable for security/DevSecOps familiarity and schema-heavy YAML. Distribution is `uv tool` / pip.
- Tests validate YAML through Pydantic and golden projected trees, not ad-hoc string equality on host-specific dumps only.
- Core remains host-agnostic when a third adapter is added.

## Alternatives rejected

- **Go CLI:** better binary story; not chosen.
- **TypeScript/npm:** closer to Cursor JSON; weaker default fit for policy/SCA teams; not chosen.
- **Host files as source of truth:** duplicates content and diverges Cursor vs Claude.
- **Profiles hardcoded in CLI:** breaks composability and configuration-as-code.
