# Travelogue · 预览 Dock 视觉 V5 产品需求文档（PRD · Dock Ink Glass）

| 属性 | 内容 |
|------|------|
| **产品代号** | Travelogue Studio |
| **文档版本** | **v0.1.0** |
| **状态** | **Draft · W1–W2 已编码**（方案 B + 轻雾墨玻）· 待目视验收 / W3 回归 |
| **DOC-STATUS** | **active** |
| **主题代号** | 「预览 Dock 视觉 V5」— **DIG**（Dock Ink Glass） |
| **触发来源** | 2026-08-12 产品走查：现网 Dock「很好用但样式丑」；设计方案对比 A/B/C/D 后签核 **B（墨色编辑 / Quiet Luxury）**，并采纳 **轻雾墨玻**（非重玻璃拟态） |
| **前置条件** | 预览 Dock v4 已落地（[PRD-COVER-OPTIMIZATION-V4](./PRD-COVER-OPTIMIZATION-V4.md)）；导出 split / 人话平台名（[SNR](./PRD-SHARE-NARRATIVE-READINESS-V1.md) C8）；AI Sheet 互斥（[SAS](./PRD-STUDIO-AI-SURFACE-V1.md)）；精修 Sheet 指针规则（[PMX](./PRD-POST-MERGE-UX-FIXPACK-V1.md) / Refine V1.1）保持有效 |
| **关联文档** | [PRD-COVER-OPTIMIZATION-V4.md](./PRD-COVER-OPTIMIZATION-V4.md) · [PRD-PREVIEW-EXPORT-FACADE-V1.md](./PRD-PREVIEW-EXPORT-FACADE-V1.md) · [PRD-SHARE-NARRATIVE-READINESS-V1.md](./PRD-SHARE-NARRATIVE-READINESS-V1.md) · [PRD-STUDIO-AI-SURFACE-V1.md](./PRD-STUDIO-AI-SURFACE-V1.md) · [PRD-HELP-ONBOARDING-V1.md](./PRD-HELP-ONBOARDING-V1.md) · [PRD-PREVIEW-REFINE-UX-V1.1.md](./PRD-PREVIEW-REFINE-UX-V1.1.md) · `templates/studio/preview-toolbar/dock.css` · `tokens.css` · `init-v3.js` / `dock.js` |
| **设计附件** | `assets/toolbar-b-hifi-page.png` · `assets/toolbar-b-hifi-closeup-v2.png` · `assets/toolbar-b-hifi-states-v2.png` · `assets/toolbar-b-hifi-mobile.png`（会话产出高保真；落地以本文 token 为准） |
| **评审记录** | 待补（产品 + FE + QA；建议三席即可，因本主题**零业务逻辑变更**） |
| **验收** | 本文 §11（AC-DIG-*）；可选再拆 `ACCEPTANCE-PREVIEW-DOCK-VISUAL-V5.md` |
| **实施清单** | [IMPLEMENTATION-PREVIEW-DOCK-VISUAL-V5.md](./IMPLEMENTATION-PREVIEW-DOCK-VISUAL-V5.md)（W0–W3 任务卡 · v0.1.0） |
| **更新日期** | 2026-08-12 |

> **定位（首席 UX / 设计视角）**
>
> Dock 的信息架构已经够好：顺序短、导出一键、窄屏可收。问题在**视觉系统叠了多套皮肤**——帮助正圆描边、播放/精修「框中框」、薄荷绿字 + 青绿 active + 香槟铜导出并行，主 CTA 金渐变过重。用户感知是「拼装工具箱」，不是「一条属于旅记的时尚轨」。
>
> 本主题是**第四次**面向 Dock 的优化波次，但边界极窄：**只换皮，不换骨**。方向锁定为 **墨色编辑（方案 B）+ 轻雾墨玻壳**——全栏唯一实心强调仍是铜色导出；玻璃只做容器通透，不做彩虹拟态。
>
> **一句话目标**：用户打开任意成册预览，右上 Dock 一眼读成「玻璃墨轨 + 一块铜色导出」；功能、顺序、互斥、文案合同与现网完全一致。
>
> **产品铁律**
>
> 1. **功能零回退** — 帮助 / 返回 / 播放 / 分章 / 精修 / AI / 文件夹 / 导出 / 设置，顺序与行为不变。  
> 2. **单一强调** — 全 Dock 只有导出 split 为实心铜；其余统一 ghost。  
> 3. **轻雾墨玻** — 容器半透明 + blur；禁止彩边折射 / 高透白玻璃 / 每钮一层小玻璃。  
> 4. **铜钮不玻璃化** — 主 CTA 保持不透明平涂。  
> 5. **喜欢项不倒退** — SNR 人话平台名、导出 ≤1 次点击、Sheet/AI 互斥与 hit-test、40px 触控、窄屏收字策略全部保留。  
> 6. **Fail-open** — `backdrop-filter` 不支持时仍可读（实色近黑底回退），不得导致按钮不可点。

