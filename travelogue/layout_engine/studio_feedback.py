"""Studio edit → LSE layout feedback sidecar (CAP-05 wiring)."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from travelogue.config import AppConfig, get_config
from travelogue.layout_contract.feedback import record_g1_edit
from travelogue.layout_engine.capabilities import effective_capabilities
from travelogue.layout_engine.feedback import append_layout_feedback
from travelogue.layout_engine.registry import get_strategy_pack


def _feedback_export_enabled(cfg: AppConfig) -> bool:
    if not cfg.layout.strategy_engine.enabled:
        return False
    pack = None
    try:
        se = cfg.layout.strategy_engine
        pack = get_strategy_pack(se.default_strategy_id, se.policy_path)
    except Exception:
        pack = None
    caps = effective_capabilities(cfg, pack)
    if caps.implicit_feedback_export:
        return True
    if pack is not None:
        fb = pack.raw.get("feedback") if isinstance(pack.raw.get("feedback"), dict) else {}
        return bool(fb.get("enabled", False))
    return bool(cfg.layout.strategy_engine.feedback.enabled)


def persist_studio_layout_feedback(
    trip_id: str,
    trip_dir: Path,
    before_trip: dict[str, Any],
    after_trip: dict[str, Any],
    *,
    cfg: AppConfig | None = None,
) -> dict[str, Any] | None:
    """Record implicit layout edit and append to runs/layout-feedback.jsonl when enabled."""
    app = cfg or get_config()
    if not _feedback_export_enabled(app):
        return None
    record = record_g1_edit(trip_id, before_trip, after_trip)
    path = append_layout_feedback(trip_dir, record, export_pairwise=True)
    if path is None:
        return None
    return {
        "feedbackPath": f"runs/{path.name}",
        "editType": record.edit_type,
        "distance": round(record.distance, 4),
    }
