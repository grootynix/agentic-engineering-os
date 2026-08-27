# Changelog

All notable changes to this project are documented here.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.2.1] - 2026-08-27

### Fixed

- Release workflow: docker Buildx so GHCR provenance/SBOM attestations can publish; do not emit `:latest`.

## [0.2.0] - 2026-08-27

### Added

- Doctor and init **Actionables** (`action` on each finding; human + `--json`).
- PATH install (`scripts/install.sh` / `uv tool install`) and CI one-file binaries (macOS/Linux) with catalog bundled.
- This repository is dogfooded via `agentic-sdlc init`.
- Glob-scoped catalog rules: testing, engineering, documentation, Python, TypeScript, **release/branching**.
- `cut-release` skill; Dockerfile and `.github/workflows/aeos-release.yml` (tag `v*` → wheel, SHA256SUMS, GHCR, cosign OIDC).
- Guidance pack: threat-model, architecture-review, secure-api, dependency-review, privacy-review skills; verifier / security-reviewer / architecture-reviewer agents.
- `agentic-sdlc graph` walks `catalog/graphs/sdlc.yaml` against `sdlc/*.md` artifacts and prints Actionables.
- North-star product spec (`docs/spec.md`) and OSS contribution layout on `dev`.

### Fixed

- Template renderer substitutes `{{framework_version}}` only, so copied GitHub Actions keep docker-metadata `{{version}}`.

## [0.1.0] - 2026-08-27

### Added

- `agentic-sdlc` CLI: `init`, `doctor` (JSON and human reports).
- Deterministic stack detection and declarative catalog (profiles, core pack, SDLC graph stub).
- Cursor and Claude Code adapters; ownership-aware file projection and `.agentic/manifest.yaml`.
- Unit and integration tests; architecture and security docs.

[Unreleased]: https://github.com/grootynix/agentic-engineering-os/compare/v0.2.1...HEAD
[0.2.1]: https://github.com/grootynix/agentic-engineering-os/releases/tag/v0.2.1
[0.2.0]: https://github.com/grootynix/agentic-engineering-os/releases/tag/v0.2.0
[0.1.0]: https://github.com/grootynix/agentic-engineering-os/releases/tag/v0.1.0
