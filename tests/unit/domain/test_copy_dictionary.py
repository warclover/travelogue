"""COPY-DICTIONARY-V1 · frozen terms stay aligned across Python / JS / doc."""

from __future__ import annotations

from travelogue.domain.copy_dictionary import (
    ACTION,
    FORBIDDEN_ACTION_ALIAS,
    FORBIDDEN_POSITION_COPY,
    FORBIDDEN_UMBRELLA,
    HELP_SEARCH_ALIASES,
    INTENTS,
    JOURNAL_EXPORT_ARIA,
    JOURNAL_EXPORT_LABEL,
    PORTFOLIO_EXPORT_LABEL,
    PRODUCTS,
    SHELF_READY,
    SHELF_STALE,
    SUCCESS_VERB,
    SWITCH_PURPOSE,
    SWITCH_PURPOSE_DONE,
    VERTICAL_SLICE_SURFACES,
    export_aria,
    export_label,
    success_line,
)
from travelogue.paths import ROOT


def test_dictionary_forbids_umbrella_and_channel_as_action() -> None:
    assert ACTION == "导出"
    assert "分享图" in FORBIDDEN_UMBRELLA
    assert "发微信群" in FORBIDDEN_ACTION_ALIAS
    assert "验货" in FORBIDDEN_POSITION_COPY
    assert "长图" in PRODUCTS
    assert "日常分享" in INTENTS
    assert SHELF_READY == "长图已就绪"
    assert SHELF_STALE == "长图需更新"
    assert SWITCH_PURPOSE == "换用途"
    assert SWITCH_PURPOSE_DONE == "已换用途"


def test_export_labels_stay_identity_specific() -> None:
    assert export_label("journal") == JOURNAL_EXPORT_LABEL == "长图"
    assert export_aria("journal") == JOURNAL_EXPORT_ARIA == "导出长图"
    assert export_label("portfolio") == PORTFOLIO_EXPORT_LABEL == "导出作品集"
    assert export_aria("portfolio") == "导出作品集"


def test_success_line_names_the_product() -> None:
    assert success_line(count=5, purpose="朋友圈", product="长图") == "已导出 5 张朋友圈长图"
    assert success_line(count=3, purpose="", product="卡片") == "已导出 3 张卡片"


def test_js_dictionary_mirrors_python() -> None:
    text = (ROOT / "templates/studio/js/copy-dictionary.js").read_text(encoding="utf-8")
    assert f'action: "{ACTION}"' in text
    assert f'journalExportLabel: "{JOURNAL_EXPORT_LABEL}"' in text
    assert f'portfolioExportLabel: "{PORTFOLIO_EXPORT_LABEL}"' in text
    assert f'successVerb: "{SUCCESS_VERB}"' in text
    assert f'switchPurpose: "{SWITCH_PURPOSE}"' in text
    assert f'switchPurposeDone: "{SWITCH_PURPOSE_DONE}"' in text
    assert f'shelfReady: "{SHELF_READY}"' in text
    assert f'shelfStale: "{SHELF_STALE}"' in text
    for word in FORBIDDEN_UMBRELLA + FORBIDDEN_ACTION_ALIAS + FORBIDDEN_POSITION_COPY:
        assert word in text
    for alias in HELP_SEARCH_ALIASES:
        assert alias in text


def test_doc_and_vertical_slice_surfaces_exist() -> None:
    doc = (ROOT / "docs/COPY-DICTIONARY-V1.md").read_text(encoding="utf-8")
    assert "DOC-STATUS" in doc
    assert "分享图" in doc
    assert JOURNAL_EXPORT_LABEL in doc
    assert SHELF_READY in doc
    assert SHELF_STALE in doc
    assert SWITCH_PURPOSE in doc
    for rel in VERTICAL_SLICE_SURFACES:
        assert (ROOT / rel).is_file()
        assert rel in doc


def test_success_secondary_does_not_hardcode_old_share_phrase() -> None:
    surfaces = (
        "templates/studio/preview-toolbar/longshot.js",
        "templates/studio/preview-toolbar-v3-task-dock.js",
        "templates/studio/homepage-v2/shelf-longshot.js",
    )
    for rel in surfaces:
        text = (ROOT / rel).read_text(encoding="utf-8")
        assert "换种分享方式" not in text
        assert "COPY_DICTIONARY.switchPurpose" in text
