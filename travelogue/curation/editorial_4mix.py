"""Shim → layout_engine.editorial.four_mix."""

from __future__ import annotations

import importlib

_mod = importlib.import_module("travelogue.layout_engine.editorial.four_mix")
for _name in dir(_mod):
    if _name.startswith("_"):
        continue
    globals()[_name] = getattr(_mod, _name)
