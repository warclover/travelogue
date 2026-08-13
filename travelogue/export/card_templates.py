"""3:4 card template registry (compiled mirror of docs/templates/card-aspect-3x4/*.md).

PRD-EXPORT-CARD-COMPOSE-V1 v0.5.0 / ADR-021 v0.5. The `.md` files under
``docs/templates/card-aspect-3x4/`` are the human-authored spec of record
(28 templates, slot counts {1,2,3,4,5,6,7,8,9,10,12,13,16}); this module is
the runtime data these specs compile to. Keep both in sync when either
changes.

Grid convention: each template is defined on its own ``grid_rows x
grid_cols`` base grid (default ``3x3``; the 4 equal-grid templates added in
v0.4.0 use ``2x1``/``2x2``/``4x2``/``4x4`` instead, and the 15 templates
added in v0.5.0 use ``2x2``/``2x4``/``4x4`` — a plain N-up split or a
non-3x3 user-designed layout has no natural 3x3 mapping). ``row``/``col``
are 0-indexed cell coordinates within *that* template's own grid;
``row_span``/``col_span`` are merge sizes. ``display_aspect`` is
width/height of the merged cell on a 3:4 canvas:

- ``0.75``  → portrait/square unit cell (1x1 on a 3x3/2x2/4x4 grid) or a
  2x2/2-row/2-col hero merge on any of those grids (same ratio as the 3:4
  canvas itself).
- ``1.5``   → landscape cell (a 3x3 grid's 1x2-col merge, a bare row on the
  2x1/4x2/2x4 equal-grid templates, or a 2-col/2-row merge on a 4x4 grid).
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

# -- docs/templates/card-aspect-3x4/card-3-mini-triband.md ------------------
# 2x2 grid: v0.5.0 batch — user mockup 第三批-图3 (2026-08-05).
CARD_3_MINI_TRIBAND = CardTemplate(
    id="card-3-mini-triband",
    display_name="三图 · 顶部两竖版 + 底部横版主图",
    grid_rows=2,
    grid_cols=2,
    slots=(
        CardSlot("portrait", 0, 0),
        CardSlot("portrait", 0, 1),
        CardSlot("main", 1, 0, col_span=2, display_aspect=1.5),
    ),
)

# -- docs/templates/card-aspect-3x4/card-5-hero-mid-landscape.md ------------
# 2x4 grid: v0.5.0 batch — user mockup 第三批-图4 (2026-08-05).
CARD_5_HERO_MID_LANDSCAPE = CardTemplate(
    id="card-5-hero-mid-landscape",
    display_name="五图 · 上下两横版 + 中部横版主图",
    grid_rows=4,
    grid_cols=2,
    slots=(
        CardSlot("landscape", 0, 0, display_aspect=1.5),
        CardSlot("landscape", 0, 1, display_aspect=1.5),
        CardSlot("main", 1, 0, row_span=2, col_span=2, display_aspect=1.5),
        CardSlot("landscape", 3, 0, display_aspect=1.5),
        CardSlot("landscape", 3, 1, display_aspect=1.5),
    ),
)

# -- docs/templates/card-aspect-3x4/card-6-pinwheel-diagonal.md -------------
# 2x4 grid: v0.5.0 batch — user mockup 补充图D (2026-08-05).
CARD_6_PINWHEEL_DIAGONAL = CardTemplate(
    id="card-6-pinwheel-diagonal",
    display_name="六图 · 风车对角",
    grid_rows=4,
    grid_cols=2,
    slots=(
        CardSlot("landscape", 0, 0, display_aspect=1.5),
        CardSlot("portrait", 0, 1, row_span=2),
        CardSlot("landscape", 1, 0, display_aspect=1.5),
        CardSlot("portrait", 2, 0, row_span=2),
        CardSlot("landscape", 2, 1, display_aspect=1.5),
        CardSlot("landscape", 3, 1, display_aspect=1.5),
    ),
)

# -- docs/templates/card-aspect-3x4/card-6-sandwich-bands.md ----------------
# 2x4 grid: v0.5.0 batch — user mockup 第三批-图6 (2026-08-05).
CARD_6_SANDWICH_BANDS = CardTemplate(
    id="card-6-sandwich-bands",
    display_name="六图 · 上下横版带 + 中部竖版双柱",
    grid_rows=4,
    grid_cols=2,
    slots=(
        CardSlot("landscape", 0, 0, display_aspect=1.5),
        CardSlot("landscape", 0, 1, display_aspect=1.5),
        CardSlot("portrait", 1, 0, row_span=2),
        CardSlot("portrait", 1, 1, row_span=2),
        CardSlot("landscape", 3, 0, display_aspect=1.5),
        CardSlot("landscape", 3, 1, display_aspect=1.5),
    ),
)

# -- docs/templates/card-aspect-3x4/card-7-hero-top-halves.md ---------------
# 4x4 grid: v0.5.0 batch — user mockup 补充图H，经 2026-08-05 编号标注确认 7 槙
# (顶部主图 + 左右各两个竖排小格 + 底部两个 2x2 竖版半区)。
CARD_7_HERO_TOP_HALVES = CardTemplate(
    id="card-7-hero-top-halves",
    display_name="七图 · 顶部主图 + 底部两等分",
    grid_rows=4,
    grid_cols=4,
    slots=(
        CardSlot("portrait", 0, 0),
        CardSlot("portrait", 0, 1, row_span=2, col_span=2),
        CardSlot("portrait", 0, 3),
        CardSlot("portrait", 1, 0),
        CardSlot("portrait", 1, 3),
        CardSlot("portrait", 2, 0, row_span=2, col_span=2),
        CardSlot("portrait", 2, 2, row_span=2, col_span=2),
    ),
)

# -- docs/templates/card-aspect-3x4/card-7-triband-hero-mid.md --------------
# 4x4 grid: v0.5.0 batch — user mockup 第三批-图5 (2026-08-05).
CARD_7_TRIBAND_HERO_MID = CardTemplate(
    id="card-7-triband-hero-mid",
    display_name="七图 · 三段式横版主图",
    grid_rows=4,
    grid_cols=4,
    slots=(
        CardSlot("portrait", 0, 0),
        CardSlot("portrait", 0, 1),
        CardSlot("landscape", 0, 2, col_span=2, display_aspect=1.5),
        CardSlot("main", 1, 0, row_span=2, col_span=4, display_aspect=1.5),
        CardSlot("landscape", 3, 0, col_span=2, display_aspect=1.5),
        CardSlot("portrait", 3, 2),
        CardSlot("portrait", 3, 3),
    ),
)

# -- docs/templates/card-aspect-3x4/card-8-pinwheel-diagonal.md -------------
# 4x4 grid: v0.5.0 batch — user mockup 第三批-图2 (2026-08-05).
CARD_8_PINWHEEL_DIAGONAL = CardTemplate(
    id="card-8-pinwheel-diagonal",
    display_name="八图 · 对角双主图风车",
    grid_rows=4,
    grid_cols=4,
    slots=(
        CardSlot("portrait", 0, 0),
        CardSlot("portrait", 0, 1),
        CardSlot("portrait", 0, 2, row_span=2, col_span=2),
        CardSlot("landscape", 1, 0, col_span=2, display_aspect=1.5),
        CardSlot("portrait", 2, 0, row_span=2, col_span=2),
        CardSlot("landscape", 2, 2, col_span=2, display_aspect=1.5),
        CardSlot("portrait", 3, 2),
        CardSlot("portrait", 3, 3),
    ),
)

# -- docs/templates/card-aspect-3x4/card-9-hero-mid-triband.md --------------
# 4x4 grid: v0.5.0 batch — user mockup 补充图E (2026-08-05).
CARD_9_HERO_MID_TRIBAND = CardTemplate(
    id="card-9-hero-mid-triband",
    display_name="九图 · 中部横版主图 + 上下四等分",
    grid_rows=4,
    grid_cols=4,
    slots=(
        CardSlot("portrait", 0, 0),
        CardSlot("portrait", 0, 1),
        CardSlot("portrait", 0, 2),
        CardSlot("portrait", 0, 3),
        CardSlot("main", 1, 0, row_span=2, col_span=4, display_aspect=1.5),
        CardSlot("portrait", 3, 0),
        CardSlot("portrait", 3, 1),
        CardSlot("portrait", 3, 2),
        CardSlot("portrait", 3, 3),
    ),
)

# -- docs/templates/card-aspect-3x4/card-10-dual-hero-column.md -------------
# 4x4 grid: v0.5.0 batch — user mockup 补充图F (2026-08-05).
CARD_10_DUAL_HERO_COLUMN = CardTemplate(
    id="card-10-dual-hero-column",
    display_name="十图 · 中列双主图堆叠",
    grid_rows=4,
    grid_cols=4,
    slots=(
        CardSlot("portrait", 0, 0),
        CardSlot("portrait", 0, 1, row_span=2, col_span=2),
        CardSlot("portrait", 0, 3),
        CardSlot("portrait", 1, 0),
        CardSlot("portrait", 1, 3),
        CardSlot("portrait", 2, 0),
        CardSlot("portrait", 2, 1, row_span=2, col_span=2),
        CardSlot("portrait", 2, 3),
        CardSlot("portrait", 3, 0),
        CardSlot("portrait", 3, 3),
    ),
)

# -- docs/templates/card-aspect-3x4/card-10-dual-hero-diagonal.md -----------
# 4x4 grid: v0.5.0 batch — user mockup 图1 (2026-08-05，含同日重绘确认版)。
CARD_10_DUAL_HERO_DIAGONAL = CardTemplate(
    id="card-10-dual-hero-diagonal",
    display_name="十图 · 左上右下对角双主图",
    grid_rows=4,
    grid_cols=4,
    slots=(
        CardSlot("portrait", 0, 0, row_span=2, col_span=2),
        CardSlot("portrait", 0, 2),
        CardSlot("portrait", 0, 3),
        CardSlot("portrait", 1, 2),
        CardSlot("portrait", 1, 3),
        CardSlot("portrait", 2, 0),
        CardSlot("portrait", 2, 1),
        CardSlot("portrait", 3, 0),
        CardSlot("portrait", 3, 1),
        CardSlot("portrait", 2, 2, row_span=2, col_span=2),
    ),
)

# -- docs/templates/card-aspect-3x4/card-12-alt-side-rows.md ----------------
# 4x4 grid: v0.5.0 batch — user mockup 图2 (2026-08-05 重绘确认版为准，原稿分栏
# 位置模糊)。
CARD_12_ALT_SIDE_ROWS = CardTemplate(
    id="card-12-alt-side-rows",
    display_name="十二图 · 逐行横竖版侧位交替",
    grid_rows=4,
    grid_cols=4,
    slots=(
        CardSlot("portrait", 0, 0),
        CardSlot("portrait", 0, 1),
        CardSlot("landscape", 0, 2, col_span=2, display_aspect=1.5),
        CardSlot("landscape", 1, 0, col_span=2, display_aspect=1.5),
        CardSlot("portrait", 1, 2),
        CardSlot("portrait", 1, 3),
        CardSlot("portrait", 2, 0),
        CardSlot("portrait", 2, 1),
        CardSlot("landscape", 2, 2, col_span=2, display_aspect=1.5),
        CardSlot("landscape", 3, 0, col_span=2, display_aspect=1.5),
        CardSlot("portrait", 3, 2),
        CardSlot("portrait", 3, 3),
    ),
)

# -- docs/templates/card-aspect-3x4/card-12-center-land-rows.md -------------
# 4x4 grid: v0.5.0 batch — user mockup 补充图G (2026-08-05)。
CARD_12_CENTER_LAND_ROWS = CardTemplate(
    id="card-12-center-land-rows",
    display_name="十二图 · 每行居中横版",
    grid_rows=4,
    grid_cols=4,
    slots=(
        CardSlot("portrait", 0, 0),
        CardSlot("landscape", 0, 1, col_span=2, display_aspect=1.5),
        CardSlot("portrait", 0, 3),
        CardSlot("portrait", 1, 0),
        CardSlot("landscape", 1, 1, col_span=2, display_aspect=1.5),
        CardSlot("portrait", 1, 3),
        CardSlot("portrait", 2, 0),
        CardSlot("landscape", 2, 1, col_span=2, display_aspect=1.5),
        CardSlot("portrait", 2, 3),
        CardSlot("portrait", 3, 0),
        CardSlot("landscape", 3, 1, col_span=2, display_aspect=1.5),
        CardSlot("portrait", 3, 3),
    ),
)

# -- docs/templates/card-aspect-3x4/card-12-sandwich-bands.md ---------------
# 4x4 grid: v0.5.0 batch — user mockup 第三批-图1 (2026-08-05)。
CARD_12_SANDWICH_BANDS = CardTemplate(
    id="card-12-sandwich-bands",
    display_name="十二图 · 上下竖版带 + 中部双横版带",
    grid_rows=4,
    grid_cols=4,
    slots=(
        CardSlot("portrait", 0, 0),
        CardSlot("portrait", 0, 1),
        CardSlot("portrait", 0, 2),
        CardSlot("portrait", 0, 3),
        CardSlot("landscape", 1, 0, col_span=2, display_aspect=1.5),
        CardSlot("landscape", 1, 2, col_span=2, display_aspect=1.5),
        CardSlot("landscape", 2, 0, col_span=2, display_aspect=1.5),
        CardSlot("landscape", 2, 2, col_span=2, display_aspect=1.5),
        CardSlot("portrait", 3, 0),
        CardSlot("portrait", 3, 1),
        CardSlot("portrait", 3, 2),
        CardSlot("portrait", 3, 3),
    ),
)

# -- docs/templates/card-aspect-3x4/card-13-hero-center-stack.md ------------
# 4x4 grid: v0.5.0 batch — user mockup 补充图C (2026-08-05)。主图位于*正中间*
# (rows1-2)，与 card-13-hero-top-stack（主图在顶部 rows0-1）是两套不同模板。
CARD_13_HERO_CENTER_STACK = CardTemplate(
    id="card-13-hero-center-stack",
    display_name="十三图 · 中部主图 + 上下四等分",
    grid_rows=4,
    grid_cols=4,
    slots=(
        CardSlot("portrait", 0, 0),
        CardSlot("portrait", 0, 1),
        CardSlot("portrait", 0, 2),
        CardSlot("portrait", 0, 3),
        CardSlot("portrait", 1, 0),
        CardSlot("portrait", 1, 1, row_span=2, col_span=2),
        CardSlot("portrait", 1, 3),
        CardSlot("portrait", 2, 0),
        CardSlot("portrait", 2, 3),
        CardSlot("portrait", 3, 0),
        CardSlot("portrait", 3, 1),
        CardSlot("portrait", 3, 2),
        CardSlot("portrait", 3, 3),
    ),
)

# -- docs/templates/card-aspect-3x4/card-13-hero-top-stack.md ---------------
# 4x4 grid: v0.5.0 batch — user mockup 补充图I，经 2026-08-05 编号标注确认主图
# 在*顶部*（rows0-1），下方两整排四等分，与 card-13-hero-center-stack 不同。
CARD_13_HERO_TOP_STACK = CardTemplate(
    id="card-13-hero-top-stack",
    display_name="十三图 · 顶部主图 + 下方两整排四等分",
    grid_rows=4,
    grid_cols=4,
    slots=(
        CardSlot("portrait", 0, 0),
        CardSlot("portrait", 0, 1, row_span=2, col_span=2),
        CardSlot("portrait", 0, 3),
        CardSlot("portrait", 1, 0),
        CardSlot("portrait", 1, 3),
        CardSlot("portrait", 2, 0),
        CardSlot("portrait", 2, 1),
        CardSlot("portrait", 2, 2),
        CardSlot("portrait", 2, 3),
        CardSlot("portrait", 3, 0),
        CardSlot("portrait", 3, 1),
        CardSlot("portrait", 3, 2),
        CardSlot("portrait", 3, 3),
    ),
)

_ALL_TEMPLATES: tuple[CardTemplate, ...] = (
    CARD_1_FULL_FRAME,
    CARD_2_STACK_EQUAL,
    CARD_3_MINI_TRIBAND,
    CARD_4_SQUARE_TOP_TRIBAND,
    CARD_4_GRID_EQUAL,
    CARD_5_HERO_MID_LANDSCAPE,
    CARD_6_HERO_TL_STACK,
    CARD_6_HERO_BR_STACK,
    CARD_6_BOOKEND_ROWS,
    CARD_6_BRICK_ALT,
    CARD_6_PINWHEEL_DIAGONAL,
    CARD_6_SANDWICH_BANDS,
    CARD_7_TRIBAND_2_2_3,
    CARD_7_TRIBAND_2_3_2,
    CARD_7_HERO_TOP_HALVES,
    CARD_7_TRIBAND_HERO_MID,
    CARD_8_GRID_EQUAL,
    CARD_8_PINWHEEL_DIAGONAL,
    CARD_9_GRID_EQUAL,
    CARD_9_HERO_MID_TRIBAND,
    CARD_10_DUAL_HERO_COLUMN,
    CARD_10_DUAL_HERO_DIAGONAL,
    CARD_12_ALT_SIDE_ROWS,
    CARD_12_CENTER_LAND_ROWS,
    CARD_12_SANDWICH_BANDS,
    CARD_13_HERO_CENTER_STACK,
    CARD_13_HERO_TOP_STACK,
    CARD_16_GRID_EQUAL,
)

CARD_TEMPLATES: dict[str, CardTemplate] = {t.id: t for t in _ALL_TEMPLATES}

#: AEL L3 probe registry (BLK-AEL-01). Independent of ``_ALL_TEMPLATES``.
#: L0 keeps this empty; L3 writes rectangular probes here only. Never merge
#: into ``CARD_TEMPLATES`` / ``AVAILABLE_SLOT_COUNTS``.
PROBE_TEMPLATES: dict[str, CardTemplate] = {}

#: Distinct slot counts actually available in the library, largest first.
#: Drives CardGrouper's greedy chunking (largest-fits-first).
AVAILABLE_SLOT_COUNTS: tuple[int, ...] = tuple(
    sorted({t.slot_count for t in _ALL_TEMPLATES}, reverse=True)
)

#: Single-poster template priority (PRD §5.2 / ADR-021 D4): prefer templates
#: with a ``main`` slot and no forced crop; ``card-4-square-top-triband`` is
#: the only crop-required fallback; templates without a main slot are unused
#: for the poster product.
#:
#: v0.5.0 note: the 4 new main-slot templates added alongside the 15-template
#: user-mockup batch (``card-3/5/7/9-*``) all have a *crop-free* main slot
#: (``display_aspect`` 0.75/1.5, same as ``card-1``/``card-6-hero-*``) — they
#: are ranked ahead of ``card-4-square-top-triband`` (the only crop-required
#: template) but after the original 3 (kept first for backward-compatible
#: poster selection; ``plan_poster_card`` itself is unchanged in v0.5.0 and
#: still only picks from the original 3 + the crop-required fallback — see
#: OQ-ECC-07 below for wiring the new candidates into that selection logic).
POSTER_TEMPLATE_PRIORITY: tuple[str, ...] = (
    "card-1-full-frame",
    "card-6-hero-tl-stack",
    "card-6-hero-br-stack",
    "card-3-mini-triband",
    "card-5-hero-mid-landscape",
    "card-7-triband-hero-mid",
    "card-9-hero-mid-triband",
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
