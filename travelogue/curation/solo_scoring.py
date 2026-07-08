"""Shim → layout_engine.scoring.solo."""

from __future__ import annotations

import importlib

_mod = importlib.import_module("travelogue.layout_engine.scoring.solo")
for _name in dir(_mod):
    if _name.startswith("_"):
        continue
    globals()[_name] = getattr(_mod, _name)
