"""Studio UX gates · UX-P3-01～07 (Phase 3 §6.4)."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from tests._studio_js import read_studio_js
from tests.clustering_fixtures import load_fixture_assets
from tests.test_studio_server import (
    _distinct_album,
    _free_port,
    _get_json,
    _post_json,
    _start_studio_server,
)
from travelogue.config import AppConfig, ClusteringConfig, VisionConfig
from travelogue.curation.clustering import run_clustering_layer
from travelogue.web.studio_jobs import STAGE_COUNT
from travelogue.web.studio_stages import ingest_stage_hint, stage_hint

ROOT = Path(__file__).resolve().parents[1]
STUDIO_HTML = ROOT / "templates" / "studio" / "legacy-freeze" / "studio.classic.html"
PREVIEW_JS = ROOT / "templates" / "studio" / "preview-toolbar.js"


def test_ux_p3_01_job_stage_count_is_four() -> None:
    assert STAGE_COUNT == 4


def test_ux_p3_02_stage_hints_cover_p3_lite_and_full(tmp_path: Path) -> None:
    assert ingest_stage_hint(150) == "约 2 分钟"
    assert stage_hint("curate") == "约 30 秒"
    assets = load_fixture_assets("golden-mixed-scenes")
    trip = {"assets": [dict(a) for a in assets], "curation": {}, "chapters": []}
    cfg = AppConfig(
        clustering=ClusteringConfig(enabled="true"),
        vision=VisionConfig(enabled="true"),
    )
    result = run_clustering_layer(trip, trip_dir=tmp_path / "p3", cfg=cfg)
    assert result.geo_event_count >= 1
    assert any(
        token in (result.stage_hint or "")
        for token in ("识别", "分析", "准备", "重新")
    )


def test_ux_p3_03_advanced_options_bind_export() -> None:
    advanced_js = (ROOT / "templates" / "studio" / "js" / "advanced.js").read_text(encoding="utf-8")
    assert "bindAdvancedConfigControls" in advanced_js


def test_ux_p3_03_advanced_options_and_config_api(tmp_path: Path) -> None:
    # Classic freeze is deprecated minimal UI; advanced options live on studio-home-v2
    # (see test_ux_p3_03_v2_advanced_options_markers). This case only checks config API.
    html = STUDIO_HTML.read_text(encoding="utf-8")
    assert "Classic 首页（Deprecated）" in html

    import yaml

    from tests.test_studio_config_p3 import _start_studio_with_config

    trips_dir = tmp_path / "trips"
    trips_dir.mkdir()
    config_path = tmp_path / "config.yaml"
    config_path.write_text(
        yaml.safe_dump({"clustering": {"enabled": "true"}, "vision": {"enabled": "true"}}),
        encoding="utf-8",
    )
    port = _free_port()
    server = _start_studio_with_config(trips_dir, port, config_path=config_path)
    try:
        import urllib.request

        with urllib.request.urlopen(f"http://127.0.0.1:{port}/__travelogue/config", timeout=5) as resp:
            body = json.loads(resp.read().decode("utf-8"))
        assert body.get("clustering", {}).get("enabled") == "true"
    finally:
        server.shutdown()
        server.server_close()


def test_ux_p3_04_cluster_notice_non_blocking_string() -> None:
    """Vision/geo 降级 notice 经 job result 传递；v2 非阻断 warn 走 studioToast。"""
    subprocess_js = (
        ROOT / "travelogue" / "web" / "studio_subprocess.py"
    ).read_text(encoding="utf-8")
    assert "clusterNotice" in subprocess_js
    first_success = (
        ROOT / "templates" / "studio" / "homepage-v2" / "first-success.js"
    ).read_text(encoding="utf-8")
    assert "studioToast" in first_success
    assert "cullWarn" in first_success
    assert "dateRangeWarn" in first_success
    assert "clusterNotice" in first_success


def test_ux_p3_03_v2_advanced_options_markers() -> None:
    html = (ROOT / "templates" / "studio" / "studio-home-v2.html").read_text(encoding="utf-8")
    for expected in (
        'id="v2-advanced-toggle"',
        'id="v2-advanced-popover"',
        'id="studio-cfg-clustering"',
        'id="studio-cfg-vision"',
        'id="studio-cfg-layout-scoring"',
        "高级 · 分析选项",
        "智能排版",
    ):
        assert expected in html, f"missing v2 UX marker: {expected}"


def test_ux_p3_05_06_slow_hint_thresholds_and_copy() -> None:
    js = read_studio_js()
    assert "SLOW_JOB_MS = 30000" in js
    assert "SLOW_JOB_VISION_MS = 180000" in js
    assert "SLOW_JOB_VISION_LONG_MS = 480000" in js
    assert "比预期久一些，请耐心等待" in js
    assert "照片较多，正在仔细分析行程与场景" in js
    assert "高级 · 分析选项" in js


def test_ux_p3_07_preview_toolbar_has_no_cluster_controls() -> None:
    js = PREVIEW_JS.read_text(encoding="utf-8")
    forbidden = ("sceneCluster", "clustering.enabled", "行程识别", "studio-cfg-clustering")
    for token in forbidden:
        assert token not in js
    assert "为什么这样分章" in js or "chapter-layout" in js
    assert "layoutExplain" in js
    assert "排版引擎" in js
    assert "preview-toolbar__g1-banner" in js
    assert "preview-drawer__narrate-anchors" in js
    assert "copy-intent" in js
    assert "章级意图" in js
    assert "preview-drawer__chip-mood" in js
    assert "trapDrawerFocus" in js
    assert "toolbarConfirm" in js
    assert "window.alert(" not in js


@pytest.mark.e2e
def test_ux_p3_01_import_job_reports_four_stages(tmp_path: Path) -> None:
    album = _distinct_album(tmp_path, 6)
    trips_dir = tmp_path / "trips"
    trips_dir.mkdir()
    port = _free_port()
    server = _start_studio_server(trips_dir, port)
    base = f"http://127.0.0.1:{port}"
    try:
        status, body = _post_json(
            f"{base}/__travelogue/import",
            {"albumPath": str(album), "title": "UX", "place": "测试"},
        )
        assert status == 202
        job_id = body["jobId"]
        from tests.studio_test_helpers import wait_for_job

        ingest_progress_seen = False

        def _fetch() -> dict:
            nonlocal ingest_progress_seen
            _status, job = _get_json(f"{base}/__travelogue/status?jobId={job_id}")
            hint = str(job.get("stageHint") or "")
            if "已处理" in hint and "/" in hint:
                ingest_progress_seen = True
            return job

        last = wait_for_job(_fetch, timeout_sec=180, poll_sec=0.05)
        assert last.get("status") == "succeeded", last
        assert last.get("stageCount") == 4
        assert last.get("stageIndex") == 4
        # Large albums report 已处理 N/M; small fixtures may finish ingest between polls.
        assert ingest_progress_seen or last.get("stage") == "render"
    finally:
        server.shutdown()
        server.server_close()
