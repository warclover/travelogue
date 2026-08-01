"""Shared config enums (no service-layer imports)."""

from __future__ import annotations

VALID_NARRATIVE_SCOPES = frozenset({"frame", "frame_chapters", "full"})
VALID_ARC_MODES = frozenset({"legacy", "v2_adaptive", "v2_five_beat"})

# CSC Happy Path surface keys (layer-0) · shared by recipe + Studio config expose.
RECIPE_ID_STUDIO_DEFAULT = "studio_default"

L0_OPS_ROOTS: tuple[str, ...] = (
    "trips_dir",
    "llm",
    "ffmpeg",
    "geocode",
)

L1_RESULT_KEYS: tuple[str, ...] = (
    "clustering.enabled",
    "vision.enabled",
    "ingest.copy_source_files",
)

ADVANCED_SETTINGS_KEYS: tuple[str, ...] = (
    "layout.scoring.enabled",
    "studio.g1_confirm_structure",
)
