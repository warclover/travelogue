# Travelogue · 封面优化 V4 产品需求文档（PRD · Icon Dock + 封面首屏）

| 属性 | 内容 |
|------|------|
| **产品代号** | Travelogue |
| **文档版本** | v1.1.0 |
| **状态** | Draft · **产品已拍板核心决策** |
| **主题代号** | 「封面优化 V4」— **Icon Dock** 释放全视窗 + **右下书名卡** 一屏完整呈现艺术相册封面 |
| **前置条件** | Preview Toolbar v3 已落地；`visual-journal` Web 封面 `cover-opening` / `cover-hero` 可用 |
| **关联文档** | [preview-cover-user-sketch-v3-wireframe.html](./wireframes/preview-cover-user-sketch-v3-wireframe.html)、[preview-cover-album-v2-wireframe.html](./wireframes/preview-cover-album-v2-wireframe.html)、[preview-toolbar-v3-wireframe.html](./wireframes/preview-toolbar-v3-wireframe.html)、[PRD-PHASE5.md](./PRD-PHASE5.md) §P5-3.7 |
| **评审来源** | 2026-06-15 页面设计 × 交互专家讨论；2026-06-15 产品草图评审拍板 |
| **验收** | `ACCEPTANCE-COVER-OPTIMIZATION-V4.md`（实施后撰写） |
| **实施清单** | `IMPLEMENTATION-COVER-OPTIMIZATION-V4.md`（实施后撰写） |
| **更新日期** | 2026-06-15 |

> **定位**
>
> Studio 预览页 v3 采用 **48px 全宽顶栏** + **全幅摄影底部叠字**（方案 D），功能完整，但首屏常 **显示不全**，且工具栏与金色 CTA 干扰封面「3 秒验货」体验。
>
> 本 PRD 定义两项配套改版：
>
> 1. **Icon Dock** — 右上角四图标胶囊坞，替代全宽顶栏；`--preview-toolbar-h: 0`。
> 2. **封面首屏 · 书名卡** — 全幅 `cover-hero` + 右下 **实心书名卡**（收纳原底部文案）；一屏内完整可读。
>
> **产品共识（五条铁律 · v1.1 拍板版）**
>
> 1. **功能等价** — 返回、导出、放映、设置不丢；任务舱、Sheet、页内控件逻辑不变。  
> 2. **主路径不弱化** — 导出仍 **≤ 1 次点击**。  
> 3. **状态可见** — running / stale / pending / 首访脉冲在图标层可感知。  
> 4. **封面优先** — 摄影占满 `100dvh`；书名卡 **不宜过大**，不压封面主体观感。  
> 5. **一屏完整** — 首屏无需滚动即可看完封面图 + 书名卡全部文案（含「进入正文」）。

---

## 1. 背景与问题

### 1.1 现状摘要

| 维度 | v3 现状 | 用户感知 |
|------|---------|----------|
| **顶栏** | 48px 全宽深绿条 + 金色导出 | 像专业软件，抢封面 |
| **封面布局** | 摄影 `absolute inset:0` + 底部渐变字层 `margin-top:auto` | 长 hook/大标题常 **撑出视窗** |
| **封面高度** | `calc(100dvh - 48px)` | 非真全屏 |
| **标题** | 顶栏 + 封面重复 | 信息冗余 |
| **底层能力** | 任务舱 + Sheet 完备 | **壳层 + 封面排版**待优化 |

### 1.2 问题陈述（P-COV-*）

| ID | 问题 | 影响 |
|----|------|------|
| **P-COV-01** | 全宽顶栏遮挡封面 | 验货冲击力下降 |
| **P-COV-02** | `--preview-toolbar-h: 48px` 扣减视窗 | 无法真全屏 |
| **P-COV-03** | 顶栏与封面标题重复 | 冗余 |
| **P-COV-04** | 金色导出在封面区抢眼 | 层级错乱 |
| **P-COV-05** | 底部叠字无高度预算 | **首屏显示不全** |
| **P-COV-06** | 无「艺术相册」装帧感 | 像电影海报叠字幕 |

