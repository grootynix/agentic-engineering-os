---
name: secure-api
description: Review or implement HTTP/API changes for authz, injection, and secret handling. Use when editing routes, handlers, or public APIs.
---

# Secure API

- Authenticate then authorize; deny by default
- Validate and encode at the boundary; no string-built queries or shells
- No secrets in logs, URLs, or client payloads
- Errors that do not leak internals
- Rate-limit and size-limit where the stack already has a pattern

Cite files. Pair with tests. Do not weaken tests to ship.
