"""PFM · editorial_series catalog isolation and W1 hard-fail gate."""

from __future__ import annotations

from pathlib import Path

import pytest

from travelogue.config.edition import E_PORTFOLIO_UNAVAILABLE, PortfolioUnavailableError
from travelogue.layout_engine.editorial_series.catalog import (
    SERIES_DIR,
    assert_not_reserve_path,
    load_official_series,
    official_series_dir,
)
from travelogue.layout_engine.editorial_series.compose import compose_portfolio_trip
from travelogue.paths import ROOT

pytestmark = pytest.mark.unit


def test_official_series_dir_is_not_reserve() -> None:
    reserve = (ROOT / "docs" / "templates" / "reserve").resolve()
    runtime = official_series_dir().resolve()
    assert runtime == SERIES_DIR.resolve()
    with pytest.raises(ValueError):
        runtime.relative_to(reserve)


def test_load_official_series_skips_folio_prefix(tmp_path: Path) -> None:
    (tmp_path / "folio-16-trial.yaml").write_text("id: folio-16-trial\n", encoding="utf-8")
    (tmp_path / "magazine-16-standard.yaml").write_text(
        "id: magazine-16-standard\nphoto_span: [12, 48]\n",
        encoding="utf-8",
    )
    loaded = load_official_series(series_dir=tmp_path)
    assert [row["id"] for row in loaded] == ["magazine-16-standard"]


def test_assert_not_reserve_path_rejects_atelier() -> None:
    reserve_file = ROOT / "docs" / "templates" / "reserve" / "catalog.yaml"
    with pytest.raises(ValueError, match="must not read"):
        assert_not_reserve_path(reserve_file)
    assert_not_reserve_path(SERIES_DIR)


def test_compose_portfolio_trip_empty_catalog_hard_fails() -> None:
    with pytest.raises(PortfolioUnavailableError) as exc:
        compose_portfolio_trip([])
    assert exc.value.code == E_PORTFOLIO_UNAVAILABLE


def test_curate_fork_source_contract() -> None:
    """Journal still calls compose_trip; portfolio never silent-falls back."""
    from travelogue.curation import curate as curate_mod

    src = Path(curate_mod.__file__).read_text(encoding="utf-8")
    assert "is_portfolio_trip" in src
    assert "compose_portfolio_trip" in src
    assert "from travelogue.layout_engine.api import compose_trip" in src
    assert "禁止静默掉回" in src or "never silent" in src.lower() or "禁止静默" in src
