"""Studio 首页 v2 · 回滚演练脚本集成测试。"""



from __future__ import annotations
from tests._repo_root import repo_root

import importlib.util
import json
import sys
from pathlib import Path

import pytest

pytest.importorskip("playwright")

_SCRIPT = repo_root(__file__) / "scripts" / "studio_homepage_rollback_drill.py"
_spec = importlib.util.spec_from_file_location("studio_homepage_rollback_drill", _SCRIPT)
drill_mod = importlib.util.module_from_spec(_spec)
assert _spec and _spec.loader
sys.modules["studio_homepage_rollback_drill"] = drill_mod
_spec.loader.exec_module(drill_mod)

pytestmark = [pytest.mark.e2e, pytest.mark.playwright_serial]


def test_rollback_drill_passes(tmp_path: Path) -> None:
    out = tmp_path / "rollback.json"
    report, code = drill_mod.run_drill(write_out=out)
    assert code == 0
    assert report["passed"] is True
    assert out.is_file()
    body = json.loads(out.read_text(encoding="utf-8"))
    assert body["schema"] == "studio-homepage-rollback-drill/v1"
    assert body["checklist"]["stop_redirect"] is True
