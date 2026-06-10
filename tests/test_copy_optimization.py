"""COPY-P0 · lite copy v1.1: scope, fact skip, decorLine edit."""

from __future__ import annotations

from pathlib import Path

from travelogue.config import AppConfig, NarrativeConfig
from travelogue.services.copy_intent_infer import infer_copy_intent, resolve_copy_intent
from travelogue.services.decor_line import (
    apply_decor_lines,
    decor_line_facts_sufficient,
    extract_chapter_facts,
    generate_decor_line_candidates,
    pick_best_decor_line,
    voice_decor_candidates,
)
from travelogue.services.llm_decor_line import should_call_llm_decor
from travelogue.services.narrate import run_narrate
from travelogue.services.narrative_scope import SCOPE_FRAME, SCOPE_FULL, chapter_lead_allowed
from travelogue.services.voice_excerpt import trim_voice_for_copy
from travelogue.web.copy_patch import apply_copy_patch


def _rich_chapter_trip() -> dict:
    return {
        "tripId": "copy-opt",
        "meta": {"title": "测试", "places": ["京都"], "tone": "relaxed"},
        "assets": [
            {
                "id": "a1",
                "type": "image",
                "tags": ["寺庙", "雨"],
                "place": {"city": "京都"},
            }
        ],
        "chapters": [
            {
                "id": "ch-01",
                "index": 1,
                "patternId": "open",
                "title": "雨后",
                "items": [{"type": "media-card", "assetId": "a1"}],
                "curation": {"memoryAnchors": ["鸭川"], "places": ["京都"]},
            }
        ],
    }


def test_default_narrative_scope_is_frame() -> None:
    cfg = AppConfig()
    assert cfg.narrative.scope == "frame"


def test_decor_line_skips_when_facts_insufficient() -> None:
    trip = {
        "tripId": "sparse",
        "meta": {"title": "空"},
        "assets": [{"id": "a1", "type": "image", "tags": ["寺庙"]}],
        "chapters": [
            {
                "id": "ch-01",
                "index": 1,
                "patternId": "open",
                "title": "一章",
                "items": [{"type": "media-card", "assetId": "a1"}],
            }
        ],
    }
    chapter = trip["chapters"][0]
    cfg = AppConfig(narrative=NarrativeConfig(decor_line_min_fact_count=2))
    assert decor_line_facts_sufficient(chapter, trip, cfg=cfg) is False
    apply_decor_lines(trip, cfg=cfg)
    assert trip["chapters"][0].get("decorLine", "") == ""


def test_decor_line_voice_bypasses_fact_threshold() -> None:
    trip = {
        "tripId": "voice",
        "meta": {"title": "语音"},
        "assets": [
            {
                "id": "a1",
                "type": "image",
                "voice": {"transcriptPreview": "雨太大了先回酒店拿伞"},
            }
        ],
        "chapters": [
            {
                "id": "ch-01",
                "index": 1,
                "patternId": "open",
                "title": "",
                "items": [{"type": "media-card", "assetId": "a1"}],
            }
        ],
    }
    chapter = trip["chapters"][0]
    cfg = AppConfig(narrative=NarrativeConfig(decor_line_min_fact_count=2))
    assert decor_line_facts_sufficient(chapter, trip, cfg=cfg) is True
    facts = extract_chapter_facts(chapter, trip)
    assert facts[0].startswith("雨太大")


def test_template_candidates_exclude_filler_phrases() -> None:
    trip = _rich_chapter_trip()
    chapter = trip["chapters"][0]
    cands = generate_decor_line_candidates(chapter, trip)
    joined = " ".join(cands)
    assert "留在这一章" not in joined
    assert "记住" not in joined


def test_copy_patch_decor_line_truncates() -> None:
    trip = _rich_chapter_trip()
    long_line = "这是一句超过三十个字限制的章级点缀文案应该被截断到上限。"
    apply_copy_patch(trip, "chapters.ch-01.decorLine", long_line)
    assert len(trip["chapters"][0]["decorLine"]) <= 30


