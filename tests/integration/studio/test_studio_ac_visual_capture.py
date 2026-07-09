"""Studio AC 视觉截图脚本冒烟测试。"""



from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import pytest

from tests._repo_root import repo_root

pytest.importorskip("playwright")

_SCRIPT = repo_root(__file__) / "scripts" / "studio_ac_visual_capture.py"
_spec = importlib.util.spec_from_file_location("studio_ac_visual_capture", _SCRIPT)
cap_mod = importlib.util.module_from_spec(_spec)
assert _spec and _spec.loader
sys.modules["studio_ac_visual_capture"] = cap_mod
_spec.loader.exec_module(cap_mod)

pytestmark = [pytest.mark.e2e, pytest.mark.playwright_serial]


def test_visual_capture_produces_five_pngs(tmp_path: Path) -> None:
    out = tmp_path / "visual"
    results = cap_mod.capture_all(out_dir=out)
    assert len(results) == 5
    for row in results:
        path = Path(row["file"])
        assert path.is_file()
        assert path.stat().st_size > 1000
