"""Shim → layout_engine.intent_hints."""

from __future__ import annotations

import importlib

_mod = importlib.import_module("travelogue.layout_engine.intent_hints")
for _name in dir(_mod):
    if _name.startswith("_"):
        continue
    globals()[_name] = getattr(_mod, _name)