### 1.3 核心判断

> **工具栏改 Dock、封面改「全幅摄影 + 右下书名卡」**，二者同 PR 或紧接发布收益最大。  
> 不采用上下分屏（方案 E）为默认——产品草图已明确 **叠层相册** 构图。  
> 标题编辑迁出顶栏；游记名称视觉 **在书名卡展示**（编辑入口另有安排）。

### 1.4 评审摘要

| 来源 | 结论 |
|------|------|
| 专家线框 | 草图构图正确；书名卡需内缩、限宽限高、字数预算 |
| 产品拍板（2026-06-15） | 材质 **A 实心**；「进入正文」**卡内右侧**；**无**右下渐变衬底；宽屏书名卡 **维持紧凑上限（见 D-COV-14）** |

---

## 2. 目标与非目标

### 2.1 产品目标

| ID | 目标 | 验收口径 |
|----|------|----------|
| **G-COV-01** | 封面全视窗 | `cover-opening` = `100dvh`（`--preview-toolbar-h: 0`） |
| **G-COV-02** | 功能等价 | §4 保全表 100% |
| **G-COV-03** | 主路径不弱化 | 导出 ≤ 1 次点击 |
| **G-COV-04** | 状态可见 | §7 图标态可辨识 |
| **G-COV-05** | Dock 轻量 | ≤ `180×44px`，不挡画面中央 |
| **G-COV-06** | 无障碍不回归 | `aria-label` + focus tooltip（P1） |
| **G-COV-07** | Share 不变 | share-minimal 路径不改 |
| **G-COV-08** | **首屏完整** | 无纵向溢出；title/hook 截断后仍一屏可读 |
| **G-COV-09** | **书名卡克制** | 卡宽 ≤ 400px；面积 ≤ 约 38vh；摄影可见 ≥ 约 62% 视窗 |

### 2.2 非目标

- 不改动任务舱 / Sheet 业务逻辑
- 不改动 Share minimal 顶栏
- 不在 P0 做 Dock 滚动变淡（P2）
- 不默认上下分屏封面（E 方案仅作历史备选）
- 不使用磨砂玻璃书名卡（B）、贴边封套（C）为默认
- **不**添加摄影区右下 `corner-gradient` 衬底（已拍板取消）
- 不在本 PRD 定义书名 **编辑** 交互（另有安排）

---

## 3. 已拍板决策（D-COV · v1.1）

### 3.1 Icon Dock

| ID | 决策 |
|----|------|
| **D-COV-01** | 形态 = 右上角 Icon Dock 胶囊 |
| **D-COV-02** | 顶栏去掉标题（方案 A） |
| **D-COV-03** | 放映保留 Dock 级 |
| **D-COV-04** | 顺序：返回 → 放映 → 设置 → 导出 |
| **D-COV-05** | 导出最右 + 金色 idle |
| **D-COV-06** | `--preview-toolbar-h: 0` |
| **D-COV-07** | P0 Dock + 状态；P1 tooltip；P2 滚动变淡 |
| **D-COV-08** | 修订 v3「48px 顶栏」铁律 |

### 3.2 封面首屏 · 书名卡（2026-06-15 拍板）

| ID | 决策 | 说明 |
|----|------|------|
| **D-COV-09** | **构图 = 全幅摄影 + 右下书名卡** | 摄影 `cover-hero` 铺满；`cover-opening__panel` 改为浮动书名卡 |
| **D-COV-10** | **材质 = A 实心** | `rgba(18, 17, 16, 0.90)`；**非**磨砂、非贴边 |
| **D-COV-11** | **「进入正文」= 卡内右侧** | 与 meta/title/hook 同卡；右对齐于卡底 |
| **D-COV-12** | **无右下渐变衬底** | 禁止 `photo-corner-grad` / 角部遮罩；靠实心卡保证可读 |
| **D-COV-13** | **左 accent 线保留** | `border-left: 3px solid #7cb89a`（图录标签感） |
| **D-COV-14** | **宽屏书名卡上限 = 400px** | **不放大**至 420px+；窄屏 `min(400px, 44vw)`；**专家裁定**：优先保护封面摄影观感 |