---

## 0. 读者指南

| 章节 | 澄清什么 |
|------|----------|
| §0.1 | 术语 |
| §0.2 | 与历史 Dock 波次的关系（第几次优化） |
| §0.3 | 与相邻主题边界 |
| §1 | 背景、问题、根因 |
| §2 | 目标 / 非目标 / 成功指标 |
| §3 | 冻结决策 D-DIG-* |
| §4 | 视觉规范（token / 材质 / 排版 / 状态） |
| §5 | 布局与响应式（功能顺序合同） |
| §6 | 文案与无障碍 |
| §7 | 工程落点 |
| §8 | 错误与降级 |
| §9 | 埋点（本主题可不新增） |
| §10 | 里程碑 |
| §11 | 验收 AC-DIG-* |
| §12 | 风险与开放问题 |
| 附录 | 对比方案摘要 · 版本记录 |

### 0.1 术语

| 术语 | 含义 |
|------|------|
| **Dock / Icon Dock** | 预览页右上（窄屏可拉宽）悬浮胶囊工具栏：`.preview-toolbar__dock`，壳类 `.preview-toolbar--v4` |
| **DIG / Dock Ink Glass** | 本主题视觉语言：墨色轻雾玻璃容器 + 象牙 ghost 控件 + 唯一香槟铜实心导出 |
| **ghost 控件** | 透明底、无独立描边/阴影；hover / active 仅用淡白底或淡铜雾 |
| **轻雾墨玻** | `backdrop-filter: blur(14–16px)` + 近黑半透明渐变 + 细白边 + 顶缘微高光；**非** iOS 白玻璃、**非**彩边玻璃拟态 |
| **folio 框中框** | 现网 `--folio` 给播放/精修加的金描边浅底；本主题**退役** |
| **split CTA** | 导出主钮 + 设置 caret 组成的一体 pill（`.longshot-split`） |
| **Scheme A** | 历史墨炭 + 香槟铜色板意图；本主题**收口执行**（去掉薄荷绿第二强调色） |

### 0.2 与历史 Dock 波次的关系（第几次）

| 波次 | 文档 / 落地 | 改了什么 | 本主题关系 |
|------|-------------|----------|------------|
| **① v3 顶栏** | Preview Toolbar v3 | 全宽顶栏 + 金色导出 | 已由 V4 取代壳层 |
| **② V4 Icon Dock** | [PRD-COVER-OPTIMIZATION-V4](./PRD-COVER-OPTIMIZATION-V4.md) | 右上胶囊坞、释放封面全视窗 | **结构基线：保留** |
| **③ 能力与交互叠代** | Help / Refine / Export Facade / SAS / SNR / PMX / UI Detail Wave3 等 | 增按钮、互斥、人话 CTA、hit-test、Scheme A 描边尝试 | **行为合同：全部继承；视觉债在此清** |
| **④ DIG V5（本主题）** | 本文 | **纯视觉净化 + 轻雾墨玻** | 不改 IA、不改状态机 |

> 若产品口头称「第三次 / 第四次」：以 **V4 结构 + 交互叠代 + 本波视觉** 计为第四次面向 Dock 的优化；本 PRD 正式编号 **Visual V5**，避免与封面 Styles V5 混淆时用代号 **DIG**。

### 0.3 与相邻主题的边界

| 主题 | 关系 | 本主题做什么 / 不做什么 |
|------|------|-------------------------|
| Cover Opt V4 | **继承壳** | 不恢复全宽顶栏；不改 `--preview-toolbar-h` 占位语义（仍为顶右安全区） |
| Export Facade / Recipe | **不碰分流** | 不改平台配方、popover 内容结构；只改 Dock 上按钮皮肤 |
| SNR | **继承 CTA 文案合同** | 继续人话平台名（如「导出小红书」）；不得退回「N 个模式」优先 |
| SAS / AIR / NAS | **继承互斥与门控** | AI 显隐、Sheet 互斥、pointer-events 规则只做视觉配套，不改闸 |
| Refine V1.1 / RCI / PMX | **继承精修** | 不改 Sheet IA；精修 active/done 仅换「淡铜雾」皮 |
| Help Onboarding | **继承入口** | `?` 仍打开帮助；去掉正圆特例皮，逻辑不变 |
| Cover Styles / Calligraphy | **无交叉** | 不改封面排版；仅保证 Dock 在浅/深封面上可辨识（AC） |
| UI Detail Contract | **对齐精神** | tip / focus / 圆角家族与 Studio 细节尺子不冲突；本主题可更新 Dock 专用 token |

