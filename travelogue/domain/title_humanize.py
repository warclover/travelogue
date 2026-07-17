"""Share-Ready W2 · default trip title from folder names (D-SR-14 / BE-SR-05)."""

from __future__ import annotations

import re

_DEFAULT_TITLE = "我的旅途"
_HASH_OR_TEST_SUFFIX = re.compile(
    r"[-_]?(?:[0-9a-f]{8,}|(?:ux-)?handtest[-_\w]*|demo[-_]?\d+|copy(?:\s*\(\d+\))?)$",
    re.IGNORECASE,
)
_NOISE_PREFIX = re.compile(r"^(新建文件夹|untitled|copy)\s*", re.IGNORECASE)
_HEXISH = re.compile(r"^[0-9a-f-]{8,}$", re.IGNORECASE)


def humanize_folder_title(raw: str | None, *, limit: int = 20) -> str:
    """Clean folder/upload basename into a readable default magazine title.

    Does not decide overwrite policy — callers must skip when the user already edited.
    """
    name = (raw or "").strip()
    if not name:
        return _DEFAULT_TITLE
    name = re.sub(r"\.[^.]+$", "", name)
    name = _HASH_OR_TEST_SUFFIX.sub("", name)
    name = re.sub(r"[_\-.]+", " ", name)
    name = re.sub(r"\s+", " ", name).strip()
    name = _NOISE_PREFIX.sub("", name).strip()
    if not name or _HEXISH.match(name):
        return _DEFAULT_TITLE
    if len(name) > limit:
        return name[:limit]
    return name
