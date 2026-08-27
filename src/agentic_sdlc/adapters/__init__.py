from agentic_sdlc.adapters.claude_code import ClaudeCodeAdapter
from agentic_sdlc.adapters.cursor import CursorAdapter
from agentic_sdlc.adapters.shared import SharedAdapter

ADAPTERS = {
    SharedAdapter.name: SharedAdapter(),
    CursorAdapter.name: CursorAdapter(),
    ClaudeCodeAdapter.name: ClaudeCodeAdapter(),
}

__all__ = ["ADAPTERS", "ClaudeCodeAdapter", "CursorAdapter", "SharedAdapter"]
