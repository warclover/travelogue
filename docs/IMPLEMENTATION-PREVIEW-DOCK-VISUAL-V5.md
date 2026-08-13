# Travelogue · 预览 Dock 视觉 V5（DIG）· 实施清单

| 属性 | 内容 |
|------|------|
| **PRD** | [PRD-PREVIEW-DOCK-VISUAL-V5.md](./PRD-PREVIEW-DOCK-VISUAL-V5.md) **v0.1.0** |
| **主题代号** | **DIG**（Dock Ink Glass） |
| **DOC-STATUS** | **active** |
| **状态** | **W1–W2 已落地代码**（2026-08-12）· 待产品目视签 AC + W3 手测回归 |
| **范围** | 纯视觉：主改 `dock.css`；caret SVG 时可碰极少 DOM；**禁止改按钮顺序 / 导出状态机 / Sheet IA** |
| **建议工期** | W1–W3 合计 **0.5–1.5 人日** |
| **文档版本** | **v0.3.0** |
| **更新日期** | 2026-08-12 |

> **实施铁律（抄自 PRD）**  
> 1. 只换皮，不换骨。  
> 2. 先删后加：folio / 薄荷绿 / 金渐变 / 铜光 divider → 再写 DIG token。  
> 3. 玻璃只给容器；铜 CTA 不透明平涂。  
> 4. `pointer-events` / 互斥 / 窄屏藏字逻辑一行都不要「顺手重构」。

---

## 0. 波次总览

| 波次 | 内容 | 出口 AC | 估时 | 状态 |
|------|------|---------|------|------|
| **W0** | PRD 签核 + 高保真对齐 + 本清单确认 | Go / Conditional Go | 0.5h | ☑ 产品方向已签 · 编码先行 |
| **W1** | P0 CSS：token / 墨玻壳 / 退役 folio·正圆·金渐变 / ghost 统一 / 字距 / divider / 铜 CTA | AC-DIG-01～05 | 0.3–0.6d | ☑ 代码已合本地 |
| **W2** | P1：active·done·focus·stale·tip·caret；窄屏目视 | AC-DIG-06～10 | 0.2–0.4d | ☑ 代码已合本地 |
| **W3** | 回归互斥 / 导出主路径 / 浅深封面 / reduced-motion / 门禁 | AC-DIG-11～16 | 0.2–0.4d | ☐ 待手测 |
| **W4**（可选） | 真机狗粮 N≥3；OQ-DIG-01 是否开自适应 | acceptance-record | — | ☐ |

```mermaid
flowchart LR
  W0[W0 签核] --> W1[W1 P0 换皮]
  W1 --> W2[W2 状态与窄屏]
  W2 --> W3[W3 回归合入]
  W3 -.-> W4[W4 可选狗粮]
```

---

## 1. 改动面地图

| 文件 | W1 | W2 | W3 | 说明 |
|------|----|----|----|------|
| `templates/studio/preview-toolbar/dock.css` | **主** | **主** | 微调 | 几乎全部视觉合同落这里 |
| `templates/studio/preview-toolbar/tokens.css` | 可选 | — | — | 仅当要把 `--dock-*` 上提共享 |
| `templates/studio/preview-toolbar/longshot.css` | 核 | 核 | — | 若 idle/running 渐变与 dock 覆盖冲突，对齐平涂 |
| `templates/studio/preview-toolbar/bootstrap.js` | — | 可选 | — | 精修钮 class 含 `--folio`：可留 class、CSS 挖空；或删 class（行为不变） |
| `templates/studio/preview-toolbar/dock.js` | — | 可选 | — | 播放钮 `--folio` 同上；caret chevron SVG |
| `templates/studio/preview-toolbar/init-v3.js` | — | 可选 | — | 仅当挂 `dock--ink-glass` 修饰 class |
| 单测 / Playwright | — | — | 核 | 视觉无关断言应继续绿；补手测表 |

**禁止触碰（本主题）**：`longshot.js` 业务分支、`sheet.js` IA、`ai-sheet.js` 互斥逻辑、`chapter-panel.js` 功能、导出 Compose / Recipe。

---

## 2. W0 · 签核清单

