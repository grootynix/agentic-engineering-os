# syntax=docker/dockerfile:1
FROM ghcr.io/astral-sh/uv:python3.12-bookworm-slim AS build
WORKDIR /src
COPY pyproject.toml uv.lock README.md LICENSE ./
COPY src src
COPY catalog catalog
RUN uv sync --frozen --no-dev --no-editable \
    && uv build --wheel

FROM python:3.12-slim-bookworm
RUN useradd --create-home --uid 10001 --shell /usr/sbin/nologin app
WORKDIR /app
COPY --from=build /src/dist/*.whl /tmp/
RUN pip install --no-cache-dir /tmp/*.whl && rm /tmp/*.whl
USER app
ENTRYPOINT ["agentic-sdlc"]
CMD ["--help"]
