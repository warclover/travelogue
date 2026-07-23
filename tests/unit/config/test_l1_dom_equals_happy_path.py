"""QFX AC-15 · data-csc-tier=l1 DOM keys == happyPath.l1Keys。"""

from __future__ import annotations

import re
from pathlib import Path

from travelogue.orchestrator.happy_path_recipe import L1_RESULT_KEYS

HOME = (
    Path(__file__).resolve().parents[3]
    / "templates"
    / "studio"
    / "studio-home-v2.html"
)
_L1_KEY_RE = re.compile(
    r'data-csc-tier\s*=\s*["\']l1["\'][^>]*data-csc-key\s*=\s*["\']([^"\']+)["\']'
    r'|data-csc-key\s*=\s*["\']([^"\']+)["\'][^>]*data-csc-tier\s*=\s*["\']l1["\']',
    re.I,
)


def _dom_l1_keys(html: str) -> list[str]:
    keys: list[str] = []
    for m in _L1_KEY_RE.finditer(html):
        key = m.group(1) or m.group(2)
        if key:
            keys.append(key)
    return keys


def test_l1_dom_keys_equal_happy_path_l1_keys() -> None:
    html = HOME.read_text(encoding="utf-8")
    dom_keys = _dom_l1_keys(html)
    assert len(dom_keys) == len(set(dom_keys)), f"duplicate L1 keys: {dom_keys}"
    assert len(dom_keys) <= 10
    assert set(dom_keys) == set(L1_RESULT_KEYS)
    assert sorted(dom_keys) == sorted(L1_RESULT_KEYS)
