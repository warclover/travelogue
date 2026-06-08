# Travelogue · 页面优化 PRD（Book Surface · 成书视觉面）

| 属性 | 内容 |
|------|------|
| **产品代号** | Travelogue |
| **文档类型** | 产品 PRD · 视觉面 / Web 阅读面优化 |
| **文档版本** | v0.5 |
| **状态** | **Approved with Revisions（评审会通过 · 2026-06-08）** |
| **评审记录** | 产品 / 首席视觉 / 工程 / Curate / QA / Phase 18 集成 · 有条件采纳 → v0.5 修订落地 |
| **代号** | Book Surface Program（BSP） |
| **更新日期** | 2026-06-08 |
| **前置条件** | Phase 16 LTE + screens 引擎已上线；`export.reading` / `default_hybrid` profile 可用 |
| **关联文档** | [ROADMAP-PHASE18-BOOK-QUALITY.md](./ROADMAP-PHASE18-BOOK-QUALITY.md) · [PRD-PHASE18-layout-effect-improvement.md](./PRD-PHASE18-layout-effect-improvement.md) · [PRD-EXPERIENCE.md](./PRD-EXPERIENCE.md) · [PRD-EXPERIENCE-附录B-滚动动效.md](./PRD-EXPERIENCE-附录B-滚动动效.md) · [PRD-EXPERIENCE-附录C-Folio版式.md](./PRD-EXPERIENCE-附录C-Folio版式.md) · [web端模板.prd](./web端模板.prd) · [web-screens-ab-checklist.md](./web-screens-ab-checklist.md) |
| **主验收案例** | `trips/demo-d66fe642a9` · **仙本那精选全集**（224 素材 · 183 屏 · 2026-06-08 生成） |
| **次级回归案例** | `trips/linzhi` · ultra-wide 原生比例专项（T3 tier） |
| **Dogfood 视口（产品负责人）** | 笔记本 **2880×1920（3:2 · 243 PPI）** · 外接 **2560×1440（16:9）** |

> **定位**
>
> 本 PRD 解决 Web 游记预览的**成书视觉面**问题：从「技术正确的 16:9 / 原生比例舞台」升级为「用户愿意分享的杂志级阅读面」。  
> 不替代 Phase 18 版式算法（LSE / 求解器 / 模板 SKU），而是为渲染与阅读体验建立**视觉宪法**与**可验收的版面契约**。

---

## 1. 背景与问题

### 1.1 现象（Dogfood · 仙本那精选全集 · 2026-06-08）

**案例**：`trips/demo-d66fe642a9` · 224 素材 / 180 进排版 / 183 屏（含 36 个 breath-pause）· `cinematic + folio lite`

| ID | 用户感知 | 技术表现 | 关联实现 |
|----|----------|----------|----------|
| **BSP-P-01** | 预览「不是全屏」，**照片两侧有空白** | 103 屏 `screen-full-frame` 固定 `--screen-aspect: 16/9` + **`contain`**；3:2 / 4:3 横图在 16:9 槽内左右信箱 | `screen_planner._fits_for_screen` · `context.py` · `journal-screens.css` |
| **BSP-P-02** | 一屏重量感不稳定；**3:2 / 16:10 笔记本屏更空** | 舞台仅按**版心宽度**推高度，未按**视口宽高比**自适应；越高型视口（3:2 > 16:10 > 16:9）纵向浪费越大 | `journal-screens.css` · 缺 viewport-fit 层 |
| **BSP-P-03** | breath 间隔符异位（**本案例可稳定复现**） | 36 个 `breath-pause-screen` 全宽 border；`layout-screen` bleed 限宽 | `breath_pauses.py` · `journal-screens.css` |
| **BSP-P-04** | 照片浮在分隔线上 | folio `box-shadow` + cinematic `breath-image` lift 越过屏缝 | `breath.css` · `breath-image.js` |
| **BSP-P-05** | 精选全集像「相册目录」而非「海岛叙事」 | 开场 Plate 后接 `3×3` 九宫格，随后 **4 连 full-frame contain** 循环；pattern 单调 | `screen_planner` · curate 路径 |
| **BSP-P-06** | 编辑预览与成品阅读混淆 | Studio Preview 用 `cinematic + folio lite` + plate meta 全覆盖 | `reading_profile.py` · `preview-toolbar` |

**仙本那素材结构**（供验收对照）：

