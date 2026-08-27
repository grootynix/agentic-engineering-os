"""Cursor adapter: projects `.cursor/` files only."""

from __future__ import annotations

from agentic_sdlc.adapters.base import Adapter


class CursorAdapter(Adapter):
    name = "cursor"

    def accepts(self, dest: str) -> bool:
        return dest.replace("\\", "/").startswith(".cursor/")
