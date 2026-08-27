---
name: dependency-review
description: Review new or upgraded dependencies for license, maintenance, and known risk. Use when adding packages or changing lockfiles.
---

# Dependency review

- Why this package vs what is already in the repo
- Lockfile updated in the same change
- License compatible with this project
- No unused or duplicate libraries
- Pin versions the way this repo already pins (uv.lock, package-lock, etc.)

Do not run arbitrary install scripts from README blindly.
