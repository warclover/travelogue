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