---

## 4. 功能保全清单

| 能力 | v3 入口 | V4 入口 | 弱化？ |
|------|---------|---------|--------|
| 返回 Studio | 顶栏 | Dock ← | 否 |
| 导出长图 | 顶栏金色钮 | Dock 导出图标 | 否 |
| 导出 running/stale/error | 顶栏态 + 任务舱 | 图标态 + 任务舱 | 否 |
| 放映 | 顶栏 | Dock ▶ | 否 |
| 编辑与设置 | ⋯ → Sheet | Dock ⋯ → Sheet | 否 |
| 首访 / pending / G1 | 原路径 | 不变 | 否 |
| 封面展示 title/meta/hook | 底部叠字 | **右下书名卡** | 否（**重组**） |
| 进入正文提示 | 底部 | **卡内右侧** | 否 |
| Share 预览 | minimal | 不变 | — |
| 顶栏改杂志名 | 顶栏 title | 移除 | 有意迁移 |

---

## 5. 方案规格 · Icon Dock

### 5.1 布局

```
┌────────────────────────────────────────────────────────────┐
│                                              ┌───────────┐ │
│                                              │ ← ▶ ⋯ [↓] │ │
│         cover-hero · 全幅摄影                 └───────────┘ │
│                                                            │
│                                    ┌──────────────────┐  │
│                                    │ 书名卡（实心）    │  │
│                                    │      进入正文 ⌄  │  │
│                                    └──────────────────┘  │
└────────────────────────────────────────────────────────────┘
                         100dvh · toolbar-h = 0
```

| 属性 | 规格 |
|------|------|
| 定位 | `fixed`；`top/right: max(12px, safe-area)` |
| 容器 | `.preview-toolbar__dock` / `.preview-toolbar--v4` |
| 背景 | `rgba(26, 47, 40, 0.82)` + `blur(10px)` |
| 圆角 | 胶囊 `999px`；内钮 `36×36px` |
| z-index | `220` |
| 放映中 | 整坞隐藏 |

### 5.2 四图标

| # | 操作 | Tooltip |
|---|------|---------|
| 1 | 返回 `/` | 返回 |
| 2 | 放映 | 放映 / 退出放映 |
| 3 | 设置 → Sheet | 编辑与设置 |
| 4 | 导出 | 导出长图 / 导出中… |

状态类继承 v3：`longshot--v3`、`menu-btn--pulse`、`menu-btn--dot`、`screenplay--v3`。

### 5.3 Tooltip（P1）

hover 300ms / `:focus-visible`；深绿 custom tooltip；触屏靠 `aria-label`。

---

## 6. 方案规格 · 封面首屏（书名卡）

> 线框：[preview-cover-user-sketch-v3-wireframe.html](./wireframes/preview-cover-user-sketch-v3-wireframe.html) · Tab ② 优化稿

### 6.1 整体构图

| 层 | 块 | 行为 |
|----|-----|------|
| L0 | `cover-opening` | `position: relative`；`min-height: 100dvh`；`overflow: hidden` |
| L1 | `cover-hero` | `position: absolute; inset: 0`；`object-fit: cover`；focal 偏左中（避让右下卡） |
| L2 | `cover-opening__panel` | **书名卡**；`position: absolute`；右下浮动；**非**全宽底栏 |
| L3 | Icon Dock | 右上；见 §5 |

**禁止**：全宽底部渐变字带（现网 D 方案）；`photo-corner-grad`；上下分屏 grid 为默认。

