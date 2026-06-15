# Travelogue · 封面多样式产品需求文档（PRD · Cover Styles V5）

| 属性 | 内容 |
|------|------|
| **产品代号** | Travelogue |
| **文档版本** | v1.1.0 |
| **状态** | **P0+P1 已实施（2026-06-15）** · 跨职能评审已收敛 |
| **主题代号** | 「封面多样式 V5」— 新建游记时从 3 套 Web 封面皮肤中分配其一，增强首屏差异感 |
| **前置条件** | [PRD-COVER-OPTIMIZATION-V4.md](./PRD-COVER-OPTIMIZATION-V4.md) 已落地（Icon Dock + 右下书名卡 `card-br`）；`cover-opening.hbs` / `cover-hero` 可用；封面横竖图分端选图已合入 |
| **关联文档** | [preview-cover-album-v2-wireframe.html](./wireframes/preview-cover-album-v2-wireframe.html)（方案 E/F/G/H）、[PRD-COVER-OPTIMIZATION-V4.md](./PRD-COVER-OPTIMIZATION-V4.md)、[TEMPLATE-visual-journal.md](./TEMPLATE-visual-journal.md)、`schemas/trip.schema.json`、`travelogue/services/trip_factory.py`、`travelogue/render/assemble.py` |
| **评审来源** | 2026-06-15 封面多样式可行性讨论会；[跨职能评审纪要](./acceptance-records/cover-styles-prd-review-2026-06-15.md)；用户提供 2 张参考图（商务画册侧栏 / 时尚杂志顶题） |
| **验收** | [ACCEPTANCE-COVER-STYLES-V5.md](./ACCEPTANCE-COVER-STYLES-V5.md) |
| **实施清单** | [IMPLEMENTATION-COVER-STYLES-V5.md](./IMPLEMENTATION-COVER-STYLES-V5.md) |
| **更新日期** | 2026-06-15 |

> **定位**
>
> 现网 Web 封面仅 **一种** 排版皮肤：全幅摄影 + 右下实心书名卡（`card-br`，Cover V4）。用户新建游记时视觉同质化，不利于演示传播与「这本相册不一样」的第一印象。
>
> 本 PRD 在 **不改动 `cover-opening` 块结构** 的前提下，新增 **2 套 Web 封面皮肤**，并在 **创建游记时** 从 3 套样式中 **确定性随机** 分配一种，写入 `trip.json` 后 **终身不变**（除非 P1 手动切换）。
>
> **产品共识（八条铁律 · v1.1 拍板版）**
>
> 1. **一块 DOM，多套 CSS** — `cover-opening.hbs` 不拆模板；用 `data-cover-opening` / modifier class 分岔样式。  
> 2. **创建时分配，重渲染不变** — 样式写入 trip 数据；`render` / `rerender` **不得** 重新随机。  
> 3. **确定性「随机」** — 用 `tripId` 哈希映射样式，便于复现、测试与排错；对用户仍表现为随机。  
> 4. **均匀权重** — 三种样式 **1:1:1** 分配概率。  
> 5. **P0 仅 Web / auto** — `data-layout=mobile` 封面 **维持现网**，不随本 PRD 变化；须在 Studio 文案 **明示** Web 与 Mobile 封面版式不同步。  
> 6. **摄影逻辑不变** — `coverAssetId`、横竖分端选图、focal 与 V4 一致；只变 **排版皮肤**。  
> 7. **窄屏回落** — Web 视口 **&lt;1024px** 时，不论 trip 内样式为何，**CSS 呈现回落 `card-br`**（数据层 `meta.coverOpeningStyle` 不变）。  
> 8. **设计 token** — 新皮肤色值、圆角、阴影须用 §4.6 token；禁止实现层硬编码未文档化色值。

---

## 1. 背景与问题

### 1.1 现状摘要

| 维度 | 现网（V4 实施后） | 用户感知 |
|------|-------------------|----------|
| **封面皮肤** | 仅 `card-br`：全幅摄影 + 右下书名卡 | 每本相册首屏「长得一样」 |
| **数据模型** | `trip.json` 无封面样式字段 | 无法记录、切换或 A/B |
| **新建流程** | `create_trip()` 写 meta，不分配样式 | 无差异化入口 |
| **历史探索** | 线框 v2 已有 E 分屏 / F 画框 / G 剧场等方案 | 未产品化；V4 收敛为 `card-br` |
| **Mobile** | 竖图封面另一套逻辑 | 本 PRD **不覆盖** |

