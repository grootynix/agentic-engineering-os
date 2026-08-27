#!/bin/sh
# Install agentic-sdlc onto PATH for dogfood (requires uv).
set -eu
cd "$(dirname "$0")/.."
uv tool install --editable --force .
echo "Installed. Try: agentic-sdlc --version && agentic-sdlc doctor"
