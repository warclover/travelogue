"""Deprecated shim · moved to media (M-B1)."""

import warnings

warnings.warn(
    "travelogue.curation.media_classify is deprecated; use travelogue.media.media_classify",
    DeprecationWarning,
    stacklevel=2,
)

from importlib import import_module

_mod = import_module("travelogue.media.media_classify")
for _name, _value in vars(_mod).items():
    if _name.startswith("__"):
        continue
    globals()[_name] = _value
del _mod, _name, _value