def test_copy_patch_decor_line() -> None:
    trip = _rich_chapter_trip()
    apply_copy_patch(trip, "chapters.ch-01.decorLine", "用户改过的章级点睛。")
    assert trip["chapters"][0]["decorLine"] == "用户改过的章级点睛。"
    assert trip["chapters"][0]["edited"] is True
    assert len(trip["chapters"][0]["decorLine"]) <= 30


def test_narrate_frame_skips_lead_and_caption(tmp_path: Path) -> None:
    trip = {
        "tripId": "scope-frame",
        "meta": {"title": "京都", "tone": "relaxed", "hook": ""},
        "assets": [
            {"id": "a1", "type": "image", "caption": "旧图注"},
        ],
        "chapters": [
            {
                "id": "ch-01",
                "index": 1,
                "title": "Day",
                "lead": "旧导语",
                "items": [{"type": "media-card", "assetId": "a1", "caption": "旧图注"}],
            }
        ],
        "pipeline": {"status": "structure_locked", "locks": {"structure": True, "copy": False}},
    }
    result = run_narrate(trip, provider="stub", scope=SCOPE_FRAME, regenerate=True)
    assert not any("lead" in f for f in result.fields_updated)
    assert not any("caption" in f for f in result.fields_updated)


def test_render_decor_line_editable(tmp_path: Path) -> None:
    import json
    import shutil

    from travelogue.paths import ROOT, TEMPLATE_VISUAL_JOURNAL
    from travelogue.render.engine import render_trip

    fixture = ROOT / "schemas" / "fixtures" / "trip.render_golden.json"
    trip = json.loads(fixture.read_text(encoding="utf-8"))
    ws = tmp_path / "trips" / "render-decor"
    ws.mkdir(parents=True)
    shutil.copytree(TEMPLATE_VISUAL_JOURNAL / "assets", ws / "assets")
    (ws / "assets" / "demo" / "placeholder.m4a").write_bytes(b"")
    (ws / "assets" / "demo" / "video.mp4").write_bytes(b"")
    for ch in trip.get("chapters") or []:
        ch["decorLine"] = "章级点睛句。"
    (ws / "trip.json").write_text(json.dumps(trip, ensure_ascii=False, indent=2), encoding="utf-8")
    render_trip(ws / "trip.json", validate=False, export_mode="draft")
    html = (ws / "index.html").read_text(encoding="utf-8")
    assert 'data-editable="decor-line"' in html
    assert "chapters." in html and "decorLine" in html


def test_trim_voice_for_copy() -> None:
    assert trim_voice_for_copy("雨太大了，我们先回酒店拿伞。", max_chars=30) == "雨太大了，我们先回酒店拿伞。"


def test_voice_decor_candidate_first_in_pool() -> None:
    trip = {
        "tripId": "voice-pick",
        "meta": {"title": "语音"},
        "assets": [
            {
                "id": "a1",
                "type": "image",
                "tags": ["雨"],
                "voice": {"transcriptPreview": "雨太大了，先回酒店拿伞"},
            }
        ],
        "chapters": [
            {
                "id": "ch-01",
                "index": 1,
                "patternId": "open",
                "title": "雨后",
                "items": [{"type": "media-card", "assetId": "a1"}],
                "curation": {"memoryAnchors": ["鸭川"]},
            }
        ],
    }
    chapter = trip["chapters"][0]
    cfg = AppConfig(narrative=NarrativeConfig(decor_line_voice_first=True))
    voice_cands = voice_decor_candidates(chapter, trip, cfg=cfg)
    assert voice_cands
    assert voice_cands[0].startswith("雨太大")
    cands = generate_decor_line_candidates(chapter, trip, cfg=cfg)
    assert cands[0] == voice_cands[0]
    picked = pick_best_decor_line(cands, chapter, trip, cfg=cfg)
    assert "雨太大" in picked


