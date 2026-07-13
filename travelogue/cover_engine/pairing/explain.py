"""Pairing explain copy (PRD userOneLiner)."""

from __future__ import annotations

from typing import Any


_DEGRADED_ONELINER = "可选照片太少，已省略封底图，避免与封面重复。"


def closing_user_one_liner(
    *,
    closing_asset_id: str | None,
    degraded: bool,
    unused: bool = False,
    hard_filtered: int = 0,
) -> str:
    if degraded or not closing_asset_id:
        return _DEGRADED_ONELINER
    if unused:
        return "封底选用了正文未出现的照片，与封面形成收束。"
    if hard_filtered:
        return "已避开与封面过于接近的照片，选出更顺的收束画面。"
    return "封底与封面成对挑选，收束这一路。"


def build_closing_explain(
    *,
    closing_asset_id: str | None,
    degraded: bool,
    scores: dict[str, float] | None = None,
    hard_filtered: int = 0,
    unused: bool = False,
    pairing_version: str = "v1",
    excluded_by_moment: list[str] | None = None,
) -> dict[str, Any]:
    excluded = [str(x) for x in (excluded_by_moment or []) if x]
    return {
        "phase": "closing",
        "userOneLiner": closing_user_one_liner(
            closing_asset_id=closing_asset_id,
            degraded=degraded,
            unused=unused,
            hard_filtered=hard_filtered,
        ),
        "closingAssetId": closing_asset_id,
        "degraded": degraded,
        "pairingHardFiltered": hard_filtered,
        "pairingVersion": pairing_version,
        "scores": scores or {},
        "excludedByMoment": excluded,
    }
