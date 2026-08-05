"""3:4 card template registry (compiled mirror of docs/templates/card-aspect-3x4/*.md).

PRD-EXPORT-CARD-COMPOSE-V1 v0.4.0 / ADR-021 v0.5. The `.md` files under
``docs/templates/card-aspect-3x4/`` are the human-authored spec of record
(13 templates, slot counts {1,2,4,6,7,8,9,16}); this module is the runtime
data these specs compile to. Keep both in sync when either changes.

Grid convention: each template is defined on its own ``grid_rows x
grid_cols`` base grid (default ``3x3``; the 4 equal-grid templates added in
v0.4.0 use ``2x1``/``2x2``/``4x2``/``4x4`` instead — a plain N-up split has no
natural 3x3 mapping). ``row``/``col`` are 0-indexed cell coordinates within
*that* template's own grid; ``row_span``/``col_span`` are merge sizes.
``display_aspect`` is width/height of the merged cell on a 3:4 canvas:

- ``0.75``  → portrait/square unit cell (1x1 on a 3x3/2x2/4x4 grid) or the
  2x2 hero cell on the 3x3 grid (same ratio as the 3:4 canvas itself).
- ``1.5``   → landscape cell (a 3x3 grid's 1x2-col merge, or a bare row on
  the 2x1/4x2 equal-grid templates).
- ``1.125`` → the one near-square cell (2 rows x 3 cols merged on the 3x3
  grid), used only by ``card-4-square-top-triband``; the only slot in the
  whole library that requires a real crop (neither natural portrait nor
  landscape photos match it exactly).
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

SlotRole = Literal["portrait", "landscape", "main"]

#: Legacy alias — the original 9 templates all use a 3x3 base grid.
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
    #: Base grid this template's slot row/col coordinates are defined on.
    #: Defaults to 3x3 (all 9 original templates); equal-grid templates
    #: (card-2/4/8/16-grid-equal) declare their own N-up grid instead.
    grid_rows: int = 3
    grid_cols: int = 3

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

# -- docs/templates/card-aspect-3x4/card-2-stack-equal.md -------------------
# 2x1 grid (not 3x3): a single horizontal split into two wide bands.
CARD_2_STACK_EQUAL = CardTemplate(
    id="card-2-stack-equal",
    display_name="两图 · 上下等分",
    grid_rows=2,
    grid_cols=1,
    slots=(
        CardSlot("landscape", 0, 0, display_aspect=1.5),
        CardSlot("landscape", 1, 0, display_aspect=1.5),
    ),
)

# -- docs/templates/card-aspect-3x4/card-4-grid-equal.md --------------------
# 2x2 grid (not 3x3): plain four-up split, distinct from
# card-4-square-top-triband (which has a main slot + forced crop).
CARD_4_GRID_EQUAL = CardTemplate(
    id="card-4-grid-equal",
    display_name="四图 · 2×2 等分",
    grid_rows=2,
    grid_cols=2,
    slots=tuple(
        CardSlot("portrait", row, col, display_aspect=0.75)
        for row in range(2)
        for col in range(2)
    ),
)

# -- docs/templates/card-aspect-3x4/card-8-grid-equal.md --------------------
# 4x2 grid (not 3x3): four rows of two wide cells each.
CARD_8_GRID_EQUAL = CardTemplate(
    id="card-8-grid-equal",
    display_name="八图 · 4×2 等分",
    grid_rows=4,
    grid_cols=2,
    slots=tuple(
        CardSlot("landscape", row, col, display_aspect=1.5)
        for row in range(4)
        for col in range(2)
    ),
)

# -- docs/templates/card-aspect-3x4/card-16-grid-equal.md -------------------
# 4x4 grid (not 3x3): dense equal grid, denser variant of card-9-grid-equal.
CARD_16_GRID_EQUAL = CardTemplate(
    id="card-16-grid-equal",
    display_name="十六图 · 4×4 等分",
    grid_rows=4,
    grid_cols=4,
    slots=tuple(
        CardSlot("portrait", row, col, display_aspect=0.75)
        for row in range(4)
        for col in range(4)
    ),
)

_ALL_TEMPLATES: tuple[CardTemplate, ...] = (
    CARD_1_FULL_FRAME,
    CARD_2_STACK_EQUAL,
    CARD_4_SQUARE_TOP_TRIBAND,
    CARD_4_GRID_EQUAL,
    CARD_6_HERO_TL_STACK,
    CARD_6_HERO_BR_STACK,
    CARD_6_BOOKEND_ROWS,
    CARD_6_BRICK_ALT,
    CARD_7_TRIBAND_2_2_3,
    CARD_7_TRIBAND_2_3_2,
    CARD_8_GRID_EQUAL,
    CARD_9_GRID_EQUAL,
    CARD_16_GRID_EQUAL,
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
