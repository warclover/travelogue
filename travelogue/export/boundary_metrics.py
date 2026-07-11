"""Playwright boundary collection for Longshot 2.0 content split."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from travelogue.export.content_splitter import BOUNDARY_WEIGHT, BoundaryPoint

# Frozen selectors · RENDER-CONTRACT §Longshot 2.0
PHOTO_SELECTORS = (
    ".media-card img",
    ".media-card__visual",
    ".layout-slot__img",
)
CARD_SELECTORS = (
    ".media-card",
    "[data-block='media-card']",
    ".layout-screen",
)
CHAPTER_SEPARATOR_SELECTORS = (
    ".chapter-separator",
    "[data-block='chapter-separator']",
)
CHAPTER_START_SELECTORS = ("section.chapter",)
COVER_SELECTORS = (
    ".cover-opening",
    ".cover-hero",
    "[data-block='cover-opening']",
    "[data-block='cover-hero']",
)

# Prefer TravelogueLongshot.collectBoundaryMetrics (capture-ready layout).
# Inline fallback keeps CLI/tests working when longshot.js is absent.
COLLECT_BOUNDARIES_JS = """
() => {
  if (window.TravelogueLongshot
      && typeof window.TravelogueLongshot.collectBoundaryMetrics === 'function') {
    return window.TravelogueLongshot.collectBoundaryMetrics();
  }
  const main = document.querySelector('main');
  if (!main) {
    return { scrollHeightCss: 0, boundariesCss: [0], boundaryKinds: ['start'], photoCells: [] };
  }
  const mainRect = main.getBoundingClientRect();
  const scrollTop = window.scrollY || document.documentElement.scrollTop || 0;
  const mainTop = mainRect.top + scrollTop;

  function yTop(el) {
    const r = el.getBoundingClientRect();
    return Math.round(r.top + scrollTop - mainTop);
  }
  function yBottom(el) {
    const r = el.getBoundingClientRect();
    return Math.round(r.bottom + scrollTop - mainTop);
  }

  const scrollHeightCss = Math.max(main.scrollHeight, main.offsetHeight, 1);
  /** @type {{y:number, kind:string, priority:number}[]} */
  const raw = [];

  function add(y, kind, priority) {
    if (!Number.isFinite(y)) return;
    const yy = Math.max(0, Math.min(scrollHeightCss, Math.round(y)));
    raw.push({ y: yy, kind, priority });
  }

  document.querySelectorAll('.cover-opening, .cover-hero, [data-block="cover-opening"], [data-block="cover-hero"]').forEach((el) => {
    add(yBottom(el), 'cover', 50);
  });
  document.querySelectorAll('.chapter-separator, [data-block="chapter-separator"]').forEach((el) => {
    add(yBottom(el), 'chapter_separator', 40);
  });
  Array.from(main.querySelectorAll('section.chapter')).forEach((el, idx) => {
    if (idx === 0) return;
    add(yTop(el), 'chapter_start', 30);
  });
  document.querySelectorAll('.media-card img, .media-card__visual, .layout-slot__img').forEach((el) => {
    add(yTop(el), 'photo', 20);
  });
  document.querySelectorAll('.layout-slot').forEach((el) => {
    add(yTop(el), 'photo', 20);
  });
  document.querySelectorAll('.media-card, [data-block="media-card"], .layout-screen').forEach((el) => {
    add(yTop(el), 'card', 10);
  });

  raw.push({ y: 0, kind: 'start', priority: 100 });
  raw.push({ y: scrollHeightCss, kind: 'end', priority: 100 });

  const byY = new Map();
  for (const item of raw) {
    const prev = byY.get(item.y);
    if (!prev || item.priority > prev.priority) byY.set(item.y, item);
  }
  const sorted = Array.from(byY.values()).sort((a, b) => a.y - b.y);

  /** @type {{top:number, bottom:number, w?:number, h?:number}[]} */
  const cellRaw = [];
  const seen = new Set();
  function addCell(el) {
    const r = el.getBoundingClientRect();
    if (r.width < 72 || r.height < 72) return;
    if (r.width < 120 && r.height < 120) return;
    const top = Math.max(0, Math.min(scrollHeightCss, yTop(el)));
    const bottom = Math.max(0, Math.min(scrollHeightCss, yBottom(el)));
    if (bottom - top < 72) return;
    const key = top + ':' + bottom;
    if (seen.has(key)) return;
    seen.add(key);
    cellRaw.push({ top, bottom, w: r.width, h: r.height });
  }
  document.querySelectorAll('.layout-slot__img, .media-card img, .media-card__visual').forEach(addCell);
  if (!cellRaw.length) {
    document.querySelectorAll('.layout-slot').forEach(addCell);
  }
  cellRaw.sort((a, b) => a.top - b.top || a.bottom - b.bottom);
  /** @type {{top:number, bottom:number}[]} */
  let photoCells = [];
  for (const c of cellRaw) {
    const prev = photoCells[photoCells.length - 1];
    if (prev && Math.abs(c.top - prev.top) <= 2) {
      if (c.bottom > prev.bottom) photoCells[photoCells.length - 1] = c;
      continue;
    }
    photoCells.push({ top: c.top, bottom: c.bottom });
  }
  if (photoCells.length >= 3) {
    const heights = photoCells.map((c) => c.bottom - c.top).sort((a, b) => a - b);
    const median = heights[Math.floor(heights.length / 2)] || 1;
    const minH = Math.max(72, Math.floor(median * 0.28));
    photoCells = photoCells.filter((c) => c.bottom - c.top >= minH);
  }

  return {
    scrollHeightCss,
    boundariesCss: sorted.map((x) => x.y),
    boundaryKinds: sorted.map((x) => x.kind),
    photoCells,
  };
}
"""


@dataclass(frozen=True)
class PhotoCell:
    """One photo visual in main CSS coordinates (top inclusive, bottom exclusive-ish)."""

    top_css: float
    bottom_css: float

    def top_canvas(self, scale: int | float) -> int:
        return int(round(float(self.top_css) * float(scale)))

    def bottom_canvas(self, scale: int | float) -> int:
        return int(round(float(self.bottom_css) * float(scale)))

    @property
    def height_css(self) -> float:
        return max(0.0, float(self.bottom_css) - float(self.top_css))


@dataclass(frozen=True)
class BoundaryMetrics:
    scroll_height_css: float
    boundaries_css: list[float]
    boundary_kinds: list[str]
    photo_cells: list[PhotoCell] = field(default_factory=list)

    def as_points(self) -> list[BoundaryPoint]:
        points: list[BoundaryPoint] = []
        for y, kind in zip(self.boundaries_css, self.boundary_kinds):
            if kind in ("start", "end"):
                continue
            points.append(BoundaryPoint(float(y), str(kind)))
        return points

    def weight_for_index(self, index: int) -> float:
        kind = self.boundary_kinds[index] if 0 <= index < len(self.boundary_kinds) else "photo"
        return BOUNDARY_WEIGHT.get(kind, 1.0)


def filter_photo_cells(
    cells: list[PhotoCell],
    *,
    min_height_css: float = 72.0,
    median_ratio: float = 0.28,
) -> list[PhotoCell]:
    """Drop thin / junk cells (defense in depth after JS filter)."""
    if not cells:
        return []
    cleaned = [c for c in cells if c.height_css >= min_height_css]
    if len(cleaned) < 3:
        return cleaned
    heights = sorted(c.height_css for c in cleaned)
    median = heights[len(heights) // 2] or 1.0
    floor = max(min_height_css, median * float(median_ratio))
    return [c for c in cleaned if c.height_css >= floor]


def collect_boundaries(page: Any) -> BoundaryMetrics:
    """Evaluate boundary JS on a Playwright page."""
    payload = page.evaluate(COLLECT_BOUNDARIES_JS)
    return parse_boundary_payload(payload)


def parse_boundary_payload(payload: dict[str, Any] | None) -> BoundaryMetrics:
    data = payload or {}
    scroll = float(data.get("scrollHeightCss") or 0)
    boundaries = [float(x) for x in (data.get("boundariesCss") or [])]
    kinds = [str(x) for x in (data.get("boundaryKinds") or [])]
    if not boundaries:
        boundaries = [0.0, max(scroll, 1.0)]
        kinds = ["start", "end"]
    while len(kinds) < len(boundaries):
        kinds.append("photo")
    kinds = kinds[: len(boundaries)]
    if scroll <= 0:
        scroll = max(boundaries[-1] if boundaries else 1.0, 1.0)
    cells: list[PhotoCell] = []
    for raw in data.get("photoCells") or []:
        if not isinstance(raw, dict):
            continue
        try:
            top = float(raw.get("top"))
            bottom = float(raw.get("bottom"))
        except (TypeError, ValueError):
            continue
        if bottom - top < 1:
            continue
        cells.append(PhotoCell(top_css=top, bottom_css=bottom))
    cells = filter_photo_cells(cells)
    return BoundaryMetrics(
        scroll_height_css=scroll,
        boundaries_css=boundaries,
        boundary_kinds=kinds,
        photo_cells=cells,
    )


def count_photos_heuristic(page: Any) -> int:
    """Best-effort photo count for moments page-count rules."""
    return int(
        page.evaluate(
            """() => {
              if (window.TravelogueLongshot
                  && typeof window.TravelogueLongshot.collectBoundaryMetrics === 'function') {
                const m = window.TravelogueLongshot.collectBoundaryMetrics();
                if (m && m.photoCells && m.photoCells.length) return m.photoCells.length;
              }
              const slots = document.querySelectorAll(
                '.layout-slot__img, .media-card img, .media-card__visual'
              );
              if (slots.length) return slots.length;
              return 0;
            }"""
        )
        or 0
    )
