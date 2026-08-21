"""Select a magazine series and compute overflow cap (D-PFM-13 / D-PFM-21)."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping, Sequence


def photo_span(series: Mapping[str, Any]) -> tuple[int, int]:
    raw = series.get("photo_span") or series.get("photoSpan") or [0, 0]
    if isinstance(raw, (list, tuple)) and len(raw) >= 2:
        lo, hi = int(raw[0] or 0), int(raw[1] or 0)
        if hi < lo:
            lo, hi = hi, lo
        return lo, hi
    return 0, 0


PAGE_COUNT_CHIPS: tuple[int, ...] = (8, 12, 16, 20, 24, 28, 32, 36, 40, 44, 48)
PAGE_COUNT_SNAP_HINT = "非标准页数 · 按 {n} 页靠档"


def page_count_of(series: Mapping[str, Any]) -> int:
    return int(series.get("pageCount") or series.get("page_count") or 0)


FILL_RATE_LO = 0.85
FILL_RATE_HI = 1.05
OVERFLOW_TOLERANCE = 0.05


def series_capacity(series: Mapping[str, Any]) -> int:
    """Unique intake cap (D-MSP-07). ``photo_span`` is advisory only."""
    raw = series.get("capacity")
    if raw not in (None, ""):
        try:
            n = int(raw)
            if n > 0:
                return n
        except (TypeError, ValueError):
            pass
    total = 0
    for page in series.get("sequence") or []:
        if not isinstance(page, Mapping):
            continue
        try:
            band = int(page.get("slotBand") or page.get("slot_band") or 0)
        except (TypeError, ValueError):
            band = 0
        if band > 0:
            total += band
    return total


def catalog_chip_details(
    catalog: Sequence[Mapping[str, Any]],
    *,
    max_pages: int = 48,
) -> list[dict[str, int]]:
    """UI chip payloads: pages + baked capacity (BLK-MSP-09)."""
    by_pages: dict[int, int] = {}
    for row in catalog:
        pages = page_count_of(row)
        if not (0 < pages <= int(max_pages)):
            continue
        cap = series_capacity(row)
        if pages not in by_pages or cap > by_pages[pages]:
            by_pages[pages] = cap
    return [{"pages": n, "capacity": by_pages[n]} for n in sorted(by_pages)]


def catalog_page_count_chips(
    catalog: Sequence[Mapping[str, Any]],
    *,
    max_pages: int = 48,
) -> list[int]:
    """UI chips = official SKUs only. Empty catalog → no numeric chips (auto only)."""
    return sorted(
        {
            page_count_of(s)
            for s in catalog
            if 0 < page_count_of(s) <= int(max_pages)
        }
    )


def snap_to_chip(raw: int, *, max_pages: int = 48) -> int:
    """Nearest 4-multiple chip in 8…max_pages. Ties go down (D-PFM-13)."""
    chips = [c for c in PAGE_COUNT_CHIPS if c <= int(max_pages)]
    if not chips:
        return int(max_pages)
    n = int(raw)
    return min(chips, key=lambda c: (abs(c - n), c))


def snap_user_page_count(
    requested: int,
    catalog: Sequence[Mapping[str, Any]],
    *,
    max_pages: int = 48,
) -> tuple[int, str | None]:
    """Chip-snap, then nearest catalog SKU. Hint when used ≠ requested (AC-PFM-12)."""
    chip = snap_to_chip(int(requested), max_pages=max_pages)
    available = sorted(
        {
            page_count_of(s)
            for s in catalog
            if 0 < page_count_of(s) <= int(max_pages)
        }
    )
    used = chip
    if available and chip not in available:
        used = min(available, key=lambda c: (abs(c - chip), c))
    hint = PAGE_COUNT_SNAP_HINT.format(n=used) if used != int(requested) else None
    return used, hint


def _version(series: Mapping[str, Any]) -> int:
    try:
        return int(series.get("version") or 0)
    except (TypeError, ValueError):
        return 0


def _pick_latest(rows: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    ranked = sorted(
        rows,
        key=lambda s: (_version(s), str(s.get("id") or "")),
        reverse=True,
    )
    return dict(ranked[0])


@dataclass(frozen=True)
class SeriesChoice:
    series: dict[str, Any]
    kept_n: int
    cap: int
    upgraded: bool
    capped: bool

    @property
    def overflow_count(self) -> int:
        return max(0, self.kept_n - self.cap)

    @property
    def overflow_resolution(self) -> str | None:
        if self.overflow_count <= 0:
            return None
        if self.upgraded and self.capped:
            return "tier_upgraded_then_capped"
        if self.upgraded:
            return "tier_upgraded"
        return "capped"


def select_series(
    catalog: Sequence[Mapping[str, Any]],
    *,
    kept_n: int,
    density: str = "standard",
    page_count: int | None = None,
    page_count_source: str = "auto",
    max_pages: int = 48,
) -> SeriesChoice | None:
    """Pick one series. ``None`` only when the catalog is empty after filters."""
    density_key = str(density or "standard").strip().lower() or "standard"
    candidates = [
        dict(s)
        for s in catalog
        if str(s.get("density") or "standard").strip().lower() == density_key
    ]
    if not candidates:
        candidates = [dict(s) for s in catalog]
    if not candidates:
        return None

    bounded = [
        s
        for s in candidates
        if 0 < page_count_of(s) <= int(max_pages)
    ] or list(candidates)

    source = str(page_count_source or "auto").strip().lower()
    if source == "user" and page_count:
        pinned = [s for s in bounded if page_count_of(s) == int(page_count)]
        if not pinned:
            return None
        hit = _pick_latest(pinned)
        cap = series_capacity(hit)
        take = min(int(kept_n), cap) if cap > 0 else int(kept_n)
        return SeriesChoice(
            series=hit,
            kept_n=int(kept_n),
            cap=max(0, take),
            upgraded=False,
            capped=int(kept_n) > take,
        )

    scored: list[tuple[dict[str, Any], int, float]] = []
    for raw in bounded:
        row = dict(raw)
        cap = series_capacity(row)
        if cap <= 0:
            continue
        scored.append((row, cap, int(kept_n) / cap))
    if not scored:
        hit = _pick_latest(bounded)
        return SeriesChoice(
            series=dict(hit),
            kept_n=int(kept_n),
            cap=int(kept_n),
            upgraded=False,
            capped=False,
        )

    smallest_pages = min(page_count_of(s) for s, _cap, _ratio in scored)

    def _choice(
        row: dict[str, Any],
        cap: int,
        *,
        overflow_ok: bool = False,
    ) -> SeriesChoice:
        take = cap if overflow_ok else min(int(kept_n), cap)
        return SeriesChoice(
            series=row,
            kept_n=int(kept_n),
            cap=max(0, take),
            upgraded=page_count_of(row) > smallest_pages,
            capped=int(kept_n) > take,
        )

    window = [
        item for item in scored if FILL_RATE_LO <= item[2] <= FILL_RATE_HI
    ]
    if window:
        row, cap, _ratio = min(
            window,
            key=lambda item: (page_count_of(item[0]), str(item[0].get("id") or "")),
        )
        return _choice(row, cap, overflow_ok=int(kept_n) > cap)

    over = [item for item in scored if item[1] < int(kept_n)]
    under = [item for item in scored if item[1] >= int(kept_n)]
    if over:
        row, cap, _ratio = max(
            over,
            key=lambda item: (page_count_of(item[0]), _version(item[0])),
        )
        if (int(kept_n) - cap) / int(kept_n) <= OVERFLOW_TOLERANCE:
            return _choice(row, cap, overflow_ok=True)
    if under:
        row, cap, _ratio = min(
            under,
            key=lambda item: (item[1], page_count_of(item[0])),
        )
        return _choice(row, cap)
    row, cap, _ratio = max(
        scored,
        key=lambda item: (page_count_of(item[0]), _version(item[0])),
    )
    return _choice(row, cap)


def groups_from_assets(
    assets: Sequence[Mapping[str, Any]] | None,
    buckets: Sequence[Sequence[str]] | None = None,
) -> list[dict[str, Any]]:
    """Preserve shot-group order. Solo assets (no id) become their own group."""
    groups: list[dict[str, Any]] = []
    index: dict[str, dict[str, Any]] = {}
    if assets:
        for raw in assets:
            aid = str(raw.get("id") or raw.get("assetId") or "").strip()
            if not aid:
                continue
            gid = str(raw.get("shotGroupId") or "").strip() or f"solo-{aid}"
            kind = str(raw.get("shotGroupKind") or "scene").strip() or "scene"
            rec = index.get(gid)
            if rec is None:
                rec = {"id": gid, "kind": kind, "asset_ids": []}
                index[gid] = rec
                groups.append(rec)
            rec["asset_ids"].append(aid)
        return groups
    for i, bucket in enumerate(buckets or ()):
        ids = [str(x).strip() for x in bucket if str(x).strip()]
        if ids:
            groups.append({"id": f"bucket-{i}", "kind": "scene", "asset_ids": ids})
    return groups
