"""Resolve config.yaml for Studio (never auto-pick config.demo.yaml)."""

from __future__ import annotations

from pathlib import Path

from travelogue.paths import ROOT


def resolve_studio_config(explicit: Path | None = None) -> Path | None:
    """Prefer explicit --config, else project config.yaml (not demo overrides)."""
    if explicit is not None:
        return explicit.resolve()
    for candidate in (Path.cwd() / "config.yaml", ROOT / "config.yaml"):
        if candidate.is_file():
            return candidate.resolve()
    return None
