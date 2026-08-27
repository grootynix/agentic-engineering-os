"""Claude Code adapter: projects `.claude/` files and CLAUDE.md."""

from __future__ import annotations

from agentic_sdlc.adapters.base import Adapter


class ClaudeCodeAdapter(Adapter):
    name = "claude"

    def accepts(self, dest: str) -> bool:
        posix = dest.replace("\\", "/")
        return posix.startswith(".claude/") or posix == "CLAUDE.md"
