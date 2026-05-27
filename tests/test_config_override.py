"""Config isolation via contextvars (P0 tech-debt fix)."""

from __future__ import annotations

import threading
from dataclasses import replace

import pytest

from travelogue.config import config_override, get_config, reset_config_cache


@pytest.fixture(autouse=True)
def _clear_config_cache():
    reset_config_cache()
    yield
    reset_config_cache()


def test_config_override_restores_previous():
    base = get_config()
    alt = replace(base, ingest=replace(base.ingest, max_photos=999))

    assert get_config().ingest.max_photos != 999
    with config_override(alt):
        assert get_config().ingest.max_photos == 999
    assert get_config().ingest.max_photos == base.ingest.max_photos


def test_config_override_isolated_across_threads():
    base = get_config()
    results: dict[str, int] = {}
    barrier = threading.Barrier(2)

    def worker(name: str, max_photos: int) -> None:
        cfg = replace(base, ingest=replace(base.ingest, max_photos=max_photos))
        with config_override(cfg):
            barrier.wait(timeout=5)
            results[name] = get_config().ingest.max_photos

    t_a = threading.Thread(target=worker, args=("a", 111))
    t_b = threading.Thread(target=worker, args=("b", 222))
    t_a.start()
    t_b.start()
    t_a.join(timeout=10)
    t_b.join(timeout=10)

    assert results == {"a": 111, "b": 222}
    assert get_config().ingest.max_photos == base.ingest.max_photos


def test_nested_config_override():
    outer = replace(get_config(), ingest=replace(get_config().ingest, max_photos=10))
    inner = replace(get_config(), ingest=replace(get_config().ingest, max_photos=20))

    with config_override(outer):
        assert get_config().ingest.max_photos == 10
        with config_override(inner):
            assert get_config().ingest.max_photos == 20
        assert get_config().ingest.max_photos == 10