### 1.2 问题陈述（P-CSV-*）

| ID | 问题 | 影响 |
|----|------|------|
| **P-CSV-01** | 所有 Web 游记封面排版相同 | 演示、传播缺乏记忆点 |
| **P-CSV-02** | 无样式字段，扩展需硬编码 | 后续皮肤数增加成本高 |
| **P-CSV-03** | 若每次 render 随机样式 | 用户预览与导出 **前后不一致**（禁止） |
| **P-CSV-04** | 参考图风格未进入产品 | 商务画册 / 杂志感无法选用 |

### 1.3 核心判断

> **在 V4 稳定 DOM 上叠加 2 套 CSS 皮肤**，比新建 3 份 Handlebars 模板 **风险更低、可测性更好**。  
> **创建时一次分配 + tripId 确定性映射**，满足「随机感」与工程可复现。  
> **P0 不做 Studio 样式切换 UI**；数据层预留枚举，P1 再补交互。

### 1.4 需求讨论会拍板（2026-06-15）

| 开放项 | 决议 |
|--------|------|
| **O-1** 用户能否事后换样式？ | **P0 不做 UI**；`meta.coverOpeningStyle` 预留；P1 Studio 下拉切换 |
| **O-2** 三种样式权重？ | **均匀 1:1:1** |
| **O-3** 新样式与参考图映射？ | **`split-mat`** ≈ 商务画册侧栏实色块；**`magazine-head`** ≈ 时尚杂志顶题 + 下大图 |
| **O-4** hook 为空时？ | 各样式须 **无 hook 降级** 仍一屏可读（纳入 AC） |
| **O-5** Share 导出？ | **是**，与 Web 预览一致 |

### 1.5 跨职能评审拍板（2026-06-15 · v1.1）

| 决议 ID | 议题 | v1.1 决议 |
|---------|------|-----------|
| **R-01** | `magazine-head` 标题对齐 | **居中**；hook / place 可左对齐或居中（与 title 同轴） |
| **R-02** | 杂志款 header 高度 | **`min-height: 20vh`；`max-height: 32vh`**；摄影区 **≥ 58vh** |
| **R-03** | `split-mat` 色值 | 改为 **§4.6 设计 token 表** |
| **R-04** | 窄屏 Web | **P0 保证 ≥1024px** 完整呈现三套；**&lt;1024px CSS 回落 `card-br`** |
| **R-05** | 用户告知 | P0 Studio **首次预览** 轻 Toast（见 D-CSV-19） |
| **R-06** | 线框 | P0 开工前交付两款静态线框（见附录 C） |
| **R-07** | 对比度 | 新增 **AC-CSV-43** |
| **R-08** | longshot | 新增 **AC-CSV-44** |
| **R-09** | Dock 浅底 | 新增 **AC-CSV-45** |
| **R-10** | KPI | 新增 **G-CSV-09** telemetry |

---

## 2. 目标与非目标

### 2.1 产品目标

| ID | 目标 | 验收口径 |
|----|------|----------|
| **G-CSV-01** | 三种 Web 封面皮肤可用 | `card-br` / `split-mat` / `magazine-head` 均可渲染 |
| **G-CSV-02** | 新建时自动分配 | `create_trip` 写入 `meta.coverOpeningStyle` |
| **G-CSV-03** | 分配稳定 | 同一 `tripId` 多次 `render` 样式不变 |
| **G-CSV-04** | 均匀分布 | 大样本创建时三种样式占比 ≈ 33%（±统计误差） |
| **G-CSV-05** | 一屏完整 | 各样式 title/hook 截断后仍无封面纵向溢出 |
| **G-CSV-06** | V4 能力保留 | Icon Dock、`card-br` 默认皮肤、书名可编辑、HetangYuese 书名体 |
| **G-CSV-07** | 向后兼容 | 缺字段的老 trip 渲染为 `card-br` |
| **G-CSV-08** | Share 一致 | `?share=1` / 导出 HTML 使用 trip 内样式 |
| **G-CSV-09** | 可观测 | telemetry 记录 `coverOpeningStyle`（创建时 1 次、首次 Web 渲染 1 次） |