### 6.2 书名卡 · 实心（D-COV-10）

| 属性 | 值 |
|------|-----|
| 定位 | `right: max(20px, 3.5vw)`；`bottom: max(20px, 3.5vw)` |
| 宽度 | `width: min(400px, 44vw)`（**全断点上限 400px，不随宽屏放大**） |
| 最大高度 | `max-height: min(220px, 36vh)` |
| 内边距 | `18px 20px 14px` |
| 背景 | `rgba(18, 17, 16, 0.90)` — **实心 A** |
| 左边线 | `border-left: 3px solid var(--accent-mobile, #7cb89a)` |
| 阴影 | `0 12px 40px rgba(0,0,0,.35)` |
| z-index | `18`（低于 Dock `220`） |

### 6.3 卡内文案层级

| 元素 | 类名 | 样式 | 约束 |
|------|------|------|------|
| 元信息 | `trip-meta` / `cover-opening__place` | 9–10px；letter-spacing `.14–.18em`；uppercase；`#7cb89a` / 72% 白 | **合并一行**：`地点 · 日期范围` |
| 游记名 | `cover-opening__title` | `--font-brush`；`clamp(22px, 3.5vw, 30px)` | **line-clamp: 2** |
| 钩子 | `cover-opening__hook` | `--font-serif`；13–14px；行高 1.45 | **line-clamp: 2** |
| 进入正文 | `cover-opening__enter` | 8px；letter-spacing `.14em`；uppercase；52% 白 | 见 §6.4 |

完整 hook 可在首章前再出现；首屏只展示截断版。

### 6.4 「进入正文」· 卡内右侧（D-COV-11）

```
┌──────────────────────────────────┐
│ 东澳岛 · 2025.06.01 – 06.03      │
│ 2025东澳岛6                      │
│ 海风吹干盐粒的那刻，我们坐在…    │
│                    进入正文 ⌄   │  ← text-align: right
└──────────────────────────────────┘
```

| 属性 | 规格 |
|------|------|
| 位置 | 书名卡 **内部底行**；`text-align: right` |
| 间距 | `margin-top: 10px`（与 hook 分隔） |
| 禁止 | 左下全局浮动提示（专家稿备选，**未采纳**） |
| 可访问性 | 保持 `aria-hidden="true"`（装饰性）；滚动仍进入正文 |

### 6.5 一屏保障规则

| 规则 | 实现 |
|------|------|
| 卡不超高 | `max-height: min(220px, 36vh)` + `overflow: hidden` |
| 标题不超 2 行 | `-webkit-line-clamp: 2` |
| hook 不超 2 行 | 同上 |
| 视窗不溢出 | `cover-opening { overflow: hidden }`；首屏无纵向滚动条 |
| 摄影占比 | 书名卡 + 边距 ≤ 约 38% 视高（G-COV-09） |

### 6.6 `data-layout` 范围

| 布局 | 是否应用书名卡 |
|------|----------------|
| `web` | **是**（Studio 预览 + Web 分享） |
| `auto` | **是**（≥48rem 段同 web） |
| `mobile` | **否**（维持现有 mobile 封面，本 PRD 不改动） |

### 6.7 CSS 草案

```css
html[data-layout="web"] .cover-opening,
html[data-layout="auto"] .cover-opening {
  min-height: 100dvh;
  overflow: hidden;
}

html[data-layout="web"] .cover-opening__panel,
html[data-layout="auto"] .cover-opening__panel {
  position: absolute;
  right: max(20px, 3.5vw);
  bottom: max(20px, 3.5vw);
  left: auto;
  width: min(400px, 44vw);
  max-height: min(220px, 36vh);
  margin: 0;
  padding: 18px 20px 14px;
  background: rgba(18, 17, 16, 0.90);
  border-left: 3px solid var(--accent-mobile, #7cb89a);
  box-shadow: 0 12px 40px rgba(0, 0, 0, 0.35);
  /* 取消现网全宽渐变底 */
  background-image: none;
  text-align: left;
}

html[data-layout="web"] .cover-opening__enter,
html[data-layout="auto"] .cover-opening__enter {
  display: block;
  margin-top: 10px;
  text-align: right;
}

html[data-layout="web"] .cover-opening__title,
html[data-layout="auto"] .cover-opening__title {
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

html[data-layout="web"] .cover-opening__hook,
html[data-layout="auto"] .cover-opening__hook {
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}
```

