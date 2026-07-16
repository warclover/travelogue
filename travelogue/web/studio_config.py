"""Resolve config.yaml for Studio (never auto-pick config.demo.yaml)."""

from __future__ import annotations

import logging
import os
from pathlib import Path

from travelogue.paths import ROOT, is_frozen, user_config_path

_log = logging.getLogger(__name__)


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


def resolve_studio_trips_dir(
    *,
    cli_trips_dir: Path | None,
    cfg_trips_dir: Path,
) -> tuple[Path, str]:
    """Resolve Studio trips root (BE-FTUE-04).

    Priority: ``--trips-dir`` > ``TRAVELOGUE_TRIPS_DIR`` > ``config.yaml`` ``trips_dir``.

    Returns ``(resolved_path, source)`` where source is ``cli`` | ``env`` | ``config``.
    """
    if cli_trips_dir is not None:
        root = Path(cli_trips_dir).expanduser().resolve()
        return root, "cli"
    env = (os.environ.get("TRAVELOGUE_TRIPS_DIR") or "").strip()
    if env:
        root = Path(env).expanduser().resolve()
        return root, "env"
    root = Path(cfg_trips_dir).expanduser().resolve()
    return root, "config"


def log_studio_trips_dir(root: Path, source: str) -> None:
    """INFO log for FTUE dogfood / desktop studio.log."""
    _log.info("studio trips_dir source=%s path=%s", source, root)
