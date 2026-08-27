# Session status — Agentic Engineering OS

Handoff for the next agent or human. Product contract: [docs/spec.md](docs/spec.md). Architecture: [docs/architecture.md](docs/architecture.md).

**Repo:** https://github.com/grootynix/agentic-engineering-os  
**Default branch:** `main` (stable). **Contribute on:** `dev`. **Cut from:** `release`.  
**Open PR (unmerged as of this file):** https://github.com/grootynix/agentic-engineering-os/pull/19 — `feat/dogfood-release-harness` → `dev`

If that PR is already merged, continue from `dev` and ignore the branch name below.

---

## What this product is

Portable harness for Cursor and Claude Code. `agentic-sdlc init` projects rules/skills/manifest. The model judges; formatters, tests, hooks, and CI enforce. Guidance is not a security boundary.

CLI: Python 3.11+, package `agentic_sdlc`, command `agentic-sdlc`. Catalog is YAML in `catalog/`. Adapters project to `.cursor/` and `.claude/`.

---

## Done

### Shipped on `main` / tag `v0.1.0` (commit `85e34f1` + OSS follow-ups)

- Milestone 1: `init`, `doctor`, stack detect, core pack stubs, adapters, tests.
- OSS: CONTRIBUTING, CoC, SECURITY, CI (pytest/ruff), issue/PR templates, Dependabot, CODEOWNERS, MIT, topics, milestones M1–M5.
- Spec: [docs/spec.md](docs/spec.md). ADRs under `docs/adr/`.
- Tracking issue: [#8](https://github.com/grootynix/agentic-engineering-os/issues/8). M1 issue [#9](https://github.com/grootynix/agentic-engineering-os/issues/9) closed.

### In PR #19 (treat as done once merged)

- Doctor/init **Actionables**: each issue has `action`; human list + JSON.
- This repo **dogfooded**: `agentic-sdlc init --profile standard` then `doctor` → **OK** (Python).
- PATH install: `scripts/install.sh` / `uv tool install --editable .`.
- Standalone binary: `scripts/build_binary.py` (PyInstaller); CI job `binary` on ubuntu + macos. Local `dist/agentic-sdlc` is gitignored; local macOS build printed `0.1.0`.
- M2 start: glob-scoped Cursor rules (testing, engineering, docs, python, typescript, **release**).
- Production cut: `cut-release` skill; `.agentic/templates/` (Dockerfile, dockerignore, `aeos-release.yml`); this repo’s root `Dockerfile` + `.github/workflows/aeos-release.yml` (tag `v*` → wheel, SHA256SUMS, GHCR, cosign OIDC).
- Docs: [docs/releasing.md](docs/releasing.md).

### GitHub not finished

- **Projects board:** token lacks `project` scope. Create manually or re-auth `gh` with `project,read:project`.
- Private vulnerability reporting: enable in repo Settings → Security.

---

## What is next (priority)

1. **Merge PR #19** into `dev`, then fast-forward `release`/`main` when you want it on the default branch.
2. **M2 remainder** (issues on #8):
   - [#11](https://github.com/grootynix/agentic-engineering-os/issues/11) skills (threat-model, reviews, secure-api) — `cut-release` already exists
   - [#12](https://github.com/grootynix/agentic-engineering-os/issues/12) specialized agents (verifier, security-reviewer, architecture-reviewer)
   - [#16](https://github.com/grootynix/agentic-engineering-os/issues/16) SDLC graph walker (`catalog/graphs/sdlc.yaml` is data only today)
3. **M3 harness:** [#14](https://github.com/grootynix/agentic-engineering-os/issues/14) policy engine + hooks + pre-commit; [#18](https://github.com/grootynix/agentic-engineering-os/issues/18) `verify`; [#15](https://github.com/grootynix/agentic-engineering-os/issues/15) secret/SAST/SCA. Stubs `verify` / `update` / `hook` still exit `2`.
4. **M4:** full `secure`/`regulated` packs, `update`, doctor mandatory controls.
5. **M5:** evals, token metrics.
6. **First production tag after #19:** bump version if needed, changelog, tag `v0.2.0` (or `v0.1.1`) to exercise GHCR + cosign. `v0.1.0` predates the release workflow.

Do not start M3 until M2 agents/walker are sketched; do not treat rules as enforcement.

---

## How to run (next session)

```bash
cd /Users/smac/Documents/workspace/proj/agenticpdlc
git checkout feat/dogfood-release-harness   # or dev after merge
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
| `catalog/` | profiles, packs, rules, skills, graphs (source of truth) |
| `.agentic/` | dogfood manifest + consumer templates |
| `.cursor/` `.claude/` | projected harness (managed; re-init with `--force` if catalog wins) |
| `docs/spec.md` | north star |

Catalog YAML is data: schema-validate, never `eval`. Hooks (when built) must call the **installed** `agentic-sdlc` binary, not repo scripts.

---

## Intentional non-goals still

Windows-first CI, org catalog overlay, GitHub Projects from this token, prompt-hooks as security, dumping SOLID/KISS into always-on `AGENTS.md`.
