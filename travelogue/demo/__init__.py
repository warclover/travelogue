"""Unified demo — album to HTML via official ingest/curate/render pipeline."""

from travelogue.demo.build import DemoError, DemoResult, run_demo_from_album
from travelogue.demo.from_album import demo_from_album, scan_album

__all__ = [
    "DemoError",
    "DemoResult",
    "demo_from_album",
    "run_demo_from_album",
    "scan_album",
]