def test_llm_decor_skipped_without_facts() -> None:
    trip = {
        "tripId": "no-fact",
        "meta": {"title": "空"},
        "assets": [],
        "chapters": [{"id": "ch-01", "index": 1, "title": "", "items": []}],
    }
    cfg = AppConfig(narrative=NarrativeConfig(decor_line_llm_enabled=True))
    assert should_call_llm_decor(trip["chapters"][0], trip, cfg=cfg) is False


def test_llm_decor_candidates_via_mock() -> None:
    trip = _rich_chapter_trip()
    chapter = trip["chapters"][0]
    calls: list[list[dict[str, str]]] = []

    def fake_chat(messages: list[dict[str, str]]) -> str:
        calls.append(messages)
        return '{"candidates": ["鸭川边，雨线仍亮。", "寺庙檐下，雨未停。"]}'

    cfg = AppConfig(
        narrative=NarrativeConfig(
            decor_line_llm_enabled=True,
            decor_line_voice_first=False,
        )
    )
    cands = generate_decor_line_candidates(chapter, trip, cfg=cfg, chat_fn=fake_chat)
    assert calls
    assert any("鸭川" in c or "雨" in c for c in cands)


def test_llm_decor_prefers_llm_over_tag_template() -> None:
    trip = {
        "tripId": "tag-fallback",
        "meta": {"title": "测试"},
        "assets": [
            {
                "id": "a1",
                "type": "image",
                "tags": ["person", "face", "白天"],
                "mediaClass": "photo",
            }
        ],
        "chapters": [
            {
                "id": "ch-03",
                "index": 3,
                "title": "10月5日",
                "items": [{"type": "media-card", "assetId": "a1"}],
            }
        ],
    }
    chapter = trip["chapters"][0]

    def fake_chat(_messages: list[dict[str, str]]) -> str:
        return '{"candidates": ["制衣坊门口，阳光正好。"]}'

    cfg = AppConfig(
        narrative=NarrativeConfig(
            decor_line_llm_enabled=True,
            decor_line_voice_first=False,
        )
    )
    picked = pick_best_decor_line(
        generate_decor_line_candidates(chapter, trip, cfg=cfg, chat_fn=fake_chat),
        chapter,
        trip,
        cfg=cfg,
    )
    assert "制衣坊" in picked
    assert "person" not in picked


def test_passive_copy_intent_from_voice() -> None:
    trip = {
        "tripId": "intent",
        "meta": {"title": "吃"},
        "assets": [
            {
                "id": "a1",
                "type": "image",
                "voice": {"transcriptPreview": "这家拉面真的很好吃"},
            }
        ],
        "chapters": [
            {
                "id": "ch-01",
                "index": 1,
                "title": "午餐",
                "items": [{"type": "media-card", "assetId": "a1"}],
            }
        ],
    }
    chapter = trip["chapters"][0]
    intent = infer_copy_intent(chapter, trip)
    assert intent.get("focus") == "食物"


def test_chapter_lead_blocked_when_decor_line_present() -> None:
    chapters = [
        {"id": "ch-01", "index": 1, "decorLine": "章级一句。", "lead": "旧导语"},
        {"id": "ch-02", "index": 2},
    ]
    assert chapter_lead_allowed(chapters[0], chapters, SCOPE_FULL) is False
    assert chapter_lead_allowed(chapters[1], chapters, SCOPE_FULL) is True


def test_apply_decor_line_clears_lead() -> None:
    trip = _rich_chapter_trip()
    trip["chapters"][0]["lead"] = "旧导语应被清掉。"
    cfg = AppConfig(narrative=NarrativeConfig(decor_line_enabled=True))
    apply_decor_lines(trip, cfg=cfg)
    line = trip["chapters"][0].get("decorLine", "")
    if line:
        assert not trip["chapters"][0].get("lead")


def test_resolve_copy_intent_prefers_explicit_note() -> None:
    trip = _rich_chapter_trip()
    chapter = trip["chapters"][0]
    chapter.setdefault("curation", {})["copyIntent"] = {"note": "用户念头"}
    resolved = resolve_copy_intent(chapter, trip)
    assert resolved.get("note") == "用户念头"