| 维度 | 数据 |
|------|------|
| 画幅 | landscape 174 · portrait 42 · panorama 8 |
| Pattern 占比 | `screen-full-frame` 103 · `screen-breath-pause` 36 · `screen-landscape-1` 20 · 其余 24 |
| full-frame fit | **100% `contain`**（全部带 blurred-fill） |
| 最大连续 full-frame | 4 屏 / 组，全册多组重复 |

### 1.2 根因判断（首席视觉结论）

当前系统是 **四套未对齐的契约** 叠加：

1. **视口契约**：默认隐含 16:9 外接屏；未对 **3:2 / 16:10 笔记本** 等常见比例做 **双向自适应**（宽锚定 vs 高锚定）。
2. **比例契约**：`screen-full-frame` 强制 16:9 + contain，与「版心内全出血」北极星冲突；`screen-landscape-1` 则走原生比例——**同册两套逻辑打架**。
3. **宽度契约**：照片承载面与 `breath-pause-screen`（36 处）未共享 content rail。
4. **模式契约**：Studio 编辑面与 Reader 阅读面共用 profile；精选全集 dogfood 应用 **Reader 级** 标准审视。

**核心矛盾**：产品口头「全屏」= **在当前显示器宽高比下填满版心视域**；实现仍是 **固定 16:9 槽 + contain 保真** 或 **仅宽度锚定 native AR**。方向应对齐北极星，但需补 **Viewport-Aware Presentation** 层。

### 1.3 与 Phase 18 的关系

| 层级 | Phase 18 BQP | 本 PRD（页面优化） |
|------|----------------|-------------------|
| 选片 / 结构 / 版式算法 | WS-1 / WS-2 / WS-3 | 不替代 |
| 渲染 CSS / 阅读 profile / 动效预算 | 间接依赖 | **主战场** |
| 盲评门禁 | Layout Blind Win Rate | 提供 **Surface 截图验收** 补充维度 |

本 PRD 作为 Phase 18 **WS-2 版式** 的**视觉面落地附件**，优先 P0/P1 项可在 IG 前独立交付。

---

## 2. 视觉北极星

### 2.1 一句话原则（已采纳 · 待工程化）

> **Web 阅读 = 版心（content rail）内的全出血照片；呼吸节奏 = 版心内的停顿，不是浏览器级的分割线。**

### 2.2 视口自适应原则（v0.2+ · 已采纳）

> **舞台尺寸必须同时感知版心宽度与视口宽高比，而非默认 16:9 外接显示器。**

#### 2.2.1 视口分档（宽 ÷ 高）

视口**越高**（数值越小），仅用宽度推高度时舞台越扁、上下空白越多：

```text
16:9  ≈ 1.78   （同宽下视口最「矮」· 外接显示器主流）
16:10 = 1.60   （纵向比 16:9 多 ~11%）
3:2   = 1.50   （纵向比 16:9 多 ~19% · 笔记本高频）
```

| 视口类型 | 宽高比 | 典型设备 | 设计含义 |
|----------|--------|----------|----------|
| 外接 / 游戏屏 | 16:9 ≈ 1.78 | 1920×1080、2560×1440 | 宽、高接近平衡；现网默认隐含此档 |
| 创作者笔记本 | 16:10 = 1.6 | 1920×1200、2560×1600 | 仅宽锚定会系统性偏扁 |
| **生产力笔记本（Dogfood 主基准）** | **3:2 = 1.5** | **产品负责人：2880×1920（2.8K · 243 PPI）**；同类：3000×2000、2256×1504 | **最高型视口**；最需 `vh` 锚定；与大量 3:2 照片有天然亲和 |
| 外接显示器（Dogfood 回归） | 16:9 ≈ 1.78 | **产品负责人：2560×1440**；同类：1920×1080 | 宽锚定易先触顶；与笔记本对比可验证双向自适应 |
| 超宽屏 | ≥2.0 | 3440×1440 | 纸边留白扩大；更依赖 content rail |

**Dogfood 双视口（已登记）**：

| 设备 | 分辨率 | 比例 | PPI | 角色 |
|------|--------|------|-----|------|
| **笔记本（主）** | **2880 × 1920** | **3:2** | **243** | **P0 验收 · 日常 Studio 预览** |
| **外接显示器** | **2560 × 1440** | **16:9** | ~109–121（视尺寸） | **P1 回归 · 双屏对照** |

同一本游记（仙本那）须在 **两块屏各截图一轮**；不得出现「仅外接屏好看、笔记本偏扁」的反向塌陷。

