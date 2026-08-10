"""ACP W4 · unified blind review (Spearman / export)."""

from __future__ import annotations

from travelogue.ai.eval.blind_review import (
    export_blind_review_pack,
    format_blind_report,
    pack_from_layout_suggestions,
    sample_items,
    score_blind_labels,
    spearman_srcc,
)


def test_spearman_perfect_correlation() -> None:
    srcc = spearman_srcc([1, 2, 3, 4, 5], [2, 4, 6, 8, 10])
    assert srcc is not None and srcc > 0.99


def test_sample_items_deterministic() -> None:
    pool = [{"i": i, "score": i / 10} for i in range(20)]
    a = sample_items(pool, sample_rate=0.25, seed=7)
    b = sample_items(pool, sample_rate=0.25, seed=7)
    assert a == b
    assert 1 <= len(a) <= 20


def test_export_and_score_layout_critic() -> None:
    suggestions = [
        {
            "chapterId": f"ch-{i}",
            "suggestion": f"建议{i}",
            "confidence": 0.1 * i,
            "suggestedPatternId": "screen-portrait-3",
        }
        for i in range(1, 12)
    ]
    pack = pack_from_layout_suggestions(suggestions, sample_rate=1.0, seed=1)
    assert pack.agent == "layout_critic"
    assert pack.items
    labeled = []
    for i, item in enumerate(pack.items):
        labeled.append(
            {
                **item,
                "humanScore": float((i % 5) + 1),
                "predictedOverall": float(item.get("predictedOverall") or 0.5),
            }
        )
    scores = score_blind_labels(labeled)
    assert scores["sampleCount"] == len(labeled)
    report = format_blind_report("layout_critic", scores, pack=pack)
    assert "SRCC" in report


def test_export_rejects_unknown_agent() -> None:
    try:
        export_blind_review_pack("not_an_agent", [])
        raise AssertionError("expected ValueError")
    except ValueError:
        pass