- [ ] 产品确认：功能顺序零变更、只换皮范围可接受  
- [ ] 设计确认：PRD §4 token = 签核方向（B + 轻雾墨玻）；附件仅示意  
- [ ] 前端确认：改动面可收在 CSS；互斥块（`body.preview-sheet-open` / `preview-ai-sheet-open`）不重写  
- [ ] OQ 默认解确认：OQ-DIG-01 不做自适应；OQ-DIG-02 脉冲削弱保留逻辑  
- [ ] 本 IMPLEMENTATION 勾选表可用  

**出口**：PRD 状态可改为 `Conditional Go` 或 `Go · 可开 W1`。

---

## 3. W1 · P0 换皮（先删后加）

### 3.1 引入 DIG token（`dock.css` 顶部 / `.preview-toolbar__dock`）

按 PRD §4.1 写入（名称可微调，语义不可少）：

```css
/* 合同锚点 · 见 PRD-PREVIEW-DOCK-VISUAL-V5 §4 */
--dock-bg-top: rgba(22, 24, 26, 0.78);
--dock-bg-bottom: rgba(14, 16, 18, 0.72);
--dock-border: rgba(255, 255, 255, 0.10);
--dock-highlight: rgba(255, 255, 255, 0.06);
--dock-ink: rgba(245, 247, 246, 0.92);
--dock-ink-muted: rgba(245, 247, 246, 0.62);
--dock-hover: rgba(255, 255, 255, 0.08);
--dock-press: rgba(255, 255, 255, 0.12);
--dock-accent: #c4a574;
--dock-accent-hover: #ceb08a;
--dock-accent-ink: #1c1812;
--dock-accent-caret: color-mix(in srgb, #c4a574 88%, #1c1812);
--dock-active-bg: rgba(196, 165, 116, 0.16);
--dock-active-border: rgba(196, 165, 116, 0.40);
--dock-focus: rgba(196, 165, 116, 0.55);
--dock-stale: #e0a04a;
--dock-divider: rgba(255, 255, 255, 0.14);
--dock-tip-bg: rgba(18, 20, 22, 0.96);
--dock-tip-ink: #f5f7f6;
```

- [ ] token 写入 `.preview-toolbar__dock`（或 `:root` Dock 作用域）  
- [ ] 可选：容器加修饰 class `preview-toolbar__dock--ink-glass`（D-DIG-16）

### 3.2 容器 → 轻雾墨玻

**落点**：`.preview-toolbar__dock`（约 L21–50）

| 现网 | 改为 |
|------|------|
| 底不透明度 ~0.90–0.94 | `--dock-bg-top/bottom`（更透一档） |
| `blur(12px)` | `blur(16px)` |
| 阴影 `0 6px 24px …0.18` | `0 8px 28px …0.20` |
| inset 高光 `0.05` | `var(--dock-highlight)` |

- [ ] 背景 / blur / border / shadow / inset 对齐 §4.2  
- [ ] **不改** `z-index` / `pointer-events` / `position` / safe-area  

### 3.3 退役「多皮肤」（删除或挖空）

| 目标 | 现网锚点（约） | 动作 |
|------|----------------|------|
| folio 框中框 | `.dock-btn--folio` ~L430–442 | 去掉 border / 浅底 / inset；或选择器留空规则覆盖为 ghost |
| 播放 pressed 青绿 | `[aria-pressed="true"]` ~L444–448 | 改淡铜雾 `--dock-active-*` |
| 精修 done 青绿 | `--done` ~L491–502 | 改淡铜雾 |
| 帮助正圆 | `.studio-help-open--dock` ~L611–624 | `border-radius: 999px`；去独立描边；与 40×40 ghost 同形 |
| 默认薄荷绿字 | `.dock-btn` `color: #a8dcc8` ~L343 | → `var(--dock-ink)` |
| 铜光 divider | `.dock-divider` 渐变 ~L369–383 | → 实色 `var(--dock-divider)`，高 16–18px |
| 导出金渐变 | `.dock-btn--export.longshot--v3` ~L450–463 | **删除或覆盖**为平涂；注意与 ~L626–638 平涂规则级联，最终只留一套 |
| 字距广告感 | `.dock-label` `0.08em` / 字重 600 ~L397–405 | → `0.02em` / 500–550（导出可 600） |
| 内部方角 | 按钮 `8px` / 导出 `10px` | → 统一 `999px` chip / split pill（D-DIG-08） |

