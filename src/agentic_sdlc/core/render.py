"""Trivial template substitution: language, profile, version."""

from __future__ import annotations


def render_template(text: str, *, language: str, profile: str, version: str) -> str:
    return (
        text.replace("{{language}}", language)
        .replace("{{profile}}", profile)
        .replace("{{framework_version}}", version)
    )
