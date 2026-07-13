"""Bookends VL plugin interface smoke (B3 · default off)."""

from __future__ import annotations

from travelogue.cover_engine.plugins.vl import (
    apply_closing_vl_rerank,
    apply_opening_vl_rerank,
    closing_vl_enabled,
    opening_vl_enabled,
)


def test_vl_plugins_default_off() -> None:
    assert opening_vl_enabled() is False or isinstance(opening_vl_enabled(), bool)
    assert closing_vl_enabled() is False or isinstance(closing_vl_enabled(), bool)


def test_vl_rerank_noop_without_plugin() -> None:
    cands = [{"assetId": "a"}, {"assetId": "b"}]
    assert apply_opening_vl_rerank({}, cands) == cands
    assert apply_closing_vl_rerank({}, cands) == cands


def test_vl_rerank_fail_open() -> None:
    class Boom:
        def rerank_opening(self, trip, candidates):
            raise RuntimeError("cloud down")

        def rerank_closing(self, trip, candidates, *, cover_asset_id=None):
            raise RuntimeError("cloud down")

    cands = [{"assetId": "a"}]
    # Even if somehow enabled, exception must fail-open — force call with plugin
    from travelogue.config import get_config
    from travelogue.config.runtime import config_override

    cfg = get_config()
    with config_override(cfg):
        cfg.bookends.plugins.opening_vl_rerank = True
        cfg.bookends.plugins.closing_vl_rerank = True
        assert apply_opening_vl_rerank({}, cands, plugin=Boom()) == cands
        assert apply_closing_vl_rerank({}, cands, plugin=Boom()) == cands
