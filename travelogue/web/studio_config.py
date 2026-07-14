"""Resolve config.yaml for Studio (never auto-pick config.demo.yaml)."""

from __future__ import annotations

from pathlib import Path

from travelogue.paths import ROOT, is_frozen, user_config_path


def resolve_studio_config(explicit: Path | None = None) -> Path | None:
    """Prefer explicit --config, else user/project config.yaml (not demo overrides)."""
    if explicit is not None:
        return explicit.resolve()
    candidates: list[Path] = [Path.cwd() / "config.yaml"]
    if is_frozen():
        candidates.append(user_config_path())
    else:
        candidates.append(ROOT / "config.yaml")
    for candidate in candidates:
        if candidate.is_file():
            return candidate.resolve()
    return None
