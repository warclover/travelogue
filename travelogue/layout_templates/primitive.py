"""L0 primitive template generation (PRD §4.2 · W4)."""

from __future__ import annotations

from travelogue.layout_templates.models import (
    TemplateDef,
    TemplateSlot,
    TemplateStage,
)


def uniform_grid_primitive(
    *,
    template_id: str,
    cols: int,
    rows: int,
    slot_count: int | None = None,
    role: str = "any",
    status: str = "experimental",
    display_name: str | None = None,
) -> TemplateDef:
    """Build a uniform-grid primitive TemplateDef (cols×rows tracks, equal fr)."""
    if cols < 1 or rows < 1:
        raise ValueError("cols and rows must be positive")
    count = slot_count if slot_count is not None else cols * rows
    if count < 1 or count > cols * rows:
        raise ValueError("slot_count must be in 1..cols*rows")
    stage_cols = tuple([1.0] * cols)
    stage_rows = tuple([1.0] * rows)
    slots: list[TemplateSlot] = []
    idx = 0
    for r in range(1, rows + 1):
        for c in range(1, cols + 1):
            if idx >= count:
                break
            slots.append(
                TemplateSlot(
                    index=idx,
                    rect=(c, c, r, r),
                    role=role,
                    fit="auto",
                )
            )
            idx += 1
        if idx >= count:
            break
    grid_class = f"layout-screen__grid--uniform-{cols}x{rows}-{count}"
    return TemplateDef(
        id=template_id,
        version=1,
        status=status,
        kind="primitive",
        display_name=display_name or f"uniform {cols}×{rows} · {count}",
        description="Generated uniform-grid primitive",
        aesthetic=None,
        balance_policy=None,
        stage=TemplateStage(aspect="16:9", cols=stage_cols, rows=stage_rows, grid=(cols, rows)),
        photo_count_min=count,
        photo_count_max=count,
        mix_portrait=None,
        mix_landscape=None,
        slots=tuple(slots),
        constraints={},
        compatibility_hints={},
        scoring={"base_weight": 1.0},
        render_grid_class=grid_class,
        render_css_bundle="journal-screens.css",
        render_fit_policy="auto_delegate",
        rollout={},
        raw={},
    )


def single_slot_primitive(
    *,
    template_id: str,
    stage_aspect: str,
    role: str,
    grid_class: str,
    mix_portrait: int = 0,
    mix_landscape: int = 0,
    kind: str = "primitive",
    status: str = "ga",
    display_name: str,
    description: str,
    tags: tuple[str, ...] = (),
) -> TemplateDef:
    return TemplateDef(
        id=template_id,
        version=1,
        status=status,
        kind=kind,
        display_name=display_name,
        description=description,
        aesthetic=None,
        balance_policy=None,
        stage=TemplateStage(aspect=stage_aspect, cols=(1.0,), rows=(1.0,), grid=(1, 1)),
        photo_count_min=1,
        photo_count_max=1,
        mix_portrait=mix_portrait,
        mix_landscape=mix_landscape,
        slots=(TemplateSlot(index=0, rect=(1, 1, 1, 1), role=role, fit="cover"),),
        constraints={},
        compatibility_hints={},
        scoring={"base_weight": 1.0, "tags": list(tags)},
        render_grid_class=grid_class,
        render_css_bundle="journal-screens.css",
        render_fit_policy="auto_delegate",
        rollout={},
        raw={},
    )


def column_grid_primitive(
    *,
    template_id: str,
    columns: int,
    role: str,
    grid_class: str,
    mix_portrait: int,
    mix_landscape: int,
    display_name: str,
    description: str,
    status: str = "ga",
    stage_aspect: str = "16:9",
) -> TemplateDef:
    if columns < 2:
        raise ValueError("columns must be >= 2")
    slots = tuple(
        TemplateSlot(index=i, rect=(i + 1, i + 1, 1, 1), role=role, fit="cover")
        for i in range(columns)
    )
    return TemplateDef(
        id=template_id,
        version=1,
        status=status,
        kind="primitive",
        display_name=display_name,
        description=description,
        aesthetic=None,
        balance_policy=None,
        stage=TemplateStage(
            aspect=stage_aspect,
            cols=tuple([1.0] * columns),
            rows=(1.0,),
            grid=(columns, 1),
        ),
        photo_count_min=columns,
        photo_count_max=columns,
        mix_portrait=mix_portrait,
        mix_landscape=mix_landscape,
        slots=slots,
        constraints={},
        compatibility_hints={},
        scoring={"base_weight": 1.0, "tags": [role]},
        render_grid_class=grid_class,
        render_css_bundle="journal-screens.css",
        render_fit_policy="auto_delegate",
        rollout={},
        raw={},
    )


def matrix_grid_primitive(
    *,
    template_id: str,
    cols: int,
    rows: int,
    role: str,
    grid_class: str,
    mix_portrait: int,
    mix_landscape: int,
    display_name: str,
    description: str,
    status: str = "ga",
    stage_aspect: str = "16:9",
) -> TemplateDef:
    """Uniform cols×rows grid with one slot per cell (portrait-4 / landscape-6)."""
    if cols < 1 or rows < 1:
        raise ValueError("cols and rows must be positive")
    count = cols * rows
    slots: list[TemplateSlot] = []
    idx = 0
    for r in range(1, rows + 1):
        for c in range(1, cols + 1):
            slots.append(
                TemplateSlot(index=idx, rect=(c, c, r, r), role=role, fit="cover")
            )
            idx += 1
    return TemplateDef(
        id=template_id,
        version=1,
        status=status,
        kind="primitive",
        display_name=display_name,
        description=description,
        aesthetic=None,
        balance_policy=None,
        stage=TemplateStage(
            aspect=stage_aspect,
            cols=tuple([1.0] * cols),
            rows=tuple([1.0] * rows),
            grid=(cols, rows),
        ),
        photo_count_min=count,
        photo_count_max=count,
        mix_portrait=mix_portrait,
        mix_landscape=mix_landscape,
        slots=tuple(slots),
        constraints={},
        compatibility_hints={},
        scoring={"base_weight": 1.0, "tags": [role]},
        render_grid_class=grid_class,
        render_css_bundle="journal-screens.css",
        render_fit_policy="auto_delegate",
        rollout={},
        raw={},
    )


def vertical_stack_primitive(
    *,
    template_id: str,
    slot_count: int,
    grid_class: str,
    mix_landscape: int,
    display_name: str,
    description: str,
    status: str = "ga",
    kind: str = "stack",
) -> TemplateDef:
    if slot_count < 2:
        raise ValueError("slot_count must be >= 2")
    slots = tuple(
        TemplateSlot(index=i, rect=(1, 1, i + 1, i + 1), role="landscape", fit="cover")
        for i in range(slot_count)
    )
    return TemplateDef(
        id=template_id,
        version=1,
        status=status,
        kind=kind,
        display_name=display_name,
        description=description,
        aesthetic=None,
        balance_policy=None,
        stage=TemplateStage(
            aspect="16:9",
            cols=(1.0,),
            rows=tuple([1.0] * slot_count),
            grid=(1, slot_count),
        ),
        photo_count_min=slot_count,
        photo_count_max=slot_count,
        mix_portrait=0,
        mix_landscape=mix_landscape,
        slots=slots,
        constraints={},
        compatibility_hints={},
        scoring={"base_weight": 1.0, "tags": []},
        render_grid_class=grid_class,
        render_css_bundle="journal-screens.css",
        render_fit_policy="auto_delegate",
        rollout={},
        raw={},
    )
