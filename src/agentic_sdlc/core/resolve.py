"""Load catalog YAML and resolve profile extends into a DesiredState."""

from __future__ import annotations

from pathlib import Path

import yaml

from agentic_sdlc.core.models import (
    DesiredFile,
    DesiredState,
    Graph,
    Pack,
    PackFile,
    Profile,
    StackReport,
    catalog_root,
)
from agentic_sdlc.core.render import render_template
from agentic_sdlc.errors import AdapterConflictError, CatalogError


def load_yaml(path: Path) -> dict:
    if not path.is_file():
        raise CatalogError(f"missing catalog file: {path}")
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise CatalogError(f"expected mapping in {path}")
    return data


def load_profile(name: str) -> Profile:
    path = catalog_root() / "profiles" / f"{name}.yaml"
    if not path.is_file():
        raise CatalogError(f"unknown profile: {name}", code="PROFILE_MISSING")
    return Profile.model_validate(load_yaml(path))


def load_pack(pack_id: str) -> Pack:
    path = catalog_root() / "packs" / f"{pack_id}.yaml"
    if not path.is_file():
        raise CatalogError(f"unknown pack: {pack_id}")
    pack = Pack.model_validate(load_yaml(path))
    if pack.id != pack_id:
        raise CatalogError(f"pack id mismatch: {pack.id} != {pack_id}")
    return pack


def load_graph(name: str = "sdlc") -> Graph:
    path = catalog_root() / "graphs" / f"{name}.yaml"
    if not path.is_file():
        raise CatalogError(f"unknown graph: {name}", code="GRAPH_MISSING")
    return Graph.model_validate(load_yaml(path))


def list_profiles() -> list[str]:
    profiles_dir = catalog_root() / "profiles"
    return sorted(p.stem for p in profiles_dir.glob("*.yaml"))


def resolve_profile(name: str) -> Profile:
    """Flatten `extends` (parent first). Detect cycles."""
    seen: list[str] = []
    packs: list[str] = []
    controls: dict = {}
    current: str | None = name
    chain: list[Profile] = []
    while current:
        if current in seen:
            raise CatalogError(f"profile cycle: {' -> '.join(seen + [current])}")
        seen.append(current)
        profile = load_profile(current)
        chain.append(profile)
        current = profile.extends
    # ancestors first
    chain.reverse()
    leaf_name = name
    for profile in chain:
        leaf_name = profile.name
        for pack_id in profile.packs:
            if pack_id not in packs:
                packs.append(pack_id)
        controls.update(profile.controls)
    return Profile(name=leaf_name, extends=None, packs=packs, controls=controls)


def _collect_pack_files(profile: Profile) -> list[PackFile]:
    files: list[PackFile] = []
    for pack_id in profile.packs:
        files.extend(load_pack(pack_id).files)
    dests: dict[str, str] = {}
    for item in files:
        dest = item.dest.replace("\\", "/")
        if dest in dests and dests[dest] != item.adapter:
            raise AdapterConflictError(
                f"two adapters claim dest {dest}: {dests[dest]} and {item.adapter}"
            )
        if dest in dests:
            raise AdapterConflictError(f"duplicate dest {dest}")
        dests[dest] = item.adapter
    return files


def resolve_desired_state(
    *,
    profile_name: str,
    stack: StackReport,
    version: str,
) -> DesiredState:
    profile = resolve_profile(profile_name)
    pack_files = _collect_pack_files(profile)
    root = catalog_root()
    desired: list[DesiredFile] = []
    for item in pack_files:
        source_path = root / item.source
        if not source_path.is_file():
            raise CatalogError(f"template missing: {item.source}")
        raw = source_path.read_text(encoding="utf-8")
        content = render_template(
            raw,
            language=stack.language,
            profile=profile.name,
            version=version,
        )
        desired.append(
            DesiredFile(
                dest=item.dest.replace("\\", "/"),
                content=content,
                classification=item.classification,
                adapter=item.adapter,
                source=item.source,
            )
        )
    return DesiredState(profile=profile.name, stack=stack, files=desired)
