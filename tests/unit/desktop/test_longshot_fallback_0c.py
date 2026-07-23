"""M-INS-0c · longshot client upload + playwright probe."""

from __future__ import annotations

from pathlib import Path

import pytest

from travelogue.export import longshot as longshot_mod


@pytest.fixture(autouse=True)
def _reset_pw_cache(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(longshot_mod, "_PLAYWRIGHT_AVAILABLE", None)


def test_write_longshot_upload_names_file(tmp_path: Path) -> None:
    trip = tmp_path / "t1"
    trip.mkdir()
    (trip / "trip.json").write_text(
        '{"meta":{"title":"测试旅途"}}',
        encoding="utf-8",
    )
    out = longshot_mod.write_longshot_upload(trip, b"\x89PNG\r\n\x1a\n" + b"x", fmt="png")
    assert out.is_file()
    assert out.name.endswith(".png")
    # D-SFI-07 · on-disk stem uses display title (supersede FTUE tripId naming)
    assert out.name == "测试旅途-长图.png"


def test_playwright_unavailable_without_package(monkeypatch: pytest.MonkeyPatch) -> None:
    import builtins

    real_import = builtins.__import__

    def _fake_import(name, *args, **kwargs):
        if name.startswith("playwright"):
            raise ImportError("no playwright")
        return real_import(name, *args, **kwargs)

    monkeypatch.setattr(builtins, "__import__", _fake_import)
    monkeypatch.setattr(longshot_mod, "_PLAYWRIGHT_AVAILABLE", None)
    assert longshot_mod.playwright_longshot_available() is False


def test_studio_capabilities_include_longshot_flags(monkeypatch: pytest.MonkeyPatch) -> None:
    from travelogue.web.studio_handlers import config_handlers

    monkeypatch.setattr(
        "travelogue.export.longshot.playwright_longshot_available",
        lambda: False,
    )
    monkeypatch.setattr("travelogue.paths.is_frozen", lambda: True)
    caps = config_handlers.studio_capabilities(client_host="127.0.0.1")
    assert caps["longshotServer"] is False
    assert caps["longshotClientFallback"] is True
    assert caps["desktopExit"] is True
