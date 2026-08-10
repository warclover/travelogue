"""Share Narrative Readiness · PRD 遗漏补全契约（T02 / caption / 状态 / 埋点 / F2）。"""

from __future__ import annotations

from pathlib import Path

from travelogue.curation.chapter_explain import COPY_SNR_T02, ensure_snr_outlier_explain
from travelogue.domain.share_face_copy import resolve_visible_caption
from travelogue.web.studio_entry import build_chapter_summaries

ROOT = Path(__file__).resolve().parents[3]
STUDIO = ROOT / "templates" / "studio"


def test_snr_t02_appended_for_year_outliers() -> None:
    trip = {
        "meta": {"dateStart": "2024-07-01", "dateEnd": "2024-07-05"},
        "assets": [
            {"id": "a", "takenAt": "2024-07-02T10:00:00"},
            {"id": "b", "takenAt": "2015-06-01T10:00:00", "timeOutlier": True},
        ],
        "curation": {"userSummary": {"summary": "按天成册", "details": ["已合并"]}},
    }
    explain = ensure_snr_outlier_explain({"details": ["已合并"]}, trip)
    assert COPY_SNR_T02 in explain["details"]
    assert explain["hasYearOutliers"] is True


def test_snr_resolve_visible_caption_alt_fallback() -> None:
    assert resolve_visible_caption("旅行照片", kind="caption") == ""
    assert resolve_visible_caption("", kind="alt", asset={}) == "照片"
    assert (
        resolve_visible_caption(
            "",
            kind="alt",
            asset={"place": {"city": "珞珈山"}, "takenAt": "2024-07-08T15:00:00"},
        )
        == "珞珈山 · 下午"
    )
    assert resolve_visible_caption("湖边的风", kind="alt", asset={}) == "湖边的风"


def test_snr_chapter_date_label_on_entry() -> None:
    rows = build_chapter_summaries(
        {
            "chapters": [
                {
                    "id": "c1",
                    "title": "樱园",
                    "curation": {"daySpan": ["2024-07-08"]},
                },
                {
                    "id": "c2",
                    "title": "7月9日",
                    "curation": {"daySpan": ["2024-07-09"]},
                },
            ]
        }
    )
    by_id = {r["id"]: r for r in rows}
    assert by_id["c1"]["dateLabel"] == "7月8日"
    # 主标题已含日期 → 副信息不重复
    assert by_id["c2"]["dateLabel"] == ""


def test_snr_fe_status_machine_and_prd_analytics() -> None:
    ai = (STUDIO / "preview-toolbar" / "ai-sheet.js").read_text(encoding="utf-8")
    core = (STUDIO / "preview-toolbar" / "core.js").read_text(encoding="utf-8")
    posture = (STUDIO / "preview-toolbar" / "narrative-posture.js").read_text(
        encoding="utf-8"
    )
    diff = (STUDIO / "preview-toolbar" / "narrate-diff.js").read_text(encoding="utf-8")
    longshot = (STUDIO / "preview-toolbar" / "longshot.js").read_text(encoding="utf-8")
    chapter = (STUDIO / "preview-toolbar" / "chapter-panel.js").read_text(
        encoding="utf-8"
    )

    assert 'status = "生成中"' in ai
    assert 'status = "失败可重试"' in ai
    assert 'setNarrateSheetStatus("生成中")' in core
    assert 'setNarrateSheetStatus("失败可重试")' in core

    assert 'trackStudioEvent("snr_posture_impression"' in posture
    assert 'trackStudioEvent("snr_upgrade_cta_click"' in posture
    assert 'source: "banner"' in posture
    assert 'trackStudioEvent("snr_diff_show"' in diff
    assert 'trackStudioEvent("snr_diff_jump"' in diff
    assert 'trackStudioEvent("snr_copy_pack"' in longshot
    assert 'tier: level === "L1" ? "L1" : "L0"' in longshot
    assert 'trackStudioEvent("snr_panel_mutex"' in longshot
    assert 'trackStudioEvent("snr_cta_label"' in longshot
    assert 'trackStudioEvent("snr_panel_mutex"' in ai
    assert "preview-chapter-panel__date" in chapter
    assert "ch.dateLabel" in chapter
