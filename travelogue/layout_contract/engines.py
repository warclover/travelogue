"""Layout engine id constants (layout kernel · AAD-11)."""

from __future__ import annotations

from typing import Literal

LayoutEngine = Literal["legacy", "screens"]

LAYOUT_ENGINE_LEGACY: LayoutEngine = "legacy"
LAYOUT_ENGINE_SCREENS: LayoutEngine = "screens"
LAYOUT_ENGINE_VERSION_SCREENS = "screens-2"
