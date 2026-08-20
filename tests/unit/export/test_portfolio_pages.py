"""PFM W2 · BE-PFM-13 page writer + BE-PFM-23 bundle (zip + pages)."""

from __future__ import annotations

import json
from io import BytesIO
from pathlib import Path

import pytest
from PIL import Image

from travelogue.export.longshot import (
    EXPORT_OUTPUT_DIRNAME,
    LongshotExportError,
    LongshotExportResult,
    export_trip_longshot,
)
from travelogue.export.output_recipe import resolve_output_recipe
from travelogue.export.output_recipe.types import OutputRecipeError
from travelogue.export.packager import ExportError
from travelogue.export.platform_profiles import resolve_profile
from travelogue.export.portfolio_pages import (
    PageCaptureSkip,
    export_portfolio_bundle,
    export_portfolio_pages,
    is_portfolio_pages_platform,
    list_portfolio_page_targets,
)

pytestmark = pytest.mark.unit


def _png_bytes(*, size: tuple[int, int] = (320, 180), color=(40, 80, 120)) -> bytes:
    buf = BytesIO()
    Image.new("RGB", size, color).save(buf, format="PNG")
    return buf.getvalue()


def _write_trip(trip_dir: Path, *, edition: str | None, screens: int) -> None:
    trip_dir.mkdir(parents=True, exist_ok=True)
    chapter_screens = [
        {
            "screenId": f"ch-01-sc-{i:02d}",
            "patternId": "page-2-pair-port",
            "slots": [{"assetId": f"a{i}", "slot": 0, "fit": "cover"}],
        }
        for i in range(1, screens + 1)
    ]
    data: dict = {
        "tripId": trip_dir.name,
        "meta": {"title": "奈良"},
        "chapters": [{"id": "ch-01", "screens": chapter_screens}] if screens else [],
    }
    if edition:
        data["studio"] = {"edition": edition}
    (trip_dir / "trip.json").write_text(
        json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8"
    )


def test_list_targets_cover_screens_closing(tmp_path: Path) -> None:
    _write_trip(tmp_path, edition="portfolio", screens=3)
    trip = json.loads((tmp_path / "trip.json").read_text(encoding="utf-8"))
    keys = [t.key for t in list_portfolio_page_targets(trip)]
    assert keys[0] == "cover"
    assert keys[1:4] == ["ch-01-sc-01", "ch-01-sc-02", "ch-01-sc-03"]
    assert keys[-1] == "closing"


def test_journal_trip_rejects_portfolio_pages(tmp_path: Path) -> None:
    _write_trip(tmp_path, edition=None, screens=2)

    def capture(_target):
        return _png_bytes()

    with pytest.raises(LongshotExportError) as exc:
        export_portfolio_pages(tmp_path, capture_fn=capture)
    assert exc.value.code == "E_PORTFOLIO_PAGES_JOURNAL"

    with pytest.raises(LongshotExportError) as exc:
        export_portfolio_bundle(
            tmp_path,
            capture_fn=capture,
            packager_fn=lambda trip_dir: trip_dir / "nope.zip",
        )
    assert exc.value.code == "E_PORTFOLIO_PAGES_JOURNAL"


def test_empty_screens_raises(tmp_path: Path) -> None:
    _write_trip(tmp_path, edition="portfolio", screens=0)
    with pytest.raises(LongshotExportError) as exc:
        export_portfolio_pages(tmp_path, capture_fn=lambda _t: _png_bytes())
    assert exc.value.code == "E_PORTFOLIO_PAGES_EMPTY"


def test_skip_one_page_keeps_compact_successes(tmp_path: Path) -> None:
    _write_trip(tmp_path, edition="portfolio", screens=3)

    def capture(target):
        if target.key in ("cover", "closing"):
            raise PageCaptureSkip(target.key, "no chrome")
        if target.key == "ch-01-sc-02":
            raise RuntimeError("boom")
        return _png_bytes()

    result = export_portfolio_pages(tmp_path, capture_fn=capture)
    assert result.page_count == 2
    assert len(result.outputs) == 2
    names = [p.path.name for p in result.outputs]
    assert names[0].endswith("-portfolio-01.png")
    assert names[1].endswith("-portfolio-02.png")
    assert all(p.path.parent.name == EXPORT_OUTPUT_DIRNAME for p in result.outputs)
    assert any("第 2 屏" in s for s in result.skipped_pages)
    img = Image.open(result.outputs[0].path)
    assert img.size == (1920, 1080)