---

## 1. 背景与问题

### 1.1 现状摘要（2026-08-12）

功能顺序（现网，**冻结**）：

```text
?帮助 → 返回 → | → 播放 → 分章 → 精修 → AI → | → 文件夹 → [导出·平台名 | 设置▾]
```

视觉现状（问题侧）：

| 维度 | 现网表现 | 用户感知 |
|------|----------|----------|
| 容器 | 近黑渐变 + blur(12) 已有雏形 | 偏「实心黑铁」，通透不够 |
| 控件皮肤 | 帮助正圆；播放/精修 folio 金框；其余透明 | 一排多种皮肤 |
| 强调色 | 薄荷绿字 `#a8dcc8` + 青绿 pressed + 铜色导出 | 彩虹、不时尚 |
| 主 CTA | 金渐变 / 多层高光历史残留 + 方角 10px | 像广告条 |
| 字距 | label `letter-spacing: 0.08em` / 字重 600 | 短中文显廉价 |
| 分隔 | 白→铜→白竖渐变 | 装饰过度 |

### 1.2 问题清单（P-DIG-*）

| ID | 严重度 | 用户感知 | 认领 |
|----|--------|----------|------|
| **P-DIG-01** | P0 | 「工具栏丑 / 像拼装」 | ✅ |
| **P-DIG-02** | P0 | 播放/精修金框与其余按钮不一致 | ✅ |
| **P-DIG-03** | P0 | 导出钮过重、发旧 | ✅ |
| **P-DIG-04** | P1 | 薄荷绿与铜色打架 | ✅ |
| **P-DIG-05** | P1 | 帮助钮正圆特例破坏一体感 | ✅ |
| **P-DIG-06** | P1 | 字距过松、字重过重 | ✅ |
| **P-DIG-07** | P2 | tip 偏绿底与墨轨异色 | ✅ |
| **P-DIG-08** | P2 | 亮雪景封面上 Dock 偶发发灰（通透不足或过透） | ✅（轻雾档验收） |

### 1.3 核心判断

> **好用已经成立；丑来自未收口的多皮肤。**  
> 解法不是再加一波「特色描边」，而是：**统一 ghost + 唯一铜 CTA + 轻雾墨玻壳**。  
> 年轻人向的时尚感来自克制材质与层级，不来自特效。

### 1.4 根因树

```text
Dock「丑」
├─ 层次失控
│  ├─ P-DIG-02 folio 框中框
│  ├─ P-DIG-05 帮助正圆特例
│  └─ 圆角 8 / 10 / 50% / 999 混用
├─ 强调色并行
│  ├─ P-DIG-04 薄荷绿字 + 青绿 active
│  └─ P-DIG-03 导出金渐变抢戏
├─ 排版广告感
│  └─ P-DIG-06 字距 0.08em / 字重 600
└─ 材质未升级
   ├─ 容器偏实心（通透不够）
   └─ 或矫枉过正做成重玻璃（本主题明确禁止）
```

---

## 2. 目标与非目标

### 2.1 目标

| ID | 目标 |
|----|------|
| **G-DIG-01** | 视觉语言收口为 DIG：墨色轻雾玻璃 + ghost 工具 + 唯一铜色 split CTA |
| **G-DIG-02** | 功能与顺序 100% 等价于现网 Dock v4（含窄屏收字 / 藏文件夹） |
| **G-DIG-03** | 导出仍 ≤ 1 次点击；SNR 人话平台名不回退 |
| **G-DIG-04** | Sheet / AI / 分章 / 导出设置互斥与 pointer-events 规则零回归 |
| **G-DIG-05** | 触控热区保持 ≥40×40；focus-visible 统一 |
| **G-DIG-06** | 浅底封面（如 `split-mat`）与深底封面上 Dock 均可辨识 |
| **G-DIG-07** | `backdrop-filter` 不支持时仍有可读实色回退 |

### 2.2 非目标

| 不做 | 理由 |
|------|------|
| 改按钮顺序 / 增删功能 | 用户明确要求功能不变 |
| 恢复 v3 全宽顶栏 | 封面验货已证明 Dock 正确 |
| 白玻璃 / 彩边重拟态 / 每钮小玻璃 | 与静奢冲突、易脏 |
| 重做 Sheet / 分章 / AI / 导出 popover IA | 越界 |
| 改导出算法、平台配方、长图管线 | 归 ECC / Recipe |
| 为 Dock 新建第二套组件库或换构建链 | 只改 CSS（必要时极少 DOM class） |
| 自适应「按封面亮度调透明度」算法（V5.0） | 可进 OQ；首版固定 token |

### 2.3 成功指标（狗粮向）

