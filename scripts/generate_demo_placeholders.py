#!/usr/bin/env python3
"""生成 demo-showcase dev 占位 WebP（1×1 · 合法 RIFF/WEBP）。

仅用于 loopback / CI：消除 manifest 引用 404；dogfood 仍待设计切图包（DEMO-ASSETS-BRIEF）。
"""
from __future__ import annotations

import json
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
ASSET_ROOT = REPO / "templates" / "studio" / "assets" / "demo-showcase"
MANIFEST = ASSET_ROOT / "manifest.json"

# 最小合法 lossy WebP（1×1 px）
MINIMAL_WEBP = (
    b"RIFF$\x00\x00\x00WEBPVP8 \x18\x00\x00\x00"
    b"\x30\x01\x00\x9d\x01*\x01\x00\x01\x00\x02\x00"
    b"\x34\x25\xa4\x00\x03\x70\x00\xfe\xfb\xfd\x50\x00"
)


def _collect_paths(manifest: dict) -> set[str]:
    paths: set[str] = set()
    assets = manifest.get("assets") or {}
    for key in ("background", "longshot"):
        rel = assets.get(key)
        if rel:
            paths.add(str(rel).replace("\\", "/"))
    for page in manifest.get("pages") or []:
        rel = page.get("webp")
        if rel:
            paths.add(str(rel).replace("\\", "/"))
    return paths


def main() -> None:
    data = json.loads(MANIFEST.read_text(encoding="utf-8"))
    rel_paths = sorted(_collect_paths(data))
    if not rel_paths:
        raise SystemExit("manifest 未声明任何 webp 路径")

    written = 0
    for rel in rel_paths:
        dest = ASSET_ROOT / rel
        dest.parent.mkdir(parents=True, exist_ok=True)
        if dest.exists() and dest.read_bytes() == MINIMAL_WEBP:
            continue
        dest.write_bytes(MINIMAL_WEBP)
        written += 1
        print(f"wrote {dest.relative_to(REPO)}")

    print(f"done · {len(rel_paths)} paths · {written} updated")


if __name__ == "__main__":
    main()
