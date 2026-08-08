"""CSC W1 · studio_config_expose declares Happy Path recipe contract."""

from __future__ import annotations

from travelogue.config import AppConfig, studio_config_expose
from travelogue.orchestrator.happy_path_recipe import (
    ADVANCED_SETTINGS_KEYS,
    L0_OPS_ROOTS,
    L1_RESULT_KEYS,
    RECIPE_ID_STUDIO_DEFAULT,
)


def test_studio_config_expose_includes_happy_path_recipe() -> None:
    exposed = studio_config_expose(AppConfig())
    hp = exposed["happyPath"]
    assert hp["recipeId"] == RECIPE_ID_STUDIO_DEFAULT
    assert hp["l1Keys"] == list(L1_RESULT_KEYS)
    assert hp["advancedSettingsKeys"] == list(ADVANCED_SETTINGS_KEYS)
    assert hp["l0OpsRoots"] == list(L0_OPS_ROOTS)


def test_studio_config_expose_keeps_legacy_settings_fields() -> None:
    """W1 is additive: Advanced.js still reads g1 / scoring / clustering."""
    exposed = studio_config_expose(AppConfig())
    assert "enabled" in exposed["clustering"]
    assert "enabled" in exposed["vision"]
    assert "g1ConfirmStructure" in exposed["studio"]
    assert "enabled" in exposed["layout"]["scoring"]
    assert "copySourceFiles" in exposed["ingest"]


def test_studio_config_expose_title_art_gate() -> None:
    """Front-end needs this to decide whether to show the title-art button /
    the Route C checkbox (Studio 高级面板触发入口 · OQ-CAL-06)."""
    exposed = studio_config_expose(AppConfig())
    assert exposed["titleArt"] == {"enabled": False, "routeCEnabled": True}
