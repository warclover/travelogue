# Travelogue Studio · 双端布局 PRD（Wide / Compact）

| 属性 | 内容 |
|------|------|
| **产品代号** | Travelogue Studio |
| **文档版本** | v1.0.0 |
| **状态** | **Implemented · 2026-05-31** |
| **代号** | **P10-Layout**（Studio 响应式双形态；与 P8 回归矩阵、P9 极易用正交） |
| **页面** | `GET /` → `templates/studio/studio.html` |
| **关联** | [PRD-STUDIO-HOMEPAGE.md](./PRD-STUDIO-HOMEPAGE.md) · [PRD-PHASE4.md](./PRD-PHASE4.md) · [wireframes/studio-homepage-photo-first-v3.html](./wireframes/studio-homepage-photo-first-v3.html) · `tests/test_studio_p8_regression.py` |
| **更新日期** | 2026-05-31 |

---

## 1. 背景与问题

### 1.1 现状

Studio 首页采用 **单 HTML + CSS `@media`** 适配，断点主要为 `980px`、`768px`、`480px`。核心约束：

| 元素 | 当前限制 | 用户感知 |
|------|----------|----------|
| `#studio-hero-importing` | `max-width: 540px` | 回访导入时进度区偏窄 |
| `.studio-import__panel` | `max-width: 420px` | 主文案「第 N 步…（已处理 x/y 张）」频繁换行 |
| 导入时间 | 已统一为 `#studio-import-estimate` 单行整体预估 | ✅ P10 前置修复已完成 |

### 1.2 产品定位澄清

| 场景 | 典型设备 | 主入口 |
|------|----------|--------|
| **Wide** | Windows 本机浏览器、≥981px 窗口 | `pick-folder` / 路径栏 |
| **Tablet** | 窄窗、iPad 竖屏、768–980px | 同 wide，布局单列 hybrid |
| **Compact** | ≤768px、手机浏览器 | Sheet 全屏 + 小文件夹上传 / 路径 |

Studio **不是**移动 App；Compact 形态服务于「窄窗 / 偶发手机访问本机」，功能与 Wide **一致**，仅 **presentation 与入口优先级** 可分叉。

### 1.3 与游记双 HTML 的关系

| 层 | 策略 |
|----|------|
| **Studio Hub** (`/`) | 单页 + `data-studio-layout` 三档（**不**另建 `/m`） |
| **Trip 预览** | 继续 `index.html` / `index-mobile.html` 分工 |

---

## 2. 目标与非目标

### 2.1 目标

| ID | 目标 | 衡量 |
|----|------|------|
| **G-P10-01** | Wide 导入主文案在常见桌面宽度下 **单行可读**（含 `已处理 N/M`） | 1280px 手测 + P8 CSS 断言 |
| **G-P10-02** | Compact 导入信息 **两行层级**清晰，无横向溢出 | 390px 手测 |
| **G-P10-03** | 三入口 × 五状态在 **wide / compact** 下功能等价 | P8 矩阵扩展 |
| **G-P10-04** | 布局切换 **不重启** import job / 不丢 sessionStorage | 现有状态机不变 |
| **G-P10-05** | 能力检测（pick-folder）与布局检测 **解耦** | `data-studio-layout` ≠ `data-cap-*` |

### 2.2 非目标

- 独立移动路由 `/m` 或第二套 `studio-mobile.html`
- User-Agent 判「手机型号」
- 改变 import API、job 阶段数、预估时间算法
- Trip 预览页 layout 改造（属 Experience PRD）

---

## 3. 设计原则

### 3.1 双轴检测

```
布局轴（viewport）          能力轴（platform / API）
──────────────────          ────────────────────────
data-studio-layout          pick-folder 可用 → 主 CTA 浏览文件夹
  wide    >980px            不可用 → Sheet 内上传 / 路径（已有）
  tablet  769–980px
  compact ≤768px
```

- **禁止**用 UA 字符串决定业务逻辑。
- **允许**用 `matchMedia('(max-width: …)')` + `resize` 更新 `document.documentElement.dataset.studioLayout`。
- pick-folder 成败 **不**改变 layout tier；仅影响 Sheet / Hero CTA 文案与显隐（已有 P4/P9 逻辑）。

### 3.2 功能一致 · 表现可分叉

| 模块 | Wide | Compact |
|------|------|---------|
| 状态机 | 同一 `transitionTo` | 同左 |
| Importing 文案 | 单行：`第 N 步… · 标签（hint）` | 两行：eyebrow + body |
| Import panel 宽度 | `min(920px, 92vw)`，panel `width:100%` | `width:100%`，padding 收紧 |
| Returning Hero | hybrid 左文案 + 右 3 卡 | 单列：文案上、卡片区下 |
| Success / Failed | 居中 overlay，max-width 适度放宽 | 全宽 padding，按钮 stack |
| Sheet | 居中 modal | 底 sheet 全宽（已有 `@media`） |

### 3.3 断点定义（冻结）