勾选：

- [ ] folio 默认态不可见（AC-DIG-02）  
- [ ] 帮助非正圆特例皮（AC-DIG-02）  
- [ ] divider 无铜光渐变（AC-DIG-07）  
- [ ] 计算样式：导出主钮 background 为实色铜，非 `linear-gradient(#e0ba52…)`（AC-DIG-04）  
- [ ] label letter-spacing ≤ 0.02em 量级（AC-DIG-06）  

### 3.4 Ghost 统一 + 唯一铜 CTA

- [ ] 所有非导出 dock 按钮：透明底、无默认 border、hover=`--dock-hover`、ink=`--dock-ink`  
- [ ] split：整体 `border-radius: 999px`；主区 `--dock-accent`；caret `--dock-accent-caret`；中缝保留  
- [ ] caret 字色 `--dock-accent-ink`；`letter-spacing` 与主区一致降噪  
- [ ] 目视：截掉铜色后其余按钮皮肤不可分（验收口诀）

### 3.5 W1 自检（桌面 ≥720）

| # | 检查 | ☐ |
|---|------|---|
| 1 | 顺序：? → 返回 → 播/章/修/AI → 文件夹 → 导出\|设置 | ☐ |
| 2 | 无 folio 金框、无助立正圆描边 | ☐ |
| 3 | 仅导出实心铜 | ☐ |
| 4 | 容器有模糊通透感（非纯黑铁） | ☐ |
| 5 | 字距不再「拉开广告感」 | ☐ |

**W1 出口**：AC-DIG-01～05 目视通过；可进 W2。

---

## 4. W2 · P1 状态 / tip / caret / 窄屏

### 4.1 状态色收口

| 状态 | 动作 | ☐ |
|------|------|---|
| 播放 `aria-pressed=true` | `--dock-active-bg`（+可选 border） | ☐ |
| 分章 `.is-active` | 同族淡铜雾（现网偏白底可对齐） | ☐ |
| 精修 open / `--done` | 淡铜雾，禁 `#7fcbb3` | ☐ |
| AI open（若有 pressed 类） | 同族 | ☐ |
| focus-visible | `box-shadow: 0 0 0 2px var(--dock-focus)`，全控件一致 | ☐ |
| export stale | 粗 `outline: 2px #ffb74d` → 细环 `0 0 0 1.5px var(--dock-stale)` | ☐ |
| export running | 平涂灰褐，去掉花哨渐变（caret 同步） | ☐ |
| FTUE pulse（若有） | 削弱为淡铜呼吸；禁金闪（OQ-DIG-02） | ☐ |

### 4.2 tip

**落点**：`.preview-toolbar__dock-tip` ~L289–307

- [ ] 背景 `--dock-tip-bg`（去掉偏绿 `#1a2f28`）  
- [ ] 文字 `--dock-tip-ink`  
- [ ] 延迟 300ms / 方位保持（OQ-DIG-03）

### 4.3 caret chevron（可选 JS）

**现网**：`.longshot-caret-chevron` 字符 ▾，`font-size: 24px` / `font-weight: 700`（~L144–147）

推荐（二选一）：

| 方案 | 做法 | 风险 |
|------|------|------|
| **A CSS-only** | 缩小字号至 11–12、字重 500、降低 opacity | 低 |
| **B 细 SVG**（偏好） | `dock.js` / longshot 组装处换 chevron path；热区仍 ≥40px | 需回归点击 |

- [ ] caret 视觉变细，不抢主 CTA  
- [ ] 主钮与 caret 仍为两个可聚焦控件  

### 4.4 `--folio` class 清理（可选债）

| 文件 | 现网 | 建议 |
|------|------|------|
| `dock.js` | 播放 class 含 `--folio` | W2 可删 class 字符串，或保留由 CSS 挖空 |
| `bootstrap.js` | 精修 class 含 `--folio` | 同上 |

- [ ] 决定 A：CSS 覆盖即可（更快）或 B：删 class（更干净）  
- [ ] 若改 JS：跑 `npm run tsc:preview-toolbar`

### 4.5 窄屏目视

