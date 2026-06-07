"""Apply GitOps lifecycle patches to layout template YAML (AC-P16-09)."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

from travelogue.layout_templates.geometry_diff import save_version_snapshot
from travelogue.layout_templates.registry import DEFAULT_TEMPLATES_DIR, reset_engine_cache_for_tests

_LIFECYCLE_ORDER = ("experimental", "beta", "ga", "deprecated", "disabled")


def validate_lifecycle_transition(current: str, target: str) -> str | None:
    """Return error message when target is not a forward lifecycle step."""
    if target not in _LIFECYCLE_ORDER[:3]:
        return None
    if current not in _LIFECYCLE_ORDER[:3]:
        return f"cannot promote from status={current}"
    cur_i = _LIFECYCLE_ORDER.index(current)
    tgt_i = _LIFECYCLE_ORDER.index(target)
    if tgt_i <= cur_i:
        return f"target {target} must be after current {current}"
    if tgt_i - cur_i > 1:
        return f"skip promotion {current}→{target}; advance one step at a time"
    return None


def apply_layout_template_yaml_patch(
    template_id: str,
    patch: dict[str, Any],
    *,
    templates_dir: Path | None = None,
    dry_run: bool = False,
) -> dict[str, Any]:
    root = templates_dir or DEFAULT_TEMPLATES_DIR
    yaml_path = root / f"{template_id}.yaml"
    if not yaml_path.is_file():
        raise FileNotFoundError(f"template YAML not found: {yaml_path}")
    doc = yaml.safe_load(yaml_path.read_text(encoding="utf-8"))
    if not isinstance(doc, dict):
        raise ValueError(f"invalid YAML root: {yaml_path}")
    before = {"status": doc.get("status"), "version": doc.get("version")}
    target_status = str(patch["status"]) if "status" in patch else str(doc.get("status") or "")
    if "status" in patch:
        err = validate_lifecycle_transition(str(doc.get("status") or ""), target_status)
        if err:
            raise ValueError(err)
        doc["status"] = target_status
    if "version" in patch:
        next_version = int(patch["version"])
        if next_version <= int(doc.get("version") or 0):
            raise ValueError("version bump must increase")
        save_version_snapshot(template_id, yaml_doc=dict(doc))
        doc["version"] = next_version
    after = {"status": doc.get("status"), "version": doc.get("version")}
    if not dry_run:
        yaml_path.write_text(yaml.safe_dump(doc, allow_unicode=True, sort_keys=False), encoding="utf-8")
        reset_engine_cache_for_tests()
    return {"yamlPath": str(yaml_path), "before": before, "after": after, "dryRun": dry_run}
