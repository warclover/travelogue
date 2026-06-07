#!/usr/bin/env python3
"""Promote layout template lifecycle after admission gates (AC-P16-09 · GitOps)."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from travelogue.layout_templates.promotion import apply_layout_template_yaml_patch
from travelogue.layout_templates.layout_admin import layout_template_promotion_plan
from travelogue.layout_templates.registry import DEFAULT_TEMPLATES_DIR, reset_engine_cache_for_tests


def main() -> int:
    parser = argparse.ArgumentParser(description="Layout template lifecycle promotion helper")
    parser.add_argument("template_id")
    parser.add_argument("--target", choices=("beta", "ga"), default="beta")
    parser.add_argument("--templates", type=Path, default=DEFAULT_TEMPLATES_DIR)
    parser.add_argument("--apply", action="store_true", help="Write status/version to YAML when admission ok")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    reset_engine_cache_for_tests()
    plan = layout_template_promotion_plan(args.template_id, target=args.target)
    payload: dict = {"ok": plan["canPromote"], **plan}

    if args.apply and plan["canPromote"]:
        payload["applied"] = apply_layout_template_yaml_patch(
            args.template_id,
            plan["yamlPatch"],
            templates_dir=args.templates,
            dry_run=args.dry_run,
        )
    elif args.apply and not plan["canPromote"]:
        payload["applied"] = None
        payload["error"] = "admission failed; YAML not modified"

    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0 if plan["canPromote"] or not args.apply else 1


if __name__ == "__main__":
    raise SystemExit(main())
