---
name: cut-release
description: Cut a production-grade release with branching, SemVer, changelog, signing, and container publish. Use when tagging, shipping, versioning, signing artifacts, or building Docker/GHCR images.
---

# Cut a release

## Branching

1. Land work on `dev` (PR + green CI).
2. Merge or fast-forward `dev` → `release`.
3. Tag `vX.Y.Z` on `release`. Push the tag.
4. Fast-forward `main` to that tag.
5. Do not force-push protected branches.

## Versioning

- Bump SemVer in the language manifest (`pyproject.toml`, `package.json`, …) and `__version__` / equivalent.
- Move Unreleased notes in `CHANGELOG.md` into `[X.Y.Z]`.
- Tag must equal `v` + that version.

## Artifacts

- Build what CI already builds (wheel, binary, image).
- Write `SHA256SUMS` for attached files.
- Create a GitHub Release from the tag; paste the changelog section.

## Signing

- Prefer `cosign sign` with GitHub OIDC (no long-lived keys in the repo).
- Sign the container image digest and, if present, checksum file.
- Record verify command in the release notes.

Example verify (after publish):

```bash
cosign verify ghcr.io/OWNER/IMAGE:vX.Y.Z
sha256sum -c SHA256SUMS
```

## Containerization

- Multi-stage Dockerfile; run as non-root; no secrets in `ENV`.
- Push `ghcr.io/<owner>/<name>:<tag>` and `:<git-sha>`.
- Do not use `:latest` as the production pin.

If this repo has `.github/workflows/aeos-release.yml`, prefer that workflow over ad-hoc scripts.
