"""Assemble a portfolio trip: series match → screens[].

W1: official series catalog is empty (AS-PFM-01). Fail hard — never silent
journal fallback while still labelled portfolio (D-PFM-16 / AC-PFM-11).
"""

from __future__ import annotations

from typing import Any

from travelogue.config.edition import (
    PORTFOLIO_UNAVAILABLE_MESSAGE,
    PortfolioUnavailableError,
)
from travelogue.layout_engine.editorial_series.catalog import load_official_series


def compose_portfolio_trip(
    chapters: list[dict[str, Any]],
    **_kwargs: Any,
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    """Return ``(chapters, replan_meta)`` or raise ``PortfolioUnavailableError``.

    Signature accepts the same kwargs as ``compose_trip`` so ``run_curate`` can
    branch without copying the call site. Matcher body lands after AS-PFM-01.
    """
    series = load_official_series()
    if not series:
        raise PortfolioUnavailableError(PORTFOLIO_UNAVAILABLE_MESSAGE)
    # Future: select series, group→page, write screens[]. Until then the
    # catalog is the gate — a non-empty catalog without a matcher is also a miss.
    raise PortfolioUnavailableError(PORTFOLIO_UNAVAILABLE_MESSAGE)