---

## 7. 状态迁移（Dock · v3 → v4）

| 状态 | v4 要求 |
|------|---------|
| 导出 idle | 金色图标 |
| 导出 running | 灰底 + spinner；禁用放映/设置 |
| 导出 stale | 琥珀描边 |
| 设置 pulse / dot | 迁移到 Dock 设置图标 |
| 放映 active | `aria-pressed` + 高亮 |
| Sheet open | 设置钮 `aria-expanded` |

色彩铁律：金色仅导出 idle；running 非金色 disabled。

---

## 8. 布局与 CSS 变量

| 模式 | `--preview-toolbar-h` |
|------|------------------------|
| Studio v4 | `0` |
| Share | `48px`（不变） |

| 文件 | 变更 |
|------|------|
| `journal.css` | 书名卡 §6.7；`cover-opening` 全屏 |
| `preview-toolbar.css` | Dock §5；Sheet `top: 12px` |

---

## 9. 实施分期

### 9.1 P0 · Dock + 书名卡 + 状态（推荐同迭代）

| 项 | 内容 |
|----|------|
| Dock | §5 DOM/CSS/状态迁移 |
| 书名卡 | §6 `cover-opening__panel` 实心卡；取消底栏渐变 |
| 标题 | 移除顶栏 `title-wrap` |
| 变量 | `--preview-toolbar-h: 0` |
| 测试 | 更新 toolbar 测试 + 封面一屏快照/人工 AC |

### 9.2 P1 · 体验补全

| 项 | 内容 |
|----|------|
| Dock tooltip | §5.3 |
| Sheet focus 归还 | 设置图标 |
| 验收文档 | `ACCEPTANCE-COVER-OPTIMIZATION-V4.md` |

### 9.3 P2 · 可选

| 项 | 内容 |
|----|------|
| Dock 滚动变淡 | 滚过封面后 opacity 降低 |
| 触屏长按 tooltip | 可选 |

---

## 10. 工程映射

| 模块 | 路径 | 变更 |
|------|------|------|
| 工具栏 | `templates/studio/preview-toolbar.js` | v4 Dock |
| 工具栏样式 | `templates/studio/preview-toolbar.css` | Dock |
| **封面** | `templates/visual-journal/journal.css` | **书名卡 §6** |
| 块结构 | `cover-opening.hbs` | **无变更**（仅 CSS 重组 panel） |
| 任务舱/Sheet | 原路径 | 无变更 |
| 测试 | `tests/test_preview_toolbar_v3.py` 等 | 增补封面 AC |

---

## 11. 验收标准（AC-COV）

### 11.1 P0 · Dock

| ID | 则 |
|----|-----|
| AC-COV-01 | 无全宽顶栏；右上四图标坞 |
| AC-COV-02 | Studio 预览 `--preview-toolbar-h: 0`；封面可占满 `100dvh` |
| AC-COV-03 | 导出长图 **≤ 1 次点击**（Dock 导出图标） |
| AC-COV-04 | 导出 idle：金色图标（`longshot--v3`） |
| AC-COV-05 | 导出 running：灰底 + spinner；放映/设置禁用 |
| AC-COV-06 | 导出 stale：琥珀描边；任务舱同步提示 |
| AC-COV-07 | 放映保留 Dock 级；`aria-pressed` 切换 |
| AC-COV-08 | 放映 active 时 Dock 不可见（`visibility: hidden`） |
| AC-COV-09 | 设置 → Sheet 四 Tab（文字/结构/排版/高级） |
| AC-COV-10 | 首访 pulse / pending dot 迁移到 Dock 设置图标 |
| AC-COV-11 | Share 预览（`?share=1`）仍为 `share-minimal` 顶栏 |
| AC-COV-12 | 任务舱 running/success/stale 与 Dock 图标态一致 |

