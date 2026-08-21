"""PFM · trip.studio.edition + portfolio_pipeline parent switch."""

from __future__ import annotations

from dataclasses import replace

import pytest

from travelogue.config import AppConfig, PortfolioPipelineConfig, studio_config_expose
from travelogue.config.edition import (
    EDITION_JOURNAL,
    EDITION_PORTFOLIO,
    E_PORTFOLIO_PLATFORM_REQUIRED,
    E_PORTFOLIO_UNAVAILABLE,
    PortfolioPlatformRequiredError,
    PortfolioUnavailableError,
    apply_import_edition,
    apply_refine_edition,
    apply_refine_page_count,
    make_studio_edition_mutator,
    read_page_count_intent,
    is_portfolio_pipeline_enabled,
    is_portfolio_trip,
    normalize_edition,
    require_explicit_export_target,
    resolve_edition,
)
from travelogue.config.layout_vibe import (
    VIBE_FIT_PHOTO_EXPERIMENTAL,
    VIBE_MAGAZINE_DEFAULT,
    set_trip_layout_vibe,
)

pytestmark = pytest.mark.unit


def _cfg(*, enabled: bool = False) -> AppConfig:
    base = AppConfig()
    return replace(
        base,
        studio=replace(
            base.studio,
            portfolio_pipeline=PortfolioPipelineConfig(enabled=enabled),
        ),
    )


def test_normalize_edition_unknown_is_journal() -> None:
    assert normalize_edition(None) == EDITION_JOURNAL
    assert normalize_edition("") == EDITION_JOURNAL
    assert normalize_edition("folio") == EDITION_PORTFOLIO
    assert normalize_edition("portfolio") == EDITION_PORTFOLIO
    assert normalize_edition("surface") == EDITION_JOURNAL


def test_missing_field_is_journal_and_not_portfolio() -> None:
    assert resolve_edition({}) == EDITION_JOURNAL
    assert resolve_edition({"studio": {}}) == EDITION_JOURNAL
    assert is_portfolio_trip({}) is False
    assert is_portfolio_trip({"studio": {"edition": "portfolio"}}) is True


def test_apply_import_edition_journal_does_not_write_field() -> None:
    trip: dict = {}
    assert apply_import_edition(trip, None, _cfg(enabled=True)) == EDITION_JOURNAL
    assert "studio" not in trip or "edition" not in trip.get("studio", {})


def test_apply_import_edition_flag_off_rejects_portfolio() -> None:
    with pytest.raises(PortfolioUnavailableError) as exc:
        apply_import_edition({}, "portfolio", _cfg(enabled=False))
    assert exc.value.code == E_PORTFOLIO_UNAVAILABLE


def test_apply_import_edition_flag_on_stamps_portfolio() -> None:
    trip: dict = {}
    assert apply_import_edition(trip, "portfolio", _cfg(enabled=True)) == EDITION_PORTFOLIO
    assert trip["studio"]["edition"] == "portfolio"
    assert trip["studio"]["portfolio"]["pageCountSource"] == "auto"
    assert "folio" not in trip["studio"]


def test_min_kept_override_beats_catalog() -> None:
    from travelogue.config.edition import min_kept_for_portfolio

    cfg = _cfg(enabled=True)
    cfg = replace(
        cfg,
        studio=replace(
            cfg.studio,
            portfolio_pipeline=PortfolioPipelineConfig(
                enabled=True, min_kept_override=30
            ),
        ),
    )
    assert min_kept_for_portfolio(cfg, catalog_min=8) == 30
    assert min_kept_for_portfolio(_cfg(), catalog_min=8) == 8
    assert min_kept_for_portfolio(_cfg()) == 12


def test_apply_refine_edition_journal_keeps_portfolio() -> None:
    trip = {
        "studio": {
            "edition": "portfolio",
            "portfolio": {"pageCount": 16, "seriesId": "magazine-16-standard"},
            "layoutVibe": "magazine_default",
        }
    }
    assert apply_refine_edition(trip, "journal", _cfg(enabled=True)) == EDITION_JOURNAL
    assert "edition" not in trip["studio"]
    assert trip["studio"]["portfolio"]["pageCount"] == 16
    assert trip["studio"]["layoutVibe"] == "magazine_default"


