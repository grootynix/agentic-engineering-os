# Session status — Agentic Engineering OS

Handoff for the next agent or human. Product contract: [docs/spec.md](docs/spec.md). Architecture: [docs/architecture.md](docs/architecture.md).

**Repo:** https://github.com/grootynix/agentic-engineering-os  
**Default branch:** `main`  
**Contribute on:** `dev`.  
**Cut from:** `release`.  
**Current release:** `v0.2.0`

Work from `dev`. PRs target **`dev`**.

---

## What this product is

Portable harness for Cursor and Claude Code. `agentic-sdlc init` projects rules/skills/manifest. The model judges; formatters, tests, hooks, and CI enforce. Guidance is not a security boundary.

CLI: Python 3.11+, package `agentic_sdlc`, command `agentic-sdlc`. Catalog is YAML in `catalog/`. Adapters project to `.cursor/` and `.claude/`.

---

## Done

### `v0.1.0`

- Milestone 1: `init`, `doctor`, stack detect, core pack stubs, adapters, tests.
- Tracking [#8](https://github.com/grootynix/agentic-engineering-os/issues/8). M1 [#9](https://github.com/grootynix/agentic-engineering-os/issues/9) closed.

### `v0.2.0`

- Doctor/init Actionables; dogfood; PATH + CI binaries; glob rules; cut-release + GHCR/cosign workflow.
- Guidance pack (review skills + specialized agents).
- `agentic-sdlc graph` walker (artifact-based, not an LLM).

### GitHub still open

- **Projects board:** needs `project` token scope (or create the board in the UI).
- Enable private vulnerability reporting in Settings → Security.
- Dependabot PRs targeting `dev` — review separately.

---

## What is next (priority)

1. **M3:** [#14](https://github.com/grootynix/agentic-engineering-os/issues/14) hooks/pre-commit; [#18](https://github.com/grootynix/agentic-engineering-os/issues/18) `verify`; [#15](https://github.com/grootynix/agentic-engineering-os/issues/15) scanners. CLI stubs still exit `2`.
2. **M4:** `secure`/`regulated` packs, `update`, mandatory-control doctor.
3. **M5:** evals, token metrics.

Do not treat rules or graph Actionables as enforcement.

---

## How to run

```bash
git checkout dev
git pull
uv sync --extra dev
uv run pytest
uv run agentic-sdlc doctor
uv run agentic-sdlc graph
```

PRs target **`dev`**. Do not force-push `main` / `dev` / `release`.

---

## Layout cheat sheet

| Path | Role |
| --- | --- |
| `src/agentic_sdlc/` | CLI, detect, resolve, doctor, graph walker, adapters |
| `catalog/` | profiles, packs, rules, skills, agents, graphs |
| `.agentic/` | dogfood manifest + consumer templates |
| `.cursor/` `.claude/` | projected harness (managed) |
| `docs/spec.md` | north star |

Catalog YAML is data. Future hooks must call the installed `agentic-sdlc` binary, not repo scripts.

---

## Intentional non-goals still

Windows-first CI, org catalog overlay, prompt-hooks as security, dumping SOLID/KISS into always-on `AGENTS.md`.
