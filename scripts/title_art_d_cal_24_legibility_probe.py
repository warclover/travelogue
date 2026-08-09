"""D-CAL-24 Phase 1 · 路线 B 可读性自检 · 低成本人工验证探针（一次性脚本）。

不改动 ``render_b.py``/``fonts.py`` 任何生产路径；只做两件事，供人工核对：

1. **孤立单字连通域计数**：对比候选字体（``ZhiMangXing``/``鸿雷板书体``）与规整
   基线字体（``simhei``）渲染同一个字符时，alpha mask 的连通域（8-邻接 flood
   fill，纯 Python，不引入 numpy/scipy）数量差异，验证决策记录里提出的"连通域
   显著偏低 → 判定粘连风险"这个信号本身是否真的能把已知问题字（"毕"）和正常
   字分开。
2. **真实语境渲染**：额外渲染完整词/短语（"毕业" / "初中毕业照"），不是为了
   验证算法，而是让人在有上下文的情况下重新读一遍——因为孤立单字判断和真实
   阅读体验可能是两件不同的事（人类读字极依赖上下文/先验，不是逐字拼认）。

输出：
- 控制台打印每个字符在每款字体下的连通域计数
- 一张对比网格 PNG（孤立字 + 完整短语，各字体一行），供人工目测
"""

from __future__ import annotations

import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from travelogue.cover_engine.title_art.fonts import (  # noqa: E402
    FONT_POOL,
    resolve_font_source,
)

_OUT_DIR = (
    ROOT
    / "docs"
    / "acceptance-records"
    / "attachments"
    / "cover-calligraphy-title-v1-d-cal-24-route-b-legibility-plan-2026-08-09"
)

#: 候选艺术字体（来自 D-CAL-24 决策记录 §3）。
_CANDIDATES = {
    "ZhiMangXing": "ZhiMangXing-Regular.ttf",
    "鸿雷板书体": next(
        f.filename for f in FONT_POOL if f.filename.startswith("鸿雷板书体")
    ),
}
#: 规整基线字重（决策记录 §3 提出的对照对象）。
_BASELINE_NAME = "simhei"
_BASELINE_PATH = "simhei.ttf"

#: 孤立单字测试集：已知问题字 + 若干对照字（含常见字/复杂字/生僻字混合）。
_ISOLATED_CHARS = ["毕", "业", "照", "华", "斯", "兰", "藏"]

#: 真实语境测试集：呼应真实样本 b01「初中毕业照」。
_CONTEXT_PHRASES = ["毕业", "初中毕业照"]

_PROBE_SIZE = 220  # 孤立单字渲染字号（放大，方便肉眼 + 连通域计数）
_CONTEXT_SIZE = 96  # 语境短语渲染字号（贴近真实标题贴纸量级）


def _load_font(path_or_name: str, size: int) -> ImageFont.FreeTypeFont:
    return ImageFont.truetype(path_or_name, size=size)


def _alpha_mask(font: ImageFont.FreeTypeFont, text: str, canvas: int) -> Image.Image:
    img = Image.new("L", (canvas, canvas), 0)
    draw = ImageDraw.Draw(img)
    bbox = draw.textbbox((0, 0), text, font=font)
    w, h = bbox[2] - bbox[0], bbox[3] - bbox[1]
    x = (canvas - w) / 2 - bbox[0]
    y = (canvas - h) / 2 - bbox[1]
    draw.text((x, y), text, font=font, fill=255)
    return img


def _connected_components(mask: Image.Image, *, threshold: int = 40) -> int:
    """8-邻接 flood fill 计数连通域；纯 Python，字符级 mask 够小，不需要 numpy。"""
    w, h = mask.size
    px = mask.load()
    visited = bytearray(w * h)
    count = 0
    for sy in range(h):
        for sx in range(w):
            idx0 = sy * w + sx
            if visited[idx0] or px[sx, sy] <= threshold:
                continue
            count += 1
            stack = [(sx, sy)]
            visited[idx0] = 1
            while stack:
                x, y = stack.pop()
                for dx in (-1, 0, 1):
                    for dy in (-1, 0, 1):
                        if dx == 0 and dy == 0:
                            continue
                        nx, ny = x + dx, y + dy
                        if 0 <= nx < w and 0 <= ny < h:
                            nidx = ny * w + nx
                            if not visited[nidx] and px[nx, ny] > threshold:
                                visited[nidx] = 1
                                stack.append((nx, ny))
    return count


