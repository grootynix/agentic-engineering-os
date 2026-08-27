"""Walk a catalog graph against artifacts on disk. Deterministic; no LLM."""

from __future__ import annotations

from pathlib import Path

from agentic_sdlc.core.models import (
    Graph,
    GraphNode,
    GraphWalkReport,
    NodeWalk,
    NodeWalkStatus,
)
from agentic_sdlc.core.resolve import load_graph


def _preds(graph: Graph) -> dict[str, list[str]]:
    preds: dict[str, list[str]] = {n.id: [] for n in graph.nodes}
    for edge in graph.edges:
        preds[edge.target].append(edge.source)
    return preds


def _heading_present(text: str, heading: str) -> bool:
    needle = heading.strip().lower()
    if not needle:
        return True
    lowered = text.lower()
    if needle in lowered:
        return True
    slug = needle.replace(" ", "")
    compact = lowered.replace(" ", "").replace("#", "")
    return slug in compact


def _inspect_node(root: Path, node: GraphNode) -> tuple[bool, list[str]]:
    if not node.artifact:
        return True, []
    path = root / node.artifact
    if not path.is_file():
        return False, list(node.required_headings)
    text = path.read_text(encoding="utf-8")
    missing = [h for h in node.required_headings if not _heading_present(text, h)]
    return not missing, missing


def walk_graph(root: Path, *, name: str = "sdlc") -> GraphWalkReport:
    root = root.resolve()
    graph = load_graph(name)
    preds = _preds(graph)
    complete: dict[str, bool] = {}
    missing_h: dict[str, list[str]] = {}
    for node in graph.nodes:
        ok, missing = _inspect_node(root, node)
        complete[node.id] = ok
        missing_h[node.id] = missing

    walked: list[NodeWalk] = []
    next_ids: list[str] = []
    for node in graph.nodes:
        parents = preds[node.id]
        parents_ok = all(complete[p] for p in parents)
        artifact = node.artifact
        if complete[node.id]:
            status = NodeWalkStatus.COMPLETE
            action = None
        elif parents_ok:
            status = NodeWalkStatus.READY
            next_ids.append(node.id)
            if artifact:
                if not (root / artifact).is_file():
                    action = f"Create {artifact} for node {node.id}"
                else:
                    action = (
                        f"Add missing headings to {artifact}: "
                        + ", ".join(missing_h[node.id])
                    )
            else:
                action = f"Complete graph node {node.id}"
        else:
            status = NodeWalkStatus.BLOCKED
            wait = [p for p in parents if not complete[p]]
            action = f"Finish predecessor node(s): {', '.join(wait)}"
        walked.append(
            NodeWalk(
                id=node.id,
                label=node.label,
                artifact=artifact,
                status=status,
                missing_headings=missing_h[node.id],
                action=action,
            )
        )
    return GraphWalkReport(name=graph.name, path=str(root), nodes=walked, next_ids=next_ids)
