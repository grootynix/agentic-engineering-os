# Product specification — north star

**Status:** living spec. Milestone 1 is implemented; everything else is planned unless marked **shipped**.  
**Audience:** maintainers and contributors.  
**Related:** [architecture.md](architecture.md), [security-model.md](security-model.md), [catalog/graphs/sdlc.yaml](../catalog/graphs/sdlc.yaml).

This document is the product contract. Architecture describes *how* the engine is split. This spec describes *what must be true* when the OS is complete.

---

## 1. Problem

Teams using Cursor and Claude Code collect prompts, rules, and skills that:

- are not versioned or tested as a product
- dump too much context (token cost)
- treat “the model will follow the rule” as a security or quality boundary
- differ by host (Cursor vs Claude) with no shared core

## 2. Product statement

An engineer clones a repository, runs `agentic-sdlc init`, and the repo is configured so AI agents default to **secure, modular, maintainable** work at **low token cost**, using Cursor and Claude Code features **on purpose**.

Anything that must always hold is implemented in **software** (hooks, tests, scanners, git, CI). The model is used for **judgment** only.

```text
clone → agentic-sdlc init → profile + stack packs projected
      → agent works inside harness (rules, skills, agents)
      → graph: intent → spec → plan → implement → verify → review → PR
      → deterministic gates (hooks, pre-commit, verify, CI)
      → human approval
```

## 3. Non-goals

- Replacing git, CI, compilers, or linters
- A new chat product or a generic second coding agent
- Encoding the entire SDLC in `AGENTS.md`
- Making the LLM deterministic (outcomes are gated; tokens are not a security control)
- Blind overwrite of repository-owned files on `update`

## 4. Users and commands

| Actor | Commands |
| --- | --- |
| App engineer | `init`, `doctor`, later `verify` |
| Agent (Cursor / Claude) | Reads projected files; later `agentic-sdlc hook` / `verify` |
| Maintainer of this OS | catalog PRs, evals, releases (`dev` → `release` → `main`) |

CLI (stable names):

| Command | Spec |
| --- | --- |
| `agentic-sdlc init` | Detect stack and existing AI config; compose profile + packs; project files; write `.agentic/manifest.yaml`; run doctor; human + `--json` report. Require `.git` unless `--force`. |
| `agentic-sdlc doctor` | Missing/stale/invalid config, hash drift, disabled mandatory controls (M4), unsupported stack. Overall `OK` / `DEGRADED` / `FAIL`. |
| `agentic-sdlc verify` | Adaptive graph of format, lint, types, unit/integration tests, secret/SAST/SCA, architecture checks **if present**. Missing checks skip or DEGRADED, never assumed. |
| `agentic-sdlc update` | Upgrade managed files only if hashes match last install; never overwrite `owned`; always regenerate `generated`. |
| `agentic-sdlc hook <id>` | Policy engine on stdin JSON; ALLOW / WARN / ASK / BLOCK + explanation. Installed binary only. |

Exit codes: `0` success, `1` failed check, `2` usage / not implemented.

## 5. Profiles

Declarative YAML. Not hardcoded in the CLI.

| Profile | Must include |
| --- | --- |
| `standard` | Engineering quality, testing, docs, architecture, format/lint. |
| `secure` | `standard` plus secret detection, SAST, SCA, security rules, threat-model skill, security-reviewer, dangerous-command and protected-path hooks, stronger verify. |
| `regulated` | `secure` plus audit artifacts, explicit approvals, traceability, mandatory controls fail-closed, protected configuration, stricter permissions. |

Org overlay (`AGENTIC_CATALOG`) is later; load order: org → profile → stack → `.agentic/config.yaml` → task skills.

## 6. Knowledge hierarchy (token budget)

| Layer | Size | When loaded |
| --- | --- | --- |
| `AGENTS.md` / `CLAUDE.md` | Short | Always. Commands, constraints, DoD, “read manifest first.” |
| Cursor `.mdc` rules | Narrow | Globs; at most one tiny `alwaysApply` pointer. |
| Skills | Progressive | `SKILL.md` + reference files on demand. |
| Specialized agents | Narrow contracts | verifier, security-reviewer, architecture-reviewer. Not a clone of the main agent. |
| `.agentic/INDEX.md` + manifest | Generated | Agents must not re-walk the repo for layout. |

