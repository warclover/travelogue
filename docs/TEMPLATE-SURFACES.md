# Visual Journal · 双端表面矩阵

| 属性 | 内容 |
|------|------|
| **模板 ID** | `visual-journal` |
| **关联** | [TEMPLATE-visual-journal.md](./TEMPLATE-visual-journal.md)、[web端模板.prd](./web端模板.prd)、[0521任务.md](./0521任务.md) |
| **更新** | 2026-05-27 |
| **阅读体验** | [PRD-EXPERIENCE.md](./PRD-EXPERIENCE.md) · [experience-matrix.yaml](./experience-matrix.yaml) |

---

## 三 HTML 表面（2026-05）

| 文件 | `data-layout` | 版式 | 长图 | 内联编辑 |
|------|---------------|------|------|----------|
| `index.html` | `web` | `screens[]` | bridge → 长图面 | ✅ draft |
| `index-longshot.html` | `longshot` | `screens` 展平为 `media-card` 竖栈 | ✅ 主入口 | ✅ draft |
| `index-mobile.html` | `mobile` | `legacy` `items[]` | ✅（legacy DOM） | ✅ draft |

- **`render --dual`**：同时写出 `index.html` + `index-mobile.html`；screens 引擎 trip 另写 **`index-longshot.html`** sidecar。
- **长图预览**：须 `python -m travelogue serve trips/<id>`（`http://`）；`file://` 会因 CORS/资源加载禁用长图导出。
- **按章长图**：>30 张默认按章；>45 张禁用「完整长图」；微信内 UA 提示长按保存。
- **share 渲染**：`export_mode=share` 时长图 bundle 仍默认包含，但 **无** inline-edit；再渲染 sidecar 为分享态。

---

## 三阅读模式（2026-05-27 · PRD-EXPERIENCE）

| 模式 | ID | 入口 | 表面 | profile 来源 |
|------|-----|------|------|--------------|
| **浏览** | `scroll` | 打开 `index.html` | web · mobile | `export.reading.profile`（mobile 强制 `legacy`） |
| **放映** | `present` | toolbar **放映** | web only · `screenplay.js` | 同上；激活时暂停 Lenis / breath |
| **长图** | `longshot` | **长图** · `index-longshot.html` | web · mobile · `longshot.js` | `performance`（捕获前 teardown 动效） |

- **屏序契约**：`chapters[].screens[]` 为 scroll / present / longshot **唯一顺序源**（ADR-003）。
- **Hybrid（默认）**：`default_hybrid` = scroll-snap proximity + breath soft + folio lite；详见 [PRD-EXPERIENCE.md §7](./PRD-EXPERIENCE.md)。
- **内联编辑**：draft 态强制 `legacy` profile，禁用 present（见 `experience-matrix.yaml` · `inline_edit`）。

---

## 数据与交付（拍板）

- **一份** `trip.json`，`exportLayout: auto`（或显式 `web` / `mobile`）。
- 交付可生成多份 HTML（如 `index.html` + `index-mobile.html`），数据不拆两个 trip 目录。

### `exportLayout=auto` 与 768px 断点（T-04）

| 交付 HTML | `data-layout` | 版式引擎 | 视口行为 |
|-----------|---------------|----------|----------|
| `index.html` | `web`（渲染时写入） | `screens` | 固定 Web 16:9 舞台 |
| `index-mobile.html` | `mobile` | `legacy` | 固定 9:16 overlay |
| 单文件 `index.html` 且 trip 为 `auto` | **不写** `data-layout` | 按 trip | CSS `@media (min-width: 48rem)` 切换 |

**封面（`exportLayout=auto`）**：`curation.coverByLayout.mobile` 优选竖图，`coverByLayout.web` 优选横/全景；渲染 `--dual` 时各 HTML 用各自封面。章内 Web 首屏可插入单图 `screen-landscape-1` / `screen-panorama-1` hero（≥4 张/章）。

Manifest：`breakpointWebPx: 768`，`breakpointWeb: 48rem`（见 `tests/test_adaptive_breakpoint.py`）。

---

## 三层契约

| 层 | 字段 | 手机 / legacy | Web screens |
|----|------|---------------|-------------|
| L1 结构 | `chapters[]`、`patternId` | 共用 | 共用 |
| L2 版式 | `items[]` | ✅ 主渲染 | 辅助（校验、legacy） |
| L2 版式 | `screens[]` | 忽略 | ✅ 主渲染 |
| L3 文案 | `meta`、`title`、`caption` | 共用 | 共用 |

---

## 表面矩阵

| 块 / 能力 | 手机 `<768px` | Web `screens` | Web `legacy`（对比） |
|-----------|--------------|---------------|----------------------|
| 封面 | `cover-hero` 9:16 · overlay 标题 | 16:9 hero | 同 screens |
| 章标题 | overlay / 深色底 | 图下 · 浅色 | 同 screens |
| 单图 | `media-card` fill | `screen-*-1` cover 满屏 | `media-card` / 横单 row |
| 竖组图 | `media-row` portrait 纵排 | `screen-portrait-2/3` | `portrait-triple` row |
| 横组图 | `media-row` landscape 纵排 | 2×2 / 3×3 宫格 | `landscape-triple` row |
| 混排 | — | `screen-portrait-1-landscape-2` | — |
| 图库章 | `media-scroll` | `screens[]`（gallery 专屏） | scroll |
| 长图按钮 | ✅ | ❌ | ✅ |
| 断点 | `exportLayout=mobile` 锁定竖版意图 | `layoutEngine=screens` | `media-row` DOM |

---

## 金样例

| 文件 | 用途 |
|------|------|
| `templates/visual-journal/golden.html` | 手机 / auto · legacy DOM |
| `templates/visual-journal/golden-web-screens.html` | Web screens pattern |
| `scripts/compare-web-layout.ps1` | 同 trip · legacy vs screens A/B |

---

## CLI 速查

```powershell
# Web screens（当前默认）
python -m travelogue from-album "<相册>" --layout auto --force
python -m travelogue render trips/<tripId>/trip.json --dual
python -m travelogue from-album "<相册>" --layout web --force

# 手机专测
python -m travelogue from-album "<相册>" --layout mobile --force

# 同 trip A/B
.\scripts\compare-web-layout.ps1 trips\<tripId>
```
