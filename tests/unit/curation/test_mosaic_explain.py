"""LTN C6 · mosaicExplain narrative for Studio «为何没拼»."""

from __future__ import annotations

from travelogue.curation.mosaic_explain import build_mosaic_explain


def test_build_mosaic_explain_top3_rejects_and_fallback():
    curation = {
        "mosaicDecisionLog": [
            {
                "isWinnerPlan": True,
                "segmentId": "ch-01",
                "fallbackUsed": True,
                "fallbackReason": "mcs_all_sizes_failed",
                "candidateSource": "signature_fallback",
                "rejectedTemplates": [
                    {"templateId": "screen-landscape-4", "reason": "geometry_invalid"},
                    {
                        "templateId": "screen-mosaic-4-hero-70-sidebar",
                        "reason": "main_ar_ineligible",
                        "detail": "blocked_panorama",
                    },
                    {"templateId": "screen-portrait-4", "reason": "ordering_failed"},
                    {"templateId": "screen-landscape-3", "reason": "hard_invalid"},
                ],
            },
            {
                "isWinnerPlan": False,
                "fallbackUsed": True,
                "fallbackReason": "low_score",
                "rejectedTemplates": [
                    {"templateId": "screen-landscape-4", "reason": "hard_invalid"}
                ],
            },
        ]
    }
    out = build_mosaic_explain(curation)
    assert out is not None
    assert "未能拼成" in out["summary"]
    assert len(out["details"]) == 1
    line = out["details"][0]
    assert "多种拼图窗宽均未成功" in line
    assert "签名未命中" in line
    assert "landscape-4：版式几何不合适" in line
    assert "hero-70-sidebar" in line
    # Top3 only — fourth reject omitted
    assert "landscape-3" not in line




def test_build_mosaic_explain_contract_source_label():
    curation = {
        "mosaicDecisionLog": [
            {
                "isWinnerPlan": True,
                "fallbackUsed": True,
                "fallbackReason": "no_candidates",
                "candidateSource": "fallback",
            }
        ]
    }
    out = build_mosaic_explain(curation)
    assert out is not None
    assert "模板合约回落" in out["details"][0]


def test_build_mosaic_explain_ignores_non_winner_only_noise():
    curation = {
        "mosaicDecisionLog": [
            {
                "isWinnerPlan": False,
                "fallbackUsed": True,
                "fallbackReason": "low_score",
            }
        ]
    }
    assert build_mosaic_explain(curation) is None


def test_build_mosaic_explain_success_summary():
    curation = {
        "mosaicDecisionLog": [
            {
                "isWinnerPlan": True,
                "winnerPatternId": "screen-mosaic-4-hero-70-sidebar",
                "plannerPath": "mosaic",
                "fallbackUsed": False,
            }
        ]
    }
    out = build_mosaic_explain(curation)
    assert out is not None
    assert out["mode"] == "ok"
    assert "1 处拼图胜出" in out["summary"]


def test_chapter_layout_handler_includes_mosaic_explain(monkeypatch):
    from travelogue.web.studio_handlers import trip_list_handlers as mod

    trip = {
        "tripId": "t1",
        "curation": {
            "mosaicDecisionLog": [
                {
                    "isWinnerPlan": True,
                    "fallbackUsed": True,
                    "fallbackReason": "no_candidates",
                    "rejectedTemplates": [
                        {"templateId": "screen-landscape-4", "reason": "hard_invalid"}
                    ],
                }
            ]
        },
        "chapters": [],
    }

    class H:
        def __init__(self):
            self.payload = None

        def _json_response(self, code, body):
            self.payload = (code, body)

    monkeypatch.setattr(mod, "trip_id_from_query", lambda h: "t1")
    monkeypatch.setattr(mod, "is_valid_studio_trip_id", lambda x: True)
    monkeypatch.setattr(mod, "load_trip_or_404", lambda h, tid: (None, trip))
    h = H()
    mod.handle_chapter_layout(h)
    code, body = h.payload
    assert code == 200
    assert body["ok"] is True
    assert body["mosaicExplain"]["summary"]
    assert body["mosaicExplain"]["details"]
