# Security policy

This project is an **agentic security product**. Treat CLI bugs, catalog injection, and path handling as security-relevant even when they look like “just a bootstrap tool.”

## Supported versions

| Version | Supported |
| --- | --- |
| 0.1.x | Yes (current) |

We do not backport to unreleased milestone designs. Report against `main` / `release`.

## Report a vulnerability

**Do not open a public GitHub issue** for a vulnerability.

1. Use [GitHub private vulnerability reporting](https://github.com/grootynix/agentic-engineering-os/security/advisories/new) if it is enabled on this repository.
2. Or email **swastik.reach@gmail.com** with:
   - affected version / commit
   - what you ran (`init`, `doctor`, catalog load, …)
   - impact (path traversal, secret leak, unexpected code execution, policy bypass)
   - a minimal reproduction

Please do not attach production secrets. Redact them.

You should hear back within **7 days**. If we confirm the issue, we will coordinate a fix on `dev`, cut `release`, and credit you unless you ask otherwise.

## Out of scope (for now)

Milestone 1 does not implement hooks, `verify`, or a policy engine. Reports that the stubs exit `2` are not vulnerabilities. Reports that **catalog YAML is executed** or that `init` writes outside the target tree are.

## Maintainer notes

Hooks (when they exist) must invoke the installed `agentic-sdlc` binary, not untrusted scripts from the consumer repo. See [docs/security-model.md](docs/security-model.md).
