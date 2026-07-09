# Travelogue · 渲染契约（Agent 3）

| 属性 | 内容 |
|------|------|
| **Agent** | Publisher（Agent 3） |
| **模板** | `visual-journal` v0.2.1 |
| **视觉裁判** | `templates/visual-journal/golden.html` + `golden.css` |
| **文档版本** | v0.2 · P23.1 inline peak |
| **更新日期** | 2026-06-14 |

---

## 1. 输入输出

| 输入 | 输出 |
|------|------|
| `trips/{id}/trip.json` | `trips/{id}/index.html` |
| `trips/{id}/assets/` | `trips/{id}/journal.css`（自模板复制或引用） |
| `templates/visual-journal/*.hbs` | 可选 `preview.jpg` |

**禁止**：LLM 生成 HTML；仅 Handlebars（或等价）填模板。

---

## 2. 页面骨架

```html
<!DOCTYPE html>
<html lang="zh-CN" data-layout="{exportLayout}">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover" />
  <title>{meta.title}</title>
  <link rel="stylesheet" href="journal.css" />
</head>
<body>
  <!-- cover-hero -->
  <!-- trip-meta + hook-line -->
  <!-- chapters[] -->
  <!-- epilogue -->
  <!-- footer-cta -->
</body>
</html>
```

`data-layout`：`trip.exportLayout`，默认 `auto`。

---

## 3. 块映射表

| trip.json / 逻辑 | `data-block` | 主要 DOM / class |
|------------------|--------------|------------------|
| 封面 `coverAssetId` | `cover-hero` | `.cover-hero`, 比例盒 9:16 / 16:9 |
| `meta` | `trip-meta` | `.trip-meta` |
| `meta.hook` | `hook-line` | `.hook-line`（空则省略块） |
| 章头 | `chapter-header` | `.chapter-header`, 序号 + `chapter.title` |
| `chapter.lead` | `chapter-lead` | 可空，省略空块 |
| `media-card` | `media-card` | 见 §4 |
| `media-row` | `media-row` | 两卡纵/横排 |
| `media-scroll` | `media-scroll` | 横滑 `overflow-x` |
| `epilogue` | `epilogue` | |
| 固定 | `footer-cta` | 生成信息 |
| Phase 23 · 高光池 | `layout-screen` | `data-role="moment"`（签名）/ `data-role="peak"`（池内其余）· `.moment-exif-bar`（见 §4c） |

---

## 4c. 高光池 inline peak（Phase 23.1 · 池内 solo + EXIF）

> 自 P23.1 起，签名与池内次高峰均走 **inline `layout-screen`**，不再使用 trip 级 `moment-screen` 块。

| 项 | 契约 |
|----|------|
| 块标记 | `data-block="layout-screen"` · `data-role="moment"`（签名 **唯一**）或 `data-role="peak"`（池内其余） |
| 策展 | `ensure_pool_assets_solo_screens()` · 池内每张从拼版拆为单槽屏 |
| 标签 | `.layout-screen__moment-label` · 中文「决定性瞬间」/ 英文 `Moment` · **仅** `data-role="moment"` |
| EXIF 脚注 | `.moment-exif-bar` · 默认池内全集（`pool_exif: true`）· 单行 mono ≤13px |
| 省略 EXIF | `performance` profile · `pool_exif: false` · `show_exif: false` |
| 保留 solo | `performance` / longshot 可省略 EXIF，**仍**拆 solo（`pool_solo: true`） |
| 配置 | `curate.moment.pool_solo` · `pool_exif` · `signature_label` |

实现：`travelogue.curation.moment_scoring.ensure_pool_assets_solo_screens()`、`travelogue.render.context.build_layout_screen()`、`partials/layout-screen.hbs`。

### 4c-legacy. `moment-screen`（v0.23.2 已废弃 · 勿新增调用）

> **历史契约**：P23-W2 曾用 trip 级独立块；P23.1 起统一 inline `layout-screen`（见 §4c）。以下字段仅供维护遗留导出产物。

