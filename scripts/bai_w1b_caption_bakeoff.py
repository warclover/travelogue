"""BAI W1b SHD-BAI-04: Pro vs old flash caption bake-off. Never prints keys."""

from __future__ import annotations

import json
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from travelogue.env import load_dotenv_files  # noqa: E402
from travelogue.llm.client import chat_completion, parse_json_content  # noqa: E402
from travelogue.llm.errors import LlmError  # noqa: E402
from travelogue.llm.user_settings import inject_secrets_into_environ, read_user_llm_secrets  # noqa: E402
from travelogue.services.llm_narrate import SYSTEM_PROMPT  # noqa: E402

OUT = ROOT / "docs" / "acceptance-records" / "attachments" / "bai-w1b-studio-dogfood-2026-08-13"
OUT.mkdir(parents=True, exist_ok=True)

BRIEFS = [
    {
        "id": "kiyomizu-rain",
        "place": "京都",
        "voiceExcerpt": "雨太大，先回酒店拿伞",
        "moment": "雨停后的清水寺石阶，地还湿着",
    },
    {
        "id": "seaside-kids",
        "place": "青岛",
        "voiceExcerpt": "别追那么深",
        "moment": "黄昏海边，孩子追浪又退回来",
    },
    {
        "id": "night-market",
        "place": "台北",
        "voiceExcerpt": "这摊要排到几点",
        "moment": "夜市摊位蒸汽和灯牌挤在一起",
    },
    {
        "id": "pass-wind",
        "place": "川西",
        "voiceExcerpt": "帽子差点飞了",
        "moment": "高山垭口风很大，经幡猎猎",
    },
]

MODELS = (
    ("qwen3.7-flash", False),
    ("deepseek-v4-pro", True),
)


def _user_prompt(brief: dict) -> str:
    payload = {
        "task": "fill media-card caption",
        "brief": {
            "place": brief["place"],
            "voiceExcerpt": brief["voiceExcerpt"],
            "moment": brief["moment"],
            "limits": {"captionMaxChars": 60},
            "fieldsRequested": ["caption"],
        },
        "outputSchema": {"items": [{"assetId": "a1", "caption": "string"}]},
    }
    return (
        "根据以下 brief 填写单张 media-card caption。\n\n"
        "brief:\n"
        + json.dumps(payload, ensure_ascii=False, indent=2)
        + "\n\n只返回 JSON，不要 markdown 代码块。"
    )


def main() -> int:
    load_dotenv_files()
    secrets = read_user_llm_secrets()
    inject_secrets_into_environ(secrets)
    rows: list[dict] = []
    for brief in BRIEFS:
        for model, thinking in MODELS:
            t0 = time.perf_counter()
            rec: dict = {
                "id": brief["id"],
                "model": model,
                "thinking": thinking,
                "ok": False,
            }
            try:
                raw = chat_completion(
                    [
                        {"role": "system", "content": SYSTEM_PROMPT},
                        {"role": "user", "content": _user_prompt(brief)},
                    ],
                    provider="dashscope",
                    model=model,
                    enable_thinking=thinking,
                    model_failover=False,
                )
                parsed = parse_json_content(raw)
                items = (parsed or {}).get("items") or []
                caption = ""
                if items and isinstance(items[0], dict):
                    caption = str(items[0].get("caption") or "").strip()
                rec["ok"] = bool(caption)
                rec["caption"] = caption
                rec["chars"] = len(caption)
                rec["json_ok"] = parsed is not None
            except LlmError as exc:
                rec["error"] = exc.code
                rec["json_ok"] = False
            rec["latency_ms"] = int((time.perf_counter() - t0) * 1000)
            rows.append(rec)
            print(json.dumps(rec, ensure_ascii=False), flush=True)
    out_path = OUT / "caption-bakeoff.json"
    out_path.write_text(json.dumps(rows, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"wrote {out_path.as_posix()}", flush=True)
    return 0 if all(r.get("ok") for r in rows) else 1


if __name__ == "__main__":
    raise SystemExit(main())
