---
name: using-agentic-sdlc
description: Use Agentic Engineering OS conventions in this repository.
---

Read AGENTS.md and `.agentic/INDEX.md` before changing harness files.
Use `agentic-sdlc doctor` to check drift. Use `agentic-sdlc graph` for the next `sdlc/*.md` artifact.
Use `agentic-sdlc verify` as the single check entry point. Missing tools skip; do not invent a pass.
Hooks must invoke `agentic-sdlc hook`, not a script in the checkout.
Do not hand-edit generated files.
