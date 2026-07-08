"""YAML loader with duplicate-key detection."""

from __future__ import annotations

from typing import Any

from travelogue.config._common import yaml
from travelogue.config.errors import ConfigError

if yaml is not None:

    class _UniqueKeyLoader(yaml.SafeLoader):
        """SafeLoader that rejects duplicate mapping keys."""

    def _construct_mapping(loader: yaml.SafeLoader, node: yaml.MappingNode, deep: bool = False) -> dict[Any, Any]:
        mapping: dict[Any, Any] = {}
        for key_node, value_node in node.value:
            key = loader.construct_object(key_node)
            if key in mapping:
                line = key_node.start_mark.line + 1
                raise ConfigError(
                    f"duplicate config key {key!r} at line {line}; "
                    f"remove the earlier or later definition in config.yaml"
                )
            value = loader.construct_object(value_node, deep=deep)
            mapping[key] = value
        return mapping

    _UniqueKeyLoader.add_constructor(
        yaml.resolver.BaseResolver.DEFAULT_MAPPING_TAG,
        _construct_mapping,
    )


def load_yaml_mapping(text: str, *, source: str = "config") -> dict[str, Any]:
    """Parse YAML text; raise ConfigError on duplicate keys."""
    if yaml is None:
        raise RuntimeError("PyYAML required to load config")
    loaded = yaml.load(text, Loader=_UniqueKeyLoader)
    if loaded is None:
        return {}
    if not isinstance(loaded, dict):
        raise ConfigError(f"{source} must be a YAML mapping at the top level")
    return loaded