### 2.2 非目标

- **不** 改动 `cover-opening.hbs` 块清单（不新增 Logo 区、英文装饰条等非 meta 字段）
- **不** 在 P0 提供 Studio 封面样式切换 UI（P1）
- **不** 定义 Mobile 三套皮肤（P2 另立项）
- **不** 改动封面 **选图** 算法（`coverAssetId` / `coverByLayout`）
- **不** 改动任务舱 / Sheet / Icon Dock 业务逻辑
- **不** 要求三种样式共用 V4 右下卡 **同一尺寸上限**（各样式独立 AC）

---

## 3. 已拍板决策（D-CSV · v1.1）

### 3.1 数据与分配

| ID | 决策 | 说明 |
|----|------|------|
| **D-CSV-01** | 字段路径 = `meta.coverOpeningStyle` | 字符串枚举，见 §4.1 |
| **D-CSV-02** | 写入时机 = `create_trip()` | Studio 导入、CLI `trip create` 同源 |
| **D-CSV-03** | 分配算法 = `tripId` 确定性哈希 | `styles[hash(tripId) % 3]`；**禁止** `random()` 无种子 |
| **D-CSV-04** | 权重 = 1:1:1 | 枚举顺序固定：`card-br`, `split-mat`, `magazine-head` |
| **D-CSV-05** | 缺省 / 非法值 = `card-br` | 老 trip、手改 JSON 容错 |
| **D-CSV-06** | rerender **不** 重算样式 | 仅读取 trip 已有值 |

### 3.2 渲染与 DOM

| ID | 决策 | 说明 |
|----|------|------|
| **D-CSV-07** | HTML 绑定 = `data-cover-opening="<style>"` | 加在 `<section class="cover-opening">` 或 `<html>`；**推荐 section** |
| **D-CSV-08** | 块结构不变 | 仍：`cover-hero` + `cover-opening__panel`（place / trip-meta / title / hook） |
| **D-CSV-09** | `data-layout=web` **与** `auto` 均应用三套皮肤 | `mobile` 忽略 `coverOpeningStyle` |
| **D-CSV-10** | Share / draft / 长图 HTML 同源 | `assemble.py` 统一输出属性 |

### 3.3 文案与字体（继承 V4 实施后现状）

| ID | 决策 | 说明 |
|----|------|------|
| **D-CSV-11** | 封面日期/天数 | **方案 A**：Web 封面 **不展示** `trip-meta`（仅保留 `cover-opening__place` 若有） |
| **D-CSV-12** | 无「进入正文」装饰文案 | V4 后续已移除；V5 **不恢复** |
| **D-CSV-13** | 书名字体 | `HetangYuese`（`--font-handwriting`）+ **微软雅黑栈兜底** |
| **D-CSV-14** | title 可编辑 | Studio 点击书名编辑；三种皮肤均须支持；**输入框宽度随 panel 区域**，三款体验一致 |
| **D-CSV-15** | `magazine-head` title 对齐 | **居中**（R-01） |
| **D-CSV-16** | `magazine-head` 高度预算 | header **`min-height: 20vh`；`max-height: 32vh`**；`cover-hero` **≥ 58vh**（R-02） |
| **D-CSV-17** | 新皮肤色值 | 仅使用 **§4.6** token；禁止散落 hex（R-03） |
| **D-CSV-18** | 窄屏 Web 回落 | `@media (max-width: 1023px)` 下 `split-mat` / `magazine-head` **CSS 呈现等同 `card-br`**；`data-cover-opening` 属性保持 trip 原值（R-04） |
| **D-CSV-19** | 首次预览告知 | Studio 首次进入该 trip 预览时 **轻 Toast 一次**（非 Modal）：「这本游记的封面版式已为你选定（电脑与手机版式不同），可在「排版」设置中更换」；`localStorage` 键按 `tripId` 去重（R-05） |
| **D-CSV-20** | 线框门禁 | P0 编码开工前须有 **附录 C** 两款静态线框（R-06） |
| **D-CSV-21** | 系列感 | 三套皮肤共用 §4.6 **圆角 / 阴影 / 衬纸** token，避免三款像独立产品 |
| **D-CSV-22** | Mobile 说明 | Studio 帮助或预览区脚注一句：**「手机预览封面版式与电脑不同，以手机效果为准」** |

