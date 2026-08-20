"""PFM · trip.studio.edition + portfolio_pipeline parent switch."""

from __future__ import annotations

from dataclasses import replace

import pytest

from travelogue.config import AppConfig, PortfolioPipelineConfig, studio_config_expose
from travelogue.config.edition import (
    EDITION_JOURNAL,
    EDITION_PORTFOLIO,
    E_PORTFOLIO_UNAVAILABLE,
    PortfolioUnavailableError,
    apply_import_edition,
    is_portfolio_pipeline_enabled,
    is_portfolio_trip,
    normalize_edition,
    resolve_edition,
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


def test_portfolio_pipeline_defaults_off() -> None:
    cfg = AppConfig()
    assert is_portfolio_pipeline_enabled(cfg) is False
    pipe = studio_config_expose(cfg)["studio"]["portfolioPipeline"]
    assert pipe["enabled"] is False
    assert pipe["homepageEntry"] is False
    assert pipe["maxPages"] == 32