SOLID, DRY, KISS, logging, production practices: **observable rules + stack checks**, not slogans in global files. Load by language/framework glob.

## 7. SDLC graph

Canonical graph: `intent → spec → plan → implement → verify → review → PR`.

`plan.md` required sections: objective, existing architecture, files to change, files not to change, sequence, risks, security, test strategy, docs, rollback, definition of done.

`agentic-sdlc graph` walks the catalog DAG against files on disk (complete / ready / blocked). It is not an LLM. Plan-drift (file set vs `files not to change`) is still later.

## 8. Harness and security layering

```text
Guidance → Detection → Enforcement → Verification → Human approval
```

| Must be deterministic | May be the model |
| --- | --- |
| Detect, resolve, render, doctor, ownership, schema | Design, implementation |
| Format, lint, types, tests | Threat-model reasoning |
| Secret/SAST/SCA, dependency policy | Review commentary |
| Path/command/MCP allow–deny | Plan writing |

**Trust:** installed `agentic-sdlc` (version pinned in manifest) is trusted. Repo files, README, MCP, generated code, repo-local hook scripts, extra catalogs are **untrusted data**. Catalog YAML is never `eval`’d.

Hook classes: dangerous-command, protected-path, test-protection, secret-detection (cheap patterns), format-on-edit (advisory), audit. Fast path on edit; heavy scans at commit/PR/CI. BLOCK explains what, why, policy id, legitimate path. Fail closed for mandatory secure/regulated controls.

Pre-commit uses the **same** policy engine as agent hooks.

## 9. Host adapters

Shared: catalog, engine, `.agentic/`, SDLC templates, CI, evals.

**Cursor:** `.cursor/rules/*.mdc`, `.cursor/hooks.json` → `agentic-sdlc hook`, `.cursor/skills/`, subagent briefs.

**Claude Code:** `CLAUDE.md` (pointers, no duplicate prose), `.claude/settings.json`, `.claude/skills/`, `.claude/agents/`. Same `Decision` object, different JSON.

## 10. Stacks

Detect without an LLM: Python, JavaScript/TypeScript, Java, Go, Terraform (and more later). Overlays supply architecture checks, test runners, logging conventions.

## 11. Verification and evals

One entry point: `agentic-sdlc verify` or a recorded native command.

Evals (`evals/`): security, architecture, testing, quality, documentation, token-efficiency. Score traces (nodes, tools, turns, tokens, retries, verify loops, success). Correctness first; then measure; then cut tokens.

## 12. Acceptance — north star “done”

A cloned app repo after `init --profile secure` (or `regulated` where required):

1. Cursor and Claude Code both receive projected config; `doctor` is `OK` or an explained `DEGRADED`.
2. Always-on context stays small; specialized skills/agents load by task.
3. Quality: format/lint/types/tests run via `verify` when those tools exist.
4. Security: secrets/SAST/SCA and hook denylists fail closed for mandatory controls; threat-model and security-reviewer exist as graph nodes.
5. Pre-commit and CI invoke the same gates as the agent harness.
6. `update` does not clobber `owned` files or unmanaged hash-drift.
7. Untrusted content cannot instruct the agent to skip gates (hooks/CI still run).
8. Token metrics exist and evals regress “weakened tests” / “skipped verify” classes.

## 13. Milestone map

| ID | Name | Shipped when |
| --- | --- | --- |
| **M1** | Bootstrap | CLI, init, detect, catalog stubs, doctor, tests, docs. **Shipped in 0.1.0.** |
| **M2** | Guidance graph | **On `dev`:** glob rules, cut-release, guidance pack (review skills + specialized agents), `agentic-sdlc graph` walker. |
| **M3** | Harness | Hooks, pre-commit, verify, secret/SAST/SCA. |
| **M4** | Profiles and update | Full secure/regulated packs, `update`, mandatory-control doctor. |
| **M5** | Evals | Agent evals, token instrumentation, maturity scoring. |

## 14. Out of Milestone 1

Hooks, verify, update, real security packs, evals, org catalog, Windows as a first-class CI target (code uses `pathlib`).

## 15. Change control

Changes to this spec land on `dev` via PR. Behavior changes should update this file and [CHANGELOG.md](../CHANGELOG.md) in the same PR.