#### 2.2.2 工程语义

对齐 `screenplay.css` 的 contain-maximize 思路，Web 阅读面增加连续变量，**禁止**用离散 breakpoint 假装覆盖所有屏：

```text
--viewport-ar: calc(100vw / 100dvh)   /* 运行时视口宽高比 */

给定素材有效比例 ar，版心宽 rail，视口 vw×vh，目标重量 weight：
  width  = min(rail, vw, vh × ar)
  height = min(vh × weight, width / ar)
  weight ∈ [0.55, 0.72]   // Screen Weight 目标带；3:2 视口允许触顶 weight 上限
```

**实现形态（工程约定）**：

- 在 `layout-screen` 上增加 modifier：**`layout-screen--viewport-fit`**（或等价 `data-viewport-fit="on"`），由 Render 按 presentation tier 输出。
- **viewport-fit 屏**：用 §2.2.2 的 `min()` 几何覆盖 `--screen-aspect` 推导尺寸；与现网 `width:100% + aspect-ratio` **互斥**（同一屏不同时生效）。
- **非 viewport-fit 屏**：暂维持现逻辑，直至 BSP-2 全量迁移。
- 作用域：`html[data-layout-engine="screens"]` 且 Web draft 面；mobile / longshot 不适用。

**分档行为（预期）**：

| 视口 | 谁先触顶 | 视觉效果 |
|------|----------|----------|
| **2880×1920（3:2 笔记本）** | **`vh × weight` 常先触顶** | 舞台变高 · 海岛横图更饱满 · 与 3:2 素材同构时接近「满屏」 |
| **2560×1440（16:9 外接）** | `rail` 或 `vw` 常先触顶 | 同册应仍全出血，但单屏高度略低于 3:2 笔记本属正常 |
| 16:10 | `vh` 与 `rail` 交替触顶 | 介于 3:2 与 16:9 之间 |
| 21:9 超宽 | `rail` 触顶 · 纸边显形 | 版心杂志感 |

#### 2.2.3 3:2 视口 × 3:2 照片（仙本那多数横图）

当 `ar_photo ≈ 1.5` 且 `ar_viewport ≈ 1.5` 时，viewport-aware 尺寸应使**单张 hero 接近整屏 contain-maximize**，无需 16:9 槽内左右信箱。这是仙本那 full-frame 改版的高收益路径。

**呈现优先级**：**presentation tier + viewport-fit > 单一 native `--screen-aspect`**（避免 T1 与 full-frame 规则打架）。

#### 2.2.4 高 PPI 笔记本（243 PPI · 2880×1920）

逻辑分辨率 2880×1920 在 243 PPI 下 CSS 视口通常为 **1440×960 CSS px**（`devicePixelRatio = 2`），`100dvh` 仍按逻辑高度计。注意：

- **不要用物理像素写死舞台**。
- **Playwright / CI 统一配置**：`viewport: { width: 1440, height: 960 }` · `deviceScaleFactor: 2`（与 CSS 布局一致；等价物理 2880×1920）。
- 高 PPI 下 folio 小字 / plate meta 更易显杂；**Reader 模式**在笔记本上收益更高。
- `srcset` 应能喂饱 2800px 级版心宽（仙本那已配 1600w/3200 sizes，基本够用）。

**禁止**：全局写死 `--screen-aspect: 16/9` 作为唯一舞台（仙本那 full-frame 现状）。

### 2.3 「一屏」定义（必须拍板）

| 模式 | 「一屏」填满什么 | 典型场景 |
|------|------------------|----------|
| **A · 视口沉浸** | 视口高度为主锚（55–75vh 画面重量） | Reader View · 分享前终检 |
| **B · 版心杂志** | `--content-rail` 宽度内排版，允许超宽屏纸边 | Folio · 精装书感 |
| **C · 素材保真** | 槽位内不压扁；允许 cover 裁切，禁止信箱压扁 | 所有模式底层 |

**默认组合**：Reader = **A+B+C+视口自适应**；Studio Preview = B+C（可显示 plate meta，不追求 A）。

### 2.4 非目标

| ID | 非目标 |
|----|--------|
| **NG-BSP-01** | 不推翻 LTE 模板几何与 `screens[]` 数据结构 |
| **NG-BSP-02** | 不在本 PRD 首版改动 LSE / MCS 求解逻辑 |
| **NG-BSP-03** | 不强制所有横图回到**单一**固定 16:9 槽（但允许按 tier 选用 16:9 / 21:9 等**视口感知**阶梯） |
| **NG-BSP-04** | 不引入用户手动拖拽版心或逐屏确认流 |