def test_record_copy_metrics_on_apply_decor_lines() -> None:
    trip = _rich_chapter_trip()
    cfg = AppConfig(narrative=NarrativeConfig(decor_line_enabled=True))
    apply_decor_lines(trip, cfg=cfg)
    metrics = trip.get("curation", {}).get("copyMetrics") or {}
    assert metrics.get("phase") == "lite-copy-v1.1"
    assert metrics.get("decorLineCount", 0) >= 1
    assert "copy_total_chars" in metrics


def test_visual_facts_from_tags() -> None:
    from travelogue.services.visual_facts import extract_visual_facts

    trip = _rich_chapter_trip()
    chapter = trip["chapters"][0]
    facts = extract_visual_facts(chapter, trip)
    assert facts
    assert any("寺庙" in f or "雨" in f for f in facts)


def test_copy_patch_records_metrics() -> None:
    from travelogue.web.copy_patch import apply_copy_patches

    trip = _rich_chapter_trip()
    apply_copy_patches(trip, [{"path": "chapters.ch-01.decorLine", "value": "用户改句。"}])
    metrics = trip["curation"]["copyMetrics"]
    assert metrics.get("decorLineCount") >= 1
    assert metrics.get("edited_decor_line_count") >= 1


def test_intent_adoption_rate() -> None:
    from travelogue.services.copy_metrics import compute_intent_adoption_rate, record_copy_metrics

    trip = _rich_chapter_trip()
    trip["chapters"][0].setdefault("curation", {})["copyIntent"] = {"note": "雨停"}
    record_copy_metrics(trip)
    assert compute_intent_adoption_rate(trip) == 1.0
    assert trip["curation"]["copyMetrics"]["intent_adoption_rate"] == 1.0


def test_copy_ui_event_photos_only_rate() -> None:
    from travelogue.services.copy_metrics import record_copy_ui_event

    trip = _rich_chapter_trip()
    record_copy_ui_event(trip, "photos_only_on")
    record_copy_ui_event(trip, "photos_only_on")
    record_copy_ui_event(trip, "photos_only_off")
    metrics = trip["curation"]["copyMetrics"]
    assert metrics["clientEventCounts"]["photos_only_on"] == 2
    assert metrics["photos_only_rate"] == round(2 / 3, 3)


def test_passive_intent_improves_intent_fit_score() -> None:
    from travelogue.services.copy_intent_infer import infer_copy_intent
    from travelogue.services.decor_line import _score_candidate

    trip = {
        "tripId": "intent-fit",
        "meta": {"title": "吃"},
        "assets": [
            {
                "id": "a1",
                "type": "image",
                "voice": {"transcriptPreview": "这家拉面真的很好吃"},
            }
        ],
        "chapters": [
            {
                "id": "ch-01",
                "index": 1,
                "title": "午餐",
                "items": [{"type": "media-card", "assetId": "a1"}],
            }
        ],
    }
    chapter = trip["chapters"][0]
    candidate = "这家拉面真的很好吃"
    facts = ["这家拉面真的很好吃"]
    passive = infer_copy_intent(chapter, trip)
    assert passive.get("focus") == "食物"
    score_food = _score_candidate(
        candidate,
        chapter,
        facts,
        {"focus": "食物"},
        use_intent=True,
        voice_snippets=[candidate],
    )
    score_place = _score_candidate(
        candidate,
        chapter,
        facts,
        {"focus": "地方"},
        use_intent=True,
        voice_snippets=[candidate],
    )
    score_passive = _score_candidate(
        candidate,
        chapter,
        facts,
        passive,
        use_intent=True,
        voice_snippets=[candidate],
    )
    assert score_food == score_passive
    assert score_food > score_place


def test_decor_line_disabled_rollback() -> None:
    trip = _rich_chapter_trip()
    cfg = AppConfig(narrative=NarrativeConfig(decor_line_enabled=False))
    assert apply_decor_lines(trip, cfg=cfg) == []


