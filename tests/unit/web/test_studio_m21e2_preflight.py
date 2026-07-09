"""Tests for scripts/studio_m21e2_preflight.py."""



from __future__ import annotations

import importlib.util
import sys

from tests._repo_root import repo_root

_SCRIPT = repo_root(__file__) / "scripts" / "studio_m21e2_preflight.py"
_spec = importlib.util.spec_from_file_location("studio_m21e2_preflight", _SCRIPT)
mod = importlib.util.module_from_spec(_spec)
assert _spec and _spec.loader
sys.modules["studio_m21e2_preflight"] = mod
_spec.loader.exec_module(mod)


def test_candidate_paths_include_v3_triplet() -> None:
    paths = set(mod.CANDIDATE_DELETE_PATHS)
    assert "templates/studio/studio.html" in paths
    assert "templates/studio/studio.js" in paths
    assert "templates/studio/studio.css" in paths


def test_build_report_requires_observation_window() -> None:
    report = mod.build_report(observed_release=False)
    assert report["ready"] is False
    assert "OBSERVATION_WINDOW_REQUIRED" in report["reasons"]


def test_preflight_main_nonzero_without_observation() -> None:
    code = mod.main([])
    assert code == 1
