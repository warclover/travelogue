"""LTE command-line interface (R-P16-11)."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

import jsonschema
import yaml

from travelogue.layout_templates.registry import (
    DEFAULT_TEMPLATES_DIR,
    LayoutTemplateEngine,
    schema_path,
    template_def_from_yaml,
)
from travelogue.layout_templates.validator import (
    ValidateMode,
    format_slot_aspect_doc,
    validate_template_def,
)


def _load_schema() -> dict[str, Any]:
    with schema_path().open(encoding="utf-8") as f:
        return json.load(f)


def _iter_template_files(root: Path) -> list[Path]:
    if root.is_file():
        return [root]
    files = sorted(root.glob("*.yaml")) + sorted(root.glob("*.yml"))
    return [p for p in files if not p.name.startswith("_")]


def _validate_yaml_file(path: Path, validator: jsonschema.Draft202012Validator) -> list[str]:
    try:
        doc = yaml.safe_load(path.read_text(encoding="utf-8"))
    except (OSError, yaml.YAMLError) as exc:
        return [f"{path.name}: failed to parse YAML ({exc})"]

    if not isinstance(doc, dict):
        return [f"{path.name}: root must be a mapping"]

    errors: list[str] = []
    for err in sorted(validator.iter_errors(doc), key=lambda e: list(e.path)):
        loc = ".".join(str(p) for p in err.path) or "(root)"
        errors.append(f"{path.name} [{loc}] {err.message}")
    return errors


def _semantic_validate_file(path: Path, mode: ValidateMode) -> list[str]:
    doc = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(doc, dict):
        return []
    report = validate_template_def(template_def_from_yaml(doc), mode=mode)
    prefix = path.name
    return [f"{prefix} [{issue.code}] {issue.message}" for issue in report.issues if issue.level != "warn"]


def cmd_validate(args: argparse.Namespace) -> int:
    schema = _load_schema()
    jsonschema.Draft202012Validator.check_schema(schema)

    root = Path(args.path) if args.path else DEFAULT_TEMPLATES_DIR
    if not root.exists():
        print(json.dumps({"ok": False, "errors": [f"path not found: {root}"]}, ensure_ascii=False))
        return 1

    files = _iter_template_files(root)
    if not files:
        print(json.dumps({"ok": True, "validated": 0, "errors": []}, ensure_ascii=False))
        return 0

    schema_validator = jsonschema.Draft202012Validator(schema)
    all_errors: list[str] = []
    for path in files:
        all_errors.extend(_validate_yaml_file(path, schema_validator))
        if args.semantic or args.publish:
            mode: ValidateMode = "publish" if args.publish else "ci"
            all_errors.extend(_semantic_validate_file(path, mode))

    if args.semantic or args.publish:
        templates_root = root if root.is_dir() else DEFAULT_TEMPLATES_DIR
        engine = LayoutTemplateEngine.load(templates_root)
        from travelogue.layout_templates.registry import check_active_quotas

        for msg in check_active_quotas(engine):
            all_errors.append(f"quota [{msg}]")

    payload = {"ok": len(all_errors) == 0, "validated": len(files), "errors": all_errors}
    print(json.dumps(payload, ensure_ascii=False, indent=2 if args.verbose else None))
    return 0 if payload["ok"] else 1


def cmd_export(args: argparse.Namespace) -> int:
    root = Path(args.templates) if args.templates else DEFAULT_TEMPLATES_DIR
    engine = LayoutTemplateEngine.load(root, rebuild_cache=True)
    from travelogue.layout_templates.css_gen import (
        TrailingLegacyCssError,
        filter_templates_by_family,
        sync_journal_screens_css,
        sync_portfolio_pages_css,
        write_generated_css,
    )

    wrote = False
    if args.out:
        family = args.target or "all"
        selected = filter_templates_by_family(engine._templates, family)
        write_generated_css(selected, Path(args.out))
        print(f"generated CSS → {args.out} ({len(selected)} templates, family={family})")
        wrote = True
    if args.sync_journal:
        on_trailing_legacy = "warn" if args.warn_trailing_legacy else "strict"
        try:
            journal = sync_journal_screens_css(engine._templates, on_trailing_legacy=on_trailing_legacy)
        except TrailingLegacyCssError as exc:
            print(str(exc), file=sys.stderr)
            return 1
        print(f"synced LTE marker → {journal}")
        wrote = True
    if args.sync_portfolio:
        portfolio = sync_portfolio_pages_css(engine._templates)
        print(f"synced LTE marker → {portfolio}")
        wrote = True
    if not wrote:
        print(
            "nothing to write; pass --sync-journal, --sync-portfolio, and/or --out "
            "(D-DPI-17: mixed journal-screens.generated.css is no longer a default product)"
        )
    return 0


def cmd_promote_pages(args: argparse.Namespace) -> int:
    from travelogue.layout_templates.page_promote import P0_PAGE_IDS, promote_pages

    ids = list(args.ids or [])
    if args.p0_only:
        ids = list(P0_PAGE_IDS)
    elif not ids:
        ids = None
    written, skips = promote_pages(ids=ids, write=True)
    print(f"promoted {len(written)} page-* YAML → {DEFAULT_TEMPLATES_DIR}")
    for skip in skips:
        print(f"skip {skip.page_id}: {skip.reason}")
    return 0 if written else 1


def cmd_docgen(args: argparse.Namespace) -> int:
    root = Path(args.templates) if args.templates else DEFAULT_TEMPLATES_DIR
    out_dir = Path(args.out) if args.out else Path("docs/templates/slot-aspect")
    out_dir.mkdir(parents=True, exist_ok=True)
    engine = LayoutTemplateEngine.load(root)
    for tid in sorted(engine._templates):
        doc = format_slot_aspect_doc(engine._templates[tid])
        path = out_dir / f"{tid}.md"
        path.write_text(doc, encoding="utf-8")
    print(f"docgen → {out_dir} ({len(engine._templates)} files)")
    return 0


def cmd_solve_tracks(args: argparse.Namespace) -> int:
    import json

    from travelogue.layout_templates.geometry import slot_aspect_table, solve_tracks

    engine = LayoutTemplateEngine.load(args.templates)
    template_id = str(args.template_id).strip()
    try:
        tpl = engine.get(template_id)
    except KeyError:
        print(f"unknown template: {template_id}", file=sys.stderr)
        return 1
    aspects = slot_aspect_table(tpl)
    targets = [(row.display_aspect, 1.0) for row in aspects]
    rects = [s.rect for s in tpl.slots]
    cols, rows = solve_tracks(
        targets,
        stage_aspect=tpl.stage.aspect,
        rects=rects,
    )
    payload = {
        "templateId": template_id,
        "stageAspect": tpl.stage.aspect,
        "cols": cols,
        "rows": rows,
        "currentCols": list(tpl.stage.cols or ()),
        "currentRows": list(tpl.stage.rows or ()),
    }
    if args.json:
        print(json.dumps(payload, indent=2, ensure_ascii=False))
    else:
        print(f"{template_id}: cols={cols} rows={rows}")
    return 0


def cmd_check_primitives(args: argparse.Namespace) -> int:
    from travelogue.layout_templates.primitive_catalog import check_primitive_yaml_drift

    root = Path(args.templates)
    errors = check_primitive_yaml_drift(templates_dir=root)
    payload = {"ok": not errors, "errors": errors}
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0 if payload["ok"] else 1


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="travelogue.layout_templates.cli", description="LTE CLI")
    sub = parser.add_subparsers(dest="command", required=True)

    validate = sub.add_parser("validate", help="JSON Schema + optional semantic validate")
    validate.add_argument("--path", help="Template file or directory")
    validate.add_argument("-v", "--verbose", action="store_true")
    validate.add_argument(
        "--semantic",
        action="store_true",
        help="Run CI semantic gates (V-P16-01~14, errors only)",
    )
    validate.add_argument(
        "--publish",
        action="store_true",
        help="Run publish gates (strict blocks, AC-P16-03)",
    )
    validate.set_defaults(func=cmd_validate)

    export = sub.add_parser("export", help="Export generated grid CSS bundle")
    export.add_argument("--templates", type=Path)
    export.add_argument("--out", type=Path)
    export.add_argument(
        "--sync-journal",
        action="store_true",
        help="Inject screen-* CSS into templates/visual-journal/journal-screens.css marker",
    )
    export.add_argument(
        "--sync-portfolio",
        action="store_true",
        help="Inject page-* CSS into templates/visual-journal/portfolio-pages.css marker",
    )
    export.add_argument(
        "--target",
        choices=("journal", "portfolio", "all"),
        help="Family filter for --out (default: all). Does not change --sync-* behavior.",
    )
    export.add_argument(
        "--warn-trailing-legacy",
        action="store_true",
        help=(
            "Warn (exit 0) instead of failing when hand-written CSS is found after "
            "@journal-overlays:end (T-LRG-12 migration bypass); default is strict fail-fast"
        ),
    )
    export.set_defaults(func=cmd_export)

    promote = sub.add_parser(
        "promote-pages",
        help="Compile atelier page-* faces into LTE YAML (does not scan reserve at runtime)",
    )
    promote.add_argument("--p0-only", action="store_true", help="Only magazine-16's 11 faces")
    promote.add_argument("--id", action="append", dest="ids", help="Face id to promote")
    promote.set_defaults(func=cmd_promote_pages)

    docgen = sub.add_parser("docgen", help="Generate slot-aspect markdown docs")
    docgen.add_argument("--templates", type=Path)
    docgen.add_argument("--out", type=Path)
    docgen.set_defaults(func=cmd_docgen)

    solve = sub.add_parser("solve-tracks", help="Inverse-design track weights (W4)")
    solve.add_argument("template_id", help="Layout template id")
    solve.add_argument("--templates", type=Path, default=DEFAULT_TEMPLATES_DIR)
    solve.add_argument("--json", action="store_true", help="Emit JSON payload")
    solve.set_defaults(func=cmd_solve_tracks)

    check_prim = sub.add_parser(
        "check-primitives",
        help="Verify screen-planner primitive YAML matches parameterized catalog (W4)",
    )
    check_prim.add_argument("--templates", type=Path, default=DEFAULT_TEMPLATES_DIR)
    check_prim.set_defaults(func=cmd_check_primitives)

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return int(args.func(args))


if __name__ == "__main__":
    raise SystemExit(main())
