"""Playwright boundary collection for Longshot 2.0 content split."""

from __future__ import annotations

from dataclasses import dataclass
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
    return { scrollHeightCss: 0, boundariesCss: [0], boundaryKinds: ['start'] };
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
  return {
    scrollHeightCss,
    boundariesCss: sorted.map((x) => x.y),
    boundaryKinds: sorted.map((x) => x.kind),
  };
}
"""


@dataclass(frozen=True)
class BoundaryMetrics:
    scroll_height_css: float
    boundaries_css: list[float]
    boundary_kinds: list[str]

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
    return BoundaryMetrics(
        scroll_height_css=scroll,
        boundaries_css=boundaries,
        boundary_kinds=kinds,
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
