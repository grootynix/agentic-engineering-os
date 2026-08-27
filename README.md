# Agentic Engineering OS

[![CI](https://github.com/grootynix/agentic-engineering-os/actions/workflows/ci.yml/badge.svg?branch=main)](https://github.com/grootynix/agentic-engineering-os/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Python 3.11+](https://img.shields.io/badge/python-3.11%2B-blue.svg)](pyproject.toml)

A versioned, testable engineering operating system for AI coding agents.

Clone a repo, run `agentic-sdlc init`, and the project gets a portable harness for [Cursor](https://cursor.com) and [Claude Code](https://docs.anthropic.com/en/docs/claude-code): short instructions, scoped rules and skills, a machine-readable manifest, and (later) hooks, verification, and review nodes. This is not a prompt pack. Guidance tells the agent how to work. Formatters, tests, hooks, and CI are what actually enforce it.

```bash
uv sync --extra dev
uv run agentic-sdlc init --path /path/to/your-app --profile standard
uv run agentic-sdlc doctor --path /path/to/your-app
```

**Status:** Milestone 1 — bootstrap CLI (`init`, `doctor`), stack detection, catalog, adapters. Not yet a full secure SDLC. See [Roadmap](#roadmap).

---

## Why this exists

Models are good at judgment: design, implementation, tradeoffs, diagnosis.

They are a poor compiler, linter, secret scanner, and policy engine. They also should not receive a 40-page always-on manifesto (token cost goes up; security does not).

This project splits the work:

| Layer | Job |
| --- | --- |
| **Model** | Architecture, code, threat-model reasoning, review commentary |
| **Catalog** | Versioned profiles, packs, rules, skills, graphs |
| **Harness** | Context assembly, permissions, hooks, verify loops, stop conditions |
| **Graph** | Typed SDLC steps (`intent → spec → plan → implement → verify → review → PR`) |

Cursor and Claude Code are **host** harnesses. `agentic-sdlc` is the portable layer you install into any repository.

---

## What you get after `init` (today)

The CLI inspects the target tree (language, package manager, tests, existing Cursor/Claude files) and projects a **desired state** from a declarative profile.

Typical files:

- `AGENTS.md` / `CLAUDE.md` — short: commands, constraints, definition of done, “read the manifest first”
- `.agentic/manifest.yaml` — framework version, profile, stack, file hashes
- `.agentic/INDEX.md` — pointer map so agents do not re-explore the repo
- `.agentic/config.yaml` — yours (not overwritten on later updates)
- Stub Cursor rule + skill under `.cursor/`
- Stub Claude skill under `.claude/`

Profiles are YAML, not hardcoded CLI flags: `standard`, `secure`, `regulated`. Only the **core** pack is populated in Milestone 1. `secure` and `regulated` exist so the composition model is real; they do not yet add scanners or attestations.

---

## Install

Requires **Python 3.11+**. Prefer [uv](https://docs.astral.sh/uv/).

```bash
git clone https://github.com/grootynix/agentic-engineering-os.git
cd agentic-engineering-os
uv sync --extra dev
uv run agentic-sdlc --version
```

From a checkout without uv:

```bash
python3.11 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
agentic-sdlc --version
```

`init` requires a `.git` directory in the **target** app unless you pass `--force`.

```bash
uv run agentic-sdlc init                          # cwd, profile standard when non-interactive
uv run agentic-sdlc init --path ../my-app --profile standard
uv run agentic-sdlc init --json --force
uv run agentic-sdlc doctor --path ../my-app --json
```

Exit codes: `0` success, `1` init/doctor failure, `2` usage or not implemented.

`verify`, `update`, and `hook` are stubs in Milestone 1 (exit `2`).

---

## Design in one page

**Least context.** Almost no `alwaysApply` rules. Skills load when the task matches.

**Guidance vs enforcement.** A rule that says “don’t weaken tests” is advice. A hook or CI job that rejects deleted assertions is control.

**Configuration is code.** Packs and profiles live in [`catalog/`](catalog/) and are schema-validated. Changing them is a reviewed change.

**Do not trust the checkout.** Repo README, skills, MCP output, and local hook scripts are untrusted data. Later, security hooks should call the **installed** `agentic-sdlc` binary, not an arbitrary script in the project.

**North star (not all shipped):** clone in Cursor → `init` → agents default to secure, modular, maintainable work, with pre-commit, threat modeling, security review, quality gates, and production practices **where they apply**, at low token cost.

Details: [docs/spec.md](docs/spec.md) (north-star product contract), [docs/architecture.md](docs/architecture.md), [docs/security-model.md](docs/security-model.md), [ADR: Python + catalog](docs/adr/0001-python-cli-and-catalog.md), [ADR: harness and graph](docs/adr/0002-harness-and-graph-engineering.md).

---

## Repository layout

```text
src/agentic_sdlc/     CLI, detect/resolve/render, adapters (Cursor, Claude, shared)
catalog/              profiles, packs, templates, stacks, graphs (data, not Python)
tests/                unit + init/doctor integration against fixture repos
docs/                 architecture, security, ADRs
```

The engine does not speak Cursor or Claude. Adapters project the same catalog into each host’s file layout.

---

## Roadmap

1. **Milestone 1 (this repo):** CLI, `init`, manifest, stack detection, templates, `doctor`
2. **Rules, skills, specialized agents** as graph nodes (verifier, security-reviewer, architecture-reviewer)
3. **Harness:** hooks, pre-commit, secret/SAST/SCA, `agentic-sdlc verify`
4. **Profiles in full, `update`, mandatory-control validation**
5. **Evals, token metrics, maturity scoring**

---

## Development

```bash
uv sync --extra dev
uv run pytest
uv run ruff check src tests
```

PRs target **`dev`**. See [CONTRIBUTING.md](CONTRIBUTING.md) for the `dev` / `release` / `main` model, [docs/releasing.md](docs/releasing.md) for cuts, and [CHANGELOG.md](CHANGELOG.md) for shipped changes.

---

## License

[MIT](LICENSE)

Please read [CODE_OF_CONDUCT.md](CODE_OF_CONDUCT.md) and [SECURITY.md](SECURITY.md) before contributing.
