"""FTUE W2 · trips 优先级与 stub Copy 合同。"""

from __future__ import annotations

from pathlib import Path

import pytest

pytestmark = pytest.mark.unit


def test_resolve_studio_trips_dir_priority(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    from travelogue.web.studio_config import resolve_studio_trips_dir

    cli = tmp_path / "cli-trips"
    env = tmp_path / "env-trips"
    cfg = tmp_path / "cfg-trips"
    cli.mkdir()
    env.mkdir()
    cfg.mkdir()

    root, source = resolve_studio_trips_dir(cli_trips_dir=cli, cfg_trips_dir=cfg)
    assert source == "cli"
    assert root == cli.resolve()

    monkeypatch.setenv("TRAVELOGUE_TRIPS_DIR", str(env))
    root, source = resolve_studio_trips_dir(cli_trips_dir=None, cfg_trips_dir=cfg)
    assert source == "env"
    assert root == env.resolve()

    monkeypatch.delenv("TRAVELOGUE_TRIPS_DIR", raising=False)
    root, source = resolve_studio_trips_dir(cli_trips_dir=None, cfg_trips_dir=cfg)
    assert source == "config"
    assert root == cfg.resolve()

    # CLI wins over env
    monkeypatch.setenv("TRAVELOGUE_TRIPS_DIR", str(env))
    root, source = resolve_studio_trips_dir(cli_trips_dir=cli, cfg_trips_dir=cfg)
    assert source == "cli"
    assert root == cli.resolve()


def test_stub_copy_no_engineering_words() -> None:
    from travelogue.services import narrate as narrate_mod

    src = Path(narrate_mod.__file__).read_text(encoding="utf-8")
    for banned in ("竖构图", "方构图", "竖长一帧", "一帧。", "行程归档", "Day {", 'f"Day '):
        assert banned not in src, banned
    assert "第{chapter_index}天" in src or "第" in src
    assert "把{place}收进这一本" in src or "收进这一本" in src
    assert "竖幅" in src
