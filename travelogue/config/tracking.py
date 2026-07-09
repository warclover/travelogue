"""Track config key consumption for unknown-key warnings."""

from __future__ import annotations

from typing import Any

# Top-level sections documented as planning-only (not wired to runtime yet).
_ALLOW_EXTRA_TOP_LEVEL = frozenset({"ffmpeg", "preview", "phase6", "template_admin"})


def wrap_tracked(data: dict[str, Any], *, path: str = "", allow_extra: bool = False) -> TrackedDict:
    node = TrackedDict({}, path=path, allow_extra=allow_extra)
    for key, val in data.items():
        child_path = f"{path}.{key}" if path else str(key)
        child_allow_extra = allow_extra or key in _ALLOW_EXTRA_TOP_LEVEL
        if isinstance(val, dict):
            node[key] = wrap_tracked(val, path=child_path, allow_extra=child_allow_extra)
        else:
            node[key] = val
    return node


class TrackedDict(dict):
    """Dict wrapper that records which keys were read during parsing."""

    __slots__ = ("_path", "_allow_extra", "_accessed")

    def __init__(
        self,
        *args: Any,
        path: str = "",
        allow_extra: bool = False,
        **kwargs: Any,
    ) -> None:
        super().__init__(*args, **kwargs)
        self._path = path
        self._allow_extra = allow_extra
        self._accessed: set[str] = set()

    @property
    def allow_extra(self) -> bool:
        return self._allow_extra

    def mark_keys(self, *keys: str) -> None:
        for key in keys:
            if key:
                self._accessed.add(str(key))

    def _touch(self, key: object) -> None:
        if isinstance(key, str):
            self._accessed.add(key)

    def get(self, key: str, default: Any = None) -> Any:  # type: ignore[override]
        self._touch(key)
        return super().get(key, default)

    def __getitem__(self, key: str) -> Any:  # type: ignore[override]
        self._touch(key)
        return super().__getitem__(key)

    def __contains__(self, key: object) -> bool:  # type: ignore[override]
        if isinstance(key, str):
            self._touch(key)
        return super().__contains__(key)


def collect_unknown_keys(root: TrackedDict) -> list[str]:
    unknown: list[str] = []

    def walk(node: TrackedDict, prefix: str) -> None:
        if node.allow_extra:
            return
        for key, val in node.items():
            if key not in node._accessed:
                unknown.append(f"{prefix}.{key}" if prefix else str(key))
            if isinstance(val, TrackedDict):
                child_prefix = f"{prefix}.{key}" if prefix else str(key)
                walk(val, child_prefix)

    walk(root, "")
    return sorted(unknown)