---

## 4. 封面样式目录

### 4.1 枚举定义

| 值 | 显示名 | 说明 | 状态 |
|----|--------|------|------|
| `card-br` | 右下书名卡 | 现网 V4：全幅摄影 + 右下实心卡 | **已上线**，作默认 |
| `split-mat` | 分屏衬纸 | 摄影区 + 侧栏（或右栏）实色文案区；白边/画框感 | **P0 新增** |
| `magazine-head` | 杂志顶题 | 上方杂志式大标题区 + 分隔线 + 下方大图 | **P0 新增** |

```json
"meta": {
  "coverOpeningStyle": "split-mat"
}
```

**Schema（P0 须合入 `trip.schema.json`）**

```json
"coverOpeningStyle": {
  "type": "string",
  "enum": ["card-br", "split-mat", "magazine-head"],
  "description": "Web cover opening layout skin; assigned at trip create"
}
```

### 4.2 样式 A · `card-br`（基线 · 已上线）

| 属性 | 规格 |
|------|------|
| **构图** | `cover-hero` 全幅 `absolute inset:0`；`cover-opening__panel` 右下浮动实心卡 |
| **参考** | Cover V4 实施后现状（1.6× 书名卡、无进入正文、HetangYuese 书名） |
| **CSS 范围** | 现有 `journal.css` V4 规则；`data-cover-opening="card-br"` 显式匹配或作为 default |
| **一屏** | `cover-opening` = `100dvh`（`--preview-toolbar-h: 0`） |

> **说明**：`card-br` 行为以 **当前已合并代码** 为准，本 PRD 不回退 V4 初稿 400px 上限。

### 4.3 样式 B · `split-mat`（P0 新增）

**用户参考**：商务画册排版 — 白边画框 + 摄影主区 + **右侧实色文案块**（棕/深色衬纸）。

| 层级 | 行为 |
|------|------|
| L0 `cover-opening` | `100dvh`；衬纸底 **`var(--cover-mat-ground)`**；内边距画框 **`var(--cover-mat-frame-pad)`** |
| L1 `cover-hero` | 占左侧主区（CSS Grid **`1.45fr 1fr`**，约 58/42）；`border-radius: var(--cover-mat-radius)` |
| L2 `cover-opening__panel` | 占右侧文案区；实色底 **`var(--cover-mat-panel-bg)`** |
| 文案色 | **`var(--cover-mat-panel-text)`**（深衬纸 + 白字） |
| place / title / hook | 纵排左对齐；title 使用 `--font-handwriting` |
| Icon Dock | 仍在右上；z-index 高于画框；须满足 **AC-CSV-45** |
| 无 hook | 隐藏 hook 行后 title 垂直居中或顶对齐，**不得**撑破 `100dvh` |

**线框渊源**：`preview-cover-album-v2` **方案 E**（分屏）+ **方案 F**（画框）融合。  
**高保真线框（R-06）**：[cover-styles-v5-split-mat.html](./wireframes/cover-styles-v5-split-mat.html)

### 4.4 样式 C · `magazine-head`（P0 新增）

**用户参考**：时尚杂志 — **顶部大标题** + 细横线 + 小字 + **下方大幅摄影**。

| 层级 | 行为 |
|------|------|
| L0 `cover-opening` | `100dvh`；`display: flex; flex-direction: column` |
| L1 `cover-opening__panel` | **置顶**（flex `order: -1`）；**`min-height: 20vh`；`max-height: 32vh`**；浅底 **`var(--cover-mag-header-bg)`** |
| L2 分隔线 | `cover-opening__panel` 底边 **`1px solid var(--cover-mag-rule)`**，或 `::after` |
| L3 `cover-hero` | **剩余高度** `flex: 1`；摄影区 **≥ 58vh**；`object-fit: cover` |
| title | **`text-align: center`**；**`clamp(2.25rem, 5.5vw, 3.75rem)`**（略大于另两款）；`--font-handwriting` |
| hook | 小于 title；**居中**；单行或两行 `line-clamp` |
| place | title 上方小字 uppercase；**居中** |
| 无 hook | 仅 title + place，header 区 **`min-height: 20vh`** 保证不塌陷 |