| 项 | 契约 |
|----|------|
| 块标记 | `data-block="moment-screen"` · 全册 **唯一** |
| 插入位置 | 末章最后 `layout-screen` 之后、`cover-closing` 之前（`before_closing`） |
| 主图 | `.layout-slot--moment` · `img.layout-slot__img--{fit}` · focal CSS 变量 |
| 标签 | `.moment-screen__label` · 中文「最佳时刻」/ 英文 `Moment` |
| EXIF 脚注 | `.moment-exif-line` · **仅本屏** · 单行 mono ≤13px · 非 overlay |
| 省略 | `performance` profile · `momentSkipped` · longshot 主 HTML 不含 moment 屏 |
| secondary | `momentSecondaryIds` 融入正文屏，**不**渲染额外 moment 屏 |

实现：`travelogue.render.moment_screen.build_moment_screen_context()`、`partials/moment-screen.hbs`（遗留，勿新增调用）。

---

## 4. `media-card` 渲染

### 4.1 类名合成

```
media-card
  media-card--bleed      if layout.bleed
  media-card--fill       if layout.fill (default true)
  media-card--overlay    if layout.overlay OR mobile profile
  media-card--video      if asset.type === video
  media-card--portrait   if height > width (optional)
```

### 4.2 图片

优先：

```html
<img class="media-card__visual"
  src="{displayFile}"
  srcset="{srcset compiled}"
  sizes="100vw"
  alt="{title or caption or meta title}"
  loading="lazy"
  decoding="async" />
```

`exportLayout: mobile` 时可选 `cropMobile` 为 `src`。

### 4.3 视频

```html
<video class="media-card__visual" poster="{posterFile}"
  muted playsinline loop preload="metadata">
  <source src="{displayFile}" type="video/mp4" />
</video>
```

有 `hasAudio` 时角标「轻触开声」；**不**同卡渲染 voice-bar。

### 4.4 标题与文案

| 形态 | 位置 |
|------|------|
| mobile / overlay | `.media-card__overlay` 内 title + caption |
| web | `.media-card__body` 在图下 |

### 4.5 语音

```html
<div class="voice-bar" data-asset-id="...">
  <audio controls src="{voice.audioFile}"></audio>
  <details class="voice-transcript">...</details>
</div>
```

`share` 模式：`details` 默认折叠。

---

## 5. Pattern → items 校验

渲染前 L2 校验（`VALIDATION-RULES.md`）。不在渲染器内「自动改 pattern」。

| patternId | 期望 items |
|-----------|------------|
| open | ≥2 media-card |
| gallery | 1 media-scroll |
| moment | ≥2 视觉单元（card/row/scroll 各 1 + 每屏 1；见 VR-P05） |
| close | ≥1 media-card |

---

## 6. 模式 `draft` vs `share`

| 项 | draft | share |
|----|-------|-------|
| `data-editable` | 保留 | 移除 |
| 转写 | 可展开 | `<details>` 默认关 |
| EXIF | 不剥离源 assets | 导出副本剥离 |

---

## 7. 与 golden 对齐

| 检查项 | 方法 |
|--------|------|
| 断点 768px | 缩放手窗对比 golden |
| 9:16 / 16:9 | `data-layout` mobile/web |
| 深色手机底 | `golden.css` 变量一致 |
| 5 处 voice-bar | 样例 trip 对照 |

**回归**：同一 fixture `copy_locked` 渲染后，关键块 DOM 结构应与 golden 同构（类名一致，文案可不同）。

---

## 8. `preview.jpg`（ADR-001 · Pillow MVP）

分享漏斗第一屏；**零 LLM**，Agent 3 在 `export` 时生成。

### 8.1 画布

| 项 | 值 |
|----|-----|
| 尺寸 | 1080 × 1920（9:16） |
| 格式 | JPEG quality 88 或 WebP |
| 输出 | `trips/{id}/preview.jpg` |

### 8.2 版式（杂志 / KINFOLK 启发）

```
┌────────────────────┐
│   [顶部细边距]      │
│                    │
│   大图 area        │  ← coverAsset cropMobile 或 9:16 center crop
│   (约 70% 高)      │
│                    │
│   渐变遮罩（底）    │
│   城市名 衬线大字   │  ← meta.places[0]
│   日期 小字         │  ← dateStart–dateEnd
│   hook 金句 1–2行   │  ← meta.hook，无则 title
└────────────────────┘
```