| 断点 | 检查 | ☐ |
|------|------|---|
| ≤720 | 文件夹隐藏；label 隐藏；铜 CTA 可辨 | ☐ |
| ≤480 | 导出可收图标宽；Dock 不横向溢出 | ☐ |
| safe-area | 刘海/Home 条不裁切 | ☐ |

**W2 出口**：AC-DIG-06～10。

---

## 5. W3 · 回归与合入

### 5.1 行为回归（禁止红）

| ID | 场景 | 期望 | ☐ |
|----|------|------|---|
| R1 | 点导出主钮 | 启动导出 / 既有主路径；≤1 点击 | ☐ |
| R2 | 点设置 caret | 打开导出设置 popover | ☐ |
| R3 | 主钮文案 | 人话平台名（如「导出小红书」），非「N 个模式」优先 | ☐ |
| R4 | 开精修 Sheet | 返回可点；× 可关；导出区按现网失活 | ☐ |
| R5 | 开 AI Sheet | × 可点，不被 Dock caret 挡死 | ☐ |
| R6 | 分章面板 | 开/关/改名入口可用 | ☐ |
| R7 | 播放 | pressed 态可见；功能不变 | ☐ |
| R8 | 帮助 `?` | 仍打开帮助抽屉 | ☐ |
| R9 | 文件夹（桌面） | 仍打开既有目录/能力 | ☐ |
| R10 | `share=1` | 仍走 share-minimal，**无** v4 Dock | ☐ |

### 5.2 视觉回归样片

| 样片类型 | 建议 trip | 检查 | ☐ |
|----------|-----------|------|---|
| 深色风景封面 | 任意旅记深英雄图 | 墨玻浮在图上、图标可辨 | ☐ |
| 浅底封面 | `split-mat` / `magazine-head` 类 | 延续 AC-CSV-45 精神 | ☐ |

### 5.3 降级 / a11y

- [ ] DevTools 关掉 `backdrop-filter`：底变更实、按钮仍可读可点（AC-DIG-15）  
- [ ] `prefers-reduced-motion: reduce`：无动画依赖可用性（AC-DIG-16）  
- [ ] Tab 焦点环为淡铜、顺序合理  

### 5.4 自动化门禁

```bash
# 若未改 JS，以下应保持既有绿灯；改了 JS 则必跑
npm run tsc:preview-toolbar

# 与 Dock 相关的既有契约（按需，不强制全库）
# pytest tests/unit/web/test_preview_toolbar_v3.py
# pytest tests/unit/curation/test_cover_optimization_v4.py -k dock
```

- [ ] `tsc:preview-toolbar` exit 0（若碰 JS）  
- [ ] 既有 toolbar / dock 单测无新增失败  
- [ ] 无新增埋点、无 COPY 表改动  

### 5.5 合入说明模板（PR body 可用）

```text
## Summary
- DIG：预览 Dock 视觉 V5（墨色轻雾玻璃 + ghost 统一 + 唯一铜色导出）
- 功能顺序 / 互斥 / 导出状态机零变更

## Test plan
- [ ] AC-DIG-01～16（见 PRD §11）
- [ ] 精修 / AI Sheet 关闭路径
- [ ] 深色 + 浅色封面各 1 本
- [ ] ≤720 / ≤480 窄屏
```

**W3 出口**：可合入；PRD / 本清单状态改为「已实现 · 待狗粮」或「Closed」。

---

## 6. W4 · 可选狗粮

- [ ] 真人或内部 N≥3：主观「比旧版好看 / 不妨碍操作」  
- [ ] 记录：`docs/acceptance-records/preview-dock-visual-v5-dogfood-YYYY-MM-DD.md`  
- [ ] 决议 OQ-DIG-01（亮度自适应）keep/open  
- [ ] 可选：拆独立 `ACCEPTANCE-PREVIEW-DOCK-VISUAL-V5.md`（若团队要正式盖章）

---

## 7. 任务拆解卡（按人日排期）

