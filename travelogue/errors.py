"""Shared application error types with stable ``code`` fields."""

from __future__ import annotations


class CodeError(Exception):
    """Base error: ``str(exc)`` is ``"{code}: {message}"``."""

    def __init__(self, code: str, message: str) -> None:
        self.code = code
        self.message = message
        super().__init__(f"{code}: {message}")


class PlainCodeError(CodeError):
    """Legacy errors where ``str(exc)`` must equal ``message`` (no code prefix)."""

    def __init__(self, message: str, *, code: str) -> None:
        self.code = code
        self.message = message
        Exception.__init__(self, message)


class ConfigError(ValueError):
    """Invalid or ambiguous config.yaml / intent content (layer-0 safe)."""
