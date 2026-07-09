"""Playwright browser pool thread affinity (M14 longshot regression)."""

from __future__ import annotations

import threading

import pytest

from travelogue.export.longshot import _PlaywrightBrowserPool

pytestmark = pytest.mark.unit


def test_browser_pool_recreates_when_job_thread_changes(monkeypatch) -> None:
    launch_count = {"n": 0}
    stop_count = {"n": 0}

    class FakeBrowser:
        def close(self) -> None:
            pass

    fake_browser = FakeBrowser()

    class FakeChromium:
        def launch(self, **kwargs):
            launch_count["n"] += 1
            return fake_browser

        def close(self) -> None:
            pass

    class FakePlaywright:
        chromium = FakeChromium()

        def stop(self) -> None:
            stop_count["n"] += 1

    class FakeManager:
        def start(self) -> FakePlaywright:
            return FakePlaywright()

    monkeypatch.setattr("playwright.sync_api.sync_playwright", lambda: FakeManager())

    pool = _PlaywrightBrowserPool()
    errors: list[BaseException] = []
    # Keep both threads alive so get_ident() values stay distinct (IDs can be
    # reused after a thread exits, which would falsely skip pool recreation).
    barrier = threading.Barrier(2)

    def run_in_thread() -> None:
        try:
            barrier.wait(timeout=5)
            browser = pool.acquire()
            assert browser is fake_browser
            pool.release()
        except BaseException as exc:
            errors.append(exc)

    t1 = threading.Thread(target=run_in_thread)
    t2 = threading.Thread(target=run_in_thread)
    t1.start()
    t2.start()
    t1.join()
    t2.join()

    assert not errors
    assert launch_count["n"] == 2
    assert stop_count["n"] == 1