| 指标 | 门槛 |
|------|------|
| 截掉文字后仍能辨出「左浅图标 + 右铜色块」 | 产品 / 设计 目视 **通过** |
| 播放 / 精修 / 分章 / AI / 文件夹默认态皮肤不可互相区分（除图标字形） | **通过** |
| 深色封面 + 浅色封面各 ≥1 本样片：图标对比可辨 | **2/2** |
| 精修开 / AI 开：关闭路径与返回可点（现网合同） | **回归 100%** |
| 导出主路径：点主钮即可开始（设置仍走 caret） | **≤1 次点击** |
| `prefers-reduced-motion: reduce` 下无动画依赖可用性 | **通过** |

---

## 3. 冻结决策（D-DIG-*）

| ID | 决策 | 说明 |
|----|------|------|
| **D-DIG-01** | **方向 = 方案 B + 轻雾墨玻** | 静奢墨轨；容器通透一档；否决 C 重甜橙、D 炫 mesh、A 白玻璃为默认 |
| **D-DIG-02** | **只换皮** | 默认不改 `init-v3.js` 按钮插入顺序；不改 longshot / sheet 状态机 |
| **D-DIG-03** | **唯一实心 = 导出 split** | 主区 + caret 同色系一体 pill；caret 略暗一档 |
| **D-DIG-04** | **退役 folio 框中框与帮助正圆特例** | 全部工具统一 ghost chip（全圆角） |
| **D-DIG-05** | **退役薄荷绿 / 青绿 active 为默认强调** | ink 改象牙/近白；active/done/pressed 改淡 accent 雾 |
| **D-DIG-06** | **导出平涂强调色，禁止金渐变多层立体** | 现为铅灰 `#3f454c`（D-DIG-24）；至多 2% 纵向明暗 |
| **D-DIG-07** | **玻璃只给容器** | 子按钮默认无描边、无独立阴影、无 inset 高光 |
| **D-DIG-08** | **圆角同族** | Dock `999px`；内部控件统一 `999px`（chip）；split 整体一个 pill |
| **D-DIG-09** | **字距降噪** | dock label `12px / 500–550`，`letter-spacing: 0.02em` |
| **D-DIG-10** | **分隔两条实线** | `rgba(255,255,255,.14)`，去掉铜光渐变 |
| **D-DIG-11** | **caret 用细 chevron SVG（或等价细图标）** | 禁止 `24px/700` 字符 ▾ 抢戏 |
| **D-DIG-12** | **stale = 细琥珀环** | `box-shadow: 0 0 0 1.5px`，勿粗 outline |
| **D-DIG-13** | **focus = 淡 accent 环** | `color-mix(accent 55%, transparent)`，取代绿焦点 |
| **D-DIG-14** | **窄屏策略继承** | ≤720 藏文件夹与多数 label；≤480 导出可收成铜块+图标；safe-area 保留 |
| **D-DIG-15** | **不新增埋点** | 纯视觉；沿用现有 click 事件即可 |
| **D-DIG-16** | **DOM class 可加修饰，不改语义角色** | 允许加 `dock--ink-glass` 或 token 作用域；`aria-*` / `data-*` 行为钩子保持 |
| **D-DIG-17** | **封面整面深链关闭（方案 C）** | 点封面/封底空白**不再**打开精修；只走 Dock「精修」。`openRefineCoverSeg` 保留给 AI Sheet 等显式跳转（修订 RCI G-RCI-06 的「点封面图→照片」） |
| **D-DIG-18** | **玻璃强度加档** | `blur(28px) saturate(1.2)`；去掉容器 `opacity<1`；顶缘高光加强。底 alpha：**≈0.85 / 0.82**（可读优先，仍保留雾面） |
| **D-DIG-20** | **对比可读优先** | ghost 图标/字用近纯白 `#fff`；可加极轻字影；CTA 区不加字影 |
| **D-DIG-21** | **Dock 内清掉 `.ctl` 默认浅底** | `shell.css` 的 ctl 描边/浅底不得泄漏进 v4 Dock；仅 `aria-pressed` / `aria-expanded` / `.is-active` / `--done` 显示淡 accent 雾；返回图标无外圈 |
| **D-DIG-19** | **Dock 图标对齐效果图** | 返回圈箭、播放三角、分章列表、精修滑杆、AI 星芒、帮助圈问号 |
| **D-DIG-22** | **强调色试色通道** | 退役香槟铜 `#c4a574` 与松绿 `#3d6b5a`；曾试暗陶赤 `#A65D4E`（狗粮否决） |
| **D-DIG-23** | **混合方案：Dock 深 / 弹层浅** | Dock 保持墨玻深底；精修 / AI / 导出 / 帮助 / 分章 = 浅色阅读面（`#f7f5f0` / `#fff`）+ 当前强调色。深炭全套弹层已否决 |
| **D-DIG-24** | **试色 D · 铅灰加深档 D2（当前默认）** | Accent `#3F454C` / hover `#4E555C` / strong `#2E3338` / on-accent ink `#F5F0E8`。基线曾为 `#5C636A`；曾试 A 墨青 |
| **D-DIG-25** | **浅色弹层可读与版式** | Tab/分段 active 用深字（禁 accent-ink 浅上浅）；bookends 操作钮取消 sticky；侧栏宽 ≈640；muted 略加深 |

