"""Local .env loading."""

from __future__ import annotations

import os

from travelogue.env import _parse_env_line, load_dotenv_files


def test_parse_env_line():
    assert _parse_env_line('DEEPSEEK_API_KEY=sk-abc') == ("DEEPSEEK_API_KEY", "sk-abc")
    assert _parse_env_line('export FOO="bar"') == ("FOO", "bar")
    assert _parse_env_line("# comment") is None


def test_load_dotenv_files(tmp_path, monkeypatch):
    import travelogue.env as env_mod

    env_mod._ENV_LOADED = False
    env_file = tmp_path / ".env"
    env_file.write_text("DEEPSEEK_API_KEY=from-dotenv\n", encoding="utf-8")
    monkeypatch.delenv("DEEPSEEK_API_KEY", raising=False)
    monkeypatch.setattr(env_mod, "ROOT", tmp_path)
    monkeypatch.chdir(tmp_path)
    loaded = load_dotenv_files()
    assert loaded
    assert os.environ.get("DEEPSEEK_API_KEY") == "from-dotenv"
