"""Trip JSON load-time migrations (M-B6 · PRD §5.5).

Version rules (trip.version):
- Add optional fields without bumping (e.g. meta.revision defaults to 0).
- Semantic change or field removal bumps the minor version.
- migrate_trip applies registered migrations in order for trips at or below each step.
- Supported load window: MIN_SUPPORTED_TRIP_VERSION … CURRENT_TRIP_VERSION (one minor back).
"""

from __future__ import annotations

from collections.abc import Callable

CURRENT_TRIP_VERSION = "0.2"
MIN_SUPPORTED_TRIP_VERSION = "0.2"


class TripVersionError(ValueError):
    """Readable error when trip.version is outside the supported window."""

    def __init__(self, version: str, *, supported: str = CURRENT_TRIP_VERSION) -> None:
        super().__init__(
            f"trip.version {version!r} is not supported; "
            f"upgrade Travelogue or migrate the file (supported: {supported})"
        )
        self.version = version
        self.supported = supported


def strip_legacy_curation_fields(trip: dict) -> dict:
    """Remove deprecated curation.insights (ADR-007 · PRD §11)."""
    curation = trip.get("curation")
    if isinstance(curation, dict) and "insights" in curation:
        cleaned = dict(curation)
        cleaned.pop("insights", None)
        trip["curation"] = cleaned
    return trip


MigrationFn = Callable[[dict], dict]

MIGRATIONS: list[tuple[str, MigrationFn]] = [
    ("0.2", strip_legacy_curation_fields),
]


def _trip_version(trip: dict) -> str:
    raw = trip.get("version")
    if raw is None or raw == "":
        return MIN_SUPPORTED_TRIP_VERSION
    return str(raw)


def _assert_supported_version(version: str) -> None:
    if version != CURRENT_TRIP_VERSION:
        if version < MIN_SUPPORTED_TRIP_VERSION or version > CURRENT_TRIP_VERSION:
            raise TripVersionError(version)


def migrate_trip(trip: dict) -> dict:
    """Apply registered migrations in order for the trip's version."""
    version = _trip_version(trip)
    _assert_supported_version(version)
    body = trip
    for target_version, migrate_fn in MIGRATIONS:
        if version <= target_version:
            body = migrate_fn(body)
    return body
