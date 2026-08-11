# CCF · 本地狗粮 / craft 前后截图（2026-08-11）

| 属性 | 内容 |
|------|------|
| **主题** | Cover Craft Focus（CCF）· dogfood + AC-CCF-03 |
| **方法** | trip 目录内 `render` + `TRAVELOGUE_COVER_CRAFT=1/0` + Playwright 首屏；脚本 `scripts/ccf_capture_covers.py` |
| **附件** | [attachments/ccf-craft-focus-dogfood-2026-08-11/](./attachments/ccf-craft-focus-dogfood-2026-08-11/) |
| **CSS 真相源** | **`templates/visual-journal/journal.css`**（非 `trips/linzhi/journal.css`） |

---

## 核对项

| # | 项 | 结果 |
|---|-----|------|
| 1 | CCF 开时 assignable = Hero Set 三款 | ✅ `veil-footer` / `folio-overlap` / `band-cut` |
| 2 | craft-on HTML 含 `data-cover-craft="ccf-v1"` | ✅ |
| 3 | craft-off HTML 无该属性 | ✅ |
| 4 | craft-on/off 截图字节级不同（Hero） | ✅ veil / band / folio 均 DIFF |
| 5 | contact-stamp 历史版式仍可渲染 | ✅ 截图存在；Studio `coverCraft.legacyCurrent=true` + hint |
| 6 | 一键撤回 | ✅ `TRAVELOGUE_COVER_CRAFT=0` 后无 craft 属性、截图回退 |

---

## 样本

| 风格 | trip | craft-on | craft-off |
|------|------|----------|-----------|
| veil-footer | demo-3ee2727aea | [craft-on](./attachments/ccf-craft-focus-dogfood-2026-08-11/veil-footer__demo-3ee2727aea__craft-on.png) | [craft-off](./attachments/ccf-craft-focus-dogfood-2026-08-11/veil-footer__demo-3ee2727aea__craft-off.png) |
| band-cut | demo-1b67b06546 | [craft-on](./attachments/ccf-craft-focus-dogfood-2026-08-11/band-cut__demo-1b67b06546__craft-on.png) | [craft-off](./attachments/ccf-craft-focus-dogfood-2026-08-11/band-cut__demo-1b67b06546__craft-off.png) |
| folio-overlap | demo-0ebda73294 | [craft-on](./attachments/ccf-craft-focus-dogfood-2026-08-11/folio-overlap__demo-0ebda73294__craft-on.png) | [craft-off](./attachments/ccf-craft-focus-dogfood-2026-08-11/folio-overlap__demo-0ebda73294__craft-off.png) |
| contact-stamp（侧菜） | demo-81d3442e92 | [craft-on](./attachments/ccf-craft-focus-dogfood-2026-08-11/contact-stamp__demo-81d3442e92__craft-on.png) | [craft-off](./attachments/ccf-craft-focus-dogfood-2026-08-11/contact-stamp__demo-81d3442e92__craft-off.png) |

---

## 目视结论

- **veil-footer**：craft-on 雾底更深、题名区更收束，电影开场感略强；撤回差异可辨。
- **band-cut**：切线约 62%、纸签更紧；风景断带语言清楚。W1b token 已合入模板 CSS。
- **folio-overlap**：纸栏比例/纸色微调后对页感更明确（on/off 体积差最大）。W2 token 已合入。
- **contact-stamp**：侧菜仍渲染；Hero craft token 对其几乎无影响（on/off 同哈希属预期）。Studio 入口已返回 `legacyHint`。

## 踩坑（已修）

首轮把 craft 写进 `trips/linzhi/journal.css`，但 `render` 拷贝的是 **`templates/visual-journal/journal.css`**，导致 on/off 截图曾完全一致。已迁到模板真相源并重跑。

## 下一步

- 人工打开 Studio 点验 FE-CCF-02（`demo-81d3442e92`）
- W3 盲评（AC-CCF-BLIND）再决定是否默认生产
- 清理可选：`attachments/.../_html/` 旧失败产物
