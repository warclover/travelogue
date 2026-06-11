"""Generate legacy mosaic Python snapshot from LTE registry (PRD R-P16-02)."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from travelogue.layout_templates.registry import DEFAULT_POLICY_PATH, LayoutTemplateEngine


def _grid_bounds(specs: list[tuple[int, int, int, int]]) -> tuple[int, int]:
    max_col = max(spec[1] for spec in specs)
    max_row = max(spec[3] for spec in specs)
    return max_col, max_row


def export_legacy_data(engine: LayoutTemplateEngine) -> dict[str, Any]:
    """YAML-driven legacy fragments (no handwritten grid_specs lookup)."""
    templates = engine._templates
    explicit: dict[str, list[tuple[int, int, int, int]]] = {}
    bounds: dict[str, tuple[int, int]] = {}
    for tid, tpl in templates.items():
        if tpl.kind != "composite":
            continue
        specs = [tuple(s.rect) for s in tpl.slots]
        explicit[tid] = specs
        bounds[tid] = _grid_bounds(specs)

    auto_flow: dict[str, tuple[int, int, int]] = {}
    for tid, tpl in templates.items():
        if tpl.kind != "primitive" or not tpl.stage.grid:
            continue
        cols, rows = tpl.stage.grid
        auto_flow[tid] = (cols, rows, len(tpl.slots))

    stack = frozenset(tid for tid, tpl in templates.items() if tpl.kind == "stack")
    pattern_grid_class = {
        tid: tpl.render_grid_class
        for tid, tpl in templates.items()
        if tpl.kind in ("composite", "primitive", "stack")
    }
    wide, tall = {}, {}
    for tid, tpl in templates.items():
        c = tpl.constraints or {}
        w = c.get("portrait_forbidden_in_wide_slots") or []
        h = c.get("landscape_forbidden_in_tall_slots") or []
        if w:
            wide[tid] = sorted(int(x) for x in w)
        if h:
            tall[tid] = sorted(int(x) for x in h)

    portrait_dominant = sorted(
        tid
        for tid, tpl in templates.items()
        if tpl.kind == "primitive" and str(tpl.stage.aspect) == "9:16"
    )

    from travelogue.layout_templates.mosaic_groups import build_mosaic_unified_groups

    mosaic_groups = build_mosaic_unified_groups(engine)

    return {
        "explicit_grid_specs": explicit,
        "explicit_grid_bounds": bounds,
        "auto_flow_grids": auto_flow,
        "stack_patterns": sorted(stack),
        "pattern_grid_class": pattern_grid_class,
        "portrait_forbidden_wide": wide,
        "landscape_forbidden_tall": tall,
        "portrait_dominant_auto_flow": portrait_dominant,
        "mosaic_unified_groups": mosaic_groups,
        "registry_content_hash": engine._content_hash,
    }


def _load_mosaic_unified_groups() -> dict[str, tuple[str, ...]]:
    import yaml

    if not DEFAULT_POLICY_PATH.is_file():
        return {}
    try:
        doc = yaml.safe_load(DEFAULT_POLICY_PATH.read_text(encoding="utf-8")) or {}
    except (OSError, yaml.YAMLError):
        return {}
    raw = doc.get("mosaic_unified_groups") or {}
    if not isinstance(raw, dict):
        return {}
    out: dict[str, tuple[str, ...]] = {}
    for key, ids in raw.items():
        if isinstance(ids, list):
            out[str(key)] = tuple(str(x) for x in ids)
    return out


def _format_dict(name: str, value: Any, *, indent: int = 0) -> str:
    if isinstance(value, dict):
        if not value:
            return f"{name}: dict[str, Any] = {{}}"
        lines = [f"{name}: dict[str, Any] = {{"]
        for key, val in value.items():
            key_repr = json.dumps(key, ensure_ascii=False)
            lines.append(f"    {key_repr}: {_format_value(val)},")
        lines.append("}")
        return "\n".join(lines)
    if isinstance(value, (list, tuple, frozenset, set)):
        return f"{name} = {_format_value(value)}"
    return f"{name} = {_format_value(value)}"


def _format_value(value: Any) -> str:
    if isinstance(value, frozenset):
        inner = ", ".join(json.dumps(x, ensure_ascii=False) for x in sorted(value))
        return f"frozenset({{{inner}}})"
    if isinstance(value, tuple):
        inner = ", ".join(_format_value(x) for x in value)
        return f"({inner})"
    if isinstance(value, list):
        if not value:
            return "[]"
        if all(isinstance(x, (int, float)) for x in value):
            return repr(value)
        inner = ", ".join(_format_value(x) for x in value)
        return f"[{inner}]"
    if isinstance(value, dict):
        if not value:
            return "{}"
        parts = [f"{json.dumps(k, ensure_ascii=False)}: {_format_value(v)}" for k, v in value.items()]
        return "{" + ", ".join(parts) + "}"
    return repr(value)


def render_legacy_python_module(data: dict[str, Any]) -> str:
    content_hash = data.pop("registry_content_hash", "")
    portrait_dominant = data.pop("portrait_dominant_auto_flow", [])
    mosaic_groups = data.pop("mosaic_unified_groups", {})
    chunks = [
        '"""LTE-generated legacy mosaic constants — do not edit by hand.',
        "",
        "Regenerate:",
        "  python scripts/lte_export_legacy.py --sync-python",
        f'Content hash: {content_hash}',
        '"""',
        "",
        "from __future__ import annotations",
        "",
        "from typing import Any",
        "",
    ]
    order = [
        "explicit_grid_specs",
        "explicit_grid_bounds",
        "auto_flow_grids",
        "stack_patterns",
        "pattern_grid_class",
        "portrait_forbidden_wide",
        "landscape_forbidden_tall",
    ]
    for key in order:
        val = data[key]
        if key == "stack_patterns":
            chunks.append(_format_dict("STACK_PATTERNS", frozenset(val)))
        elif key.endswith("_wide") or key.endswith("_tall"):
            py_name = "_" + key.upper()
            formatted = {k: frozenset(v) for k, v in val.items()}
            chunks.append(_format_dict(py_name, formatted))
        else:
            py_name = key.upper()
            chunks.append(_format_dict(py_name, val))
        chunks.append("")
    chunks.append(
        f"PORTRAIT_DOMINANT_AUTO_FLOW: frozenset[str] = "
        f"frozenset({{{', '.join(json.dumps(x, ensure_ascii=False) for x in portrait_dominant)}}})"
    )
    chunks.append("")
    for group_name in sorted(mosaic_groups):
        ids = mosaic_groups[group_name]
        inner = ", ".join(json.dumps(x, ensure_ascii=False) for x in ids)
        chunks.append(f"{group_name}: tuple[str, ...] = ({inner},)")
        chunks.append("")
    chunks.append(
        "MOSAIC_UNIFIED_PATTERN_IDS: tuple[str, ...] = ("
        + ", ".join(
            f"*{name}" for name in sorted(mosaic_groups)
        )
        + ")"
    )
    chunks.append("")
    return "\n".join(chunks).rstrip() + "\n"


def write_legacy_python_module(
    engine: LayoutTemplateEngine,
    *,
    out_path: Path,
) -> Path:
    data = export_legacy_data(engine)
    text = render_legacy_python_module(data)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(text, encoding="utf-8")
    return out_path
