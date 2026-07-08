"""Backward-compat shim for ``from tests.test_ingest import _album``."""

from __future__ import annotations

from tests.studio_test_helpers import make_test_album as _album

__all__ = ["_album"]
