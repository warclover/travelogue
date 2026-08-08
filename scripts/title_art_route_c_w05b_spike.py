"""Route C W0.5b 冲质量 Spike 矩阵（E1 重试 / E2 Prompt v2 / E3 风险桶）。

相对 W0.5（``title_art_route_c_spike.py`` 基线）本脚本额外报告：
  - first_pass：首次 OCR 通过率
  - after_retry：OCR 失败后再生成 1 次后的累计通过率（E1）
  - prompt_version=v1|v2 对照（E2；``--samples 2`` 同标题同风格各采 2 次）
  - 风险规则命中桶（E3）：标点/叠字若在生产会短路，此处仍可 ``--include-risk`` 强跑

用法（需 ``$env:DASHSCOPE_API_KEY``）：

    python scripts/title_art_route_c_w05b_spike.py --dry-run
    python scripts/title_art_route_c_w05b_spike.py --limit 5
    python scripts/title_art_route_c_w05b_spike.py --prompt-version v2 --retries 1
    python scripts/title_art_route_c_w05b_spike.py --prompt-version both --samples 2
"""

from __future__ import annotations

import argparse
import base64
import io
import json
import sys
import time
from dataclasses import asdict, dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")  # type: ignore[union-attr]
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")  # type: ignore[union-attr]
except (AttributeError, ValueError):
    pass

# 沿用 W0.5 样本 + 少量 GB2312 一级内易错对照
TITLE_SAMPLES: tuple[tuple[str, str], ...] = (
    ("拾光", "baseline_control"),
    ("光", "extreme_short_1char"),
    ("甪直古镇", "rare_char_place"),
    ("涠洲岛落日", "rare_char_place"),
    ("婺源篁岭", "rare_char_place"),
    ("黟县宏村", "rare_char_place"),
    ("龟兹寻踪", "rare_char_place"),
    ("阆中古城", "rare_char_place"),
    ("措浪日记", "rare_char_place"),
    ("硇洲岛", "rare_char_place"),
    ("邺城旧梦", "rare_char_place"),
    ("麤犇靐齉爩", "extreme_rare_stress"),
    ("厦门老城区", "polyphone_place"),
    ("重庆火锅魂", "polyphone_place"),
    ("重走318国道", "digits_mixed"),
    ("西藏骑行Vlog", "latin_mixed"),
    ("三亚Vlog", "latin_mixed"),
    ("海边·日落", "punctuation"),
    ("一路向西…", "punctuation"),
    ("稻城亚丁行", "common_scenic"),
    ("阿勒泰散记", "common_scenic"),
    ("918公里", "digits_mixed"),
    ("秋去秋又来", "repeated_char"),
    ("一茶一饭间", "repeated_char"),
    ("雾锁南迦巴瓦", "long_boundary_8char"),
    ("苔痕上阶绿", "poetic_phrase"),
    ("拾光记", "common_easy_extra"),
    ("山海间", "common_easy_extra"),
)


@dataclass
class AttemptRecord:
    attempt: int
    ok: bool
    latency_ms: int | None
    ocr_matched: bool | None
    ocr_recognized: str | None
    failure_reason: str | None
    image_path: str | None


@dataclass
class SpikeRow:
    index: int
    title: str
    category: str
    style_id: str
    model: str
    prompt_version: str
    sample_i: int
    risk_reason: str | None
    common_chars_ok: bool
    skipped_by_policy: bool
    first_pass: bool | None
    after_retry: bool | None
    attempts: list[AttemptRecord] = field(default_factory=list)


def _ocr_read(img: Any, expected: str) -> tuple[bool, str]:
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


def _one_generate(
    *,
    style_id: str,
    title: str,
    model: str | None,
    prompt_version: str,
    out_path: Path,
) -> AttemptRecord:
    from travelogue.cover_engine.title_art.route_c import RouteCFailure
    from travelogue.cover_engine.title_art.route_c import generate_raw as route_c_generate_raw

    t0 = time.monotonic()
    try:
        raw = route_c_generate_raw(
            style_id, title=title, model=model, prompt_version=prompt_version
        )
    except RouteCFailure as exc:
        return AttemptRecord(
            attempt=0,
            ok=False,
            latency_ms=int((time.monotonic() - t0) * 1000),
            ocr_matched=None,
            ocr_recognized=None,
            failure_reason=exc.reason,
            image_path=None,
        )
    latency_ms = int((time.monotonic() - t0) * 1000)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    raw.image.save(out_path)
    try:
        matched, recognized = _ocr_read(raw.image, title)
    except Exception as exc:  # noqa: BLE001
        matched, recognized = False, f"(OCR调用异常: {exc})"
    return AttemptRecord(
        attempt=0,
        ok=True,
        latency_ms=latency_ms,
        ocr_matched=matched,
        ocr_recognized=recognized,
        failure_reason=None if matched else "E_CAL_C_OCR_MISMATCH",
        image_path=str(out_path.relative_to(ROOT)),
    )


