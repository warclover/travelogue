"""Share-Face Integrity · works brand three-state (D-SFI-13 / FE-SFI-11)."""

from __future__ import annotations

from typing import Any, Literal

BrandMode = Literal["default", "custom", "hidden"]
DEFAULT_BRAND_LINE = "Travelogue"
BRAND_TEXT_MAX = 14


def normalize_works_brand_mode(raw: Any) -> BrandMode:
    mode = str(raw or "default").strip().lower()
    if mode in ("custom", "hidden", "default"):
        return mode  # type: ignore[return-value]
    return "default"


def resolve_works_brand(meta: dict | None) -> dict[str, Any]:
    """Return render flags for cover-closing + longshot footer (同源).

    - default →「Travelogue」
    - custom → 用户文案（≤14），取消 uppercase
    - hidden → 不渲染 brand；stats 行仍可保留
    """
    meta = meta if isinstance(meta, dict) else {}
    mode = normalize_works_brand_mode(meta.get("worksBrandMode"))
    text = str(meta.get("worksBrandText") or "").strip()[:BRAND_TEXT_MAX]
    if mode == "hidden":
        return {
            "worksBrandMode": "hidden",
            "showWorksBrand": False,
            "worksBrandLine": "",
            "worksBrandCustom": False,
        }
    if mode == "custom" and text:
        return {
            "worksBrandMode": "custom",
            "showWorksBrand": True,
            "worksBrandLine": text,
            "worksBrandCustom": True,
        }
    return {
        "worksBrandMode": "default",
        "showWorksBrand": True,
        "worksBrandLine": DEFAULT_BRAND_LINE,
        "worksBrandCustom": False,
    }
