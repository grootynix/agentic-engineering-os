---
name: architecture-review
description: Review module boundaries, dependencies, and cohesion. Use when asked for an architecture review, circular deps, or layering.
---

# Architecture review

Check, with evidence (file paths):

- One primary reason to change per module
- Domain not importing infrastructure adapters
- No new circular imports
- Extension via existing hooks/packs/adapters before editing stable cores
- Complexity hotspots (oversized functions) called out, not silently rewritten

Do not re-implement the product. Prefer `agentic-sdlc graph` to see if plan/spec exist.
