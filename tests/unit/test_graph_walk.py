from __future__ import annotations

from pathlib import Path

from agentic_sdlc.core.graph import walk_graph
from agentic_sdlc.core.models import NodeWalkStatus


def test_empty_repo_ready_at_intent(tmp_path: Path) -> None:
    report = walk_graph(tmp_path)
    assert report.next_ids == ["intent"]
    by_id = {n.id: n for n in report.nodes}
    assert by_id["intent"].status is NodeWalkStatus.READY
    assert by_id["spec"].status is NodeWalkStatus.BLOCKED
    assert by_id["intent"].action
    assert "sdlc/intent.md" in by_id["intent"].action


def test_intent_unlocks_spec(tmp_path: Path) -> None:
    path = tmp_path / "sdlc" / "intent.md"
    path.parent.mkdir(parents=True)
    path.write_text("# intent\n", encoding="utf-8")
    report = walk_graph(tmp_path)
    by_id = {n.id: n for n in report.nodes}
    assert by_id["intent"].status is NodeWalkStatus.COMPLETE
    assert report.next_ids == ["spec"]


def test_plan_missing_headings(tmp_path: Path) -> None:
    sdlc = tmp_path / "sdlc"
    sdlc.mkdir()
    for name in ("intent.md", "spec.md"):
        (sdlc / name).write_text("ok\n", encoding="utf-8")
    (sdlc / "plan.md").write_text("# plan\n\n## objective\nship it\n", encoding="utf-8")
    report = walk_graph(tmp_path)
    plan = next(n for n in report.nodes if n.id == "plan")
    assert plan.status is NodeWalkStatus.READY
    assert plan.missing_headings
    assert "files to change" in plan.missing_headings