---

## 3. 目标

| ID | 目标 | 衡量 |
|----|------|------|
| **G-BSP-01** | Content Rail 统一 | 照片屏、breath、章分隔、屏间 rhythm **同宽同轨** |
| **G-BSP-02** | Aspect 分层呈现 | T1 full-frame **无左右信箱**；T3 ultra-wide 不再「细带屏」 |
| **G-BSP-03** | 节奏视觉连续 | 屏间无「线穿帮、图悬浮」；盲评「成书感」≥ 4/5 |
| **G-BSP-04** | 模式分离 | Studio Preview ≠ Reader View 的配置与动效预算可切换 |
| **G-BSP-05** | 可验收 | 8 本 golden trip 有固定截图点位与 pass/fail 表 |

---

## 4. Book Surface Spec（成书视觉宪法）

以下五条为工程实现的**权威约束**；具体数值可灰度，但语义不可删。

### 4.1 Content Rail（版心轨）

| 项 | 规范 |
|----|------|
| **变量** | `--content-rail: var(--bleed-width)`（首期等价；后续可独立 tuning） |
| **适用块** | `layout-screen`、`breath-pause-screen`、`chapter-separator`、屏间 rhythm 容器 |
| **规则** | `width: 100%; max-width: var(--content-rail); margin-inline: auto;` |
| **禁止** | 节奏/分隔元素使用 `100vw` 或无视 bleed 的全宽 border |

**验收**：任意相邻两 `layout-screen` 与其间 `breath-pause-screen` 的 `getBoundingClientRect().width` 差 ≤ 1px。

### 4.2 Screen Weight（屏重量 · 视口双向约束）

按素材 **Aspect Presentation Tier** 决定舞台策略（见 §5）。目标区间：

| Tier | 目标占视口高度 | 备注 |
|------|----------------|------|
| Standard | 45–65vh | 常规横图 · 3:2 / 16:9 |
| Wide | 50–68vh | 21:9 / 2:1 槽 |
| Ultra-wide | 55–72vh | **高度锚定**，非 native 扁条 |
| Portrait（单张） | 65–85vh | 沿用现有人物竖屏 hint 策略 |

**视口基准矩阵**（人工验收必测 · 按优先级）：

| 优先级 | 分辨率 | 比例 | PPI / 备注 | 用途 |
|--------|--------|------|------------|------|
| **P0** | **2880 × 1920** | **3:2** | **243 PPI · DPR≈2 · 逻辑 ~1440×960** | **产品负责人笔记本 · Studio 日常预览** |
| **P1** | **2560 × 1440** | **16:9** | 外接屏 | **产品负责人外接 · 双屏回归** |
| P2 | 1920×1200 | 16:10 | — | 创作者笔记本泛化 |
| P2 | 1920×1080 | 16:9 | — | 主流外接屏泛化 |
| P3 | 3440×1440 | 21:9 | — | 超宽纸边 |

**vh 测量规范（AC 必遵）**：

| 项 | 规范 |
|----|------|
| **浏览器状态** | 最大化窗口 · 仙本那 `index.html` · Studio **preview-toolbar 展开**（与日常 Dogfood 一致） |
| **测量对象** | `layout-screen` 内 **`img.layout-slot__img` 可视区高度**（不含 `folio-plate-meta` / plate caption） |
| **分母** | `window.innerHeight`（逻辑 px）；不用含浏览器 chrome 的物理像素 |
| **信箱判定** | 槽内 img 渲染宽度 / 槽宽度 ≥ **0.98**（自动化可脚本化） |

**验收（仙本那 · 双视口）**：

- `screen-full-frame` 横图（3:2 类）在 **P0（1440×960@2x）** 下：照片可视区域高度 ≥ **62vh**，**左右信箱 = 0**。
- 同一屏在 **P1（2560×1440）** 下：高度 ≥ **58vh**，全出血；可略矮于 P0，但不得出现左右信箱。
- **跨视口**：P0 必须比 P1 更饱满或持平，不得反向塌陷。

### 4.3 Rhythm Grammar（节奏语法）

