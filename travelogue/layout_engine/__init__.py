"""Layout Strategy Engine (LSE) · Phase 17.

Public surface: ``travelogue.layout_engine.api`` (also re-exported here).
Internal packages ``planner`` / ``mosaic`` are not a stable cross-package API.
"""

from __future__ import annotations

from travelogue.layout_engine import api as _api
from travelogue.layout_engine.api import *  # noqa: F403

__all__ = list(_api.__all__)