**线框渊源**：方案 E **上下颠倒**（文上拍下）。  
**高保真线框（R-06）**：[cover-styles-v5-magazine-head.html](./wireframes/cover-styles-v5-magazine-head.html)

### 4.5 三种样式共用约束

| 约束 | 说明 |
|------|------|
| 块 ID 不变 | `data-block="cover-opening"` 等保持，供 inline-edit / breath 绑定 |
| trip-meta | Web 封面 **隐藏**（方案 A） |
| title `line-clamp` | 最多 **2 行** |
| hook `line-clamp` | 最多 **2 行** |
| 溢出 | `cover-opening { overflow: hidden }` |
| focal | 沿用 `cover-hero` `--focal-x/y`；`split-mat` / `magazine-head` 须验横竖图 |
| 系列感 | 圆角、阴影、衬纸色统一引用 **§4.6** token（D-CSV-21） |
| 短书名 | title 1–2 字（如「林芝」）时 panel 须有 **最小内边距**，不得贴边 |
| 窄屏 Web | **&lt;1024px** CSS 回落 `card-br` 布局（D-CSV-18）；`data-cover-opening` 保持 trip 原值 |

### 4.6 设计 token 表（R-03 · 规范性）

定义于 `journal.css` `:root` 或 `html[data-layout="web"]` 作用域。**实现禁止**使用本表外色值。

| Token | 值 / 引用 | 用途 |
|-------|-----------|------|
| `--cover-mat-ground` | `var(--bg-page)` 或 `#f4f1ea` | `split-mat` 衬纸底 |
| `--cover-mat-frame-pad` | `max(16px, 2vw)` | `split-mat` 画框内边距 |
| `--cover-mat-panel-bg` | `#3d2b1f` | `split-mat` 右侧文案区底 |
| `--cover-mat-panel-text` | `#f5f3f0` | `split-mat` 文案色 |
| `--cover-mag-header-bg` | `var(--surface)` 或 `#fafafa` | `magazine-head` 顶区底 |
| `--cover-mag-rule` | `var(--border)` | `magazine-head` 分隔线 |
| `--cover-mag-header-text` | `var(--text)` | `magazine-head` 标题区文案 |
| `--cover-mat-radius` | `6px` | 摄影区圆角（三款共用） |
| `--cover-panel-shadow` | `0 8px 32px rgba(0,0,0,0.12)` | `card-br` 卡 / `split-mat` panel 可选阴影 |

> **对比度**：`--cover-mat-panel-text` on `--cover-mat-panel-bg`、`--cover-mag-header-text` on `--cover-mag-header-bg` 须满足 **AC-CSV-43**。

---

## 5. 分配算法（规范性）

### 5.1 伪代码

```python
COVER_OPENING_STYLES = ("card-br", "split-mat", "magazine-head")

def assign_cover_opening_style(trip_id: str) -> str:
    digest = hashlib.sha256(trip_id.encode("utf-8")).hexdigest()
    index = int(digest[:8], 16) % len(COVER_OPENING_STYLES)
    return COVER_OPENING_STYLES[index]
```

### 5.2 要求

| 规则 | 说明 |
|------|------|
| 输入 | 规范化后的 `tripId`（与目录名一致） |
| 输出 | 三者之一，**仅创建时写入一次** |
| 测试 | 固定 `tripId` 快照测试期望样式；分布测试 ≥1000 个 id 计数 |
| 禁止 | `render` / `rerender` / `curate` 内调用分配函数覆盖已有值 |

---

## 6. 渲染绑定

### 6.1 Handlebars

`cover-opening.hbs` **P0 不改结构**。可选 P0 微改：

```handlebars
<section class="cover-opening" data-block="cover-opening" data-cover-opening="{{coverOpeningStyle}}">
```

`coverOpeningStyle` 由 `assemble.py` / `build_render_context` 注入，默认 `card-br`。

### 6.2 HTML 根节点（可选）

不在 `<html>` 重复挂载；**仅 section 级** `data-cover-opening` 即可满足 CSS 作用域。

