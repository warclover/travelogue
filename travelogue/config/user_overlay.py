"""User-data config overlay (Desktop LLM Setup · config.user.yaml).

Kept in config layer so load_config does not import travelogue.llm.
"""

from __future__ import annotations

import logging
from typing import Any

_log = logging.getLogger(__name__)

_USER_CONFIG_NAME = "config.user.yaml"


def load_user_llm_config_overlay() -> dict[str, Any]:
    """Return mapping suitable for merging into load_config data."""
    from travelogue.paths import user_data_dir

    path = user_data_dir(ensure=False) / _USER_CONFIG_NAME
    if not path.is_file():
        return {}
    try:
        from travelogue.config.yaml_loader import load_yaml_mapping

        loaded = load_yaml_mapping(path.read_text(encoding="utf-8"), source=str(path))
    except Exception:
        _log.warning("user config overlay unreadable", exc_info=True)
        return {}
    return loaded if isinstance(loaded, dict) else {}
