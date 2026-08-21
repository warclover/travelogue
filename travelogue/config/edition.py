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
E_PORTFOLIO_PAGE_COUNT = "E_PORTFOLIO_PAGE_COUNT"
E_PORTFOLIO_PAGES_JOURNAL = "E_PORTFOLIO_PAGES_JOURNAL"
E_PORTFOLIO_PLATFORM_REQUIRED = "E_PORTFOLIO_PLATFORM_REQUIRED"
PORTFOLIO_UNAVAILABLE_MESSAGE = "作品集暂时排不出，可改回游记"
PORTFOLIO_PLATFORM_REQUIRED_MESSAGE = (
    "作品集须指定 --platform（portfolio_pages / wechat_chat）"
)

# Display fallback when series catalog has no photo_span yet (D-PFM-29).
DEFAULT_MIN_KEPT_DISPLAY = 12
# Align refine pin with trip.schema.json studio.portfolio.pageCount.
PAGE_COUNT_MIN = 4
PAGE_COUNT_MAX = 48


class PortfolioUnavailableError(CodeError):
    """Flag off, no series, or assembler cannot place a book."""

    def __init__(self, message: str = PORTFOLIO_UNAVAILABLE_MESSAGE) -> None:
        super().__init__(E_PORTFOLIO_UNAVAILABLE, message)


class PortfolioPlatformRequiredError(CodeError):
    """CLI · 作品集 trip 未传 --platform（D-PFM-31）。"""

    def __init__(self, message: str = PORTFOLIO_PLATFORM_REQUIRED_MESSAGE) -> None:
        super().__init__(E_PORTFOLIO_PLATFORM_REQUIRED, message)


def require_explicit_export_target(
    trip: Mapping[str, Any] | None,
    *,
    platform: object | None,
) -> None:
    """Journal may omit --platform. Portfolio must name one (AC-PFM-40)."""
    if not is_portfolio_trip(trip):
        return
    if str(platform or "").strip():
        return
    raise PortfolioPlatformRequiredError()


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


def min_kept_for_portfolio(cfg: AppConfig | None, *, catalog_min: int | None = None) -> int:
    """Wizard grey-out threshold (D-PFM-29). Override > catalog min span > 12."""
    override = portfolio_pipeline_config(cfg).min_kept_override
    if override is not None and int(override) > 0:
        return int(override)
    if catalog_min is not None and int(catalog_min) > 0:
        return int(catalog_min)
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


def apply_refine_edition(
    trip: dict[str, Any],
    raw_edition: object | None,
    cfg: AppConfig | None,
) -> str:
    """精修/书架切身份。改回游记清除 edition 字段，但保留 ``studio.portfolio``（D-PFM-17）。"""
    edition = normalize_edition(raw_edition)
    if edition == EDITION_PORTFOLIO:
        return apply_import_edition(trip, EDITION_PORTFOLIO, cfg)
    studio = trip.get("studio")
    if isinstance(studio, dict):
        studio.pop("edition", None)
        if not studio:
            trip.pop("studio", None)
    return EDITION_JOURNAL


def apply_refine_page_count(trip: dict[str, Any], raw: object | None) -> tuple[str, int | None]:
    """精修钉页数。``auto`` 清用户钉档；数字留给装配段靠档（D-PFM-13）。"""
    studio = trip.get("studio")
    if not isinstance(studio, dict):
        studio = {}
        trip["studio"] = studio
    folio = studio.get("portfolio")
    if not isinstance(folio, dict):
        folio = {}
        studio["portfolio"] = folio
    if raw is None or str(raw).strip().lower() in ("", "auto"):
        folio["pageCountSource"] = "auto"
        folio.pop("pageCount", None)
        match = folio.get("match")
        if isinstance(match, dict):
            match.pop("pageCountRequested", None)
            match.pop("pageCountHint", None)
        return "auto", None
    try:
        page_count = int(raw)
    except (TypeError, ValueError) as exc:
        raise ValueError("invalid page count") from exc
    if page_count < PAGE_COUNT_MIN or page_count > PAGE_COUNT_MAX:
        raise ValueError("invalid page count")
    folio["pageCountSource"] = "user"
    folio["pageCount"] = page_count
    return "user", page_count


def read_page_count_intent(trip: Mapping[str, Any] | None) -> tuple[str, int | None]:
    """Current refine pin: auto, or user + requested (pre-snap) count."""
    if not isinstance(trip, Mapping):
        return "auto", None
    studio = trip.get("studio")
    if not isinstance(studio, Mapping):
        return "auto", None
    folio = studio.get("portfolio")
    if not isinstance(folio, Mapping):
        return "auto", None
    source = str(folio.get("pageCountSource") or "auto").strip().lower() or "auto"
    if source != "user":
        return "auto", None
    match = folio.get("match") if isinstance(folio.get("match"), Mapping) else {}
    raw = match.get("pageCountRequested")
    if raw in (None, ""):
        raw = folio.get("pageCount")
    try:
        return "user", int(raw) if raw not in (None, "") else None
    except (TypeError, ValueError):
        return "user", None


def _clear_edition_field(trip: dict[str, Any]) -> None:
    studio = trip.get("studio")
    if not isinstance(studio, dict):
        return
    studio.pop("edition", None)
    studio.pop("portfolio", None)
    if not studio:
        trip.pop("studio", None)


def make_studio_edition_mutator(memory_trip: dict[str, Any]):
    """Persist ``studio.edition`` / ``portfolio`` / ``copyOrphans`` without clobbering LVP."""

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
            if mem_studio.get("copyOrphans"):
                disk_studio["copyOrphans"] = mem_studio["copyOrphans"]
            else:
                disk_studio.pop("copyOrphans", None)
        else:
            disk_studio.pop("edition", None)
            disk_studio.pop("portfolio", None)
            disk_studio.pop("copyOrphans", None)
        if disk_studio:
            disk_trip["studio"] = disk_studio
        elif "studio" in disk_trip and not disk_trip["studio"]:
            disk_trip.pop("studio", None)

    return mutator
