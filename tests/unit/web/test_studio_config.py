"""Studio config resolution (avoid config.demo.yaml for imports)."""

from __future__ import annotations

from pathlib import Path

from travelogue.web.studio_config import resolve_studio_config


def test_resolve_studio_config_prefers_config_yaml_over_demo(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    (tmp_path / "config.demo.yaml").write_text("trips_dir: ./trips\n", encoding="utf-8")
    (tmp_path / "config.yaml").write_text(
        "trips_dir: ./trips\nnarrative:\n  decor_line_llm_enabled: true\n",
        encoding="utf-8",
    )
    resolved = resolve_studio_config()
    assert resolved == (tmp_path / "config.yaml").resolve()
