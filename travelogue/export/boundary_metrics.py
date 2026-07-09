"""Playwright boundary collection for Longshot 2.0 content split."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from travelogue.export.content_splitter import BOUNDARY_WEIGHT, BoundaryPoint

# Frozen selectors · RENDER-CONTRACT §Longshot 2.0
PHOTO_SELECTORS = (
    ".media-card img",
    ".media-card__visual",
    ".layout-slot",
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
CHAPTER_START_SELECTORS = (
    "section.chapter",
)
COVER_SELECTORS = (
    ".cover-opening",
    ".cover-hero",
    "[data-block='cover-opening']",
    "[data-block='cover-hero']",
)

COLLECT_BOUNDARIES_JS = """
() => {
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

  // Deduplicate by y: keep highest priority
  const byY = new Map();
  for (const item of raw) {
    const prev = byY.get(item.y);
    if (!prev || item.priority > prev.priority) byY.set(item.y, item);
  }
  const sorted = Array.from(byY.values()).sort((a, b) => a.y - b.y);

  // Photo cells (top/bottom) for photo_led Moments — prefer visual/img over slot wrappers
  /** @type {{top:number, bottom:number}[]} */
  const cellRaw = [];
  const seen = new Set();
  function addCell(el) {
    const top = Math.max(0, Math.min(scrollHeightCss, yTop(el)));
    const bottom = Math.max(0, Math.min(scrollHeightCss, yBottom(el)));
    if (bottom - top < 8) return;
    const key = top + ':' + bottom;
    if (seen.has(key)) return;
    seen.add(key);
    cellRaw.push({ top, bottom });
  }
  document.querySelectorAll('.layout-slot__img, .media-card img, .media-card__visual').forEach(addCell);
  if (!cellRaw.length) {
    document.querySelectorAll('.layout-slot').forEach(addCell);
  }
  if (!cellRaw.length) {
    document.querySelectorAll('main img').forEach(addCell);
  }
  cellRaw.sort((a, b) => a.top - b.top || a.bottom - b.bottom);
  // Drop nested/overlapping duplicates (keep outer-most by top, then taller)
  /** @type {{top:number, bottom:number}[]} */
  const photoCells = [];
  for (const c of cellRaw) {
    const prev = photoCells[photoCells.length - 1];
    if (prev && Math.abs(c.top - prev.top) <= 2) {
      if (c.bottom > prev.bottom) photoCells[photoCells.length - 1] = c;
      continue;
    }
    photoCells.push(c);
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
              const slots = document.querySelectorAll('.layout-slot__img, .media-card img, .media-card__visual');
              if (slots.length) return slots.length;
              return document.querySelectorAll('main img').length;
            }"""
        )
        or 0
    )
