"""Adapter protocol. Core never names Cursor or Claude."""

from __future__ import annotations

from abc import ABC, abstractmethod
from pathlib import Path

from agentic_sdlc.core.models import DesiredFile


class Adapter(ABC):
    name: str

    @abstractmethod
    def accepts(self, dest: str) -> bool:
        """Whether this adapter is responsible for dest."""

    def write(self, root: Path, item: DesiredFile) -> Path:
        path = root / item.dest
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(item.content, encoding="utf-8")
        return path
