"""Shared config enums (no service-layer imports)."""

from __future__ import annotations

VALID_NARRATIVE_SCOPES = frozenset({"frame", "frame_chapters", "full"})
VALID_ARC_MODES = frozenset({"legacy", "v2_adaptive", "v2_five_beat"})
