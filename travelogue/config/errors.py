"""Configuration loading errors (M-A2 fail-loud).

``ConfigError`` lives in ``travelogue.errors`` so layer-0 packages
(``layout_contract``) can raise it without importing ``travelogue.config``.
"""

from __future__ import annotations

from travelogue.errors import ConfigError

__all__ = ["ConfigError"]
