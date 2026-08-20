"""PFM · trip.studio.edition (journal | portfolio).

Identity lives here — ``layoutEngine`` stays ``screens`` (D-PFM-04).
Journal trips must not persist ``studio.edition`` (D-PFM-32).
"""

from __future__ import annotations

from typing import Any, Mapping

from travelogue.config.app import AppConfig
from travelogue.config.studio import PortfolioPipelineConfig
from travelogue.errors import CodeError

EDITION_JOURNAL = "journal"
EDITION_PORTFOLIO = "portfolio"
KNOWN_EDITIONS = frozenset({EDITION_JOURNAL, EDITION_PORTFOLIO})

E_PORTFOLIO_UNAVAILABLE = "E_PORTFOLIO_UNAVAILABLE"
PORTFOLIO_UNAVAILABLE_MESSAGE = "作品集暂时排不出，可改回游记"

# Display fallback when series catalog has no photo_span yet (D-PFM-29).
DEFAULT_MIN_KEPT_DISPLAY = 12


class PortfolioUnavailableError(CodeError):
    """Flag off, no series, or assembler cannot place a book."""

    def __init__(self, message: str = PORTFOLIO_UNAVAILABLE_MESSAGE) -> None:
        super().__init__(E_PORTFOLIO_UNAVAILABLE, message)


def normalize_edition(raw: object | None) -> str:
    """Unknown / blank → journal. Never invent a third value."""
    text = str(raw or "").strip().lower()
    if text in ("portfolio", "folio"):
        # ``folio`` is a forbidden identifier (D-PFM-01); still map inbound aliases.
        return EDITION_PORTFOLIO
    return EDITION_JOURNAL


def read_trip_edition(trip: Mapping[str, Any] | None) -> str | None:
    """Raw stored value, or None when the field is absent (journal default)."""
    if not isinstance(trip, Mapping):
        return None
    studio = trip.get("studio")
    if not isinstance(studio, Mapping):
        return None
    raw = studio.get("edition")
    if raw is None or str(raw).strip() == "":
        return None
    return str(raw).strip().lower()


def resolve_edition(trip: Mapping[str, Any] | None) -> str:
    """Authoritative edition. Missing field ≡ journal (D-PFM-32)."""
    return normalize_edition(read_trip_edition(trip))


def is_portfolio_trip(trip: Mapping[str, Any] | None) -> bool:
    return resolve_edition(trip) == EDITION_PORTFOLIO


def portfolio_pipeline_config(cfg: AppConfig | None) -> PortfolioPipelineConfig:
    studio = getattr(cfg, "studio", None) if cfg is not None else None
    pipe = getattr(studio, "portfolio_pipeline", None) if studio is not None else None
    return pipe if isinstance(pipe, PortfolioPipelineConfig) else PortfolioPipelineConfig()


def is_portfolio_pipeline_enabled(cfg: AppConfig | None) -> bool:
    return bool(portfolio_pipeline_config(cfg).enabled)


def min_kept_for_portfolio(cfg: AppConfig | None) -> int:
    """Wizard grey-out threshold. Override wins; else display fallback."""
    override = portfolio_pipeline_config(cfg).min_kept_override
    if override is not None and int(override) > 0:
        return int(override)
    return DEFAULT_MIN_KEPT_DISPLAY


def apply_import_edition(
    trip: dict[str, Any],
    raw_edition: object | None,
    cfg: AppConfig | None,
) -> str:
    """Stamp portfolio identity on a new trip. Journal leaves the field unset.

    Raises ``PortfolioUnavailableError`` when the user asked for portfolio but
    the parent switch is off (AC-PFM-07).
    """
    edition = normalize_edition(raw_edition)
    if edition != EDITION_PORTFOLIO:
        _clear_edition_field(trip)
        return EDITION_JOURNAL
    if not is_portfolio_pipeline_enabled(cfg):
        raise PortfolioUnavailableError("此功能已关闭")
    studio = trip.get("studio")
    if not isinstance(studio, dict):
        studio = {}
        trip["studio"] = studio
    studio["edition"] = EDITION_PORTFOLIO
    folio = studio.get("portfolio")
    if not isinstance(folio, dict):
        folio = {}
        studio["portfolio"] = folio
    folio.setdefault("pageCountSource", "auto")
    return EDITION_PORTFOLIO


def _clear_edition_field(trip: dict[str, Any]) -> None:
    studio = trip.get("studio")
    if not isinstance(studio, dict):
        return
    studio.pop("edition", None)
    studio.pop("portfolio", None)
    if not studio:
        trip.pop("studio", None)


def make_studio_edition_mutator(memory_trip: dict[str, Any]):
    """Persist ``studio.edition`` / ``studio.portfolio`` without clobbering LVP."""

    def mutator(disk_trip: dict[str, Any]) -> None:
        mem_studio = memory_trip.get("studio")
        disk_studio = disk_trip.get("studio")
        if not isinstance(disk_studio, dict):
            disk_studio = {}
        if isinstance(mem_studio, dict):
            if "edition" in mem_studio:
                disk_studio["edition"] = mem_studio["edition"]
            else:
                disk_studio.pop("edition", None)
            if "portfolio" in mem_studio:
                disk_studio["portfolio"] = mem_studio["portfolio"]
            elif "edition" not in mem_studio:
                disk_studio.pop("portfolio", None)
        else:
            disk_studio.pop("edition", None)
            disk_studio.pop("portfolio", None)
        if disk_studio:
            disk_trip["studio"] = disk_studio
        elif "studio" in disk_trip and not disk_trip["studio"]:
            disk_trip.pop("studio", None)

    return mutator
