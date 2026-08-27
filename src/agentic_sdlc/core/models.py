"""Pydantic models for catalog, detection, init, and doctor."""

from __future__ import annotations

import os
from datetime import datetime
from enum import StrEnum
from pathlib import Path
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from agentic_sdlc.errors import CatalogError


class FileClass(StrEnum):
    MANAGED = "managed"
    GENERATED = "generated"
    OWNED = "owned"


class Severity(StrEnum):
    WARN = "warn"
    ERROR = "error"


class OverallStatus(StrEnum):
    OK = "OK"
    DEGRADED = "DEGRADED"
    FAIL = "FAIL"


class HarnessPresence(BaseModel):
    cursor_dir: bool = False
    agents_md: bool = False
    claude_dir: bool = False
    claude_md: bool = False


class StackReport(BaseModel):
    primary: str
    language: str
    confidence: str
    ambiguous: bool = False
    markers: list[str] = Field(default_factory=list)
    scores: dict[str, int] = Field(default_factory=dict)
    harness: HarnessPresence = Field(default_factory=HarnessPresence)


class StackDef(BaseModel):
    """Catalog stack detector (YAML)."""

    id: str
    language: str
    priority: int = 0
    files: list[str] = Field(default_factory=list)
    globs: list[str] = Field(default_factory=list)
    package_json_deps: list[str] = Field(default_factory=list)


class PackFile(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    source: str
    dest: str
    classification: FileClass = Field(alias="class")
    adapter: str


class Pack(BaseModel):
    id: str
    files: list[PackFile] = Field(default_factory=list)


class Profile(BaseModel):
    name: str
    extends: str | None = None
    packs: list[str] = Field(default_factory=list)
    controls: dict[str, Any] = Field(default_factory=dict)


class DesiredFile(BaseModel):
    dest: str
    content: str
    classification: FileClass
    adapter: str
    source: str


class DesiredState(BaseModel):
    profile: str
    stack: StackReport
    files: list[DesiredFile] = Field(default_factory=list)


class ManifestFile(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    path: str
    classification: FileClass = Field(alias="class")
    sha256: str
    source: str


class FrameworkInfo(BaseModel):
    name: str
    version: str


class Manifest(BaseModel):
    framework: FrameworkInfo
    profile: str
    stack: StackReport
    files: list[ManifestFile] = Field(default_factory=list)
    created_at: datetime

    def file_by_path(self, path: str) -> ManifestFile | None:
        posix = path.replace("\\", "/")
        for item in self.files:
            if item.path == posix:
                return item
        return None


class DoctorIssue(BaseModel):
    code: str
    severity: Severity
    message: str
    path: str | None = None


class DoctorReport(BaseModel):
    overall: OverallStatus
    path: str
    issues: list[DoctorIssue] = Field(default_factory=list)
    manifest_present: bool = False
    profile: str | None = None
    stack: StackReport | None = None

    @property
    def ok(self) -> bool:
        return self.overall != OverallStatus.FAIL


class InitReport(BaseModel):
    ok: bool
    path: str
    profile: str | None = None
    stack: StackReport | None = None
    files_written: list[str] = Field(default_factory=list)
    files_skipped: list[str] = Field(default_factory=list)
    doctor: DoctorReport | None = None
    error: str | None = None
    code: str | None = None


class GraphNode(BaseModel):
    id: str
    label: str | None = None


class GraphEdge(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    source: str = Field(alias="from")
    target: str = Field(alias="to")


class Graph(BaseModel):
    name: str
    nodes: list[GraphNode]
    edges: list[GraphEdge] = Field(default_factory=list)

    @field_validator("nodes")
    @classmethod
    def unique_nodes(cls, nodes: list[GraphNode]) -> list[GraphNode]:
        ids = [n.id for n in nodes]
        if len(ids) != len(set(ids)):
            raise ValueError("duplicate graph node ids")
        return nodes

    @model_validator(mode="after")
    def edges_reference_nodes(self) -> Graph:
        ids = {n.id for n in self.nodes}
        for edge in self.edges:
            if edge.source not in ids or edge.target not in ids:
                raise ValueError(
                    f"graph edge {edge.source}->{edge.target} references unknown node"
                )
        return self


def catalog_root() -> Path:
    env = os.environ.get("AGENTIC_SDLC_CATALOG")
    if env:
        path = Path(env).expanduser().resolve()
        if not path.is_dir():
            raise CatalogError(f"catalog path does not exist: {path}")
        return path
    pkg = Path(__file__).resolve().parent.parent
    for candidate in (pkg / "catalog", pkg.parent.parent / "catalog"):
        if candidate.is_dir():
            return candidate
    raise CatalogError("catalog directory not found; set AGENTIC_SDLC_CATALOG")