| 元素 | 形态 | 颜色来源 |
|------|------|----------|
| 屏间 breath | **隙（gap）**，非横线 HR | `--screen-tone` → `--folio-paper` 柔和过渡 |
| breath 标签「···」 | 可选；`clamp(6px, 0.9vh, 10px)` 级低对比 | `--folio-ink` 38% |
| 屏底阴影 | 仅 `layout-screen--plate` / featured | 普通 `screen-landscape-1` 连续页禁用 `box-shadow` 分隔 |
| 屏间距 | 统一 token：`--screen-rhythm-gap: clamp(8px, 1vh, 16px)` | 替代零散 `12px` margin + breath border 叠层 |

**验收**：连续 10 屏滚动无「双线分隔」；breath 处无全宽 border 穿帮。

### 4.4 Motion Budget（动效预算）

| 场景 | 位移上限 | scale 上限 | 屏缝 overlap |
|------|----------|------------|--------------|
| Reader · cinematic | 8px | 1.02 | **禁止** |
| Studio Preview · cinematic | 12px | 1.035 | **禁止** |
| breath / rhythm 区域 | 0 | 1 | disable scrub |

**规则**：`breath-image` 仅作用于 slot 内；`<img>` transform 不得使像素越过 `layout-screen` 底边进入 rhythm gap。

**破坏性变更说明**：现网 cinematic `breath-image` lift 最大约 **20px** / scale **1.055**；本 PRD 收紧后 Reader/Studio 预算如上表——属 **有意识的体验变更**，需在 BSP-1 发布说明中注明。

**验收**：屏缝处截图叠加比对，上层照片不透明像素不覆盖下层 rhythm 区域 > 2px。

### 4.5 Surface Split（阅读面拆分）

| Surface | profile 建议 | folio | breath | plate meta |
|---------|--------------|-------|--------|------------|
| **Studio Preview** | `studio_preview`（新） | lite | soft / 关 | 显示 |
| **Reader View** | `reader_immersive`（新） | off 或 lite（无 plate） | cinematic（克制） | 隐藏 |
| **Share / ZIP** | `performance` | off | off | 隐藏 |

首期可在 toolbar 增加「阅读视图」切换，不必改 URL 路由。

---

## 5. Aspect Presentation Tier（比例呈现分层）

### 5.1 分档定义

| Tier | 宽高比 w/h | 典型素材 | 舞台策略 |
|------|------------|----------|----------|
| **T1 · Standard** | 1.08 – 2.0 | 3:2、4:3、16:9 裁切 | 原生 `--screen-aspect` 或吸附阶梯 |
| **T2 · Wide** | 2.0 – 2.8 | 21:9 感 | 固定槽 `21/9` 或 `2/1` + `cover` |
| **T3 · Ultra-wide** | ≥ 2.8 | 3000×680 类全景条 | **vh 锚定舞台** + `cover` + focal |

### 5.2 仙本那类案例：full-frame 策略修订（P0 · 本册主矛盾）

**现状**（`demo-d66fe642a9`）：103 屏 `screen-full-frame` · 固定 `16/9` · **100% contain** → 3:2 / 4:3 海景观在槽内**左右信箱**，与「全出血」北极星直接冲突。

**目标**：

| 条件 | fit | 舞台 |
|------|-----|------|
| 风景横图（仙本那主体） | `cover` | viewport-aware（§2.2） |
| 人物正脸 / 合影 | `contain` + blur-fill | 保持现策略 |
| 比例 ∈ [1.7, 1.85]（近 16:9） | `cover` 优先 | 可吸附 16:9 |

**人物判定（工程）**：复用现有 **`portrait_fit_for_asset`**（与 `screen-portrait-1` 同路径）；风景默认 `cover`，人物 retain `contain`。

**原则**：精选海岛游记的 full-frame 应以 **沉浸** 为先；contain 仅服务人脸安全，而非默认。

### 5.3 T3 渲染策略（林芝类 ultra-wide · 次级回归）

**现状**：`--screen-aspect: 3000 / 680` → 舞台极扁。

**目标**：

```text
舞台：min-height: clamp(52vh, 60dvh, 72vh)
宽度：min(content-rail, vw, vh × ar)
图片：object-fit: cover；focal 来自 asset.focalPoint
```

**原则**：保真 ≠ 舞台像素比等于素材像素比；**轻微裁切换节奏重量**是杂志排版的正当交易。

### 5.4 精选全集叙事节奏（仙本那专项）

