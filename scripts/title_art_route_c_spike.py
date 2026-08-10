"""Route C W0.5 完整 Spike (PRD-COVER-CALLIGRAPHY-TITLE-V1 · AC-CAL-11 · OQ-CAL-06/07)。

用 20~30 条真实/边界标题系统性验证通义万相字形准确率/成本/延迟/审核拒绝率，
补齐此前仅现场实测 2 组标题的 W0.5-lite（见 PRD v0.4.0 变更记录），是
`AC-CAL-11`（路线 C OCR 回读通过率钉定阈值）与 `route_c_enabled` 默认开启
评估的前置条件。

标题样本覆盖（§5.5.1 五款风格轮转分配）：
  - 极短/极长（1 字 ~ 合同上限 8 字，`contract.MAX_MAIN_CHARS`）
  - 生僻字地名（本 app 是游记工具，地名生僻字是真实高频边界场景，非人造压力测试）
  - 多音字地名（测字形是否正确，不测发音）
  - 数字/英文混排、标点、叠字、古诗词句

用法（需先 ``$env:DASHSCOPE_API_KEY = "..."``；同一个 key 同时用于文生图
提交和 OCR 回读校验，见 ``travelogue.llm.client.resolve_llm_runtime``）：

    python scripts/title_art_route_c_spike.py
    python scripts/title_art_route_c_spike.py --limit 5          # 冒烟，先跑 5 条
    python scripts/title_art_route_c_spike.py --model wanx2.1-t2i-turbo
    python scripts/title_art_route_c_spike.py --dry-run          # 不调用任何 API，只打印样本表

结果落盘：
  - 逐条生成图 PNG → docs/acceptance-records/attachments/
    cover-calligraphy-title-v1-route-c-w05-spike-<date>/
  - 汇总 JSON/Markdown → docs/acceptance-records/
    cover-calligraphy-title-v1-route-c-w05-spike-<date>.json / .md
"""

from __future__ import annotations

import argparse
import base64
import io
import json
import sys
import time
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

# Windows PowerShell 默认控制台代码页是 GBK，print() 遇到 ✓/✗ 等符号会直接
# UnicodeEncodeError 崩掉整个 spike——落盘文件已用显式 utf-8 encoding 不受影响，
# 这里只是让终端进度输出不再因为控制台代码页而中断脚本本身。
try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")  # type: ignore[union-attr]
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")  # type: ignore[union-attr]
except (AttributeError, ValueError):
    pass

# fmt: off
#: (title, category) —— 每条 ≤ MAX_MAIN_CHARS（8），跟真实路线 C 入口
#: （engine.py 用 contract.resolve_title_text 截断后的文本）保持同一约束，
#: 不测"故意超长直接喂给 route_c"这种线上不会出现的路径。
TITLE_SAMPLES: tuple[tuple[str, str], ...] = (
    ("拾光", "baseline_control"),           # 已现场实测过（v0.4.0），作对照
    ("光", "extreme_short_1char"),
    ("甪直古镇", "rare_char_place"),          # 甪 rare radical
    ("涠洲岛落日", "rare_char_place"),         # 涠
    ("婺源篁岭", "rare_char_place"),          # 婺 高笔画数
    ("黟县宏村", "rare_char_place"),          # 黟
    ("龟兹寻踪", "rare_char_place"),          # 龟兹组合词
    ("阆中古城", "rare_char_place"),          # 阆
    ("措浪日记", "rare_char_place"),          # 措（藏地地名常用字）
    ("硇洲岛", "rare_char_place"),           # 硇 极罕见
    ("邺城旧梦", "rare_char_place"),          # 邺
    ("麤犇靐齉爩", "extreme_rare_stress"),     # 5 连超罕见字，字形准确率下限探测
    ("厦门老城区", "polyphone_place"),         # 厦：xià 非常见 shà 音，测字形非发音
    ("重庆火锅魂", "polyphone_place"),         # 重：chóng 非 zhòng
    ("重走318国道", "digits_mixed"),           # 8 字整，数字+常见词
    ("西藏骑行Vlog", "latin_mixed"),           # 中英混排，8 字整
    ("三亚Vlog", "latin_mixed"),
    ("海边·日落", "punctuation"),             # 中文间隔号
    ("一路向西…", "punctuation"),             # 省略号
    ("稻城亚丁行", "common_scenic"),           # 热门地名，非边界，做基线对照
    ("阿勒泰散记", "common_scenic"),
    ("918公里", "digits_mixed"),             # 纯数字+单位
    ("秋去秋又来", "repeated_char"),           # 叠字"秋"
    ("一茶一饭间", "repeated_char"),           # 叠字"一"
    ("雾锁南迦巴瓦", "long_boundary_8char"),    # 8 字整，含生僻地名"迦"
    ("苔痕上阶绿", "poetic_phrase"),           # 古诗词句，草书意境测试
)
# fmt: on


@dataclass
class SpikeResult:
    index: int
    title: str
    category: str
    style_id: str
    model: str
    ok: bool
    failure_reason: str | None
    failure_detail: str | None
    latency_ms: int | None
    ocr_matched: bool | None
    ocr_recognized: str | None
    image_path: str | None


