from __future__ import annotations

from agentic_sdlc.core.resolve import resolve_profile


def test_standard_has_core() -> None:
    profile = resolve_profile("standard")
    assert profile.name == "standard"
    assert profile.packs == ["core"]


def test_secure_extends_standard() -> None:
    profile = resolve_profile("secure")
    assert profile.name == "secure"
    assert profile.packs == ["core"]
    assert profile.controls.get("secret_scanning") is True


def test_regulated_extends_secure() -> None:
    profile = resolve_profile("regulated")
    assert profile.name == "regulated"
    assert profile.packs == ["core"]
    assert profile.controls.get("secret_scanning") is True
    assert profile.controls.get("audit_log") is True
