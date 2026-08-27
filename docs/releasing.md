# Cutting a release

Maintainers only. Matches the `cut-release` skill.

## Branching

1. Land work on `dev` (PR, CI green).
2. Fast-forward `release` to `dev`.
3. Tag `vX.Y.Z` on `release` and push the tag. Workflow `.github/workflows/aeos-release.yml` builds the wheel, checksums, GHCR image, and cosign signature.
4. Fast-forward `main` to that tag.
5. Do not force-push `main`, `dev`, or `release`.

## Versioning

Set the same SemVer in `pyproject.toml` and `src/agentic_sdlc/__init__.py`. Move Unreleased notes in `CHANGELOG.md` to `[X.Y.Z]`. The git tag must be `v` plus that version.

## Signing and containers

- Images: `ghcr.io/grootynix/agentic-engineering-os:<version>` and `sha-<gitsha>`.
- Cosign uses GitHub OIDC (`id-token: write`). Verify with `cosign verify ghcr.io/grootynix/agentic-engineering-os:vX.Y.Z`.
- Wheels on the GitHub Release include `SHA256SUMS`.
- Local image: `docker build -t agentic-sdlc:dev .`

Pin production deploys to a digest or SemVer tag, not `:latest`.
