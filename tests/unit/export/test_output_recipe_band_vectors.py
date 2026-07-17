"""SFH W0b · Band 共享向量：Python classify_band / resolve 与 JS 夹具对齐。"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from travelogue.export.output_recipe import BandThresholds, classify_band, resolve_output_recipe

pytestmark = pytest.mark.unit

ROOT = Path(__file__).resolve().parents[3]
VECTORS_PATH = ROOT / "tests" / "fixtures" / "output_recipe_band_vectors.json"


@pytest.fixture(scope="module")
def vectors() -> dict:
    return json.loads(VECTORS_PATH.read_text(encoding="utf-8"))


def _thresholds(vectors: dict, set_id: str) -> BandThresholds:
    raw = vectors["thresholdSets"][set_id]
    return BandThresholds(
        sparse_max=int(raw["sparseMax"]),
        ambiguous_max=int(raw["ambiguousMax"]),
        narrative_chapter_hint_at=int(raw["narrativeChapterHintAt"]),
    )


def test_band_vectors_match_classify_band(vectors: dict) -> None:
    for case in vectors["bandCases"]:
        t = _thresholds(vectors, case["thresholds"])
        assert classify_band(int(case["keptN"]), t) == case["band"], case


def test_client_resolve_vectors_match_server_resolve(vectors: dict) -> None:
    """无 session 时，客户端 resolve 与服务端 resolve 的 band/needs_intent/intent 对齐。"""
    for case in vectors["clientResolveCases"]:
        if case.get("sessionIntent"):
            # session 覆盖走服务端 session_override；与 JS 侧单独测
            r = resolve_output_recipe(
                kept_n=int(case["keptN"]),
                entrypoint=str(case["entrypoint"]),
                enabled=bool(case["enabled"]),
                thresholds=_thresholds(vectors, case["thresholds"]),
                session_override={"intent": case["sessionIntent"]},
            )
        else:
            r = resolve_output_recipe(
                kept_n=int(case["keptN"]),
                entrypoint=str(case["entrypoint"]),
                enabled=bool(case["enabled"]),
                thresholds=_thresholds(vectors, case["thresholds"]),
            )
        assert r.band == case["band"], case["id"]
        assert r.needs_intent is bool(case["needsIntent"]), case["id"]
        expect_intent = case["intent"] or ""
        assert (r.intent or "") == expect_intent, case["id"]


def test_server_map_vectors_band_matches_classify(vectors: dict) -> None:
    """serverMapCases 中的 kept_n → band 与 classify_band 一致（夹具自洽）。"""
    for case in vectors["serverMapCases"]:
        body = case["body"]
        kept = int(body.get("keptN", body["recipe"]["kept_n"]))
        t = _thresholds(vectors, case["thresholds"])
        assert classify_band(kept, t) == case["expect"]["band"], case["id"]
        if body["recipe"].get("band"):
            assert body["recipe"]["band"] == case["expect"]["band"], case["id"]


def test_or_x06_threshold_sets_have_sparse_lt_ambiguous(vectors: dict) -> None:
    """OR-X-06 · 共享向量内阈值集须 sparseMax < ambiguousMax。"""
    for set_id, raw in vectors["thresholdSets"].items():
        assert int(raw["sparseMax"]) < int(raw["ambiguousMax"]), set_id


def test_or_x05_python_classify_accepts_zero_kept_n() -> None:
    """OR-X-05 对照：Python classify 对 kept_n=0 归 sparse（与 JS Number||0 一致）。"""
    t = BandThresholds(sparse_max=9, ambiguous_max=30)
    assert classify_band(0, t) == "sparse"