def test_apply_refine_page_count_auto_and_user() -> None:
    trip: dict = {"studio": {"edition": "portfolio", "portfolio": {}}}
    assert apply_refine_page_count(trip, 18) == ("user", 18)
    assert trip["studio"]["portfolio"]["pageCountSource"] == "user"
    assert trip["studio"]["portfolio"]["pageCount"] == 18
    assert apply_refine_page_count(trip, "auto") == ("auto", None)
    assert trip["studio"]["portfolio"]["pageCountSource"] == "auto"
    assert "pageCount" not in trip["studio"]["portfolio"]
    with pytest.raises(ValueError, match="invalid page count"):
        apply_refine_page_count(trip, 1)
    with pytest.raises(ValueError, match="invalid page count"):
        apply_refine_page_count(trip, 48)


def test_read_page_count_intent_prefers_requested() -> None:
    trip = {
        "studio": {
            "portfolio": {
                "pageCountSource": "user",
                "pageCount": 16,
                "match": {"pageCountRequested": 18},
            }
        }
    }
    assert read_page_count_intent(trip) == ("user", 18)
    assert read_page_count_intent({}) == ("auto", None)


def test_apply_refine_edition_flag_off_rejects_portfolio() -> None:
    with pytest.raises(PortfolioUnavailableError) as exc:
        apply_refine_edition({}, "portfolio", _cfg(enabled=False))
    assert exc.value.code == E_PORTFOLIO_UNAVAILABLE


def test_require_explicit_export_target_portfolio_only() -> None:
    require_explicit_export_target({}, platform=None)
    require_explicit_export_target({"studio": {}}, platform=None)
    require_explicit_export_target(
        {"studio": {"edition": "portfolio"}},
        platform="portfolio_pages",
    )
    require_explicit_export_target(
        {"studio": {"edition": "portfolio"}},
        platform="wechat_chat",
    )
    with pytest.raises(PortfolioPlatformRequiredError) as exc:
        require_explicit_export_target({"studio": {"edition": "portfolio"}}, platform=None)
    assert exc.value.code == E_PORTFOLIO_PLATFORM_REQUIRED
    assert "portfolio_pages" in str(exc.value)
    assert "wechat_chat" in str(exc.value)


def test_portfolio_pipeline_defaults_off() -> None:
    cfg = AppConfig()
    assert is_portfolio_pipeline_enabled(cfg) is False
    pipe = studio_config_expose(cfg)["studio"]["portfolioPipeline"]
    assert pipe["enabled"] is False
    assert pipe["homepageEntry"] is False
    assert pipe["maxPages"] == 32


def test_iso06_lvp_write_does_not_change_edition() -> None:
    trip = {
        "studio": {
            "edition": "portfolio",
            "layoutVibe": VIBE_MAGAZINE_DEFAULT,
            "portfolio": {"seriesId": "magazine-16-standard"},
        }
    }
    set_trip_layout_vibe(trip, VIBE_FIT_PHOTO_EXPERIMENTAL)
    assert trip["studio"]["edition"] == "portfolio"
    assert trip["studio"]["layoutVibe"] == VIBE_FIT_PHOTO_EXPERIMENTAL
    assert trip["studio"]["portfolio"]["seriesId"] == "magazine-16-standard"


def test_iso06_edition_switch_does_not_change_layout_vibe() -> None:
    trip = {
        "studio": {
            "edition": "portfolio",
            "layoutVibe": VIBE_FIT_PHOTO_EXPERIMENTAL,
            "portfolio": {"pageCount": 16},
        }
    }
    apply_refine_edition(trip, "journal", _cfg(enabled=True))
    assert "edition" not in trip["studio"]
    assert trip["studio"]["layoutVibe"] == VIBE_FIT_PHOTO_EXPERIMENTAL
    disk = {"studio": {"layoutVibe": VIBE_FIT_PHOTO_EXPERIMENTAL, "other": 1}}
    make_studio_edition_mutator(trip)(disk)
    assert disk["studio"]["layoutVibe"] == VIBE_FIT_PHOTO_EXPERIMENTAL
    assert "edition" not in disk["studio"]
