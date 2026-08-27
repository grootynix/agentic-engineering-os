from __future__ import annotations

import yaml

from agentic_sdlc.core.models import Graph, Pack, Profile, StackDef, catalog_root
from agentic_sdlc.core.resolve import list_profiles, load_graph, load_pack, load_profile


def test_profiles_load() -> None:
    names = list_profiles()
    assert set(names) >= {"standard", "secure", "regulated"}
    for name in names:
        Profile.model_validate(load_profile(name).model_dump())


def test_core_pack_load() -> None:
    pack = load_pack("core")
    dests = {f.dest for f in pack.files}
    assert "AGENTS.md" in dests
    assert "CLAUDE.md" in dests
    assert ".agentic/INDEX.md" in dests
    assert ".agentic/config.yaml" in dests
    assert ".cursor/rules/agentic-os.mdc" in dests
    assert ".cursor/skills/using-agentic-sdlc/SKILL.md" in dests
    assert ".claude/skills/using-agentic-sdlc/SKILL.md" in dests
    Pack.model_validate(pack.model_dump(by_alias=True))


def test_guidance_pack_load() -> None:
    pack = load_pack("guidance")
    dests = {f.dest for f in pack.files}
    assert ".cursor/skills/threat-model/SKILL.md" in dests
    assert ".claude/agents/security-reviewer.md" in dests
    Pack.model_validate(pack.model_dump(by_alias=True))


def test_graph_load_and_validate() -> None:
    graph = load_graph("sdlc")
    ids = [n.id for n in graph.nodes]
    assert ids == [
        "intent",
        "spec",
        "plan",
        "implementation",
        "verification",
        "review",
        "pr",
    ]
    assert len(graph.edges) == 6
    assert graph.nodes[2].artifact == "sdlc/plan.md"
    Graph.model_validate(graph.model_dump(by_alias=True))


def test_stacks_load() -> None:
    stacks_dir = catalog_root() / "stacks"
    ids = []
    for path in stacks_dir.glob("*.yaml"):
        data = yaml.safe_load(path.read_text(encoding="utf-8"))
        stack = StackDef.model_validate(data)
        ids.append(stack.id)
    assert set(ids) >= {"python", "typescript", "go", "java", "terraform"}