def run_matrix(
    *,
    model: str | None,
    limit: int | None,
    out_dir: Path,
    dry_run: bool,
    prompt_versions: tuple[str, ...],
    samples: int,
    retries: int,
    include_risk: bool,
) -> list[SpikeRow]:
    from travelogue.cover_engine.title_art.char_frequency import title_has_only_common_chars
    from travelogue.cover_engine.title_art.risk_rules import route_c_risk_reason
    from travelogue.cover_engine.title_art.style_registry import list_styles

    styles = list_styles(prompt_version="v1")
    sample_titles = TITLE_SAMPLES[:limit] if limit else TITLE_SAMPLES
    rows: list[SpikeRow] = []
    out_dir.mkdir(parents=True, exist_ok=True)
    max_attempts = 1 + max(0, retries)

    row_i = 0
    for title_i, (title, category) in enumerate(sample_titles):
        style = styles[title_i % len(styles)]
        common_ok = title_has_only_common_chars(title)
        risk = route_c_risk_reason(title)
        for pv in prompt_versions:
            for sample_i in range(max(1, samples)):
                skip = (not common_ok) or (risk is not None and not include_risk)
                row = SpikeRow(
                    index=row_i,
                    title=title,
                    category=category,
                    style_id=style.style_id,
                    model=model or "(default)",
                    prompt_version=pv,
                    sample_i=sample_i,
                    risk_reason=risk,
                    common_chars_ok=common_ok,
                    skipped_by_policy=skip,
                    first_pass=None,
                    after_retry=None,
                )
                row_i += 1
                label = (
                    f"[{row.index + 1}] {title!r} · {style.style_id} · "
                    f"pv={pv} · s={sample_i}"
                )
                if skip:
                    print(f"{label} … SKIP policy (common={common_ok} risk={risk})")
                    rows.append(row)
                    continue
                if dry_run:
                    print(f"{label} … dry-run")
                    rows.append(row)
                    continue

                print(f"{label} …", flush=True)
                attempts: list[AttemptRecord] = []
                passed = False
                for attempt in range(max_attempts):
                    img_name = (
                        f"{row.index:03d}-{style.style_id}-pv{pv}-"
                        f"s{sample_i}-a{attempt}-{category}.png"
                    )
                    rec = _one_generate(
                        style_id=style.style_id,
                        title=title,
                        model=model,
                        prompt_version=pv,
                        out_path=out_dir / img_name,
                    )
                    rec = AttemptRecord(
                        attempt=attempt,
                        ok=rec.ok,
                        latency_ms=rec.latency_ms,
                        ocr_matched=rec.ocr_matched,
                        ocr_recognized=rec.ocr_recognized,
                        failure_reason=rec.failure_reason,
                        image_path=rec.image_path,
                    )
                    attempts.append(rec)
                    status = "✓" if rec.ocr_matched else "✗"
                    print(
                        f"  a{attempt} {status} recognized={rec.ocr_recognized!r} "
                        f"latency={rec.latency_ms}ms"
                    )
                    if rec.ocr_matched:
                        passed = True
                        break
                    if not rec.ok:
                        break
                row.attempts = attempts
                row.first_pass = bool(attempts and attempts[0].ocr_matched)
                row.after_retry = passed
                if attempts and attempts[0].ok:
                    row.model = model or "(default)"
                rows.append(row)
    return rows


def summarize(rows: list[SpikeRow]) -> dict[str, Any]:
    attempted = [r for r in rows if not r.skipped_by_policy and r.after_retry is not None]
    first_ok = [r for r in attempted if r.first_pass]
    retry_ok = [r for r in attempted if r.after_retry]
    skipped = [r for r in rows if r.skipped_by_policy]
    by_pv: dict[str, dict[str, int]] = {}
    for r in attempted:
        bucket = by_pv.setdefault(r.prompt_version, {"n": 0, "first": 0, "retry": 0})
        bucket["n"] += 1
        if r.first_pass:
            bucket["first"] += 1
        if r.after_retry:
            bucket["retry"] += 1
    risk_hits = {
        "punctuation": sum(1 for r in rows if r.risk_reason == "punctuation"),
        "repeated_char": sum(1 for r in rows if r.risk_reason == "repeated_char"),
        "uncommon_chars": sum(1 for r in rows if not r.common_chars_ok),
    }

    def _rate(num: int, den: int) -> float | None:
        return round(num / den, 4) if den else None

    return {
        "total_rows": len(rows),
        "skipped_by_policy": len(skipped),
        "attempted": len(attempted),
        "first_pass_rate": _rate(len(first_ok), len(attempted)),
        "after_retry_rate": _rate(len(retry_ok), len(attempted)),
        "by_prompt_version": {
            pv: {
                **stat,
                "first_pass_rate": _rate(stat["first"], stat["n"]),
                "after_retry_rate": _rate(stat["retry"], stat["n"]),
            }
            for pv, stat in by_pv.items()
        },
        "risk_bucket_counts": risk_hits,
        "ac_cal_11_threshold": 0.9,
        "ac_cal_11_after_retry_met": (
            (len(retry_ok) / len(attempted) >= 0.9) if attempted else False
        ),
        "note": (
            "AC-CAL-11 看 after_retry_rate（尝试子集）；skipped 含 D-CAL-21 生僻字 "
            "+ 风险规则（除非 --include-risk）。未达标不得默认开启 route_c_enabled。"
        ),
    }


