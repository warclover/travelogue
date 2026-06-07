"""Parameterized primitive templates (PRD §4.2 · W4)."""

from __future__ import annotations

from pathlib import Path

import yaml

from travelogue.layout_templates.models import TemplateDef, TemplateSlot
from travelogue.layout_templates.primitive import (
    column_grid_primitive,
    single_slot_primitive,
    vertical_stack_primitive,
)
from travelogue.layout_templates.registry import DEFAULT_TEMPLATES_DIR, template_def_from_yaml

PRIMITIVE_TEMPLATE_IDS: tuple[str, ...] = (
    "screen-portrait-1",
    "screen-landscape-1",
    "screen-portrait-2",
    "screen-landscape-2",
)


def generated_primitive_catalog() -> dict[str, TemplateDef]:
    return {
        "screen-portrait-1": single_slot_primitive(
            template_id="screen-portrait-1",
            stage_aspect="9:16",
            role="portrait",
            grid_class="layout-screen__grid--1col",
            mix_portrait=1,
            display_name="单张竖版",
            description="章末孤儿竖图 cover 满屏（screen_planner · AC-P16-02）。",
            tags=("portrait", "single"),
        ),
        "screen-landscape-1": single_slot_primitive(
            template_id="screen-landscape-1",
            stage_aspect="16:9",
            role="landscape",
            grid_class="layout-screen__grid--1col",
            mix_landscape=1,
            display_name="单张横版",
            description="横/全景单开一屏 cover（screen_planner · AC-P16-02）。",
            tags=("landscape", "single"),
        ),
        "screen-portrait-2": column_grid_primitive(
            template_id="screen-portrait-2",
            columns=2,
            role="portrait",
            grid_class="layout-screen__grid--2col",
            mix_portrait=2,
            mix_landscape=0,
            display_name="双竖",
            description="两张竖图 2 列栅格（screen_planner · AC-P16-02）。",
        ),
        "screen-landscape-2": vertical_stack_primitive(
            template_id="screen-landscape-2",
            slot_count=2,
            grid_class="layout-screen__grid--landscape-stack-2",
            mix_landscape=2,
            display_name="landscape · 2",
            description="Reverse-migrated from legacy mosaic sources (Phase 16 W1).",
        ),
    }


def _slot_signature(slots: tuple[TemplateSlot, ...]) -> list[tuple[int, tuple[int, int, int, int], str]]:
    return [(s.index, s.rect, s.role) for s in slots]


def primitive_drift_messages(expected: TemplateDef, actual: TemplateDef) -> list[str]:
    msgs: list[str] = []
    if actual.kind != expected.kind:
        msgs.append(f"kind {actual.kind} != {expected.kind}")
    if actual.photo_count_min != expected.photo_count_min or actual.photo_count_max != expected.photo_count_max:
        msgs.append(
            f"photoCount {actual.photo_count_min}/{actual.photo_count_max} "
            f"!= {expected.photo_count_min}/{expected.photo_count_max}"
        )
    if actual.render_grid_class != expected.render_grid_class:
        msgs.append(f"gridClass {actual.render_grid_class} != {expected.render_grid_class}")
    if list(actual.stage.cols or ()) != list(expected.stage.cols or ()):
        msgs.append("stage.cols mismatch")
    if list(actual.stage.rows or ()) != list(expected.stage.rows or ()):
        msgs.append("stage.rows mismatch")
    if _slot_signature(actual.slots) != _slot_signature(expected.slots):
        msgs.append("slots topology mismatch")
    return msgs


def check_primitive_yaml_drift(
    *,
    templates_dir: Path | None = None,
    template_ids: tuple[str, ...] | None = None,
) -> list[str]:
    root = templates_dir or DEFAULT_TEMPLATES_DIR
    catalog = generated_primitive_catalog()
    ids = template_ids or PRIMITIVE_TEMPLATE_IDS
    errors: list[str] = []
    for tid in ids:
        path = root / f"{tid}.yaml"
        if not path.is_file():
            errors.append(f"{tid}: missing YAML")
            continue
        doc = yaml.safe_load(path.read_text(encoding="utf-8"))
        if not isinstance(doc, dict):
            errors.append(f"{tid}: invalid YAML root")
            continue
        actual = template_def_from_yaml(doc)
        expected = catalog[tid]
        errors.extend(f"{tid}: {msg}" for msg in primitive_drift_messages(expected, actual))
    return errors
