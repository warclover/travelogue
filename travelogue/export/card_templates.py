"""3:4 card template registry (compiled mirror of docs/templates/card-aspect-3x4/*.md).

PRD-EXPORT-CARD-COMPOSE-V1 v0.3.0 / ADR-021 v0.4. The `.md` files under
``docs/templates/card-aspect-3x4/`` are the human-authored spec of record
(9 templates, slot counts {1,4,6,7,9}); this module is the runtime data these
specs compile to. Keep both in sync when either changes.

Grid convention: every template is defined on a 3x3 base grid (``GRID=3``).
``row``/``col`` are 0-indexed cell coordinates; ``row_span``/``col_span`` are
merge sizes. ``display_aspect`` is width/height of the merged cell on a 3:4
canvas — only three values occur across the whole library:

- ``0.75``  → portrait/square unit cell (1x1) or the 2x2 hero cell (same
  ratio as the 3:4 canvas itself).
- ``1.5``   → landscape cell (1 row x 2 cols merged).
- ``1.125`` → the one near-square cell (2 rows x 3 cols merged), used only by
  ``card-4-square-top-triband``; the only slot in the library that requires a
  real crop (neither natural portrait nor landscape photos match it exactly).
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

SlotRole = Literal["portrait", "landscape", "main"]

GRID = 3


@dataclass(frozen=True)
class CardSlot:
    role: SlotRole
    row: int
    col: int
    row_span: int = 1
    col_span: int = 1
    display_aspect: float = 0.75


@dataclass(frozen=True)
class CardTemplate:
    id: str
    display_name: str
    slots: tuple[CardSlot, ...]

    @property
    def slot_count(self) -> int:
        return len(self.slots)

    @property
    def has_main_slot(self) -> bool:
        return any(s.role == "main" for s in self.slots)


# -- docs/templates/card-aspect-3x4/card-1-full-frame.md --------------------
CARD_1_FULL_FRAME = CardTemplate(
    id="card-1-full-frame",
    display_name="单图 · 满版",
    slots=(CardSlot("main", 0, 0, row_span=3, col_span=3, display_aspect=0.75),),
)

# -- docs/templates/card-aspect-3x4/card-4-square-top-triband.md ------------
CARD_4_SQUARE_TOP_TRIBAND = CardTemplate(
    id="card-4-square-top-triband",
    display_name="四图 · 顶部近方图 + 底部三竖版",
    slots=(
        CardSlot("main", 0, 0, row_span=2, col_span=3, display_aspect=1.125),
        CardSlot("portrait", 2, 0),
        CardSlot("portrait", 2, 1),
        CardSlot("portrait", 2, 2),
    ),
)

# -- docs/templates/card-aspect-3x4/card-6-hero-tl-stack.md -----------------
CARD_6_HERO_TL_STACK = CardTemplate(
    id="card-6-hero-tl-stack",
    display_name="六图 · 左上主图 + 右侧堆叠 + 底部三等分",
    slots=(
        CardSlot("main", 0, 0, row_span=2, col_span=2),
        CardSlot("portrait", 0, 2),
        CardSlot("portrait", 1, 2),
        CardSlot("portrait", 2, 0),
        CardSlot("portrait", 2, 1),
        CardSlot("portrait", 2, 2),
    ),
)

# -- docs/templates/card-aspect-3x4/card-6-hero-br-stack.md -----------------
CARD_6_HERO_BR_STACK = CardTemplate(
    id="card-6-hero-br-stack",
    display_name="六图 · 顶部三等分 + 左侧堆叠 + 右下主图",
    slots=(
        CardSlot("portrait", 0, 0),
        CardSlot("portrait", 0, 1),
        CardSlot("portrait", 0, 2),
        CardSlot("portrait", 1, 0),
        CardSlot("portrait", 2, 0),
        CardSlot("main", 1, 1, row_span=2, col_span=2),
    ),
)

# -- docs/templates/card-aspect-3x4/card-6-bookend-rows.md ------------------
CARD_6_BOOKEND_ROWS = CardTemplate(
    id="card-6-bookend-rows",
    display_name="六图 · 首尾呼应",
    slots=(
        CardSlot("landscape", 0, 0, col_span=2, display_aspect=1.5),
        CardSlot("portrait", 0, 2),
        CardSlot("landscape", 1, 0, col_span=2, display_aspect=1.5),
        CardSlot("portrait", 1, 2),
        CardSlot("portrait", 2, 0),
        CardSlot("landscape", 2, 1, col_span=2, display_aspect=1.5),
    ),
)

# -- docs/templates/card-aspect-3x4/card-6-brick-alt.md ---------------------
CARD_6_BRICK_ALT = CardTemplate(
    id="card-6-brick-alt",
    display_name="六图 · 逐行交替",
    slots=(
        CardSlot("landscape", 0, 0, col_span=2, display_aspect=1.5),
        CardSlot("portrait", 0, 2),
        CardSlot("portrait", 1, 0),
        CardSlot("landscape", 1, 1, col_span=2, display_aspect=1.5),
        CardSlot("landscape", 2, 0, col_span=2, display_aspect=1.5),
        CardSlot("portrait", 2, 2),
    ),
)

# -- docs/templates/card-aspect-3x4/card-7-triband-2-2-3.md -----------------
CARD_7_TRIBAND_2_2_3 = CardTemplate(
    id="card-7-triband-2-2-3",
    display_name="七图 · 第1/2行各两图，第3行三等分",
    slots=(
        CardSlot("landscape", 0, 0, col_span=2, display_aspect=1.5),
        CardSlot("portrait", 0, 2),
        CardSlot("portrait", 1, 0),
        CardSlot("landscape", 1, 1, col_span=2, display_aspect=1.5),
        CardSlot("portrait", 2, 0),
        CardSlot("portrait", 2, 1),
        CardSlot("portrait", 2, 2),
    ),
)

# -- docs/templates/card-aspect-3x4/card-7-triband-2-3-2.md -----------------
CARD_7_TRIBAND_2_3_2 = CardTemplate(
    id="card-7-triband-2-3-2",
    display_name="七图 · 第1/3行各两图，第2行三等分",
    slots=(
        CardSlot("landscape", 0, 0, col_span=2, display_aspect=1.5),
        CardSlot("portrait", 0, 2),
        CardSlot("portrait", 1, 0),
        CardSlot("portrait", 1, 1),
        CardSlot("portrait", 1, 2),
        CardSlot("portrait", 2, 0),
        CardSlot("landscape", 2, 1, col_span=2, display_aspect=1.5),
    ),
)

# -- docs/templates/card-aspect-3x4/card-9-grid-equal.md --------------------
CARD_9_GRID_EQUAL = CardTemplate(
    id="card-9-grid-equal",
    display_name="九图 · 3×3 等分",
    slots=tuple(
        CardSlot("portrait", row, col) for row in range(3) for col in range(3)
    ),
)

_ALL_TEMPLATES: tuple[CardTemplate, ...] = (
    CARD_1_FULL_FRAME,
    CARD_4_SQUARE_TOP_TRIBAND,
    CARD_6_HERO_TL_STACK,
    CARD_6_HERO_BR_STACK,
    CARD_6_BOOKEND_ROWS,
    CARD_6_BRICK_ALT,
    CARD_7_TRIBAND_2_2_3,
    CARD_7_TRIBAND_2_3_2,
    CARD_9_GRID_EQUAL,
)

CARD_TEMPLATES: dict[str, CardTemplate] = {t.id: t for t in _ALL_TEMPLATES}

#: Distinct slot counts actually available in the library, largest first.
#: Drives CardGrouper's greedy chunking (largest-fits-first).
AVAILABLE_SLOT_COUNTS: tuple[int, ...] = tuple(
    sorted({t.slot_count for t in _ALL_TEMPLATES}, reverse=True)
)

#: Single-poster template priority (PRD §5.2 / ADR-021 D4): prefer templates
#: with a ``main`` slot and no forced crop; ``card-4-square-top-triband`` is
#: the only crop-required fallback; templates without a main slot are unused
#: for the poster product.
POSTER_TEMPLATE_PRIORITY: tuple[str, ...] = (
    "card-1-full-frame",
    "card-6-hero-tl-stack",
    "card-6-hero-br-stack",
    "card-4-square-top-triband",
)


def templates_by_slot_count(n: int) -> list[CardTemplate]:
    """All templates with exactly ``n`` slots, sorted by id for determinism."""
    return sorted(
        (t for t in _ALL_TEMPLATES if t.slot_count == n), key=lambda t: t.id
    )


def pick_template_for_count(n: int, *, card_index: int = 0) -> CardTemplate:
    """Pick a template with ``n`` slots.

    OQ-ECC-04 default resolution (2026-08-05 review): when multiple templates
    share the same slot count, round-robin by ``card_index`` for visual
    variety across a multi-card export. Deterministic given the same inputs.
    """
    candidates = templates_by_slot_count(n)
    if not candidates:
        raise ValueError(f"no card template with slot_count={n}")
    return candidates[card_index % len(candidates)]
