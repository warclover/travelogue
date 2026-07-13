"""VL / MLLM rerank plugin hooks (PRD §6.5 · B3). Default off; fail-open."""

from __future__ import annotations

from typing import Any, Protocol


class OpeningVlRerank(Protocol):
    def rerank_opening(
        self,
        trip: dict,
        candidates: list[dict[str, Any]],
    ) -> list[dict[str, Any]]:
        """Return reordered candidates; must not raise to callers (engine wraps)."""


class ClosingVlRerank(Protocol):
    def rerank_closing(
        self,
        trip: dict,
        candidates: list[dict[str, Any]],
        *,
        cover_asset_id: str | None = None,
    ) -> list[dict[str, Any]]:
        """Return reordered closing candidates; fail-open on error."""


def opening_vl_enabled() -> bool:
    try:
        from travelogue.config import get_config

        return bool(get_config().bookends.plugins.opening_vl_rerank)
    except Exception:
        return False


def closing_vl_enabled() -> bool:
    try:
        from travelogue.config import get_config

        return bool(get_config().bookends.plugins.closing_vl_rerank)
    except Exception:
        return False


def apply_opening_vl_rerank(
    trip: dict,
    candidates: list[dict[str, Any]],
    plugin: OpeningVlRerank | None = None,
) -> list[dict[str, Any]]:
    """No-op unless config enabled and plugin provided. Fail-open."""
    if not opening_vl_enabled() or plugin is None or not candidates:
        return candidates
    try:
        out = plugin.rerank_opening(trip, candidates)
        return out if isinstance(out, list) and out else candidates
    except Exception:
        return candidates


def apply_closing_vl_rerank(
    trip: dict,
    candidates: list[dict[str, Any]],
    *,
    cover_asset_id: str | None = None,
    plugin: ClosingVlRerank | None = None,
) -> list[dict[str, Any]]:
    if not closing_vl_enabled() or plugin is None or not candidates:
        return candidates
    try:
        out = plugin.rerank_closing(
            trip, candidates, cover_asset_id=cover_asset_id
        )
        return out if isinstance(out, list) and out else candidates
    except Exception:
        return candidates
