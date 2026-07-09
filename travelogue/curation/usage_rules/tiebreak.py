"""Shim → layout_engine.usage_rules.tiebreak."""

from __future__ import annotations

import importlib

_mod = importlib.import_module("travelogue.layout_engine.usage_rules.tiebreak")
for _name in dir(_mod):
    if _name.startswith("_"):
        continue
    globals()[_name] = getattr(_mod, _name)
