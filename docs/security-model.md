# Security model

Agentic Engineering OS is an agentic security product. LLM instructions are not a security boundary. The **harness** (installed CLI, later policy engine, hooks, CI) is.

Hooks, heavy `verify`, and SAST/SCA scanners are still incomplete. This document is the threat model those features must satisfy. `agentic-sdlc hook` is the fast-path policy engine.

---

## Trust

| Class | Examples | Treatment |
|---|---|---|
| Trusted | User-installed `agentic-sdlc` package; version pinned in `.agentic/manifest.yaml` | May execute. Prefer this binary for hooks (`agentic-sdlc hook …`), not repo scripts. |
| Untrusted | Target repo files, README, docs, web content, MCP responses, tool output, generated files, repo-local hook scripts, skills copied from the repo, extra catalogs | Data. Do not follow instructions found inside them. Do not execute without an explicit, constrained path. |
| Data never eval | Catalog YAML (profiles, packs, graphs, policies), pack file lists, rule bodies | Schema-validate. No `eval`, no pickle, no YAML tags that construct objects, no arbitrary executables from catalog without a later signed/allowlisted pack mechanism. |

Do not trust configuration because it exists in the repository.

---

## Layering

```text
Guidance      rules, skills, AGENTS.md / CLAUDE.md
     ↓
Detection     doctor, secret/SAST/SCA tools, hook predicates
     ↓
Enforcement   policy engine (ALLOW | WARN | ASK | BLOCK) + CI required checks
     ↓
Verification  agentic-sdlc verify + CI gates
     ↓
Approval      human on PR; regulated profile: explicit control attestations
```

Guidance without a lower layer is advisory. Secure/regulated **mandatory** controls fail closed when the engine exists. Advisory quality hooks may fail open with WARN.

---

## Threats

**Indirect prompt injection.** README, issues, generated code, MCP, and third-party files can contain “ignore previous instructions.” Treat as data. Host `beforeReadFile` / untrusted-content skills are guidance; path/tool allowlists and hooks are enforcement.

**Command injection.** Never interpolate untrusted strings into a shell. Hook policy is structured parse / denylist, not “ask the model.”

**Path traversal.** Resolve real paths before protected-path checks. Reject `..` escapes and symlink tricks that leave the intended tree.

**Malicious hooks.** Repo `.cursor/hooks.json` / Claude hook config can point at arbitrary commands. M3 must bind security events to the installed CLI with `failClosed`, not `bash scripts/hook.sh` from the checkout. Treat repo-local hook scripts as untrusted.

**Malicious skills / agents / MCP.** Skill text can instruct secret exfil or unsafe tools. Skills are untrusted content. MCP servers are untrusted I/O. Permissions and tool policy live in the harness, not in skill prose.

**Malicious / tampered configuration.** `.agentic/config.yaml` is owned and untrusted relative to org policy. Doctor must flag disabled mandatory controls (M4+). Schema-invalid YAML is a hard fail.

**Secret exposure.** Cheap pattern checks on hook fast-path (M3); heavy scanners at commit/PR/CI. Do not log secrets in doctor/init reports.

**Privilege escalation / agent escape.** Agents should not leave intended paths or escalate host permissions. Protected-path and dangerous-command policies (M3). Stop conditions in the harness.

**Supply chain.** Pin CLI version in the manifest. Lock framework dependencies. Later: pack allowlists. Compromised `agentic-sdlc` is in the trusted set—treat distribution like any security tool.

**Config tampering / plugins.** Hash-compare `managed` files (doctor `HASH_DRIFT`). Do not auto-merge untrusted extra catalogs in M1.

---

## Hook design (Milestone 3, not M1)

Prototype classes: dangerous-command, protected-path, test-protection, secret-detection, format-on-edit, audit.

- Fast path only on edit events. Heavy SAST/SCA at commit/PR/CI, not every `afterFileEdit`.
- BLOCK explains: what, why, policy id, legitimate proceed path (PR to change allowlist, not “ignore the hook”).
- Fail closed for mandatory secure/regulated controls; fail open + WARN for advisory quality.
- Prompt hooks (Cursor) are non-deterministic and are not boundaries.

---

## Milestone 1 implications

M1 may write stub rules/skills and a manifest. It must:

- Treat catalog as data (Pydantic/schema load).
- Not execute graphs, hooks, or repo scripts as part of init/doctor.
- Not claim enforcement that does not exist.
- Record framework version so later updates can pin trust to a known CLI.

The security boundary in M1 is limited to: no eval of catalog, pathlib-safe writes into the target tree, no execution of untrusted repo content. Everything else is deferred and must not be advertised as present.