def test_legacy_copy_phase_triggers_decor_regenerate() -> None:
    from travelogue.services.decor_line import chapter_needs_decor_line

    trip = {
        "curation": {"copyStyle": {"phase": "p11-lite-line"}},
        "chapters": [{"id": "ch-01", "decorLine": "记住face"}],
    }
    assert chapter_needs_decor_line(trip["chapters"][0], trip) is True


def test_empty_decor_line_still_needs_fill() -> None:
    from travelogue.services.decor_line import chapter_needs_decor_line

    chapter = {"id": "ch-01", "decorLine": ""}
    assert chapter_needs_decor_line(chapter, {}) is True


def test_tag_stub_decor_line_triggers_regenerate_when_llm_enabled() -> None:
    from travelogue.services.decor_line import chapter_needs_decor_line

    trip = {
        "curation": {"copyStyle": {"phase": "lite-copy-v1.1"}},
        "chapters": [{"id": "ch-03", "decorLine": "person · face · 白天，photo"}],
    }
    cfg = AppConfig(narrative=NarrativeConfig(decor_line_llm_enabled=True))
    assert chapter_needs_decor_line(trip["chapters"][0], trip, cfg=cfg) is True
    cfg_off = AppConfig(narrative=NarrativeConfig(decor_line_llm_enabled=False))
    assert chapter_needs_decor_line(trip["chapters"][0], trip, cfg=cfg_off) is False


def test_apply_copy_intent_cascade() -> None:
    from travelogue.services.decor_line import apply_copy_intent_cascade

    trip = {
        "tripId": "cascade",
        "chapters": [
            {"id": "ch-01", "index": 1, "curation": {}},
            {"id": "ch-02", "index": 2, "curation": {}},
            {"id": "ch-03", "index": 3, "curation": {}},
        ],
    }
    updated = apply_copy_intent_cascade(
        trip,
        "ch-02",
        {"mood": "松弛", "focus": "地方", "note": "鸭川"},
        apply_to_subsequent=True,
    )
    assert updated == ["ch-02", "ch-03"]
    assert trip["chapters"][0].get("curation", {}).get("copyIntent") is None
    assert trip["chapters"][1]["curation"]["copyIntent"]["note"] == "鸭川"
    assert trip["chapters"][2]["curation"]["copyIntent"]["focus"] == "地方"


def test_inline_edit_photos_only_guard() -> None:
    from travelogue.paths import TEMPLATE_VISUAL_JOURNAL

    src = (TEMPLATE_VISUAL_JOURNAL / "inline-edit.js").read_text(encoding="utf-8")
    assert "function isPhotosOnly()" in src
    assert "if (isPhotosOnly()) return;" in src


def test_present_surface_has_no_decor_line_editable(tmp_path: Path) -> None:
    import json
    import shutil

    from travelogue.paths import ROOT, TEMPLATE_VISUAL_JOURNAL
    from travelogue.render.engine import render_trip

    fixture = ROOT / "schemas" / "fixtures" / "trip.render_golden.json"
    trip = json.loads(fixture.read_text(encoding="utf-8"))
    for ch in trip.get("chapters") or []:
        ch["decorLine"] = "章级点睛句。"
    ws = tmp_path / "trips" / "present-copy"
    ws.mkdir(parents=True)
    shutil.copytree(TEMPLATE_VISUAL_JOURNAL / "assets", ws / "assets")
    (ws / "assets" / "demo" / "placeholder.m4a").write_bytes(b"")
    (ws / "assets" / "demo" / "video.mp4").write_bytes(b"")
    (ws / "trip.json").write_text(json.dumps(trip, ensure_ascii=False, indent=2), encoding="utf-8")
    render_trip(
        ws / "trip.json",
        validate=False,
        export_mode="present-preview",
        index_name="index-present.html",
    )
    html = (ws / "index-present.html").read_text(encoding="utf-8")
    assert 'data-editable="decor-line"' not in html
