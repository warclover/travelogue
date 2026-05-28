"""Shared pytest fixtures and resource hygiene for the test suite."""

from __future__ import annotations

import gc

import pytest


@pytest.fixture(autouse=True)
def _release_resources_before_playwright(request: pytest.FixtureRequest):
    """Reduce open_clip/torch ↔ Playwright contention for longshot capture.

    The longshot subprocess spawns a Chromium browser via Playwright. When the
    parent process has open_clip + PyTorch resident (because earlier tests
    loaded the CLIP weights), Chromium launch can fail on resource-tight
    Windows boxes. We GC before/after so transient objects are collected and
    the browser process gets more headroom.

    NOTE: unloading torch/open_clip from sys.modules is **not safe** — their C
    extensions have lingering finalizers and can segfault the interpreter.
    The longshot test itself retries once on launch failure for robustness.
    """
    if request.node.get_closest_marker("playwright_serial") is None:
        yield
        return

    try:
        import torch  # type: ignore

        if torch.cuda.is_available():
            torch.cuda.empty_cache()
    except Exception:
        pass

    gc.collect()
    yield
    gc.collect()
