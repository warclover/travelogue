"""Tests for scripts/studio_telemetry_alert.py (OQ-TELEMETRY)."""



from __future__ import annotations
from tests._repo_root import repo_root

import importlib.util
import json
import sys
from pathlib import Path
from unittest.mock import patch

_SCRIPT = repo_root(__file__) / "scripts" / "studio_telemetry_alert.py"
_spec = importlib.util.spec_from_file_location("studio_telemetry_alert", _SCRIPT)
alert_mod = importlib.util.module_from_spec(_spec)
assert _spec and _spec.loader
sys.modules["studio_telemetry_alert"] = alert_mod
_spec.loader.exec_module(alert_mod)


def test_exit_code_rollback_on_conversion_drop() -> None:
    recs = (
        [{"event": "import_start", "meta": {"variant": "v3"}}] * 10
        + [{"event": "import_success", "meta": {"variant": "v3"}}] * 10
        + [{"event": "import_start", "meta": {"variant": "v2"}}] * 10
        + [{"event": "import_success", "meta": {"variant": "v2"}}] * 3
    )
    flags, _ = alert_mod.evaluate(events=recs)
    assert alert_mod.exit_code_for_flags(flags) == 1


def test_exit_code_ok_on_insufficient_data() -> None:
    flags, _ = alert_mod.evaluate(events=[{"event": "homepage_view", "meta": {"variant": "v2"}}])
    assert alert_mod.exit_code_for_flags(flags) == 0
    assert any("INSUFFICIENT_DATA" in f for f in flags)


def test_flags_from_report_json() -> None:
    report = {
        "should_rollback": True,
        "funnel": {"v2": {"homepage_view": 10, "import_conversion": 0.5}},
        "flags": {"all": ["ROLLBACK: import 转化率下降 50.0%"]},
    }
    flags, summary = alert_mod.evaluate(report=report)
    assert flags[0].startswith("ROLLBACK:")
    assert summary["v2"]["homepage_view"] == 10


def test_main_dry_run_no_slack(tmp_path) -> None:
    src = tmp_path / "events.jsonl"
    src.write_text(
        json.dumps({"ts": "2026-06-01T00:00:00Z", "event": "homepage_view", "meta": {"variant": "v2"}})
        + "\n",
        encoding="utf-8",
    )
    with patch.dict("os.environ", {"TRAVELOGUE_STUDIO_TELEMETRY_SLACK_WEBHOOK": "https://example.com/hook"}):
        rc = alert_mod.main(["--input", str(src), "--notify", "--dry-run"])
    assert rc == 0


def test_post_slack_sends_payload() -> None:
    captured: dict = {}

    class _Resp:
        status = 200

        def __enter__(self):
            return self

        def __exit__(self, *args):
            return False

    def _fake_urlopen(req, timeout=10.0):
        captured["data"] = req.data.decode("utf-8")
        return _Resp()

    with patch("urllib.request.urlopen", _fake_urlopen):
        alert_mod.post_slack("https://hooks.slack.com/test", "hello holdback")
    body = json.loads(captured["data"])
    assert body["text"] == "hello holdback"