| ID | 任务 | 波次 | 落点 | 依赖 | ☐ |
|----|------|------|------|------|---|
| **DIG-01** | 写入 `--dock-*` token | W1 | `dock.css` | W0 | ☑ |
| **DIG-02** | 容器轻雾墨玻 | W1 | `dock.css` | DIG-01 | ☑ |
| **DIG-03** | 挖空 folio / 帮助正圆 / 薄荷绿 | W1 | `dock.css` | DIG-01 | ☑ |
| **DIG-04** | divider 实线 + label 字距字重 | W1 | `dock.css` | DIG-01 | ☑ |
| **DIG-05** | 导出金渐变清除 + split pill 圆角/平涂 | W1 | `dock.css`（压过 longshot idle） | DIG-01 | ☑ |
| **DIG-06** | active/done/focus/stale/running 收口 | W2 | `dock.css` | DIG-03/05 | ☑ |
| **DIG-07** | tip 改墨炭 | W2 | `dock.css` | DIG-01 | ☑ |
| **DIG-08** | caret 细 chevron（CSS 或 SVG） | W2 | `dock.css` + `init-v3.js` SVG | DIG-05 | ☑ |
| **DIG-09** | 可选删除 `--folio` class 字符串 | W2 | CSS 挖空兼容（class 暂留） | DIG-03 | ☑ CSS-only |
| **DIG-10** | 窄屏目视微调 | W2 | `dock.css` @720/@480 | DIG-05 | ☑ |
| **DIG-11** | 互斥 + 导出 + 封面回归 | W3 | 手测 | W2 | ☐ |
| **DIG-12** | 门禁 / PR | W3 | CI + PR | DIG-11 | ☐ |

---

## 8. 已知坑（实施前必读）

1. **导出样式双轨**  
   `dock.css` 内同时存在金渐变规则（~L450）与平涂铜规则（~L626）。W1 必须让**最终计算样式**只剩平涂，避免「改了一处截图仍是渐变」。

2. **`--folio` 在 JS 里写死**  
   CSS 挖空即可过 AC；若删 class，勿改相邻 class 顺序与 aria。

3. **互斥靠 CSS `pointer-events`**  
   `body.preview-sheet-open` / `preview-ai-sheet-open` 块（~L68–105）**禁止重排选择器语义**；只允许改颜色无关属性之外的视觉。

4. **chapter-panel 同文件**  
   `dock.css` 后半有分章面板样式；本主题**不要**顺手改面板布局（OQ-DIG-04 共享 token 可另开）。

5. **缓存**  
   trip 输出目录可能缓存旧 CSS；验证时确认 Studio 静态资源已刷新（硬刷新 / 清 ETag）。

---

## 9. DoD（完成定义）

- [ ] PRD AC-DIG-01～16 勾选完成（或注明豁免 + 产品签字）  
- [ ] 本清单 DIG-01～12 勾选完成  
- [ ] 无功能回归（§5.1 R1–R10）  
- [ ] DOC-STATUS 本行说明更新为已实现 / Closed  
- [ ] PRD 版本记录追加实施完成注记  

---

## 10. 版本记录

| 版本 | 日期 | 说明 |
|------|------|------|
| **v0.1.0** | 2026-08-12 | 首稿：对照现网 `dock.css` 行级锚点拆 W0–W3 任务卡；待签核后开编 |
| **v0.2.0** | 2026-08-12 | W1–W2 落地：`dock.css` DIG token/墨玻/ghost/铜 CTA；`bootstrap.js` `--ink-glass`；`init-v3.js` caret SVG；W3 手测待签 |
| **v0.3.0** | 2026-08-12 | 狗粮：封面深链 C（DIG-COVER-C）；玻璃 alpha/blur 加档；`dockIconSvg` 换效果图线标；帮助改 SVG |
| **v0.4.0** | 2026-08-12 | D-DIG-22：暗陶赤试色 + 深炭弹层；契约测试跟色 |
| **v0.5.0** | 2026-08-12 | D-DIG-23 混合：弹层改回浅色；Dock 深墨玻保留 |
| **v0.6.0** | 2026-08-12 | D-DIG-24：试色 A 墨青 `#3F6F7A` |
| **v0.7.0** | 2026-08-12 | D-DIG-24：改试色 D 铅灰 `#5C636A` |
| **v0.8.0** | 2026-08-12 | D-DIG-24：铅灰加深档 D2 `#3F454C` |
| **v0.9.0** | 2026-08-12 | D-DIG-25：Tab 深字、bookends 去 sticky、侧栏 640、muted 加深 |
