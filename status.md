# Session status — Agentic Engineering OS

Handoff for the next agent or human. Product contract: [docs/spec.md](docs/spec.md). Architecture: [docs/architecture.md](docs/architecture.md).

**Repo:** https://github.com/grootynix/agentic-engineering-os  
**Default branch:** `main` (still the v0.1.0-era snapshot until you fast-forward it).  
**Contribute on:** `dev` (includes merged PR [#19](https://github.com/grootynix/agentic-engineering-os/pull/19), closed).  
**Cut from:** `release`.

Work from `dev` (`47df34b` Merge pull request #19). Do not check out `feat/dogfood-release-harness`.

---

## What this product is

Portable harness for Cursor and Claude Code. `agentic-sdlc init` projects rules/skills/manifest. The model judges; formatters, tests, hooks, and CI enforce. Guidance is not a security boundary.

CLI: Python 3.11+, package `agentic_sdlc`, command `agentic-sdlc`. Catalog is YAML in `catalog/`. Adapters project to `.cursor/` and `.claude/`.

---

## Done

### On `main` / tag `v0.1.0`

- Milestone 1: `init`, `doctor`, stack detect, core pack stubs, adapters, tests.
- OSS: CONTRIBUTING, CoC, SECURITY, CI, issue/PR templates, Dependabot, CODEOWNERS, MIT, topics, milestones M1–M5.
- Spec and ADRs. Tracking [#8](https://github.com/grootynix/agentic-engineering-os/issues/8). M1 [#9](https://github.com/grootynix/agentic-engineering-os/issues/9) closed.

### On `dev` (PR #19 merged)

- Doctor/init **Actionables** (`action` field; human + JSON).
- Repo **dogfooded**: `init --profile standard` then `doctor` → OK (Python).
- PATH: `scripts/install.sh` / `uv tool install --editable .`.
- Binary: `scripts/build_binary.py`; CI `binary` job (ubuntu, macos). `dist/` gitignored.
- M2 start: glob-scoped rules (testing, engineering, docs, python, typescript, **release**).
- Production cut: `cut-release` skill; `.agentic/templates/`; root `Dockerfile` + `.github/workflows/aeos-release.yml` (`v*` → wheel, SHA256SUMS, GHCR, cosign OIDC).
- [docs/releasing.md](docs/releasing.md).

### GitHub still open

- **Projects board:** needs `project` token scope (or create the board in the UI).
- Enable private vulnerability reporting in Settings → Security.
- Dependabot PRs targeting `dev` (actions checkout/setup-uv, pip bumps) — review separately.

---

## What is next (priority)

1. **Promote `dev` → `release` → `main`** when you want GitHub’s default branch to match dogfood (optional; not done by #19).
2. **M2 remainder** ([#8](https://github.com/grootynix/agentic-engineering-os/issues/8)):
   - [#11](https://github.com/grootynix/agentic-engineering-os/issues/11) skills (threat-model, reviews, secure-api)
   - [#12](https://github.com/grootynix/agentic-engineering-os/issues/12) specialized agents
   - [#16](https://github.com/grootynix/agentic-engineering-os/issues/16) graph walker (`catalog/graphs/sdlc.yaml` is data only)
3. **M3:** [#14](https://github.com/grootynix/agentic-engineering-os/issues/14) hooks/pre-commit; [#18](https://github.com/grootynix/agentic-engineering-os/issues/18) `verify`; [#15](https://github.com/grootynix/agentic-engineering-os/issues/15) scanners. CLI stubs still exit `2`.
4. **M4:** `secure`/`regulated` packs, `update`, mandatory-control doctor.
5. **M5:** evals, token metrics.
6. **Tag after promote:** `v0.2.0` (or `v0.1.1`) to run `aeos-release.yml`. `v0.1.0` predates that workflow.

Do not start M3 until M2 agents/walker are sketched. Rules are not enforcement.

---

## How to run

```bash
cd /Users/smac/Documents/workspace/proj/agenticpdlc
git checkout dev
git pull
uv sync --extra dev
uv run pytest
uv run agentic-sdlc doctor
# PATH: sh scripts/install.sh
# Binary: uv sync --extra binary && uv run python scripts/build_binary.py
```

PRs target **`dev`**. Do not force-push `main` / `dev` / `release`.

---

## Layout cheat sheet

| Path | Role |
| --- | --- |
| `src/agentic_sdlc/` | CLI, detect, resolve, doctor, adapters |
| `catalog/` | profiles, packs, rules, skills, graphs |
| `.agentic/` | dogfood manifest + consumer templates |
| `.cursor/` `.claude/` | projected harness (managed) |
| `docs/spec.md` | north star |

Catalog YAML is data. Future hooks must call the installed `agentic-sdlc` binary, not repo scripts.

---

## Intentional non-goals still

Windows-first CI, org catalog overlay, prompt-hooks as security, dumping SOLID/KISS into always-on `AGENTS.md`.
