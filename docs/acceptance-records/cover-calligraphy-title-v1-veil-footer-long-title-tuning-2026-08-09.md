# veil-footer 长标题贴纸字号微调（W3 b06 留痕跟进）

**日期**：2026-08-09
**状态**：已落地（低风险微调，非结构性重排）
**关联**：[W3 盲评进度](./cover-calligraphy-title-v1-w3-blind-2026-08-08.md) §「结论」（b06）· [PRD-COVER-CALLIGRAPHY-TITLE-V1](../PRD-COVER-CALLIGRAPHY-TITLE-V1.md)

## 1. 起因

W3 盲评 12 对里唯一一例现网 CSS 胜出的 `b06`（veil-footer · 「夏睿彤年度精选」，7 字）：

> 主观印象是该标题较长且贴纸字号在这张构图下偏小，视觉冲击力不如现网大字 CSS 标题；不影响整体结论，留痕供后续 `veil-footer` 长标题字号调优参考，**不单独建 OQ**（样本量 n=1 不足以定性为系统性问题）。

产品负责人当时的判定是"低优先级留痕"，本记录对应"成本最低的一次跟进"，不做结构性重排（如拆两行），只做参数级微调。

## 2. 根因

`render_b.py::render_title_art` 对主字有一段收缩循环：字号从 `_MAIN_TEXT_SIZE_RATIO_BY_STYLE[style] * 720` 起步，若渲染宽度超过 `_MAIN_TEXT_MAX_WIDTH_RATIO_BY_STYLE.get(style, 0.86) * 1200`，逐步收缩直到不超限或触底 `min_size`。

贴纸导出的是固定 1200×720 画布（含透明留白），前端 CSS 用 `width:auto` 把整张画布按等比缩放进题签区——也就是说画布的**显示缩放比例固定**，主字在画布内的**像素字号**直接决定了它在屏幕上的视觉大小。

veil-footer 起始字号比例全风格最大（0.52，对应"电影感抒情"调性），但长标题一旦触发收缩，会收缩到远低于短标题的字号：实测「夏睿彤年度精选」（7 字）从起始 374px 一步收缩到 157px（收缩后仅剩画布高度的 21.8%），而同风格短标题基本不触发收缩、能留在 350px+ 量级——两者视觉体量差 1 倍以上，这正是评审"字号偏小"的直接原因。

## 3. 修复

`_MAIN_TEXT_MAX_WIDTH_RATIO_BY_STYLE` 里给 `veil-footer` 单独放宽到 `0.94`（共享默认是 `0.86`）——收缩循环允许主字占用更多画布宽度，同一 7 字标题收缩后的字号从 157px 提到 171px（+9%）。

```python
_MAIN_TEXT_MAX_WIDTH_RATIO_BY_STYLE: dict[str, float] = {
    "band-cut": 0.62,
    "contact-stamp": 0.62,
    "veil-footer": 0.94,
}
```

**为什么不做得更激进**：把比例进一步推到 0.98 边际收益递减（size 只从 171→178，+4%），继续推逼近画布边缘会挤压 `_veil_footer_backdrop` 柔光垫底的留白，风险收益比转差；不改用两行排版——那需要重排 `content_box`/`baseline_y`/副标题/印章的整套定位数学，跟本次"低成本跟进"的定级不匹配，留给未来若样本量证明是系统性问题再做。

**为什么短标题不受影响**：短标题本就不会触发收缩循环（`main_w <= max_w` 循环条件不成立），放宽 `max_w` 上限对它们完全是死代码路径，零回归——已用单测覆盖（见 §5）。

## 4. 效果对比（同一 7 字标题「夏睿彤年度精选」，同一字体）

上：旧共享默认 `max_w_ratio=0.86`（size≈157px）；下：本次放宽 `max_w_ratio=0.94`（size≈171px）。

![放宽前后对比](./attachments/cover-calligraphy-title-v1-front-cover-identity-line-2026-08-09/veil-footer-b06-before-after.png)

## 5. 测试

`tests/unit/cover_engine/test_title_art_render_b.py` 新增 3 条：

- `test_veil_footer_max_width_ratio_wider_than_shared_default`：配置断言，`veil-footer` 比共享默认 `0.86` 更宽。
- `test_veil_footer_long_title_renders_bigger_with_relaxed_max_width`：真实渲染同一长标题，放宽后的字形高度（非透明像素竖直跨度）应大于共享默认。
- `test_veil_footer_short_title_unaffected_by_wider_max_width`：短标题在两种比例下字形高度应完全一致（零回归）。

回归：`tests/unit/cover_engine/test_title_art_render_b.py` 16 passed。

## 6. 范围声明

这是参数级微调，不改变：贴纸的整体设计语言（单行、柔光垫底、左对齐）、其它 3 款白名单风格的任何行为、`_MAIN_TEXT_MIN_SIZE_RATIO` 收缩下限。若未来有更多样本证明这是系统性问题（而不是 n=1 的个案），再评估是否需要两行排版等结构性方案。