### 8.3 Pillow 实现要点

- 字体：系统衬线栈或 bundled Noto Serif SC（注意授权）。  
- 文本自动换行 + 最大行数，超出截断。  
- 对比度不足时加强底部渐变。  

### 8.4 P1：Playwright 可选

对 `templates/visual-journal/cover-share.html` 节点截图，与 golden 像素级一致时再切换。

---

## 8b. 主 HTML 与 Base64

| 项 | MVP |
|----|-----|
| 图片/视频 | **仅相对路径** `assets/...` |
| Base64 内嵌 | ❌ 默认关闭 |

---

## 8c. 保存长图（P0 · 渐进增强 JS bundle）

| 项 | 说明 |
|----|------|
| 触发 | `export.longShot` 默认 `true`；`false` 或 `--no-longshot` 关闭 |
| HTML | `<html … data-longshot="on">`；`partials/longshot-toolbar.hbs` |
| 复制文件 | `longshot.js`、`longshot.css`、`vendor/html2canvas.min.js` → trip 根目录 |
| 阅读态 | 未点击按钮前，主内容仍可无 JS 浏览 |
| share zip | 默认 **包含** longshot bundle（微信群分享 P0） |
| 私密 HTML | 小程序鉴权场景见 `SHARING.md` §3；`golden-share.html` 为无长图参考页 |

实现：`travelogue.render.engine.copy_longshot_bundle()`、`should_include_long_shot()`。

| `layoutEngine` | 长图 |
|----------------|------|
| `legacy`（含 Web `media-row`） | ✅ 默认开启 |
| `screens`（`layout-screen`） | ❌ 主 HTML 无 toolbar；✅ **`index-longshot.html` sidecar**（screens 展平） |

规格详见 `PRD-MVP.md` §6.7.1。

---

## 9. 失败处理

| 情况 | 行为 |
|------|------|
| 缺 `displayFile` | `E_RENDER_ASSET_MISSING`，不写入 index.html |
| L2 失败 | `E_VALIDATE_MANIFEST` |
| 缺 alt | 用 caption → title → `"旅行照片"` |

---

## 10. 模板文件规划

```
templates/visual-journal/
  golden.html          # 开发预览（手写维护）
  golden.css           # @import journal.css + 预览顶栏
  journal.css          # 用户 zip 交付样式
  golden-share.html    # 分享态金样例（gen_golden_variants.py）
  golden-minimal.html  # 空状态金样例
  cover-share.html     # preview.jpg 版式对照
  GOLDEN-CHECKLIST.md
  journal.hbs
  longshot.js          # 可选：保存长图
  longshot.css
  vendor/html2canvas.min.js
  partials/
    cover-hero.hbs
    media-card.hbs
    longshot-toolbar.hbs
    chapter.hbs
```

---

## 11. Longshot 2.0 · boundary selectors（D-LNG2-26）

平台切分（`boundary_metrics.collect`）冻结 selector；变更须同步 `travelogue/export/boundary_metrics.py` 与 golden 快照。

| 边界类型 | kind | Selector |
|----------|------|----------|
| cover 底边 | `cover` | `.cover-opening` / `.cover-hero` / `[data-block="cover-opening"]` / `[data-block="cover-hero"]` |
| 章分隔底边 | `chapter_separator` | `.chapter-separator` / `[data-block="chapter-separator"]` |
| 章首顶边（非首章） | `chapter_start` | `section.chapter` |
| photo cell 顶边 | `photo` | `.media-card img` / `.media-card__visual` / `.layout-slot` / `.layout-slot__img` |
| media-card / screen 顶边 | `card` | `.media-card` / `[data-block="media-card"]` / `.layout-screen` |

坐标：`y_canvas = round(y_css × scale)`；切点权重见 PRD §6.3.7。

---

## 12. 版本历史

| 版本 | 日期 | 说明 |
|------|------|------|
| v0.1 | 2026-05-19 | 初稿 |
| v0.3 | 2026-07-09 | §11 Longshot 2.0 boundary selectors |
