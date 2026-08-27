# Cutting a release

Maintainers only.

1. On `dev`, set the version in `pyproject.toml` and `src/agentic_sdlc/__init__.py`. Move items from Unreleased to a new section in `CHANGELOG.md`.
2. Open a PR from `dev` into `release` (or fast-forward `release` if history is linear and CI is green).
3. Tag the merge commit: `git tag -a v0.x.y -m "v0.x.y"` and `git push origin v0.x.y`.
4. Fast-forward `main` to that tag so GitHub’s default branch matches the published version.
5. GitHub Releases: create a release from the tag; paste the changelog section.

Do not force-push `main`, `dev`, or `release`.