def _ocr_read(img: Any, expected: str) -> tuple[bool, str]:
    """跟 ``ocr_verify.ocr_verify`` 同一套 prompt，但额外把 ``recognized`` 文本
    带出来供人审——Spike 想知道"哪个字错了"，不只是"过没过"这个布尔值。
    """
    from travelogue.llm.client import parse_json_content, vision_chat_completion

    buf = io.BytesIO()
    img.convert("RGB").save(buf, format="JPEG", quality=90)
    data_url = f"data:image/jpeg;base64,{base64.b64encode(buf.getvalue()).decode('ascii')}"
    expected_norm = "".join(expected.split())
    messages = [
        {
            "role": "system",
            "content": (
                "你是严格的书法文字校验器。只输出 JSON，格式："
                '{"recognized": "画面中识别到的汉字（按从上到下、从左到右顺序，'
                '不含印章/水印/其他装饰文字）", "match": true 或 false}。'
                "match 表示 recognized 是否与用户给出的期望文字完全一致（不含空白）。"
            ),
        },
        {
            "role": "user",
            "content": [
                {"type": "text", "text": f"期望文字：{expected_norm}"},
                {"type": "image_url", "image_url": {"url": data_url}},
            ],
        },
    ]
    content = vision_chat_completion(
        messages, provider="dashscope", model="qwen-vl-plus", temperature=0.0
    )
    data = parse_json_content(content)
    recognized = "".join(str(data.get("recognized") or "").split())
    matched = bool(data.get("match")) and recognized == expected_norm
    return matched, recognized


def run_spike(
    *, model: str | None, limit: int | None, out_dir: Path, dry_run: bool
) -> list[SpikeResult]:
    from travelogue.cover_engine.title_art.route_c import RouteCFailure
    from travelogue.cover_engine.title_art.route_c import generate_raw as route_c_generate_raw
    from travelogue.cover_engine.title_art.style_registry import list_styles

    styles = list_styles()
    samples = TITLE_SAMPLES[:limit] if limit else TITLE_SAMPLES
    results: list[SpikeResult] = []
    out_dir.mkdir(parents=True, exist_ok=True)

    for i, (title, category) in enumerate(samples):
        style = styles[i % len(styles)]
        print(f"[{i + 1}/{len(samples)}] {title!r} ({category}) · style={style.style_id} ...", flush=True)
        if dry_run:
            results.append(
                SpikeResult(
                    index=i, title=title, category=category, style_id=style.style_id,
                    model=model or "(default)", ok=True, failure_reason=None,
                    failure_detail=None, latency_ms=None, ocr_matched=None,
                    ocr_recognized=None, image_path=None,
                )
            )
            continue

        t0 = time.monotonic()
        try:
            raw = route_c_generate_raw(style.style_id, title=title, model=model)
        except RouteCFailure as exc:
            latency_ms = int((time.monotonic() - t0) * 1000)
            print(f"  ✗ FAILED {exc.reason}: {exc.detail}")
            results.append(
                SpikeResult(
                    index=i, title=title, category=category, style_id=style.style_id,
                    model=model or "(default)", ok=False, failure_reason=exc.reason,
                    failure_detail=exc.detail, latency_ms=latency_ms, ocr_matched=None,
                    ocr_recognized=None, image_path=None,
                )
            )
            continue
        latency_ms = int((time.monotonic() - t0) * 1000)

        image_path = out_dir / f"{i:02d}-{style.style_id}-{category}.png"
        raw.image.save(image_path)

        try:
            matched, recognized = _ocr_read(raw.image, title)
        except Exception as exc:  # noqa: BLE001 — Spike 想看到失败原因，不吞异常
            print(f"  ⚠ OCR call itself failed: {exc}")
            matched, recognized = False, f"(OCR调用异常: {exc})"

        status = "✓" if matched else "✗"
        print(f"  {status} ocr_matched={matched} recognized={recognized!r} latency={latency_ms}ms")
        results.append(
            SpikeResult(
                index=i, title=title, category=category, style_id=style.style_id,
                model=raw.model, ok=True, failure_reason=None, failure_detail=None,
                latency_ms=latency_ms, ocr_matched=matched, ocr_recognized=recognized,
                image_path=str(image_path.relative_to(ROOT)),
            )
        )
    return results