---

## 4. 视觉规范（可落地 token）

> 建议落在 `templates/studio/preview-toolbar/dock.css`（或 `tokens.css` 的 Dock 作用域）。数值为合同默认；实施可 ±1–2px 微调，但不得破坏层级原则。

### 4.1 颜色

| Token | 值 | 用途 |
|-------|-----|------|
| `--dock-bg-top` | `rgba(22, 24, 26, 0.85)` | 容器渐变顶（对比可读） |
| `--dock-bg-bottom` | `rgba(14, 16, 18, 0.82)` | 容器渐变底 |
| `--dock-border` | `rgba(255, 255, 255, 0.18)` | 外描边 |
| `--dock-highlight` | `rgba(255, 255, 255, 0.16)` | 顶缘 inset 高光 |
| `--dock-ink` | `#ffffff` | 默认图标/字 |
| `--dock-ink-muted` | `rgba(255, 255, 255, 0.78)` | 次要（帮助） |
| `--dock-hover` | `rgba(255, 255, 255, 0.10)` | hover 底 |
| `--dock-press` | `rgba(255, 255, 255, 0.14)` | press 底 |
| `--dock-accent` | `var(--preview-accent)` → `#3f454c` | **唯一强调**（导出；铅灰） |
| `--dock-accent-hover` | `#4e555c` | 导出 hover |
| `--dock-accent-ink` | `#f5f0e8` | 导出上文字/图标 |
| `--dock-accent-caret` | `color-mix(accent 88%, #1c1812)` | caret 半区略暗 |
| `--dock-active-bg` | `color-mix(accent 22%, transparent)` | 播放/精修/分章 active |
| `--dock-active-border` | `color-mix(accent 45%, transparent)` | active 细边（可选 1px） |
| `--preview-panel-bg` | `#f7f5f0` | 精修/AI/导出/帮助/分章弹层底（浅） |
| `--preview-surface` | `#ffffff` | 弹层卡片/输入面 |
| `--preview-elevated` | `#f3f1ec` | 弹层次级底 |
| `--preview-ink` | `#14110d` | 弹层正文（Dock 仍用 `--dock-ink`） |
| `--dock-focus` | `rgba(196, 165, 116, 0.55)` | focus ring |
| `--dock-stale` | `#e0a04a` | stale 细环 |
| `--dock-running` | `#5c574f` 系 | 导出中实心（可沿用现网灰褐，去掉花哨渐变） |
| `--dock-divider` | `rgba(255, 255, 255, 0.14)` | 分隔 |
| `--dock-tip-bg` | `rgba(18, 20, 22, 0.96)` | tip 底（去绿） |
| `--dock-tip-ink` | `#f5f7f6` | tip 字 |

**明确退役（视觉层）**：`#a8dcc8` 薄荷绿字、`#7fcbb3` 青绿 active、导出金渐变 `#e0ba52…`、divider 铜光渐变、帮助独立正圆描边系统。

### 4.2 材质（轻雾墨玻）

| 项 | 规范 |
|----|------|
| 背景 | `linear-gradient(160deg, var(--dock-bg-top), var(--dock-bg-bottom))` |
| 模糊 | `backdrop-filter: blur(28px) saturate(1.2)`；`-webkit-backdrop-filter` 同步 |
| 阴影 | `0 10px 32px rgba(0,0,0,.22)` + 顶缘/底缘微高光 |
| 顶缘 | `inset 0 1px 0 var(--dock-highlight)` |
| 字影 | ghost 区 `0 1px 2px rgba(0,0,0,.35)`；铜 CTA 区关闭 |
| 边框 | `1px solid var(--dock-border)` |
| 子按钮 | **无**独立 box-shadow / inset / 默认 border |
| 主 CTA | 平涂 `--dock-accent`；阴影至多 `0 1px 2px rgba(0,0,0,.22)` |

**禁止**：彩色折射边、强内发光、脉冲光晕作为默认态（FTUE pulse 若保留，须克制且可关）。

### 4.3 形状与尺寸