### 6.3 CSS 组织（`journal.css`）

```css
/* 默认 = card-br（向后兼容无属性） */
html[data-layout="web"] .cover-opening[data-cover-opening="card-br"],
html[data-layout="web"] .cover-opening:not([data-cover-opening]) { /* V4 现规则 */ }

html[data-layout="web"] .cover-opening[data-cover-opening="split-mat"] { /* §4.3 */ }
html[data-layout="web"] .cover-opening[data-cover-opening="magazine-head"] { /* §4.4 */ }

/* 窄屏回落 card-br（D-CSV-18） */
@media (max-width: 1023px) {
  html[data-layout="web"] .cover-opening[data-cover-opening="split-mat"],
  html[data-layout="web"] .cover-opening[data-cover-opening="magazine-head"] {
    /* 应用 card-br 布局规则；data-cover-opening 属性不改动 */
  }
}
```

`data-layout="auto"` 在 `min-width: 48rem` 段 **同 web**；**&lt;1024px** 同样触发回落。

---

## 7. 影响面

| 模块 | 路径 | 变更 |
|------|------|------|
| Schema | `schemas/trip.schema.json` | `meta.coverOpeningStyle` |
| 创建 | `travelogue/services/trip_factory.py` | 分配 + 写入 |
| 渲染上下文 | `travelogue/render/assemble.py` | 注入 `coverOpeningStyle` |
| 模板 | `templates/visual-journal/partials/cover-opening.hbs` | 可选 `data-cover-opening` 属性 |
| 样式 | `templates/visual-journal/journal.css` | §4.6 token + `split-mat` / `magazine-head` + 窄屏回落 |
| Studio 编辑 | `templates/studio/preview-toolbar.js` | 书名编辑三款一致；**首次预览 Toast**（D-CSV-19）；Mobile 说明脚注 |
| 线框 | `docs/wireframes/cover-styles-v5-*.html` | **开工前交付**（R-06） |
| 测试 | `tests/test_cover_styles_v5.py`（新建） | 分配 + 渲染 + 布局 + 回落 |
| 金样 | `tests/test_cover_optimization_v4.py` | `card-br` 回归保持 |
| 文档 | 本 PRD + 实施后 ACCEPTANCE / IMPLEMENTATION | — |

**不改动**：`coverAssetId` 策展、`preview-toolbar` Dock 结构、Mobile `journal.css` 封面段。

---

## 8. 分阶段交付

### 8.1 P0（本 PRD 范围）

**开工门禁（须先于编码）**

| 项 | 交付 |
|----|------|
| 静态线框 `cover-styles-v5-split-mat.html` | ✓（R-06） |
| 静态线框 `cover-styles-v5-magazine-head.html` | ✓（R-06） |

| 项 | 交付 |
|----|------|
| Schema + `create_trip` 分配 | ✓ |
| §4.6 token + `split-mat` + `magazine-head` CSS | ✓ |
| `card-br` 显式选择器 / 默认兼容 + **&lt;1024px 回落** | ✓ |
| 渲染属性 + Share 一致 | ✓ |
| Studio 首次预览 Toast + Mobile 说明脚注 | ✓ |
| telemetry `coverOpeningStyle`（G-CSV-09） | ✓ |
| 单元 / 布局测试 + linzhi 人工抽测 + **5 人走查** | ✓ |
| 文档 | ACCEPTANCE + IMPLEMENTATION |

**预估**：约 3–5 人日（含测试与文档）。

### 8.2 P1（可选 · 非 P0）

| 项 | 说明 |
|----|------|
| Studio 封面样式 **预览 + 切换** | Sheet「排版」Tab 顶部「封面版式」三选一缩略图；切换后 `meta.coverOpeningStyle` 更新 + stale | ✓ |
| 创建前预览「你将得到哪种封面」 | 低优先级 | ⏭ |

### 8.3 P2（另立项）

| 项 | 说明 |
|----|------|
| Mobile 多封面 | 需独立 PRD；竖图逻辑与 Web 不同 |
| 用户权重偏好 / 品牌默认样式 | 运营向 |

---

## 9. 验收标准（AC-CSV）

### 9.1 P0 · 数据与分配

