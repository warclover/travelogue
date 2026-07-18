"""TPC W1 · config / mix index / debt aggregation / BLK-10 wiring smoke."""

from __future__ import annotations

import pytest

from travelogue.config.mosaic import mosaic_from_dict
from travelogue.layout_contract.orientations import AspectKind
from travelogue.layout_engine.contract.debt import (
    merge_debt_reports,
    summarize_mosaic_decision_log,
    window_mix_histogram,
)
from travelogue.layout_engine.contract.mix_index import (
    build_mix_inverted_index,
    format_mix_key,
    mix_key_from_aspects,
)


def test_mix_key_from_aspects_maps_panorama_and_tall() -> None:
    aspects: dict[str, AspectKind] = {
        "a": "panorama",
        "b": "tall",
        "c": "square",
        "d": "landscape",
    }
    assert mix_key_from_aspects(["a", "b", "c", "d"], aspects) == (2, 1, 1)
    assert format_mix_key((2, 1, 1)) == "L2P1S1"


def test_build_mix_inverted_index_stable_order() -> None:
    from travelogue.layout_templates.registry import get_engine

    templates = {t.id: t for t in get_engine().list_active(enforce_quotas=False)}
    index = build_mix_inverted_index(templates)
    assert index
    # keys sorted; values lexicographic
    keys = list(index.keys())
    assert keys == sorted(keys)
    for ids in index.values():
        assert ids == sorted(ids)


def test_summarize_mosaic_decision_log_legacy_rate() -> None:
    logs = [
        {"plannerPath": "mosaic", "windowSize": 5},
        {"plannerPath": "legacy", "windowSize": 5, "fallbackUsed": True, "fallbackReason": "no_candidates"},
        {"plannerPath": "legacy", "windowSize": 4, "fallbackUsed": True, "fallbackReason": "low_score"},
        {
            "plannerPath": "mosaic",
            "windowSize": 5,
            "selfHealApplied": True,
            "selfHealStep": "tightened_rescore",
        },
    ]
    summary = summarize_mosaic_decision_log(logs)
    assert summary["windowCount"] == 4
    assert summary["legacyCount"] == 2
    assert summary["legacyRate"] == 0.5
    assert summary["fallbackReasonCounts"]["no_candidates"] == 1
    assert summary["selfHealStepCounts"]["tightened_rescore"] == 1


def test_window_mix_histogram_and_merge() -> None:
    chapters = [
        {
            "screens": [
                {
                    "patternId": "screen-mosaic-5-main-portrait-3land",
                    "slots": [
                        {"assetId": "p1"},
                        {"assetId": "l1"},
                        {"assetId": "l2"},
                        {"assetId": "l3"},
                        {"assetId": "l4"},
                    ],
                }
            ]
        }
    ]
    assets = [
        {"id": "p1", "width": 1000, "height": 1500},
        {"id": "l1", "width": 1600, "height": 900},
        {"id": "l2", "width": 1600, "height": 900},
        {"id": "l3", "width": 1600, "height": 900},
        {"id": "l4", "width": 1600, "height": 900},
    ]
    hist = window_mix_histogram(chapters, {a["id"]: a for a in assets})
    assert hist.get("L4P1S0") == 1

    merged = merge_debt_reports(
        [
            {
                "tripId": "t1",
                "legacy": {"windowCount": 4, "legacyCount": 1, "legacyRate": 0.25, "plannerPathCounts": {"mosaic": 3, "legacy": 1}, "fallbackReasonCounts": {}},
                "aspectPatternMatchRate": 0.8,
                "windowMixHistogram": hist,
                "mixHoles": [{"mix": "L2P2S0", "windowFreq": 2}],
            }
        ]
    )
    assert merged["legacyRate"] == 0.25
    assert merged["mixHoleTop"][0]["mix"] == "L2P2S0"


def test_template_contract_defaults_off() -> None:
    cfg = mosaic_from_dict({})
    assert cfg.template_contract.enabled is False
    assert cfg.template_contract.shadow_log is True


def test_candidates_attach_contract_shadow_when_log_on(lte_pattern_enabled) -> None:
    from dataclasses import replace

    from tests._golden.helpers import build_mosaic_five_2p3l_window
    from travelogue.config import get_config
    from travelogue.layout_engine.mosaic.candidates import (
        generate_window_candidates_with_rejections,
    )

    ids, aspects, assets_map = build_mosaic_five_2p3l_window()
    cfg = replace(
        get_config().mosaic,
        template_contract=replace(
            get_config().mosaic.template_contract, enabled=False, shadow_log=True
        ),
    )
    result = generate_window_candidates_with_rejections(
        ids, aspects, assets_map, cfg=cfg
    )
    assert result.contract_shadow is not None
    assert "windowMix" in result.contract_shadow
    assert "hasDiff" in result.contract_shadow
    # Selection path unchanged: candidates still populated from live try_order.
    assert isinstance(result.candidates, list)
