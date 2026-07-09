"""Deprecated shim · moved to layout_engine (M-B4b)."""

import warnings

warnings.warn(
    "travelogue.curation.mosaic.render_check is deprecated; use travelogue.layout_engine.mosaic.render_check",
    DeprecationWarning,
    stacklevel=2,
)

from importlib import import_module

_mod = import_module('travelogue.layout_engine.mosaic.render_check')
for _name, _value in vars(_mod).items():
    if _name.startswith('__'):
        continue
    globals()[_name] = _value
del _mod, _name, _value