| ID | 给定 | 当 | 则 |
|----|------|-----|-----|
| **AC-CSV-01** | 调用 `create_trip("any-id", …)` | 读取 `trip.json` | `meta.coverOpeningStyle` 存在且为三者之一 |
| **AC-CSV-02** | 固定 `tripId` 样本集（≥10） | 重复创建（不同目录） | 同 id 同样式；分布含三种 |
| **AC-CSV-03** | 已有 `coverOpeningStyle` 的 trip | `render` ×2 | HTML `data-cover-opening` 不变 |
| **AC-CSV-04** | 老 trip 无字段 | `render` | 视为 `card-br` |
| **AC-CSV-05** | 非法枚举值 | `render` | 回退 `card-br`；不崩溃 |

### 9.2 P0 · `card-br` 回归

| ID | 则 |
|----|-----|
| **AC-CSV-10** | `card-br` 与当前 V4 实施后布局一致（右下卡、Dock、一屏） |
| **AC-CSV-11** | `tests/test_cover_optimization_v4.py` 仍通过 |

### 9.3 P0 · `split-mat`

| ID | 给定 | 当 | 则 |
|----|------|-----|-----|
| **AC-CSV-20** | `data-cover-opening=split-mat`，Studio 预览 | 首屏 | `cover-opening` 高度 = `100dvh`（±2px） |
| **AC-CSV-21** | 同上 | 布局 | 可见 **画框/分屏**；摄影区与文案区 **同时可见** |
| **AC-CSV-22** | 长 title + 长 hook | 首屏 | 无纵向滚动；title/hook 各 ≤2 行 |
| **AC-CSV-23** | hook 为空 | 首屏 | 无空白塌陷；title 可读 |
| **AC-CSV-24** | 点击书名编辑 | 编辑 | 输入框可用、宽度随 panel、保存后 rerender 样式仍为 `split-mat` |
| **AC-CSV-25** | `split-mat`，视口 **1023px** | Studio 预览 | **CSS 呈现等同 `card-br`**；`data-cover-opening` 仍为 `split-mat` |

### 9.4 P0 · `magazine-head`

| ID | 给定 | 当 | 则 |
|----|------|-----|-----|
| **AC-CSV-30** | `data-cover-opening=magazine-head` | 首屏 | `100dvh`；**上文下图** 结构 |
| **AC-CSV-31** | 同上 | 标题区 | title 位于摄影上方且 **水平居中** |
| **AC-CSV-32** | 长 title + 长 hook | 首屏 | 无纵向滚动 |
| **AC-CSV-33** | hook 为空 | 首屏 | header 区不塌陷（**≥ 20vh**） |
| **AC-CSV-34** | Share `?share=1` | 加载 | 样式与 draft 一致 |
| **AC-CSV-35** | `magazine-head`，视口 **1023px** | Studio 预览 | **CSS 呈现等同 `card-br`**；`data-cover-opening` 仍为 `magazine-head` |
| **AC-CSV-36** | `magazine-head` | 首屏 | 摄影区高度 **≥ 58vh**（视口 ≥1024px） |

### 9.5 P0 · 跨样式

| ID | 则 |
|----|-----|
| **AC-CSV-40** | `data-layout=mobile` 忽略 `coverOpeningStyle`，布局与现网一致 |
| **AC-CSV-41** | 三种样式均隐藏 Web 封面 `trip-meta`（方案 A） |
| **AC-CSV-42** | 书名字体为 `HetangYuese` 栈（子集缺字时微软雅黑兜底） |
| **AC-CSV-43** | 各样式 **文案区**（panel / header）正文对比度 **≥ 4.5:1**；大标题 **≥ 3:1**（WCAG AA） |
| **AC-CSV-44** | 三种样式 `longshot` 封面首帧无异常裁切或空白条 |
| **AC-CSV-45** | `split-mat` / `magazine-head` 浅底场景下 Icon Dock 图标与胶囊可辨识（对比度或描边） |
| **AC-CSV-46** | 首次 Studio 预览该 trip | 轻 Toast 出现 **一次**；文案含「版式已选定」与「排版」设置引导 |
| **AC-CSV-47** | title 仅 1–2 字 | 三款 panel | 最小内边距，文字不贴边 |

### 9.6 P0 · 视口范围

