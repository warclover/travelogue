"""Phase 7 rollback verification smoke test (M29-B-06)."""



from __future__ import annotations
from tests._repo_root import repo_root

import importlib.util
import sys
from pathlib import Path

ROOT = repo_root(__file__)


def _load_verify_module():
    path = ROOT / "scripts" / "phase7_verify_rollback.py"
    spec = importlib.util.spec_from_file_location("phase7_verify_rollback_testmod", path)
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    sys.modules["phase7_verify_rollback_testmod"] = mod
    spec.loader.exec_module(mod)
    return mod


def test_rollback_patch_values() -> None:
    mod = _load_verify_module()
    patch = mod.rollback_patch()
    assert patch["vision"]["batch_size"] == 0
    assert patch["pipeline"]["parallel_embed"] is False
    assert patch["ingest"]["webp_method"] == 6
    assert patch["layout_scoring"]["incremental"] is False


def test_verify_patch_applied_detects_mismatch() -> None:
    mod = _load_verify_module()
    patch = mod.rollback_patch()
    cfg = {
        "vision": {"batch_size": 16},
        "pipeline": {"parallel_embed": True},
        "ingest": {"webp_method": 4},
        "layout_scoring": {"incremental": True},
    }
    issues = mod._verify_patch_applied(cfg, patch)
    assert issues

    rolled = {
        "vision": {"batch_size": 0, "prefer_web_derivative": False},
        "pipeline": {"parallel_embed": False},
        "ingest": {"webp_method": 6},
        "layout_scoring": {"incremental": False},
    }
    assert mod._verify_patch_applied(rolled, patch) == []
