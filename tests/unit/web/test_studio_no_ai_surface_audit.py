"""NAS · 禁词审计脚本冒烟。"""

from __future__ import annotations

from scripts.studio_no_ai_surface_audit import audit


def test_nas_audit_w1_clean():
    hits = audit("w1")
    assert hits == [], "\n".join(hits)


def test_nas_audit_w2_clean():
    hits = audit("w2")
    assert hits == [], "\n".join(hits)