| ID | 则 |
|----|-----|
| **AC-CSV-50** | **≥1024px** Web 视口下，`split-mat` / `magazine-head` 按 §4.3 / §4.4 完整呈现 |
| **AC-CSV-51** | **&lt;1024px** Web 视口下，不论 trip 样式，封面 **CSS 回落 `card-br`**（D-CSV-18） |

---

## 10. 风险与缓解

| 风险 | 缓解 |
|------|------|
| 分屏在窄 Web 视口破版 | **已拍板**：`&lt;1024px` CSS 回落 `card-br`（D-CSV-18 · AC-CSV-25/35/51） |
| 杂志款上区过高挤掉摄影 | **`max-height: 32vh`** + `line-clamp`；摄影 **≥ 58vh**（D-CSV-16 · AC-CSV-36） |
| 亮/暗摄影与衬纸对比 | 各样式 **自包含** 文案区底色（§4.6 token）；不依赖摄影渐变 |
| 长图截取构图变化 | **AC-CSV-44**；每种样式抽测 `longshot` 封面帧 |
| 与 V4 测试冲突 | `card-br` 显式命名；V4 fixture 写 `data-cover-opening="card-br"` |
| 用户不知道被随机分配 | **AC-CSV-46** 首次预览 Toast；P1 提供切换 |
| 用户满意度不可观测 | **G-CSV-09** telemetry；P1 改样式率看板 |

---

## 11. 开放项（P0 后）

| 项 | 说明 |
|----|------|
| Studio 样式切换 UI | **P1 已交付**；见 O-1 |
| Mobile 多皮肤 | **P2** |
| 第四套皮肤（如横册对开 H） | 需新增枚举 + 线框 |
| 样式与 `export.reading.profile` 联动 | 非 P0 |

---

## 12. 修订记录

| 版本 | 日期 | 变更 |
|------|------|------|
| v1.0.0 | 2026-06-15 | 初稿：三种 Web 封面皮肤、创建时确定性分配、讨论会开放项拍板 |
| v1.1.0 | 2026-06-15 | 跨职能评审收敛：R-01～R-10 并入；§4.6 token；窄屏回落 `card-br`；新增 AC-CSV-25/35/36/43～47/50～51；G-CSV-09；开工线框门禁 |
| v1.1.2 | 2026-06-15 | P1 Studio 切换 UI；G-CSV-09 创建 telemetry；D-CSV-22 脚注；AC-CSV-24/44 测试 |

---

## 附录 A · 与 Cover V4 关系

| 项 | Cover V4 | Cover Styles V5 |
|----|----------|-----------------|
| 默认皮肤 | 右下书名卡 | 命名为 `card-br`，行为不变 |
| DOM | `cover-opening.hbs` | **不改块结构** |
| 顶栏 | Icon Dock | 不变 |
| 进入正文 | 已移除 | 不恢复 |
| 日期 meta | 方案 A 隐藏 | 三种皮肤均适用 |
| Mobile | 不在 V4 范围 | 仍不在 V5 范围 |

## 附录 B · 用户故事

| ID | 作为 | 我想要 | 以便 |
|----|------|--------|------|
| US-CSV-01 | 新用户 | 新建游记时得到不同的封面排版 | 感觉每本相册有独特气质 |
| US-CSV-02 | 分享者 | 封面样式在预览与导出中一致 | 不出现「预览一种、分享另一种」 |
| US-CSV-03 | 开发者 | 固定 tripId 可复现样式 | 测试与排错 |
| US-CSV-04 | 产品演示 | 连建三本 trip 看到三种皮肤 | 展示产品丰富度 |

## 附录 C · 线框与参考图映射

| 皮肤 ID | 用户参考图 | 线框方案 |
|---------|------------|----------|
| `card-br` | —（现网） | V4 右下卡 / 草图 v3 |
| `split-mat` | 商务画册 · 右栏棕块 | 相册 v2 **E + F** → **[cover-styles-v5-split-mat.html](./wireframes/cover-styles-v5-split-mat.html)** |
| `magazine-head` | 时尚杂志 · 顶题 + 下图 | 相册 v2 **E 上下颠倒** → **[cover-styles-v5-magazine-head.html](./wireframes/cover-styles-v5-magazine-head.html)** |
