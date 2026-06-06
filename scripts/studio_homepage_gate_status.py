#!/usr/bin/env python3
"""M20-j · 打印当前 Studio 首页门控决策（不启动服务器）。

用法：
    TRAVELOGUE_STUDIO_HOMEPAGE_V2=auto TRAVELOGUE_STUDIO_HOMEPAGE_V2_PERCENT=10 \\
        python scripts/studio_homepage_gate_status.py

    python scripts/studio_homepage_gate_status.py --ua "M20jTest/5"

    python scripts/studio_homepage_gate_status.py --config config.yaml --ua "M20jTest/5" --json
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

from travelogue.web.studio_homepage_gate import (
    decide_root_variant,
    resolve_mode,
    resolve_percent,
    should_redirect_root_to_v2,
    stable_bucket,
)


def _load_config_dict(path: Path) -> dict | None:
    import yaml

    if not path.is_file():
        return None
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    return data if isinstance(data, dict) else None


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Studio 首页 v2 门控状态")
    parser.add_argument("--ua", default="Mozilla/5.0", help="模拟 User-Agent")
    parser.add_argument("--bucket", type=int, default=None, help="覆盖分桶 0–99")
    parser.add_argument(
        "--config",
        type=Path,
        default=None,
        help="config.yaml 路径（读 studio.homepage.v2_bento.percent）",
    )
    parser.add_argument("--json", action="store_true", help="JSON 输出")
    args = parser.parse_args(argv)

    mode = resolve_mode()
    config_dict = _load_config_dict(args.config) if args.config else None
    percent = resolve_percent(config_dict)
    bucket = args.bucket if args.bucket is not None else stable_bucket(args.ua)
    variant = decide_root_variant(mode=mode, percent=percent, bucket=bucket)
    redirect = should_redirect_root_to_v2(mode=mode, variant=variant)

    payload = {
        "env_mode": os.environ.get("TRAVELOGUE_STUDIO_HOMEPAGE_V2", "off"),
        "env_percent": os.environ.get("TRAVELOGUE_STUDIO_HOMEPAGE_V2_PERCENT"),
        "config_path": str(args.config.resolve()) if args.config else None,
        "mode": mode,
        "percent": percent,
        "user_agent": args.ua,
        "bucket": bucket,
        "root_variant": variant,
        "redirect_root_to_v2": redirect,
        "root_behavior": f"200 serve {variant} at /",
        "v2_compat_path": "GET /v2 → 302 /",
        "classic_path": "GET /classic → legacy-freeze classic (deprecated)",
    }

    if args.json:
        print(json.dumps(payload, ensure_ascii=False, indent=2))
    else:
        print("=== Studio 首页 v2 门控（M21）===")
        for key, val in payload.items():
            print(f"  {key}: {val}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