def main() -> None:
    _OUT_DIR.mkdir(parents=True, exist_ok=True)

    baseline_font = _load_font(_BASELINE_PATH, _PROBE_SIZE)
    candidate_fonts = {
        name: _load_font(resolve_font_source(fname), _PROBE_SIZE)
        for name, fname in _CANDIDATES.items()
    }

    print("=== 孤立单字连通域计数（越低 = 笔画越粘连/越少独立笔段） ===")
    rows: list[tuple[str, dict[str, int]]] = []
    for ch in _ISOLATED_CHARS:
        counts: dict[str, int] = {}
        base_mask = _alpha_mask(baseline_font, ch, _PROBE_SIZE)
        counts[_BASELINE_NAME] = _connected_components(base_mask)
        for name, font in candidate_fonts.items():
            mask = _alpha_mask(font, ch, _PROBE_SIZE)
            counts[name] = _connected_components(mask)
        rows.append((ch, counts))
        ratio_zmx = counts.get("ZhiMangXing", 0) / max(1, counts[_BASELINE_NAME])
        ratio_hl = counts.get("鸿雷板书体", 0) / max(1, counts[_BASELINE_NAME])
        print(
            f"  {ch}: {_BASELINE_NAME}={counts[_BASELINE_NAME]:>2}  "
            f"ZhiMangXing={counts.get('ZhiMangXing', 0):>2} (ratio={ratio_zmx:.2f})  "
            f"鸿雷板书体={counts.get('鸿雷板书体', 0):>2} (ratio={ratio_hl:.2f})"
        )

    # ---- 对比网格图：每行一款字体，每列一个孤立字 + 语境短语 ----
    cell_w, cell_h = 160, 200
    font_names = [_BASELINE_NAME, *candidate_fonts.keys()]
    all_items = list(_ISOLATED_CHARS) + list(_CONTEXT_PHRASES)
    col_widths = [cell_w if i < len(_ISOLATED_CHARS) else cell_w * 3 for i in range(len(all_items))]
    grid_w = sum(col_widths) + 20
    grid_h = cell_h * len(font_names) + 60
    grid = Image.new("RGB", (grid_w, grid_h), (255, 255, 255))
    draw = ImageDraw.Draw(grid)
    label_font = ImageFont.truetype("simhei.ttf", size=20)

    for row_i, fname in enumerate(font_names):
        y0 = 40 + row_i * cell_h
        draw.text((4, y0 + cell_h // 2 - 12), fname, font=label_font, fill=(0, 0, 0))
        x_cursor = 90
        for col_i, item in enumerate(all_items):
            cw = col_widths[col_i]
            size = _PROBE_SIZE if col_i < len(_ISOLATED_CHARS) else _CONTEXT_SIZE
            if fname == _BASELINE_NAME:
                font = _load_font(_BASELINE_PATH, size)
            else:
                font = _load_font(resolve_font_source(_CANDIDATES[fname]), size)
            bbox = draw.textbbox((0, 0), item, font=font)
            tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
            tx = x_cursor + (cw - tw) / 2 - bbox[0]
            ty = y0 + (cell_h - th) / 2 - bbox[1]
            draw.text((tx, ty), item, font=font, fill=(20, 20, 20))
            x_cursor += cw
    for col_i, item in enumerate(all_items):
        x0 = 90 + sum(col_widths[:col_i])
        draw.text((x0 + 4, 8), item, font=label_font, fill=(150, 0, 0))

    out_path = _OUT_DIR / "d-cal-24-legibility-probe-grid.png"
    grid.save(out_path)
    print(f"\n对比网格已保存: {out_path}")


if __name__ == "__main__":
    main()
