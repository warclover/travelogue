"""Structural geometry diff between layout template versions (PRD §3.3)."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import yaml

from travelogue.layout_templates.geometry import slot_aspect_table
from travelogue.layout_templates.models import TemplateDef
from travelogue.layout_templates.registry import (
    DEFAULT_TEMPLATES_DIR,
    get_engine,
    template_def_from_yaml,
)

VERSION_HISTORY_DIR = DEFAULT_TEMPLATES_DIR / ".version_history"


def version_history_path(template_id: str, version: int) -> Path:
    return VERSION_HISTORY_DIR / template_id / f"v{version}.yaml"


def save_version_snapshot(template_id: str, *, yaml_doc: dict[str, Any] | None = None) -> Path | None:
    """Persist YAML snapshot before a version bump (GitOps promotion)."""
    if yaml_doc is None:
        try:
            yaml_doc = get_engine().get(template_id).raw
        except KeyError:
            return None
    version = int(yaml_doc.get("version") or 0)
    if version <= 0:
        return None
    dest = version_history_path(template_id, version)
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text(yaml.safe_dump(dict(yaml_doc), allow_unicode=True, sort_keys=False), encoding="utf-8")
    return dest


def load_template_at_version(template_id: str, version: int) -> TemplateDef | None:
    """Load a template version from history snapshots or the live registry."""
    engine = get_engine()
    current = engine.get(template_id)
    if current.version == version:
        return current
    hist = version_history_path(template_id, version)
    if hist.is_file():
        doc = yaml.safe_load(hist.read_text(encoding="utf-8"))
        if isinstance(doc, dict):
            return template_def_from_yaml(doc)
    return None


def geometry_snapshot(template: TemplateDef) -> dict[str, Any]:
    aspects = slot_aspect_table(template)
    return {
        "version": template.version,
        "status": template.status,
        "stage": {
            "aspect": template.stage.aspect,
            "grid": list(template.stage.grid or ()),
            "cols": list(template.stage.cols or ()),
            "rows": list(template.stage.rows or ()),
            "gap": template.stage.gap,
        },
        "render": {
            "gridClass": template.render_grid_class,
            "cssBundle": template.render_css_bundle,
            "fitPolicy": template.render_fit_policy,
        },
        "slots": [
            {
                "index": s.index,
                "rect": list(s.rect),
                "role": s.role,
                "fit": s.fit,
                "displayAspect": round(row.display_aspect, 6),
            }
            for s, row in zip(template.slots, aspects, strict=True)
        ],
    }


def diff_geometry_snapshots(
    left: dict[str, Any],
    right: dict[str, Any],
    *,
    left_label: str,
    right_label: str,
) -> dict[str, Any]:
    changes: list[dict[str, Any]] = []

    def _walk(path: str, a: Any, b: Any) -> None:
        if a == b:
            return
        if isinstance(a, dict) and isinstance(b, dict):
            keys = sorted(set(a) | set(b))
            for key in keys:
                _walk(f"{path}.{key}" if path else key, a.get(key), b.get(key))
            return
        if isinstance(a, list) and isinstance(b, list):
            if len(a) != len(b):
                changes.append(
                    {
                        "path": path,
                        "left": left_label,
                        "right": right_label,
                        "before": a,
                        "after": b,
                        "kind": "list_length",
                    }
                )
                return
            for idx, (ai, bi) in enumerate(zip(a, b, strict=False)):
                _walk(f"{path}[{idx}]", ai, bi)
            return
        changes.append(
            {
                "path": path,
                "left": left_label,
                "right": right_label,
                "before": a,
                "after": b,
                "kind": "value",
            }
        )

    _walk("", left, right)
    return {
        "left": left_label,
        "right": right_label,
        "changed": bool(changes),
        "changeCount": len(changes),
        "changes": changes,
    }


def geometry_diff(template_id: str, va: int, vb: int) -> dict[str, Any]:
    """Compare two template versions for Studio version_diff (va → vb)."""
    left = load_template_at_version(template_id, va)
    right = load_template_at_version(template_id, vb)
    missing: list[str] = []
    if left is None:
        missing.append(f"v{va}")
    if right is None:
        missing.append(f"v{vb}")
    if missing:
        return {
            "templateId": template_id,
            "va": va,
            "vb": vb,
            "ok": False,
            "error": "E_VERSION_NOT_FOUND",
            "missing": missing,
            "message": "历史版本快照不可用；晋升前会自动写入 .version_history",
        }
    snap_a = geometry_snapshot(left)
    snap_b = geometry_snapshot(right)
    diff = diff_geometry_snapshots(snap_a, snap_b, left_label=f"v{va}", right_label=f"v{vb}")
    return {
        "templateId": template_id,
        "va": va,
        "vb": vb,
        "ok": True,
        "left": snap_a,
        "right": snap_b,
        "diff": diff,
    }


def geometry_diff_json(template_id: str, va: int, vb: int) -> str:
    return json.dumps(geometry_diff(template_id, va, vb), ensure_ascii=False, indent=2)
