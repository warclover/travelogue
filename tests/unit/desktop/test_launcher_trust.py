"""Desktop launcher defaults."""

from __future__ import annotations

import os
import sys

import pytest

from travelogue.desktop import launcher


def test_launcher_opts_in_trust_local_album(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("TRAVELOGUE_STUDIO_TRUST_LOCAL_ALBUM", raising=False)
    called: list[bool] = []

    def _fake_app() -> None:
        called.append(True)
        assert os.environ.get("TRAVELOGUE_STUDIO_TRUST_LOCAL_ALBUM") == "1"

    monkeypatch.setattr(sys, "argv", ["travelogue-studio"])
    monkeypatch.setattr(launcher, "app", _fake_app, raising=False)

    # launcher.main imports app inside the function — patch the module it imports from.
    import travelogue.cli as cli_mod

    monkeypatch.setattr(cli_mod, "app", _fake_app)
    launcher.main()
    assert called == [True]


def test_launcher_respects_explicit_trust_off(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("TRAVELOGUE_STUDIO_TRUST_LOCAL_ALBUM", "0")

    def _fake_app() -> None:
        assert os.environ.get("TRAVELOGUE_STUDIO_TRUST_LOCAL_ALBUM") == "0"

    monkeypatch.setattr(sys, "argv", ["travelogue-studio"])
    import travelogue.cli as cli_mod

    monkeypatch.setattr(cli_mod, "app", _fake_app)
    launcher.main()


def test_ensure_studio_trust_local_album_setdefault(monkeypatch: pytest.MonkeyPatch) -> None:
    from travelogue.web.studio_handlers.import_handlers import ensure_studio_trust_local_album

    monkeypatch.delenv("TRAVELOGUE_STUDIO_TRUST_LOCAL_ALBUM", raising=False)
    ensure_studio_trust_local_album()
    assert os.environ.get("TRAVELOGUE_STUDIO_TRUST_LOCAL_ALBUM") == "1"

    monkeypatch.setenv("TRAVELOGUE_STUDIO_TRUST_LOCAL_ALBUM", "0")
    ensure_studio_trust_local_album()
    assert os.environ.get("TRAVELOGUE_STUDIO_TRUST_LOCAL_ALBUM") == "0"
