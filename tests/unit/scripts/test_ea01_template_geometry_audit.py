"""EA-01 geometry audit: dist exclusion and three-state classification."""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import pytest
import yaml

from tests._repo_root import repo_root

ROOT = repo_root(__file__)


def _load_mod():
    path = ROOT / "scripts" / "ea01_template_geometry_audit.py"
    spec = importlib.util.spec_from_file_location("ea01_audit_test", path)
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    sys.modules["ea01_audit_test"] = mod
    spec.loader.exec_module(mod)
    return mod


def test_refuses_dist_root(tmp_path: Path) -> None:
    mod = _load_mod()
    dist = tmp_path / "dist" / "templates"
    dist.mkdir(parents=True)
    with pytest.raises(ValueError, match="dist"):
        mod.iter_source_template_paths(dist)


def test_skips_underscore_and_version_history(tmp_path: Path) -> None:
    mod = _load_mod()
    (tmp_path / "page-1-hero-land-right.yaml").write_text("id: x\n", encoding="utf-8")
    (tmp_path / "_example.yaml").write_text("id: skip\n", encoding="utf-8")
    (tmp_path / "screen-portrait-2.yaml").write_text("id: y\n", encoding="utf-8")
    names = {p.name for p in mod.iter_source_template_paths(tmp_path)}
    assert names == {"page-1-hero-land-right.yaml", "screen-portrait-2.yaml"}


def test_classify_health_three_states() -> None:
    mod = _load_mod()
    healthy = mod.classify_health([])
    warn = mod.classify_health(
        [mod.Issue("V-P16-13", "off ladder", "warn", "crop", False)]
    )
    broken = mod.classify_health(
        [mod.Issue("V-P16-01", "overlap", "error", "overlap", False)]
    )
    policy_only = mod.classify_health(
        [mod.Issue("V-LTN-FREEZE", "slots>6", "block", "other", True)]
    )
    assert healthy == "healthy"
    assert warn == "suspicious"
    assert broken == "broken"
    assert policy_only == "healthy"


def _write_tpl(path: Path, **overrides) -> None:
    doc = {
        "id": "page-1-test-ea01",
        "version": 1,
        "status": "experimental",
        "kind": "primitive",
        "displayName": "test",
        "stage": {"aspect": "16:9", "cols": [1], "rows": [1]},
        "photoCount": {"min": 1, "max": 1},
        "mix": {"portrait": 0, "landscape": 1},
        "slots": [
            {"index": 0, "rect": [1, 1, 1, 1], "role": "main", "fit": "cover"},
        ],
        "render": {
            "gridClass": "layout-screen__grid--page-1-test-ea01",
            "cssBundle": "portfolio-pages.css",
        },
    }
    doc.update(overrides)
    path.write_text(yaml.safe_dump(doc, allow_unicode=True), encoding="utf-8")


def test_overlap_is_broken(tmp_path: Path) -> None:
    mod = _load_mod()
    path = tmp_path / "page-2-overlap.yaml"
    _write_tpl(
        path,
        id="page-2-overlap",
        photoCount={"min": 2, "max": 2},
        mix={"portrait": 0, "landscape": 2},
        stage={"aspect": "16:9", "cols": [1, 1], "rows": [1]},
        slots=[
            {"index": 0, "rect": [1, 2, 1, 1], "role": "landscape", "fit": "cover"},
            {"index": 1, "rect": [1, 2, 1, 1], "role": "landscape", "fit": "cover"},
        ],
        render={
            "gridClass": "layout-screen__grid--page-2-overlap",
            "cssBundle": "portfolio-pages.css",
        },
    )
    row = mod.audit_file(path)
    assert row.health == "broken"
    assert any(i.code == "V-P16-01" for i in row.issues)


def test_source_dir_excludes_dist_and_counts_123() -> None:
    mod = _load_mod()
    paths = mod.iter_source_template_paths()
    assert all(not mod.is_dist_path(p) for p in paths)
    assert all(".version_history" not in p.parts for p in paths)
    screen = [p for p in paths if p.name.startswith("screen-")]
    page = [p for p in paths if p.name.startswith("page-")]
    assert len(screen) == 47
    assert len(page) == 76
    assert len(paths) == 123
