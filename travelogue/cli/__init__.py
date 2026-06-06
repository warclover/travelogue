"""Travelogue CLI."""

from __future__ import annotations

# Register commands (import side effects)
from travelogue.cli import cluster as _cluster  # noqa: F401
from travelogue.cli import demo as _demo  # noqa: F401
from travelogue.cli import pipeline as _pipeline  # noqa: F401
from travelogue.cli import render_cmds as _render_cmds  # noqa: F401
from travelogue.cli import trip as _trip  # noqa: F401
from travelogue.cli._apps import app as app
from travelogue.cli._apps import cluster_app as cluster_app
from travelogue.cli._apps import demo_app as demo_app
from travelogue.cli._apps import llm_app as llm_app
from travelogue.cli._apps import media_app as media_app
from travelogue.cli._apps import tier_app as tier_app
from travelogue.cli._apps import trip_app as trip_app


def main() -> None:
    app()


if __name__ == "__main__":
    main()

__all__ = [
    "app",
    "cluster_app",
    "demo_app",
    "llm_app",
    "main",
    "media_app",
    "tier_app",
    "trip_app",
]
