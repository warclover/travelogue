"""AC-CAL-04/05/13 验收数据脚本（PRD-COVER-CALLIGRAPHY-TITLE-V1 §12.3）。

用真实 trip 封面照片（非 fixture/非合成图）+ 路线 C W0.5 Spike 的真实产出图
（非 mock），跑一遍跟 ``engine.py`` 完全同一套 §6.1/§6.2 算法，产出：

- AC-CAL-04：4 款白名单风格候选矩形在真实封面上的对比度实测（
  ``pick_readable_color`` 是否达标 ``MIN_CONTRAST_RATIO``）。
- AC-CAL-05：候选矩形面积占比（自测口径，阈值 <= 0.35）+ 真实照片跑一遍
  ``score_candidate`` 确认「遮挡显著区比例」惩罚分支从未触发。
- AC-CAL-13：复用路线 C Spike 真实产出图，走一遍
  ``pick_readable_color`` → ``recolor_ink_on_white`` 链路，核对重上色产物
  忠实复现挑选出的墨色，且默认兜底白色路径可复现。

用法：

    python scripts/verify_title_art_ac04_05_13.py

结果落盘：docs/acceptance-records/attachments/
cover-calligraphy-title-v1-ac04-05-06-13-2026-08-08/verify-output.txt
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

# Windows PowerShell 默认控制台代码页是 GBK，直接 print 中文会乱码/崩溃；
# 落盘文件走显式 utf-8，不受影响（跟 title_art_route_c_spike.py 同一处理）。
try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")  # type: ignore[union-attr]
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")  # type: ignore[union-attr]
except (AttributeError, ValueError):
    pass

from PIL import Image  # noqa: E402

from travelogue.cover_engine.title_art.color import (  # noqa: E402
    MIN_CONTRAST_RATIO,
    contrast_ratio,
    pick_readable_color,
    recolor_ink_on_white,
    roi_average_color,
)
from travelogue.cover_engine.title_art.placement import score_candidate  # noqa: E402
from travelogue.cover_engine.title_art.whitelist import WHITELIST, placement_presets  # noqa: E402
from travelogue.media.source_resolve import resolve_source_path  # noqa: E402

TRIPS_DIR = ROOT / "trips"
OUT_DIR = (
    ROOT
    / "docs"
    / "acceptance-records"
    / "attachments"
    / "cover-calligraphy-title-v1-ac04-05-06-13-2026-08-08"
)


def _cover_asset_and_image(trip_dir: Path) -> tuple[dict, Image.Image, str] | None:
    trip_json = trip_dir / "trip.json"
    if not trip_json.is_file():
        return None
    trip = json.loads(trip_json.read_text(encoding="utf-8"))
    asset_id = str(trip.get("coverAssetId") or "")
    assets = trip.get("assets") or []
    asset = next((a for a in assets if str(a.get("id")) == asset_id), None)
    if asset is None:
        return None
    path = resolve_source_path(asset, trip_dir)
    if path is None or not path.is_file():
        return None
    try:
        img = Image.open(path).convert("RGB")
    except Exception:
        return None
    title = (trip.get("meta") or {}).get("title") or "(no title)"
    return asset, img, f"{trip_dir.name}::{title}"


def collect_real_covers(limit: int = 14) -> list[tuple[dict, Image.Image, str]]:
    out = []
    for d in sorted(TRIPS_DIR.iterdir()):
        if not d.is_dir() or d.name.startswith("."):
            continue
        got = _cover_asset_and_image(d)
        if got is not None:
            out.append(got)
        if len(out) >= limit:
            break
    return out


def section_ac04_ac05(covers: list[tuple[dict, Image.Image, str]]) -> None:
    print("=" * 70)
    print("AC-CAL-04 + AC-CAL-05 · 4 款白名单风格 x 真实封面测试集")
    print("=" * 70)

    print("\n候选矩形面积占比（AC-CAL-05 自测口径，阈值 <= 0.35）：")
    for style_id in WHITELIST:
        for p in placement_presets(style_id):
            tag = "primary" if p is WHITELIST[style_id] else "fallback"
            area = p.rect["w"] * p.rect["h"]
            print(
                f"  {p.opening_style_id:16s} [{tag:8s}] area={area:.4f} "
                f"({area * 100:.1f}%)  {'PASS' if area <= 0.35 else 'FAIL'}"
            )

    print(f"\n对比度实测（AC-CAL-04，MIN_CONTRAST_RATIO={MIN_CONTRAST_RATIO}）：")
    print(f"测试集：{len(covers)} 条真实 trip 封面照片（非 fixture/非合成图）\n")

    total_checks = 0
    total_pass = 0
    overlap_violations = 0

    for style_id in WHITELIST:
        for preset in placement_presets(style_id):
            tag = "primary" if preset is WHITELIST[style_id] else "fallback"
            if preset.assume_dark_veil or preset.assume_paper_bg:
                # 这两类候选的背景估计跟照片内容无关（见 engine.py），是
                # 确定性单点计算——遍历测试集重复算同一个值没有意义。
                if preset.assume_dark_veil:
                    bg = (10, 10, 10)
                    reason = "assume_dark_veil→固定近黑背景估计"
                else:
                    bg = (0xF4, 0xF1, 0xEA)
                    reason = "assume_paper_bg→固定纸面色估计(--cover-folio-paper)"
                pick = pick_readable_color(bg)
                total_checks += 1
                total_pass += int(pick.ok)
                print(
                    f"  [{style_id:14s}/{tag:8s}] {reason}: bg={bg} -> "
                    f"color={pick.color_hex} ratio={pick.ratio} ok={pick.ok}"
                )
                continue

            ratios = []
            for _asset, img, label in covers:
                w, h = img.size
                box = (
                    int(preset.rect["x"] * w),
                    int(preset.rect["y"] * h),
                    int(preset.rect["w"] * w),
                    int(preset.rect["h"] * h),
                )
                bg = roi_average_color(img, box)
                pick = pick_readable_color(bg)
                ratios.append(pick.ratio)
                total_checks += 1
                total_pass += int(pick.ok)
                if not pick.ok:
                    print(f"    !! contrast FAIL: {label} bg={bg} ratio={pick.ratio}")

                cand = score_candidate(img, preset)
                if any("超阈值" in line for line in cand.explain):
                    overlap_violations += 1
                    print(f"    !! overlap FAIL: {label} explain={cand.explain}")

            print(
                f"  [{style_id:14s}/{tag:8s}] 真实封面 N={len(ratios)}  "
                f"ratio min={min(ratios):.2f} max={max(ratios):.2f} "
                f"avg={sum(ratios) / len(ratios):.2f}  "
                f"全部达标={all(r >= MIN_CONTRAST_RATIO for r in ratios)}"
            )

    print(
        f"\n汇总：对比度检查 {total_pass}/{total_checks} 达标；"
        f"遮挡阈值违规 {overlap_violations} 例"
    )


def section_ac13(covers: list[tuple[dict, Image.Image, str]]) -> None:
    print("\n" + "=" * 70)
    print("AC-CAL-13 · 路线 C 抠字重上色是否同样满足 §6.1 对比度合同")
    print("=" * 70)

    spike_dir = (
        ROOT
        / "docs"
        / "acceptance-records"
        / "attachments"
        / "cover-calligraphy-title-v1-route-c-w05-spike-2026-08-08"
    )
    samples = sorted(spike_dir.glob("*.png"))[:6]
    print(f"复用路线 C W0.5 Spike 真实产出图（非新造/非 mock）：{len(samples)} 张")
    print(f"来源目录：{spike_dir.relative_to(ROOT)}\n")

    for i, sample_path in enumerate(samples):
        raw = Image.open(sample_path).convert("RGB")
        # 用测试集里第 i 张真实封面的 ROI 背景色，走一遍跟 engine.py 完全
        # 相同的 pick_readable_color -> recolor_ink_on_white 链路。
        _asset, cover_img, _label = covers[i % len(covers)]
        bg = roi_average_color(cover_img, (0, 0, cover_img.width, cover_img.height // 3))
        contrast = pick_readable_color(bg)
        ink = recolor_ink_on_white(raw, contrast.color_rgb)

        # 找一个足够深的墨迹像素核对重上色后的真实颜色跟目标色一致——不是
        # 只信 pick_readable_color 的返回值本身，这里验证的是「抠字重上
        # 色」这一步执行后的真实产物，是否忠实复现了挑出的墨色。
        gray = raw.convert("L")
        opaque_xy = None
        for y in range(0, gray.height, 4):
            for x in range(0, gray.width, 4):
                if gray.getpixel((x, y)) < 60:
                    opaque_xy = (x, y)
                    break
            if opaque_xy:
                break

        if opaque_xy is None:
            print(f"  [{sample_path.name}] 未找到足够深的墨迹像素，跳过核对")
            continue

        r, g, b, a = ink.getpixel(opaque_xy)
        matches_target = (r, g, b) == contrast.color_rgb
        print(
            f"  [{sample_path.name}] bg={bg} -> 目标色={contrast.color_hex} "
            f"ratio={contrast.ratio} ok={contrast.ok} | "
            f"重上色后墨迹像素={(r, g, b, a)} 颜色一致={matches_target}"
        )

    print("\n默认兜底白色可复现性核对（背景为中性灰，白/深均可能不达标时）：")
    mid_gray_bgs = [(128, 128, 128), (140, 130, 120), (110, 115, 108)]
    for bg in mid_gray_bgs:
        pick = pick_readable_color(bg)
        white_ratio = contrast_ratio((255, 255, 255), bg)
        dark_ratio = contrast_ratio((26, 26, 26), bg)
        print(
            f"  bg={bg} white_ratio={white_ratio:.2f} dark_ratio={dark_ratio:.2f} "
            f"-> 选色={pick.color_hex} ok={pick.ok} "
            f"{'（回落白色）' if pick.color_rgb == (255, 255, 255) else ''}"
        )
        assert pick.color_rgb == (255, 255, 255) or pick.ok, "非白色兜底时必须已达标"


def main() -> None:
    covers = collect_real_covers()
    print(f"real cover 测试集（{len(covers)} 条）：")
    for _asset, img, label in covers:
        print(f"  - {label}  size={img.size}")
    print()
    section_ac04_ac05(covers)
    section_ac13(covers)


if __name__ == "__main__":
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    out_path = OUT_DIR / "verify-output.txt"
    with open(out_path, "w", encoding="utf-8") as fh:
        _orig_stdout = sys.stdout
        sys.stdout = fh
        try:
            main()
        finally:
            sys.stdout = _orig_stdout
    print(f"written to {out_path}")