### 11.2 P0 · 封面书名卡

| ID | 给定 | 当 | 则 |
|----|------|-----|-----|
| **AC-COV-30** | Studio 预览 `data-layout=web` | 首屏加载 | `cover-opening` 高度 = `100dvh`（±1px） |
| **AC-COV-31** | 同上 | 观察布局 | 摄影全幅；右下实心书名卡；**无**全宽底栏渐变 |
| **AC-COV-32** | 同上 | 观察书名卡 | 宽 ≤ `min(400px, 44vw)`；高 ≤ `min(220px, 36vh)` |
| **AC-COV-33** | 长标题+长 hook | 首屏 | 无纵向滚动条；title/hook 各 ≤2 行 |
| **AC-COV-34** | 同上 | 「进入正文」 | 位于书名卡 **内底右对齐** |
| **AC-COV-35** | 同上 | 摄影区 | **无** corner-gradient / 角部遮罩 |
| **AC-COV-36** | 宽屏 ≥1280px | 书名卡宽度 | ≤ **400px**（不放大） |
| **AC-COV-37** | `data-layout=mobile` | 加载 | 封面布局 **不变**（非本次范围） |

### 11.3 P1 增补

| ID | 则 |
|----|-----|
| AC-COV-20～22 | Dock tooltip / focus |
| AC-COV-40 | meta 合并单行显示 |

---

## 12. 风险与缓解

| 风险 | 缓解 |
|------|------|
| 实心卡在亮图可读性 | 90% 不透明 + 左 accent + 阴影；亮图 trip 人工抽测 |
| 书名卡挡摄影主体 | 限宽 400px + 右下定位 + focal 偏左 |
| 无渐变后暗图字对比 | 实心卡自包含，不依赖摄影衬底 |
| hook 截断 | 正文前可再展示完整 hook |
| Dock + 书名卡同屏 | z-index 分层；Dock 右上、卡右下 |

---

## 13. 开放项

| 项 | 说明 |
|----|------|
| 书名 **编辑** 入口 | 另有安排；Sheet「文字」Tab 仍保留杂志名字段 |
| 杂志名保存 → stale | 编辑入口变更时须保留 `travelogue:copy-saved` |

---

## 14. 修订记录

| 版本 | 日期 | 变更 |
|------|------|------|
| v1.0.0 | 2026-06-15 | 初稿：Icon Dock |
| v1.1.0 | 2026-06-15 | 增补 §6 封面书名卡；拍板 D-COV-09～14；AC-COV-30～37；P0 合并封面实现 |

---

## 附录 A · 与 v3 / 线框差异

| 项 | v3 / 旧线框 | V4 |
|----|-------------|-----|
| 顶栏 | 48px 全宽 | Icon Dock |
| 封面 | 底栏渐变叠字 | 右下实心书名卡 |
| 进入正文 | 底栏左对齐 | **卡内右侧** |
| 角部渐变 | 可有 | **禁止** |
| 书名卡宽 | — | **max 400px，宽屏不放大** |

## 附录 B · 用户故事

| ID | 作为 | 我想要 | 以便 |
|----|------|--------|------|
| US-COV-01 | 分享者 | 首屏看全封面摄影和书名 | 3 秒验货 |
| US-COV-05 | 分享者 | 一屏内读完 hook 摘要 | 不用滚动找信息 |
| US-COV-02 | 分享者 | 一键导出 | 验货后出长图 |
| US-COV-06 | 读者 | 封面像艺术相册而非软件截图 | 沉浸翻册 |