> **范围说明（评审会决议）**：本节属 **Phase 18 WS-2 / curate 叙事重排**，**不阻塞 BSP-1 / BSP-1.5**。本 PRD 记录视觉预期；落地见 [PRD-PHASE18-layout-effect-improvement.md](./PRD-PHASE18-layout-effect-improvement.md) Editorial Re-ranker 与 `screen_planner` 后续迭代。BSP 仅交付 §4.3 breath 形态与 §5.2 呈现修正。

| 现状问题 | 建议 | BSP 范围 |
|----------|------|----------|
| 屏 2 即 `3×3` 九宫格 | 精选开篇应 **1–2 屏 hero full-bleed**，九宫格延后至「展开段」 | Phase 18 |
| 4 连 full-frame 循环 | 插入 `landscape-2` / 跨页 spread，打破目录感 | Phase 18 |
| 36 breath-pause | 保留节奏但改为 **gap 隙**（§4.3），且与 content rail 对齐 | **BSP-1** |
| plate meta 全覆盖 | Reader 模式隐藏；精选 dogfood 用 Reader 标准验收 | **BSP-3** |

### 5.5 决策落点

| 模块 | 职责 |
|------|------|
| **Curate / screen_planner** | 为 screen 标注 `presentationTier`（或由 aspect kind 推导） |
| **Render / context.py** | 按 tier 写 `--screen-aspect` 或 `--screen-min-height` + 槽策略 |
| **CSS / journal-screens.css** | tier 对应 overlay 规则 |

首版可仅在 Render 层由 `nativeWidth/nativeHeight` 推导 tier，无需改 trip schema。

---

## 6. 需求明细（按优先级）

### 6.1 P0 · Content Rail 对齐（必须 · Sprint BSP-1）

| ID | 需求 | 文件触点 |
|----|------|----------|
| **R-BSP-P0-01** | `breath-pause-screen` 增加与 `layout-screen` 相同的 `max-width` + 居中 | `journal-screens.css` |
| **R-BSP-P0-02** | `chapter-separator` 同步 content rail | `journal-screens.css` |
| **R-BSP-P0-03** | 移除普通屏 `folio lite` 底部分割 `box-shadow`；保留 plate | `journal-screens.css` |
| **R-BSP-P0-04** | breath-pause 去掉全宽 `border-top/bottom`；改为 gap + tone 过渡 | `journal-screens.css` |
| **R-BSP-P0-05** | `breath-image` 在 rhythm 邻域禁用 overlap（clip 或缝处 scrub=0）；lift/scale 收到 §4.4 预算 | `breath-image.js` |

**完成定义（DoD）**：仙本那 `demo-d66fe642a9` · **S3**（breath-pause index 5/10 与相邻屏同宽）· 屏缝无「线穿帮、图压线」。

### 6.2 P0.5 · full-frame 呈现修正（必须 · Sprint BSP-1.5）

> 评审会决议：仙本那主矛盾（两侧信箱）仅靠 P0 CSS **无法**消除，须联动 curate fit + render 舞台。

| ID | 需求 | 文件触点 |
|----|------|----------|
| **R-BSP-P0.5-01** | **full-frame 风景默认 `cover`**；人物 retain `contain`（`portrait_fit_for_asset`） | `screen_planner._fits_for_screen` |
| **R-BSP-P0.5-02** | `screen-full-frame` 不再无条件写死 `--screen-aspect: 16/9`；按 tier 输出 viewport-fit 或有效 AR | `context.py` |
| **R-BSP-P0.5-03** | 已生成 trip **重跑 render**（无需全量 curate）即可验证；可选 `应用排版` 刷新 fit | Studio pipeline |

**完成定义（DoD）**：仙本那 **S2**（screen-index 6–9）在 **P0 视口**下无左右信箱 · 照片高度 ≥ 62vh。

### 6.3 P1 · Viewport-fit 与自动化（高优 · Sprint BSP-2）

| ID | 需求 | 文件触点 |
|----|------|----------|
| **R-BSP-P1-01** | **`layout-screen--viewport-fit`** + `--viewport-ar` / min() 尺寸（§2.2.2） | `journal-screens.css` · `context.py` · 参考 `screenplay.css` |
| **R-BSP-P1-02** | Playwright：**AC-BSP-01/02/02a/02b** + 仙本那 S1/S3/S5 | `tests/` · `demo-d66fe642a9` |
| **R-BSP-P1-03** | 更新 checklist · P0 **1440×960@2x** + P1 **2560×1440** 双视口必测 | `docs/web-screens-ab-checklist.md` |

