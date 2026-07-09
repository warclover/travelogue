"""Tests for mosaic runtime ContextVar overrides (M-B4a · ADR-015)."""

from __future__ import annotations

import threading
from dataclasses import replace

from travelogue.config import MosaicConfig
from travelogue.layout_engine.mosaic.runtime import (
    get_effective_mosaic_config,
    reset_mosaic_config_override,
    set_mosaic_config_override,
)


def test_mosaic_override_isolated_across_threads() -> None:
    barrier = threading.Barrier(2)
    results: dict[str, str] = {}

    def worker(name: str, version: str) -> None:
        set_mosaic_config_override(replace(MosaicConfig(), scorer_version=version))
        barrier.wait()
        results[name] = get_effective_mosaic_config().scorer_version
        reset_mosaic_config_override()

    threads = [
        threading.Thread(target=worker, args=("a", "thread-a")),
        threading.Thread(target=worker, args=("b", "thread-b")),
    ]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join(timeout=30)

    assert results["a"] == "thread-a"
    assert results["b"] == "thread-b"