def test_bundle_zip_failure_still_writes_pages(tmp_path: Path) -> None:
    _write_trip(tmp_path, edition="portfolio", screens=1)

    def capture(target):
        if target.optional:
            raise PageCaptureSkip(target.key, "no chrome")
        return _png_bytes()

    def boom(_trip_dir: Path) -> Path:
        raise ExportError("E_EXPORT_PRIVACY", "privacy")

    result = export_portfolio_bundle(tmp_path, capture_fn=capture, packager_fn=boom)
    assert result.page_count == 1
    assert result.share_zip is None
    assert "打包失败" in result.user_hint
    assert result.outputs[0].path.is_file()


def test_bundle_pages_failure_still_writes_zip(tmp_path: Path) -> None:
    _write_trip(tmp_path, edition="portfolio", screens=1)

    def capture(_target):
        raise RuntimeError("capture down")

    def ok_zip(trip_dir: Path) -> Path:
        out = trip_dir / EXPORT_OUTPUT_DIRNAME / "奈良-分享.zip"
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_bytes(b"PK\x05\x06")
        return out

    result = export_portfolio_bundle(tmp_path, capture_fn=capture, packager_fn=ok_zip)
    assert result.outputs == []
    assert result.share_zip is not None and result.share_zip.is_file()
    assert "页图未产出" in result.user_hint
    assert "可打开翻阅" in result.user_hint


def test_bundle_pages_only_skips_packager(tmp_path: Path) -> None:
    _write_trip(tmp_path, edition="portfolio", screens=1)

    def capture(target):
        if target.optional:
            raise PageCaptureSkip(target.key, "no chrome")
        return _png_bytes()

    def boom(_trip_dir: Path) -> Path:
        raise AssertionError("packager must not run")

    result = export_portfolio_bundle(
        tmp_path,
        capture_fn=capture,
        packager_fn=boom,
        include_zip=False,
    )
    assert result.page_count == 1
    assert result.share_zip is None
    assert result.outputs[0].path.is_file()


def test_collage_pack_does_not_read_pattern_id() -> None:
    """AC-PFM-18 · 换种分享走 kept 池，不读作品集 patternId。"""
    src = (
        Path(__file__).resolve().parents[3]
        / "travelogue"
        / "export"
        / "collage_pack.py"
    ).read_text(encoding="utf-8")
    assert "patternId" not in src
    assert "pattern_id" not in src


def test_export_trip_longshot_routes_to_bundle(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    sentinel = LongshotExportResult(platform="portfolio_pages", page_count=2)

    def fake(trip_dir: Path, **_kwargs):
        assert trip_dir == tmp_path.resolve()
        return sentinel

    monkeypatch.setattr(
        "travelogue.export.portfolio_pages.export_portfolio_bundle",
        fake,
    )
    result = export_trip_longshot(tmp_path, platform="portfolio_pages")
    assert result is sentinel


def test_is_portfolio_pages_platform() -> None:
    assert is_portfolio_pages_platform("portfolio_pages") is True
    assert is_portfolio_pages_platform("") is False
    assert is_portfolio_pages_platform("wechat_chat") is False


def test_or_does_not_map_portfolio_pages_platform() -> None:
    with pytest.raises(OutputRecipeError) as exc:
        resolve_output_recipe(
            kept_n=18,
            trip={"studio": {"edition": "portfolio"}},
            entrypoint="cli",
            enabled=True,
            platform="portfolio_pages",
        )
    assert exc.value.code == "E_OR_UNKNOWN_PLATFORM"


def test_resolve_profile_portfolio_pages_when_longshot2_off() -> None:
    profile = resolve_profile("portfolio_pages", longshot2_enabled=False)
    assert profile.id == "portfolio_pages"