| 元素 | 规范 |
|------|------|
| Dock 容器 | `border-radius: 999px`；`padding: 5px 7px`（可微调）；`gap: 6–8px` |
| 触控 | 默认 **40×40**；labeled 高度 40、宽度随内容 |
| ghost chip | `border-radius: 999px` |
| split | 整体 `999px`；主钮左半圆、caret 右半圆；中缝 `1px solid rgba(28,24,18,.14)` |
| 分隔 | `1×16–18px`，两条（返回后、AI 后 / 导前，与现网分区一致） |
| 图标 | 24 网格；stroke ≈ 1.75；`currentColor` |

### 4.4 排版

| 元素 | 规范 |
|------|------|
| UI 字体 | `var(--studio-font-ui)` |
| dock label | `12px / 500–550 / letter-spacing: 0.02em` |
| 导出 label | `12px / 600 / letter-spacing: 0.02em`；色 `--dock-accent-ink` |
| 设置字 | `11–12px / 500`；chevron 细线 |

### 4.5 交互状态

| 状态 | 规范 |
|------|------|
| default | ghost：透明 + `--dock-ink` |
| hover | `--dock-hover`；图标提亮至接近 `#fff` |
| press | `--dock-press` |
| active / pressed / open（播放、精修、分章、AI） | `--dock-active-bg`（+ 可选 active border） |
| 精修 done | 同族淡铜雾，不跳绿 |
| disabled | `opacity: .4`；无 hover 底 |
| focus-visible | `0 0 0 2px var(--dock-focus)` |
| export hover | `--dock-accent-hover` |
| export running | `--dock-running` + spinner；cursor wait |
| export stale | 细 `--dock-stale` 环 |
| dock dim（离封面滚动） | 容器整体约 0.7，hover/focus 回 1（行为保留） |
| tip | 延迟 300ms 保留；改墨炭 tip 底 |

### 4.6 动效

- hover / opacity：`150–200ms ease`
- 尊重 `prefers-reduced-motion: reduce`（现有 media 块保留并覆盖新 transition）

---

## 5. 布局与响应式（功能顺序合同）

### 5.1 桌面（≥720px）— 顺序冻结

```text
[ ? ] [ ← 返回 ] │ [ 播放  分章  精修  AI ] │ [ 文件夹 ] 【 导出·平台名 | 设置 ▾ 】
   meta                tools (ghost)           util         primary split
```

视觉分区靠 **2 条细分隔 + 铜色实心**，不靠给中间钮加框。

### 5.2 窄屏

| 断点 | 行为（继承现网，只美化） |
|------|--------------------------|
| **≤720** | 藏文件夹；藏多数 dock-label；工具 icon+tip/aria；Dock 可拉满宽右对齐 |
| **≤480** | 导出主文案可藏，保留铜块 + 图标；caret 可仅 chevron |
| **safe-area** | `max(12px, env(safe-area-inset-*))` |

### 5.3 层叠与互斥（行为冻结 · 回归必测）

| 场景 | 合同 |
|------|------|
| `preview-sheet-open` | Dock 容器 `pointer-events: none`；返回 / 精修 / AI 等现网白名单可点 |
| `preview-ai-sheet-open` | 同上精神；导出区失活，避免挡 Sheet × |
| z-index | Dock 250 相对 Sheet 的既有关系不改为「挡死关闭」；命中规则保持 SNR/SAS/PMX |

---

## 6. 文案与无障碍

### 6.1 可见文案

- 导出主文案继续由现有 `syncLongshotCtaLabel`（或等价）驱动：**人话平台名**优先（SNR G-SNR-09）。
- 本主题不改 COPY 表；若视觉上「导出小红书」过长，优先靠窄屏藏字，不擅自改文案语义。

### 6.2 a11y

| 要求 | 口径 |
|------|------|
| 每个控件 | 保持 `aria-label` / tip |
| 对比度 | 铜底 + 墨字；ghost 图标在墨玻上可辨（浅封面靠边与阴影） |
| 焦点 | 铜环统一；键盘可及 caret 与主钮仍为**两个**控件 |
| 分隔 | `aria-hidden="true"` 保持 |
| 触控 | ≥40px |

---

## 7. 工程落点

### 7.1 预期改动面（窄）

| 文件 | 动作 | 说明 |
|------|------|------|
| `templates/studio/preview-toolbar/dock.css` | **主改** | token、容器玻璃、ghost 统一、folio 退役、split 圆角、divider、tip、状态色 |
| `templates/studio/preview-toolbar/tokens.css` | 可选 | 若需上提 CSS 变量 |
| `templates/studio/preview-toolbar/longshot.css` | 可能 | 导出渐变/状态若与 dock 重复定义则对齐 |
| `templates/studio/preview-toolbar/dock.js` / `init-v3.js` | **尽量不改**；例外：caret chevron 若需换 SVG 节点、或加 `dock--ink-glass` class | 禁止改插入顺序 |
| 单测 / Playwright | 更新选择器视觉无关断言；补截图或 contrast 手测清单 | 如 `tests/unit/web/test_preview_toolbar_v3.py`、g8 suite 等待 `.preview-toolbar--v4` |