def summarize(results: list[SpikeResult]) -> dict[str, Any]:
    total = len(results)
    generated_ok = [r for r in results if r.ok]
    ocr_checked = [r for r in generated_ok if r.ocr_matched is not None]
    ocr_passed = [r for r in ocr_checked if r.ocr_matched]
    latencies = [r.latency_ms for r in generated_ok if r.latency_ms is not None]
    failure_reasons: dict[str, int] = {}
    for r in results:
        if not r.ok and r.failure_reason:
            failure_reasons[r.failure_reason] = failure_reasons.get(r.failure_reason, 0) + 1
    by_category: dict[str, dict[str, int]] = {}
    for r in results:
        cat = by_category.setdefault(r.category, {"total": 0, "ocr_pass": 0})
        cat["total"] += 1
        if r.ocr_matched:
            cat["ocr_pass"] += 1

    return {
        "total_samples": total,
        "generation_success": len(generated_ok),
        "generation_success_rate": round(len(generated_ok) / total, 4) if total else None,
        "ocr_pass_rate_of_generated": (
            round(len(ocr_passed) / len(ocr_checked), 4) if ocr_checked else None
        ),
        "failure_reasons": failure_reasons,
        "latency_ms": {
            "avg": round(sum(latencies) / len(latencies), 1) if latencies else None,
            "min": min(latencies) if latencies else None,
            "max": max(latencies) if latencies else None,
            "p95": (
                sorted(latencies)[int(len(latencies) * 0.95) - 1] if len(latencies) >= 2 else None
            ),
        },
        "by_category": by_category,
        # 成本：DashScope 未在 image-synthesis 响应体里直接返回计费金额；
        # 需要人工核对阿里云百炼控制台账单/单价页（wanx2.1-t2i-plus 按张计费），
        # 此处只留生成成功张数，方便对着账单算总价——不在脚本里硬编码单价
        # 数字，避免过时后误导（供应商可能调价）。
        "note_on_cost": (
            "DashScope 响应不含计费字段；请用 generation_success 张数对照阿里云"
            "百炼控制台『用量/账单』页面核算实际总价，再除以张数得单价。"
        ),
    }


def write_report(results: list[SpikeResult], summary: dict[str, Any], *, report_path: Path) -> None:
    payload = {
        "generatedAt": datetime.now(UTC).replace(microsecond=0).isoformat(),
        "summary": summary,
        "results": [asdict(r) for r in results],
    }
    report_path.with_suffix(".json").write_text(
        json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8"
    )

    lines = [
        "# Route C W0.5 完整 Spike 结果",
        "",
        f"生成时间：{payload['generatedAt']}",
        "",
        "## 汇总",
        "",
        "| 指标 | 数值 |",
        "|------|------|",
        f"| 样本总数 | {summary['total_samples']} |",
        f"| 生成成功数 | {summary['generation_success']} |",
        f"| 生成成功率 | {summary['generation_success_rate']} |",
        f"| OCR 回读通过率（生成成功中） | {summary['ocr_pass_rate_of_generated']} |",
        f"| 失败原因分布 | {summary['failure_reasons']} |",
        f"| 延迟 avg/min/max/p95 (ms) | {summary['latency_ms']} |",
        "",
        "## 分类别通过率",
        "",
        "| 类别 | 总数 | OCR 通过 |",
        "|------|------|----------|",
    ]
    for cat, stat in summary["by_category"].items():
        lines.append(f"| {cat} | {stat['total']} | {stat['ocr_pass']} |")
    lines += [
        "",
        "## 逐条明细",
        "",
        "| # | 标题 | 类别 | 风格 | 生成 | OCR匹配 | OCR识别文本 | 延迟(ms) | 失败原因 | 图片 |",
        "|---|------|------|------|------|---------|--------------|----------|----------|------|",
    ]
    for r in results:
        lines.append(
            f"| {r.index} | {r.title} | {r.category} | {r.style_id} | "
            f"{'✓' if r.ok else '✗'} | {r.ocr_matched} | {r.ocr_recognized or ''} | "
            f"{r.latency_ms or ''} | {r.failure_reason or ''} | {r.image_path or ''} |"
        )
    lines.append("")
    lines.append(f"> {summary['note_on_cost']}")
    report_path.with_suffix(".md").write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--model", default=None, help="覆盖默认模型（wanx2.1-t2i-plus）")
    parser.add_argument("--limit", type=int, default=None, help="只跑前 N 条（冒烟用）")
    parser.add_argument(
        "--dry-run", action="store_true", help="不调用任何 API，只打印/落盘样本分配表"
    )
    args = parser.parse_args()

    date_tag = datetime.now(UTC).strftime("%Y-%m-%d")
    out_dir = ROOT / "docs" / "acceptance-records" / "attachments" / (
        f"cover-calligraphy-title-v1-route-c-w05-spike-{date_tag}"
    )
    report_path = ROOT / "docs" / "acceptance-records" / (
        f"cover-calligraphy-title-v1-route-c-w05-spike-{date_tag}"
    )

    if not args.dry_run:
        import os

        if not os.environ.get("DASHSCOPE_API_KEY", "").strip():
            print(
                "ERROR: 未设置 DASHSCOPE_API_KEY 环境变量（同时用于文生图提交与 OCR "
                "回读校验）。先执行 $env:DASHSCOPE_API_KEY = '你的key'，或加 --dry-run "
                "先看样本分配表。",
                file=sys.stderr,
            )
            raise SystemExit(1)

    results = run_spike(model=args.model, limit=args.limit, out_dir=out_dir, dry_run=args.dry_run)
    summary = summarize(results)
    write_report(results, summary, report_path=report_path)
    print()
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    print(f"\n报告已写入 {report_path.with_suffix('.md')} / .json")


if __name__ == "__main__":
    main()
