"""LLM error codes."""

from __future__ import annotations


class LlmError(Exception):
    def __init__(self, code: str, message: str) -> None:
        self.code = code
        super().__init__(f"{code}: {message}")