### 6.4 P1b · T3 ultra-wide 回归（可并行 · Sprint BSP-2b）

| ID | 需求 | 文件触点 |
|----|------|----------|
| **R-BSP-P1b-01** | T3 ultra-wide vh 锚定（林芝回归） | `context.py` · `journal-screens.css` |

**完成定义（DoD）**：林芝 asset-026 单屏 · 1920×1080 下高度 ≥ 52vh（**AC-BSP-02c**）。

### 6.5 P2 · 阅读面拆分（中优 · Sprint BSP-3）

| ID | 需求 | 文件触点 |
|----|------|----------|
| **R-BSP-P2-01** | 新增 `studio_preview` / `reader_immersive` profile（**须同步修订** [PRD-EXPERIENCE-附录B](./PRD-EXPERIENCE-附录B-滚动动效.md) / `experience-matrix.yaml`） | `reading_profile.py` |
| **R-BSP-P2-02** | Preview toolbar「阅读视图」切换 | `preview-toolbar.js` |
| **R-BSP-P2-03** | Reader 模式隐藏 plate meta、收紧动效 | `journal.hbs` · `breath.css` |

### 6.6 P3 · 规范沉淀（持续）

| ID | 需求 |
|----|------|
| **R-BSP-P3-01** | 将 §4 Book Surface Spec 同步进 `TEMPLATE-visual-journal.md` |
| **R-BSP-P3-02** | 自动化截图回归（Playwright）· 8+1 本 golden trip 固定点位 |
| **R-BSP-P3-03** | Phase 18 盲评表增加「Surface 连续性」维度 |
| **R-BSP-P3-04** | `.cache/book-quality/` 增 surface 截图报告模板（仙本那 S1–S5 点位） |

---

## 7. 验收标准

### 7.1 自动化 / 可脚本化

| AC ID | 条件 |
|-------|------|
| **AC-BSP-01** | 同一 chapter 内所有 `layout-screen` 与 `breath-pause-screen` 宽度一致（±1px） |
| **AC-BSP-02** | 仙本那 full-frame 横图在 **P0（1440×960@2x）** 下高度 ≥ 62vh · 无左右信箱（img 宽/槽宽 ≥ 0.98） |
| **AC-BSP-02a** | 同上屏在 **P1（2560×1440）** 下高度 ≥ 58vh · 无左右信箱 |
| **AC-BSP-02b** | P0 画面重量 ≥ P1（同屏对比，不得笔记本更扁） |
| **AC-BSP-02c** | T3 单屏（林芝 asset-026）在 1920×1080 下照片区域高度 ≥ 52vh |
| **AC-BSP-03** | `prefers-reduced-motion: reduce` 下无 transform overlap |
| **AC-BSP-04** | Reader profile 下无 `folio-plate-meta` 可见 |

### 7.2 人工盲评（Golden Dogfood · 8+1 本）

参照 [ROADMAP-PHASE18-BOOK-QUALITY.md](./ROADMAP-PHASE18-BOOK-QUALITY.md) §2.3 代表 trip 集。  
**BSP 主 Dogfood**：`demo-d66fe642a9`（仙本那精选全集）为 **第 9 本 · Surface 专项**，IG 前必评；与固定 8 本并行，不替换原 8 本序号。

| 维度 | 问题 | 通过线 |
|------|------|--------|
| **成书连续性** | 滚动时是否像翻杂志而非网页？ | ≥ 4/5 |
| **屏重量** | 横图是否「站得住」一屏？ | ≥ 4/5 |
| **分隔干净** | 是否见到错位线 / 图浮线？ | 0 例/blocker |
| **分享意愿** | 是否愿意发给朋友？ | ≥ 4/5 |

### 7.3 仙本那精选全集定点截图（最小集 · `demo-d66fe642a9`）

| 点位 | 位置 | 检查 |
|------|------|------|
| S1 | Plate · asset-006 | 版心全出血；**2880×1920** 下重量 ≥ 62vh |
| S2 | screen-index 6–9（4 连 full-frame） | 无左右信箱；节奏不单调 |
| S3 | breath-pause index 5 与 10 | 与相邻 layout-screen 同宽；无穿帮线 |
| S4 | screen-index 2（3×3 九宫格） | 仅作展开段；不抢开篇 hero 位 |
| S5 | **双视口同屏对比**：**2880×1920（笔记本）** vs **2560×1440（外接）** | 笔记本 ≥ 外接饱满度；均无信箱 |

