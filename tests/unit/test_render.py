from __future__ import annotations

from agentic_sdlc.core.render import render_template


def test_framework_version_not_docker_version() -> None:
    text = "pkg {{framework_version}}\npattern={{version}}\n"
    out = render_template(text, language="python", profile="standard", version="0.2.0")
    assert "pkg 0.2.0" in out
    assert "pattern={{version}}" in out