### 7.2 明确不改

- 导出 job / popover 业务逻辑
- Sheet / AI Sheet / chapter panel 内容
- 首页 / modal 非 Dock 表面（除非共享 tip 色需要极小对齐）

### 7.3 实施原则

1. **先删后加**：去掉 folio、薄荷绿、金渐变、铜光 divider，再写入 DIG token。  
2. **选择器兼容**：保留 `.preview-toolbar--v4` 作为壳；可用修饰 class 标记 DIG，避免双轨永久分叉。  
3. **无构建链变更**。  
4. **tsc:preview-toolbar** 保持绿灯（若未碰 JS 则无额外类型债）。

---

## 8. 错误与降级

| 情况 | 行为 |
|------|------|
| 无 `backdrop-filter` | 提高底不透明度至 ≈0.92 近黑实色，边框与 CTA 不变 |
| 极亮封面对比不足 | 允许把 `--dock-bg-*` 不透明度 +0.06～0.10（仍属墨玻，不改白玻璃） |
| 字体加载失败 | 系统 UI 回退；布局不塌 |
| reduced-motion | 取消非必要 transition；tip 可立即显示 |

---

## 9. 埋点

**D-DIG-15**：本主题不新增事件。现有导出 / 精修 / AI / 帮助点击继续上报即可。

---

## 10. 里程碑

| 里程碑 | 内容 | 出口 |
|--------|------|------|
| **W0** | PRD 评审签核（本文）+ 高保真对齐确认 | Go / Conditional Go |
| **W1** | P0 CSS：容器墨玻、folio/正圆退役、ghost 统一、铜 CTA 平涂、字距、divider | 桌面截图对照 AC-DIG-01～05 |
| **W2** | P1：active/done/focus/stale/tip/caret SVG；窄屏目视 | AC-DIG-06～10 |
| **W3** | 回归：Sheet/AI 互斥、导出主路径、浅/深封面、reduced-motion | AC-DIG-11～14；可开合入 |
| **W4**（可选） | 真机狗粮 N≥3；亮度自适应 OQ 决策 | 记录 acceptance-records |

**建议工期**：W1–W3 合计 **0.5–1.5 人日**（纯 CSS 为主）。

---

## 11. 验收（AC-DIG-*）

| ID | 断言 | 方法 |
|----|------|------|
| **AC-DIG-01** | 功能顺序与现网一致；无增删按钮 | 对照 DOM / 手测 |
| **AC-DIG-02** | 默认态：播放/精修**无**金描边框中框；帮助**非**独立正圆描边系统 | 截图 |
| **AC-DIG-03** | 全栏仅导出 split 为实心铅灰；其余 ghost | 截图 |
| **AC-DIG-04** | 导出无金渐变多层立体；平涂 `#3f454c` + 象牙白字 | 截图 / CSS |
| **AC-DIG-05** | 容器具备 blur + 半透明墨底 + 细白边 + 顶缘微高光 | 计算样式 |
| **AC-DIG-06** | label 字距 ≤ `0.02em` 量级；字重视觉 ≤550（导出可 600） | CSS |
| **AC-DIG-07** | divider 为实色细线，非铜光渐变 | CSS |
| **AC-DIG-08** | 精修/播放/分章 active 为淡陶雾，非薄荷绿/青绿 | 截图 |
| **AC-DIG-09** | focus-visible 为统一淡陶环 | 键盘测 |
| **AC-DIG-10** | ≤720 藏文件夹与 label 策略不回退；导出陶色块可识别 | 窄屏手测 |
| **AC-DIG-17** | 预览弹层为浅色阅读面 + 铅灰强调；Dock 仍为深色墨玻；无松绿主色 | 截图 |
| **AC-DIG-11** | 精修 Sheet 开：返回可点；关闭路径可用 | 回归 |
| **AC-DIG-12** | AI Sheet 开：× 可点，不被 caret 挡死 | 回归（SNR） |
| **AC-DIG-13** | 导出主钮一键可触发；设置走 caret；人话平台名仍在 | 回归（SNR/Facade） |
| **AC-DIG-14** | 浅底封面样式至少 1 款 + 深底 1 款 Dock 可辨 | 手测（延续 AC-CSV-45 精神） |
| **AC-DIG-15** | `backdrop-filter` 关闭或模拟不支持时按钮仍可点可读 | DevTools / 降级 |
| **AC-DIG-16** | `prefers-reduced-motion: reduce` 可用 | 系统设置 |

