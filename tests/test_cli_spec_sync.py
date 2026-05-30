"""P5-12.3 · CLI-SPEC stays aligned with implemented studio/longshot CLI."""

from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CLI_SPEC = ROOT / "docs" / "CLI-SPEC.md"


def test_cli_spec_marks_studio_implemented() -> None:
    text = CLI_SPEC.read_text(encoding="utf-8")
    assert "待实现" not in text.split("### 2.2")[1].split("### 2.3")[0]
    assert "**已实现**" in text
    assert "preview-toolbar.js" in text


def test_cli_spec_documents_studio_flags() -> None:
    text = CLI_SPEC.read_text(encoding="utf-8")
    for flag in ("--pick-folder-dialog", "--demo-album", "--allow-lan", "428"):
        assert flag in text


def test_cli_spec_documents_export_longshot() -> None:
    text = CLI_SPEC.read_text(encoding="utf-8")
    assert "### 3.13" in text
    assert "export-longshot" in text
    assert "20MB" in text


def test_cli_commands_registered() -> None:
    from travelogue.cli import app

    names = {cmd.name for cmd in app.registered_commands if cmd.name}
    for required in ("studio", "export-longshot", "serve", "quick"):
        assert required in names