def write_report(rows: list[SpikeRow], summary: dict[str, Any], *, report_path: Path) -> None:
    payload = {
        "generatedAt": datetime.now(UTC).replace(microsecond=0).isoformat(),
        "summary": summary,
        "results": [
            {
                **{k: v for k, v in asdict(r).items() if k != "attempts"},
                "attempts": [asdict(a) for a in r.attempts],
            }
            for r in rows
        ],
    }
    report_path.with_suffix(".json").write_text(
        json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    lines = [
        "# Route C W0.5b 冲质量 Spike 结果",
        "",
        f"生成时间：{payload['generatedAt']}",
        "",
        "## 汇总",
        "",
        "| 指标 | 数值 |",
        "|------|------|",
        f"| 总行数 | {summary['total_rows']} |",
        f"| 策略跳过 | {summary['skipped_by_policy']} |",
        f"| 实际尝试 | {summary['attempted']} |",
        f"| 首次 OCR 通过率 | {summary['first_pass_rate']} |",
        f"| ≤1 次重试后通过率 | {summary['after_retry_rate']} |",
        f"| AC-CAL-11（≥90%）达标 | {summary['ac_cal_11_after_retry_met']} |",
        "",
        "## 按 prompt_version",
        "",
        "| version | n | first | after_retry |",
        "|---------|---|-------|-------------|",
    ]
    for pv, stat in summary["by_prompt_version"].items():
        lines.append(
            f"| {pv} | {stat['n']} | {stat['first_pass_rate']} | {stat['after_retry_rate']} |"
        )
    lines += [
        "",
        f"> {summary['note']}",
        "",
        "## 风险桶计数（E3）",
        "",
        "```json",
        json.dumps(summary["risk_bucket_counts"], ensure_ascii=False, indent=2),
        "```",
        "",
        "## 逐条",
        "",
        "| # | 标题 | 类别 | 风格 | pv | skip | first | after_retry | risk |",
        "|---|------|------|------|----|------|-------|-------------|------|",
    ]
    for r in rows:
        lines.append(
            f"| {r.index} | {r.title} | {r.category} | {r.style_id} | {r.prompt_version} | "
            f"{r.skipped_by_policy} | {r.first_pass} | {r.after_retry} | {r.risk_reason or ''} |"
        )
    report_path.with_suffix(".md").write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--model", default=None)
    parser.add_argument("--limit", type=int, default=None)
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument(
        "--prompt-version",
        default="v2",
        choices=("v1", "v2", "both"),
        help="E2：对照 v1/v2；both 会翻倍调用",
    )
    parser.add_argument("--samples", type=int, default=1, help="同标题同风格采样次数（E2）")
    parser.add_argument("--retries", type=int, default=1, help="OCR 失败后额外生成次数（E1）")
    parser.add_argument(
        "--include-risk",
        action="store_true",
        help="仍对标点/叠字标题发 API（默认跳过，贴近生产风险规则）",
    )
    args = parser.parse_args()

    date_tag = datetime.now(UTC).strftime("%Y-%m-%d")
    out_dir = (
        ROOT
        / "docs"
        / "acceptance-records"
        / "attachments"
        / f"cover-calligraphy-title-v1-route-c-w05b-spike-{date_tag}"
    )
    report_path = (
        ROOT
        / "docs"
        / "acceptance-records"
        / f"cover-calligraphy-title-v1-route-c-w05b-spike-{date_tag}"
    )

    if not args.dry_run:
        import os

        if not os.environ.get("DASHSCOPE_API_KEY", "").strip():
            print(
                "ERROR: 未设置 DASHSCOPE_API_KEY。可先 --dry-run 看矩阵分配。",
                file=sys.stderr,
            )
            raise SystemExit(1)

    versions: tuple[str, ...]
    if args.prompt_version == "both":
        versions = ("v1", "v2")
    else:
        versions = (args.prompt_version,)

    rows = run_matrix(
        model=args.model,
        limit=args.limit,
        out_dir=out_dir,
        dry_run=args.dry_run,
        prompt_versions=versions,
        samples=args.samples,
        retries=args.retries,
        include_risk=args.include_risk,
    )
    summary = summarize(rows)
    write_report(rows, summary, report_path=report_path)
    print()
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    print(f"\n报告已写入 {report_path.with_suffix('.md')} / .json")


if __name__ == "__main__":
    main()
