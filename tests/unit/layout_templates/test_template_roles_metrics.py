"""Template role denial records permission_denied metric."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from travelogue.templating.roles import require_template_role


def test_require_template_role_records_permission_denied(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    mp = tmp_path / "template-metrics.jsonl"
    monkeypatch.setattr("travelogue.templating.metrics.metrics_path", lambda: mp)

    class H:
        def get(self, k, default=None):
            return default

    ok, role, code = require_template_role(
        H(),
        host="192.168.1.1",
        allow_lan=True,
        minimum="template_admin",
    )
    assert ok is False
    assert code == "E_TEMPLATE_PERMISSION_DENIED"
    assert mp.is_file()
    rows = [json.loads(line) for line in mp.read_text(encoding="utf-8").splitlines() if line.strip()]
    assert any(r.get("name") == "template.admin.permission_denied_count" for r in rows)
