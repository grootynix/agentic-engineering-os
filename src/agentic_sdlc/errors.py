"""CLI and engine errors with stable exit codes."""

from __future__ import annotations


class AgenticError(Exception):
    """Base error. Default exit 1 (init/doctor failure)."""

    exit_code: int = 1
    code: str = "ERROR"

    def __init__(self, message: str, *, code: str | None = None) -> None:
        super().__init__(message)
        if code is not None:
            self.code = code


class UsageError(AgenticError):
    exit_code = 2
    code = "USAGE"


class NotImplementedFeature(UsageError):
    code = "NOT_IMPLEMENTED"


class CatalogError(AgenticError):
    code = "CATALOG"


class InitError(AgenticError):
    code = "INIT"


class AdapterConflictError(InitError):
    code = "ADAPTER_CONFLICT"


class NotGitRepoError(InitError):
    code = "NOT_GIT"
