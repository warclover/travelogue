"""Share Narrative Readiness · W2 源码契约（AC-SNR-04/08/09/10）。"""

from __future__ import annotations

from pathlib import Path

from travelogue.curation.chapter_titles import (
    chapter_titles,
    scene_short_from_segment_label,
)
from travelogue.domain.narrate_diff import summarize_narrate_fields
from travelogue.domain.share_copy_pack import build_l1_body, build_share_copy_pack

ROOT = Path(__file__).resolve().parents[3]
STUDIO = ROOT / "templates" / "studio"


def test_snr_w2_thin_title_prefers_place_and_scene() -> None:
    assets = [
        {
            "id": "a",
            "takenAt": "2026-07-08T09:00:00",
            "place": {"city": "樱园"},
        },
        {
            "id": "b",
            "takenAt": "2026-07-08T15:00:00",
            "place": {"city": "樱顶"},
        },
        {"id": "c", "takenAt": "2026-07-09T10:00:00", "place": {"city": "旧图书馆"}},
    ]
    titles = chapter_titles(
        [["a"], ["b"], ["c"]],
        assets,
        {"places": ["武大"]},
        bucket_segment_ids=["s1", "s1", "s1"],
        segment_labels={"s1": "7月8–9日"},
    )
    assert "樱园" in titles[0]
    assert "樱顶" in titles[1]
    assert "旧图书馆" in titles[2]
    assert all("·二" not in t and "·三" not in t for t in titles)


def test_snr_w2_scene_from_segment_label() -> None:
    assert scene_short_from_segment_label("6月23日·初中毕业照") == "初中毕业照"
    assert scene_short_from_segment_label("7月8–9日") is None


def test_snr_w2_copy_pack_l1_when_narrative_ready() -> None:
    trip = {
        "meta": {
            "title": "斯里兰卡见闻录",
            "hook": "雨季里的第一口海风",
            "places": ["科伦坡"],
            "dateStart": "2024-07-22",
        },
        "chapters": [
            {"lead": "清晨穿过湿漉漉的市场"},
            {"lead": "午后的列车慢得刚好"},
        ],
    }
    pack = build_share_copy_pack(trip, llm_available=False)
    assert pack["level"] == "L1"
    assert "雨季里的第一口海风" in pack["body"]
    assert "清晨穿过湿漉漉的市场" in pack["body"]
    assert "已带入杂志文案摘要" in pack["hint"]
    assert build_l1_body(trip)


def test_snr_w2_copy_pack_l0_when_empty() -> None:
    pack = build_share_copy_pack(
        {"meta": {"title": "周末"}, "chapters": [{"lead": ""}]},
        llm_available=True,
    )
    assert pack["level"] == "L0"
    assert pack["body"] == ""
    assert "正文可粘贴后自填" in pack["hint"]


def test_snr_w2_narrate_diff_summary() -> None:
    summary = summarize_narrate_fields(
        ["meta.hook", "chapters[0].lead", "chapters[1].lead", "epilogue"]
    )
    assert "封面钩子" in summary["slotsLabel"]
    assert "2 段章导语" in summary["slotsLabel"]
    assert "辑封一句" in summary["slotsLabel"]
    assert summary["count"] == 4
    assert summarize_narrate_fields([])["slotsLabel"] == ""


def test_snr_w2_fe_status_diff_and_copy_pack_ui() -> None:
    ai = (STUDIO / "preview-toolbar" / "ai-sheet.js").read_text(encoding="utf-8")
    core = (STUDIO / "preview-toolbar" / "core.js").read_text(encoding="utf-8")
    panel = (STUDIO / "js" / "longshot-export-panel.js").read_text(encoding="utf-8")
    longshot = (STUDIO / "preview-toolbar" / "longshot.js").read_text(encoding="utf-8")
    init = (STUDIO / "preview-toolbar" / "init-v3.js").read_text(encoding="utf-8")
    assert 'status = "已是杂志文案"' in ai
    assert 'status = "可生成"' in ai
    assert 'status = "生成中"' in ai
    assert 'status = "失败可重试"' in ai
    assert 'status = "杂志文案已完成"' not in ai
    assert "正在生成杂志感文案" in ai
    assert "travelogue.snr.narrateDiff.v1." in core
    assert "mountNarrateDiffBar" in init
    assert 'data-action="copy-xhs-pack-titles"' in panel
    assert "仅标题和话题" in panel
    assert "生成杂志感后可带正文" in panel
    assert 'trackStudioEvent("snr_copy_pack"' in longshot
