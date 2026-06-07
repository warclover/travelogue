#!/usr/bin/env python3
"""Export LTE YAML registry to legacy mosaic fragments (T5 · R-P16-02)."""

from __future__ import annotations

import argparse
import json
from dataclasses import asdict
from pathlib import Path

from travelogue.layout_templates.legacy_codegen import write_legacy_python_module
from travelogue.layout_templates.registry import DEFAULT_TEMPLATES_DIR, LayoutTemplateEngine

DEFAULT_PY_OUT = Path("travelogue/curation/mosaic/_legacy_generated.py")


def main() -> int:
    parser = argparse.ArgumentParser(description="Export LTE registry to legacy-compatible JSON/Python")
    parser.add_argument("--templates", type=Path, default=DEFAULT_TEMPLATES_DIR)
    parser.add_argument("--out", type=Path, default=Path("dist/lte_legacy_export.json"))
    parser.add_argument(
        "--sync-python",
        action="store_true",
        help="Write travelogue/curation/mosaic/_legacy_generated.py snapshot",
    )
    parser.add_argument("--python-out", type=Path, default=DEFAULT_PY_OUT)
    args = parser.parse_args()

    engine = LayoutTemplateEngine.load(args.templates, rebuild_cache=True)
    exported = engine.export_legacy_registry()

    serializable: dict = {}
    for key, val in exported.items():
        if key == "mosaic_patterns":
            serializable[key] = {
                pid: {
                    "pattern_id": p.pattern_id,
                    "slot_count": p.slot_count,
                    "grid_class": p.grid_class,
                    "roles": list(p.roles),
                    "accepts": asdict(p.accepts),
                    "css_verified": p.css_verified,
                }
                for pid, p in val.items()
            }
        elif key == "stack_patterns":
            serializable[key] = sorted(val)
        elif key == "explicit_grid_specs":
            serializable[key] = {pid: [list(t) for t in specs] for pid, specs in val.items()}
        elif key == "auto_flow_grids":
            serializable[key] = {pid: list(t) for pid, t in val.items()}
        elif key in ("portrait_forbidden_wide", "landscape_forbidden_tall"):
            serializable[key] = {pid: sorted(v) for pid, v in val.items()}
        else:
            serializable[key] = val

    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(serializable, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"exported JSON → {args.out}")

    if args.sync_python:
        path = write_legacy_python_module(engine, out_path=args.python_out)
        print(f"synced Python → {path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
