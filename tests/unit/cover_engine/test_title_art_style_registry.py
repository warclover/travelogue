"""Unit tests · Calligraphy Style Registry (PRD §5.5.1 · D-CAL-14/15)."""

from __future__ import annotations

import pytest

from travelogue.cover_engine.title_art.style_registry import (
    STYLE_REGISTRY,
    default_style_id,
    get_style,
    list_styles,
    render_prompt,
)

pytestmark = pytest.mark.unit


def test_style_registry_has_exactly_five_initial_styles() -> None:
    # PRD 用户口径 (2)：最初设计 5 款提示词/风格，后期有需要再增加。
    assert len(STYLE_REGISTRY) == 5


def test_all_styles_have_unique_ids() -> None:
    ids = [s.style_id for s in STYLE_REGISTRY]
    assert len(ids) == len(set(ids))


def test_default_style_id_is_first_registry_entry() -> None:
    assert default_style_id() == STYLE_REGISTRY[0].style_id


def test_get_style_unknown_returns_none() -> None:
    assert get_style("does-not-exist") is None


def test_list_styles_returns_full_tuple() -> None:
    assert list_styles() == STYLE_REGISTRY


@pytest.mark.parametrize("style", STYLE_REGISTRY, ids=[s.style_id for s in STYLE_REGISTRY])
def test_render_prompt_substitutes_title_and_hides_placeholder(style) -> None:
    prompt = render_prompt(style, title="拾光")
    assert "拾光" in prompt
    assert "{{title}}" not in prompt
    assert "{{subtitle}}" not in prompt


@pytest.mark.parametrize("style", STYLE_REGISTRY, ids=[s.style_id for s in STYLE_REGISTRY])
def test_every_style_excludes_seal_and_border_via_negative_prompt(style) -> None:
    # D-CAL-12/D-CAL-17：Route C 只产出白底黑字原图，印章/边框由后处理统一叠加。
    assert "印章" in style.negative_prompt
    assert "边框" in style.negative_prompt


def test_render_prompt_only_replaces_known_placeholders_not_arbitrary_text() -> None:
    # D-CAL-15：运行时只允许替换 title/subtitle 占位符，模板主体本身不可被用户改写。
    style = get_style(default_style_id())
    assert style is not None
    prompt = render_prompt(style, title="A{{title}}B")
    assert prompt.count("A") >= 1 and prompt.count("B") >= 1
