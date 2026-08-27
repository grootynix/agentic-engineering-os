# Contributing

Thanks for looking at this repo. Milestone 1 is a bootstrap CLI; we still want small, reviewable changes rather than a rewrite of the roadmap in one PR.

## Branch model

| Branch | Role |
| --- | --- |
| `dev` | Integration. **Open pull requests against `dev`.** |
| `release` | Release line. Maintainers merge `dev` here when cutting a version. |
| `main` | Stable snapshot shown on GitHub. Updated from `release` after a cut. |

Do not push straight to `main` or `release`.

```text
feature branch  →  PR to dev  →  merge to release  →  tag  →  update main
```

## Setup

Python 3.11+ and [uv](https://docs.astral.sh/uv/).

```bash
git clone https://github.com/grootynix/agentic-engineering-os.git
cd agentic-engineering-os
git checkout dev
uv sync --extra dev
uv run pytest
uv run ruff check src tests
```

If you do not use uv:

```bash
python3.11 -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -e ".[dev]"
pytest
ruff check src tests
```

## What to change where

- **Python behavior** lives in `src/agentic_sdlc/`. Keep the CLI thin; put logic in `core/` or adapters.
- **Profiles, packs, templates, graphs** live in `catalog/`. Treat them as data: schema-valid YAML, no executable snippets.
- **Architecture decisions** go in `docs/adr/` when you change a constraint, not as a chatty comment in the CLI.
- Do not add Cursor-specific or Claude-specific logic to `core/`. Put it in `adapters/`.

## Pull requests

1. Branch from latest `dev` (`git checkout -b feat/short-name`).
2. Keep the diff focused. Catalog-only and engine-only PRs are easier to review than mixed ones.
3. Tests must pass. New detection heuristics need a fixture under `tests/fixtures/repos/`.
4. Fill in the PR template. Link an issue if one exists.
5. One concern per PR when you can.

We do not require a CLA. By opening a PR you license your contribution under the [MIT License](LICENSE).

## Code style

Ruff is the linter (`[tool.ruff]` in `pyproject.toml`). Match existing naming. Prefer `pathlib` over raw path strings.

## Security

Do not file public issues for vulnerabilities. See [SECURITY.md](SECURITY.md).

Do not commit secrets, `.env` files, or live customer configs. Catalog fixtures must be fake.

## Conduct

[Contributor Covenant](CODE_OF_CONDUCT.md) applies to issues, PRs, and discussion.
