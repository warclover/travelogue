"""Configuration loading errors (M-A2 fail-loud)."""

from __future__ import annotations


class ConfigError(ValueError):
    """Invalid or ambiguous config.yaml content."""
