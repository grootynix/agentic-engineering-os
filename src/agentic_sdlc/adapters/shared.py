"""Shared adapter: AGENTS.md, .agentic/, and other harness-neutral paths."""

from __future__ import annotations

from agentic_sdlc.adapters.base import Adapter


class SharedAdapter(Adapter):
    name = "shared"

    def accepts(self, dest: str) -> bool:
        posix = dest.replace("\\", "/")
        if posix.startswith(".cursor/") or posix.startswith(".claude/"):
            return False
        if posix == "CLAUDE.md":
            return False
        return True
