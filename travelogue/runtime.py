"""Application context: shared config and trip service construction."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING, Any

from travelogue.config import AppConfig, get_config

if TYPE_CHECKING:
    from travelogue.services.trip import TripService


@dataclass
class AppContext:
    """Single construction point for Studio/CLI trip access."""

    cfg: AppConfig
    trips_root: Path

    def trip_service(self) -> TripService:
        from travelogue.services.trip import TripService

        return TripService(root=self.trips_root.parent)


def app_context_from_handler(handler: Any) -> AppContext:
    """Build context from TripPreviewHandler / StudioMixin instance."""
    cfg = getattr(handler, "app_config", None) or get_config()
    trips_root = (getattr(handler, "trips_dir", None) or cfg.trips_dir).resolve()
    return AppContext(cfg=cfg, trips_root=trips_root)


def app_context_for_trips_dir(
    trips_dir: Path | None = None,
    *,
    cfg: AppConfig | None = None,
) -> AppContext:
    """CLI/Studio: trips root directory (contains trip id folders)."""
    active = cfg or get_config()
    trips_root = (trips_dir or active.trips_dir).resolve()
    return AppContext(cfg=active, trips_root=trips_root)


def app_context_for_trip_json(
    trip_json: Path,
    *,
    cfg: AppConfig | None = None,
) -> AppContext:
    """Derive trips root from ``…/trips/<id>/trip.json``."""
    trip_json = trip_json.resolve()
    trips_root = trip_json.parent.parent
    return AppContext(cfg=cfg or get_config(), trips_root=trips_root)