**林芝回归（T3 专项）**：asset-026 单屏 · asset-026→028 屏缝 · 连续 ultra-wide 节奏。

---

## 8. 实施节奏

```text
Sprint BSP-1（P0）    Content Rail + breath gap + 动效缝禁 overlap        ≈ 3–5 天
Sprint BSP-1.5（P0.5） full-frame cover + context 舞台 + 仙本那重渲染       ≈ 2–3 天
Sprint BSP-2（P1）    layout-screen--viewport-fit + Playwright 双视口      ≈ 5–7 天
Sprint BSP-2b（P1b）  林芝 T3 vh 锚定（可与 BSP-2 并行）                    ≈ 2–3 天
Sprint BSP-3（P2）    studio_preview / reader_immersive + toolbar           ≈ 5–8 天
────────────────────────────────────────────────────────────────────────────
IG 硬门禁（Phase 18）  AC-BSP-01 必过 · AC-BSP-02/02a/02b 必过（仙本那）
                      AC-BSP-02c 林芝回归 · 8+1 本 Surface 盲评
```

---

## 9. 风险与对策

| 风险 | 对策 |
|------|------|
| T3 vh 锚定导致裁切增多 | 依赖 focalPoint；人物图降级 T1/T2 或 `contain` + blurred fill |
| 与 PRD-EXPERIENCE appendix B 动效冲突 | Reader/Studio 分 budget；BSP-3 同步修订矩阵 YAML / 附录 B |
| linzhi 无 breath-pause 仍见缝问题 | P0 同时处理 margin/box-shadow 叠层 |
| P0.5 仅 render 不 curate 时 fit 仍旧 | 文档已注明需 curate 或 `_fits_for_screen` 改动后重跑排版 |
| toolbar 占用导致 vh 不达标 | AC 已规定 toolbar 展开 + 测量 img 可视区 |
| 超宽屏纸边仍可见 | 属 B 模式预期；Reader 可选 `bleed-width: 100vw` 实验 flag |

---

## 10. 附录

### 10.1 现网实现索引（诊断锚点）

| 主题 | 位置 |
|------|------|
| 原生舞台比例 | `travelogue/render/context.py` → `_screen_aspect_ratio_css` |
| 舞台 CSS | `templates/visual-journal/journal-screens.css` L4–14 |
| bleed 变量 | `templates/visual-journal/journal.css` → `--bleed-width` |
| breath 分隔 | `templates/visual-journal/journal-screens.css` → `.breath-pause-screen` |
| folio 屏阴影 | `journal-screens.css` → `html[data-folio="lite"] .layout-screen` |
| cinematic 图动效 | `templates/visual-journal/breath-image.js` |
| 阅读 profile | `travelogue/render/reading_profile.py` · `experience-matrix.yaml` |

### 10.2 修订记录

| 版本 | 日期 | 说明 |
|------|------|------|
| v0.1 | 2026-06-08 | 首版：由林芝预览诊断 + 首席视觉方案整理 |
| v0.2 | 2026-06-08 | 主案例切换为仙本那精选全集；补充视口自适应（16:10 基准）；full-frame contain 主矛盾 |
| v0.3 | 2026-06-08 | 视口矩阵加入 **3:2 笔记本** 为 P0 Dogfood 主基准；`--viewport-ar` 连续自适应 |
| v0.4 | 2026-06-08 | 登记产品负责人双视口：**2880×1920（243 PPI）** + **2560×1440**；高 PPI / DPR 说明 |
| v0.5 | 2026-06-08 | **评审会通过稿**：修 AC 编号 · P0.5 full-frame · viewport-fit 工程形态 · vh 测量规范 · §5.4 范围 · 8+1 golden · Sprint 重排 |

---

## 11. 审批

| 角色 | 姓名 | 日期 | 结论 |
|------|------|------|------|
| 产品 | | 2026-06-08 | ☑ 采纳附修订（v0.5） |
| 首席视觉 | | 2026-06-08 | ☑ 采纳 |
| 工程 | | 2026-06-08 | ☑ 采纳 |
| Curate | | 2026-06-08 | ☑ 采纳 |
| QA | | 2026-06-08 | ☑ 采纳附修订（v0.5） |
| Phase 18 集成 | | 2026-06-08 | ☑ 采纳 |