| Tier | 条件 | 说明 |
|------|------|------|
| `compact` | `width ≤ 768px` | 对齐现有 `@media (max-width: 768px)` |
| `tablet` | `769px ≤ width ≤ 980px` | hybrid → 单列（已有） |
| `wide` | `width > 980px` | 导入 panel 加宽、单行文案 |

> **命名**：使用 `data-studio-layout`，避免与游记 `data-layout="web|mobile"` 混淆。

---

## 4. 分状态 UI 规格

### 4.1 Importing（P0 · 本 PRD 首要）

**DOM 结构（增量）**

```html
<div class="studio-import__panel">
  <ol class="studio-import__stages">…</ol>
  <p class="studio-import__step-eyebrow" id="studio-stage-eyebrow" hidden>第 1 步，共 4 步</p>
  <p class="studio-import__step" id="studio-stage">…</p>
  <p id="studio-import-estimate" class="studio-import__estimate">预计整体约 …</p>
  …
</div>
```

**Wide**

- `#studio-hero-importing`：`max-width: min(920px, 92vw)`
- `.studio-import__panel`：去掉 `420px` 上限；`padding: 20px clamp(16px, 3vw, 28px)`
- `#studio-stage-eyebrow`：`display: none`
- `#studio-stage`：`white-space: nowrap; overflow: hidden; text-overflow: ellipsis`（≥769px）
- 时间：仅 `#studio-import-estimate` 一行（已实现）

**Compact**

- `#studio-stage-eyebrow`：显示，12–13px，字间距略宽，opacity 0.72
- `#studio-stage`：仅阶段标签 + hint，允许换行；**不含**「第 N 步」前缀
- 四步 pill：保持 4 列；若溢出则 `grid-template-columns: repeat(2, 1fr)`（≤480px 可选）

**JS**

- `progress.js` · `applyImportStageCopy(job)`：读 `data-studio-layout`，分别写入 eyebrow / stage
- `updateProgress` 调用上述函数；`aria-valuetext` 仍为完整一句

### 4.2 Empty / Returning

| 项 | Wide | Compact |
|----|------|---------|
| Hero | `--hybrid` 1280 grid | 单列（已有 980 规则） |
| 主 CTA | 横排 gold + ghost | 全宽 stack（已有 768） |
| 近期 3 卡 | 3 列 | 1 列（已有 980） |
| 样张 strip | deferred 展开 | 同左 |

**本阶段**：无新增 DOM；仅确认 980/768 规则与 `data-studio-layout` 一致。

### 4.3 Success / Failed / Loading

| 项 | Wide | Compact |
|----|------|---------|
| 容器 max-width | `min(640px, 92vw)` → 可放宽至 `720px` | `100%` + 水平 padding |
| 封面 transition | 保持 | 保持；`prefers-reduced-motion` 跳过 |

### 4.4 Import Sheet

- 已有 bottom sheet 移动端样式；Wide 保持居中宽 sheet。
- Compact：**禁止** pick-folder 失败静默降级上传（PRD 冻结，不变）。

---

## 5. 技术方案

### 5.1 模块划分

| 文件 | 职责 |
|------|------|
| `templates/studio/js/viewport.js` | `initViewport()` · `syncStudioLayout()` · `getStudioLayout()` |
| `templates/studio/js/progress.js` | `applyImportStageCopy()` · 双形态文案 |
| `templates/studio/studio.css` | `html[data-studio-layout="wide\|compact\|tablet"]` 规则块 |
| `templates/studio/studio.js` | `DOMContentLoaded` 调用 `initViewport()` |

### 5.2 状态存储

- **不**写入 `localStorage`（布局随窗口即时变化）。
- **不**在 `S` 对象存 layout（读 DOM attribute 即可，避免 render 漏同步）。

### 5.3 无障碍

- `#studio-stage` 保持 `aria-live="polite"`；eyebrow 在 compact 下 `aria-hidden="false"`，wide 下 hidden。
- 进度条 `aria-valuetext` = 完整语义句（含步序 + hint + 预估由 estimate 行单独可读）。

---

## 6. 实施任务清单

| ID | 优先级 | 任务 | 文件 | 状态 |
|----|--------|------|------|------|
| **P10-L01** | P0 | 新增 `viewport.js`，初始化 `data-studio-layout` | `js/viewport.js`, `studio.js` | ✅ |
| **P10-L02** | P0 | Wide 导入容器 + panel 加宽 | `studio.css` | ✅ |
| **P10-L03** | P0 | 导入 eyebrow DOM + `applyImportStageCopy` | `studio.html`, `progress.js` | ✅ |
| **P10-L04** | P0 | Compact / Wide 分叉 CSS | `studio.css` | ✅ |
| **P10-L05** | P1 | Success/Failed overlay wide 放宽 | `studio.css` | ✅ |
| **P10-L06** | P1 | ≤480px 导入 pill 2×2 网格 | `studio.css` | ✅ |
| **P10-L07** | P1 | Playwright：390 vs 1280 导入态 | `tests/test_studio_p10_layout_playwright.py` | ✅ |
| **P10-L08** | P2 | `data-cap-pick-folder` 能力标记 + CTA 显隐 | `config_handlers.py`, `capabilities.js`, `studio.css` | ✅ |
| **P10-L09** | P2 | Wireframe v3 同步标注三档 layout | `wireframes/…` | ✅ |