**目视验收口诀**（给产品签字）：

> 截掉文字后：左边一串浅图标、右边一块铜色。  
> 截掉铜色后：其余按钮几乎分不出皮肤差异。

---

## 12. 风险与开放问题

### 12.1 风险

| 风险 | 缓解 |
|------|------|
| 半透明在雪景封面发灰 | AC-DIG-14；必要时略增不透明（仍墨玻） |
| 改 CSS 误伤 longshot 状态类 | W3 导出 idle/running/stale/done 全路径手测 |
| caret 换 SVG 影响点击热区 | 保持 ≥40px 宽；两控件可聚焦 |
| 「又一次优化」审美疲劳 | PRD 写清只换皮；合入说明强调零功能变更 |

### 12.2 开放问题（OQ）

| ID | 问题 | 默认解（可评审改） |
|----|------|-------------------|
| **OQ-DIG-01** | 是否按封面亮度动态调容器透明度？ | **V5.0 不做**；固定 token；抱怨再开 V5.1 |
| **OQ-DIG-02** | FTUE 导出脉冲是否保留？ | **保留逻辑、削弱视觉**（淡铜呼吸，禁金闪） |
| **OQ-DIG-03** | tip 是否全面改位到下方避免贴顶裁切？ | **保持现网方位**；仅改色 |
| **OQ-DIG-04** | 是否与 chapter-panel 深色侧栏共享 ink token？ | **P2 可选**；不阻塞 W1–W3 |
| **OQ-DIG-05** | 高保真附件中文偶发字形误差 | **以本文 §4–§5 为合同**；附件仅示意 |

---

## 附录 A · 方案对比（已决策，归档用）

| 方案 | 一句话 | 结论 |
|------|--------|------|
| A 雾面白玻璃 | iOS 轻奢 | 不作为默认（偏工具 OS） |
| **B 墨色编辑** | 静奢、贴小红书旅记 | **采纳为骨架** |
| C Soft Pop | 珊瑚友好 | 否决为默认（偏甜） |
| D Soft Mesh | 创作者科技感 | 否决为默认（易脏） |
| B + 轻雾墨玻 | 通透但不炫 | **最终执行档（D-DIG-01）** |

---

## 附录 B · 版本记录

| 版本 | 日期 | 说明 |
|------|------|------|
| **v0.1.0** | 2026-08-12 | 首稿：DIG 方向签核写入；完整 token / 决策 / AC / 里程碑；明确与 V3→V4→交互叠代之「第四次 Dock 优化」关系；待评审后开 W1 |
| **v0.1.1** | 2026-08-12 | W1–W2 编码落地（见 IMPLEMENTATION v0.2.0）；待目视 AC + W3 回归 |
| **v0.1.2** | 2026-08-12 | 狗粮回写：D-DIG-17 封面深链 C；D-DIG-18 玻璃加档；D-DIG-19 效果图图标 |
| **v0.1.3** | 2026-08-12 | D-DIG-20 对比可读：底 alpha 回调 0.58–0.62；ink 纯白 + 轻字影；§4 token 与代码对齐 |
| **v0.1.4** | 2026-08-12 | D-DIG-21：清 Dock 内 `.ctl` 假选中；统一真状态高亮；返回去外圈 |
| **v0.1.5** | 2026-08-12 | 底 alpha → 0.70–0.74（对比加深一档，保留 blur） |
| **v0.1.6** | 2026-08-12 | D-DIG-22：强调色试暗陶赤 `#A65D4E`；弹层深炭家族；玻璃底锁定 ≈0.85；退役香槟铜/松绿 |
| **v0.1.7** | 2026-08-12 | D-DIG-23 混合方案：Dock 深墨玻保留；弹层拨回浅色阅读面 |
| **v0.1.8** | 2026-08-12 | D-DIG-24：曾试 A 墨青 `#3F6F7A` |
| **v0.1.9** | 2026-08-12 | D-DIG-24：改试色 D 铅灰 `#5C636A` |
| **v0.1.10** | 2026-08-12 | D-DIG-24：铅灰加深档 D2 `#3F454C` |
| **v0.1.11** | 2026-08-12 | D-DIG-25：精修弹层对比度 + 去 sticky 浮钮 + 加宽 640 |

---

## 附录 C · 评审检查清单（三席）

| 席位 | 关注点 | 签字栏 |
|------|--------|--------|
| 产品 | 功能零回退、CTA 人话名、是否接受「只换皮」范围 | |
| 设计 / UX | token 是否对齐签核高保真；禁止项是否够硬 | |
| 前端 | 改动面是否真能收在 CSS；互斥 CSS 是否误伤 | |
| QA（可选） | AC-DIG 手测表是否可执行 | |
