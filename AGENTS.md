# Agent instructions

This repository is bootstrapped by agentic-sdlc 0.2.1 (profile standard).
Primary language: python.

Read `.agentic/manifest.yaml` and `.agentic/INDEX.md` before exploring.
Run `agentic-sdlc graph` to see the next SDLC artifact (`sdlc/intent.md` first).
Run `agentic-sdlc verify` for format/lint/types/tests that exist (missing tools skip).
Specialized agents: verifier, security-reviewer, architecture-reviewer.

Keep this file short. Cursor rules under `.cursor/rules/` are glob-scoped.
For tagging, SemVer, signing, and images, use the `cut-release` skill.
See AGENTS.md from Claude Code as well; do not duplicate policy here.
Do not commit secrets.