**状态**：P10-L01～L09 已全部交付（2026-05-31）；后续补项：AC-P10-03 resize 文案刷新、Success/Failed Playwright、Loading compact、experience-matrix（2026-05-30）。

---

## 7. P8 回归矩阵扩展

在现有 **3 入口 × 5 状态** 静态断言基础上，增加 **layout 契约**（不倍增 e2e）：

### 7.1 原矩阵（保持）

|  | Empty | Returning | Importing | Success | Failed |
|--|-------|-----------|-----------|---------|--------|
| **path** | ✓ | ✓ | ✓ | ✓ | ✓ |
| **upload** | ✓ | ✓ | ✓ | ✓ | ✓ |
| **demo** | ✓ | ✓ | ✓ | ✓ | ✓ |

### 7.2 新增 Layout 契约（静态 · P8）

| ID | 断言 |
|----|------|
| **P8-L01** | 存在 `viewport.js` + `initViewport` + `data-studio-layout` |
| **P8-L02** | CSS 含 `html[data-studio-layout="wide"]` 导入 panel 加宽规则 |
| **P8-L03** | CSS 含 compact 显示 `#studio-stage-eyebrow` |
| **P8-L04** | HTML 含 `studio-stage-eyebrow` |
| **P8-L05** | `progress.js` 含 `applyImportStageCopy` |
| **P8-L06** | wide 导入 `#studio-stage` 有 nowrap（≥769 媒体块内） |
| **P8-L07** | 980px 块 recent-list 单列（已有 P8 测试，保持） |
| **P8-L08** | Success/Failed wide overlay `min(720px)` |
| **P8-L09** | `capabilities.js` + `data-cap-pick-folder` |

### 7.3 手测矩阵（发布前）

| layout | 入口 | 状态 | 检查点 |
|--------|------|------|--------|
| wide 1280 | path | Importing | 主文案单行；estimate 一行 |
| wide 1280 | upload | Success | 封面 transition + 按钮可点 |
| compact 390 | upload | Importing | eyebrow + body 两行；无溢出 |
| compact 390 | demo | Failed | hint + 重试 |
| tablet 834 | path | Returning | hybrid 单列、3 卡变 1 列 |

---

## 8. 验收标准

| ID | Given | Then |
|----|-------|------|
| **AC-P10-01** | 1280px，Importing，123 张照片 | 主 status **一行**（ellipsis 可接受）；estimate **一行** |
| **AC-P10-02** | 390px，Importing | eyebrow 与 body **分行**；无横向 scroll |
| **AC-P10-03** | 窗口从 1280 拖至 390 | job 继续；文案形态切换；无 JS 错误 |
| **AC-P10-04** | pytest `test_studio_p8_regression` | 含 P8-L01–L09 全绿 |
| **AC-P10-05** | 三入口导入成功 | wide/compact 均到达 Success，API 无差异 |

---

## 9. 风险与缓解

| 风险 | 缓解 |
|------|------|
| nowrap + ellipsis 截断长 hint | hint 仅 `已处理 N/M`，长度可控 |
| resize 频繁触发 | `syncStudioLayout` 仅写 attribute，无 layout 动画 |
| 与 P9 telemetry 混淆 | layout 事件可选 `trackStudioEvent('layout_tier', { tier })`，P10-L08 |
| 双份文案逻辑 | 单一 `applyImportStageCopy`，禁止 render 里散落字符串 |

---

## 10. 文档与索引更新（实施完成后）

- [x] `PRD-STUDIO-HOMEPAGE.md` §12 增加 M16 · P10-Layout 行
- [x] `docs/experience-matrix.yaml` 增加 `studio.homepage` layout tiers（可选）
- [x] 本文件状态改为 **Implemented** 并标注交付日期

---

## 附录 A · CSS 片段参考（Wide 导入）

```css
html[data-studio-layout="wide"] #studio-hero-importing.studio-hero__content--center {
  max-width: min(920px, 92vw);
}
html[data-studio-layout="wide"] .studio-import__panel {
  width: 100%;
  max-width: none;
}
@media (min-width: 769px) {
  html[data-studio-layout="wide"] #studio-stage {
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
  }
}
```

## 附录 B · 与 P8/P9 边界

| 阶段 | 范围 |
|------|------|
| **P8** | 3×5 状态壳、980 单列、skip link、success 无 countdown |
| **P9** | Empty 减法、demo 回流、failure hint、口语 stage 标签 |
| **P10** | **本 PRD** · viewport 三档 · 导入双形态 · P8 layout 契约扩展 |
