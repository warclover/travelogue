# PRD-EXPERIENCE · 附录 C · Folio 版式

| 属性 | 内容 |
|------|------|
| **主文档** | [PRD-EXPERIENCE.md](./PRD-EXPERIENCE.md) |
| **域** | L2a 版式 skin · scroll / present · Agent 3 |
| **Epic** | E2（lite）· E7（full） |
| **参考** | [Folio 625](https://templatemo.com/live/templatemo_625_folio_slideshow) |
| **更新** | 2026-05-27 |

> 配置：`export.reading.scroll.folio` → `off | lite | full`。longshot **强制 off**。

---

## 1. 目的

借鉴 Folio **画册式信息架构**（三层 meta / display / body），**不**照搬整站 slideshow deck。

---

## 2. 三层信息架构

```
┌────────────────────────────────────┐
│ L1 元数据带（Mono · 页眉/页脚）      │
├────────────────────────────────────┤
│ L2 Display（Serif 大标题 / 全幅图）  │
├────────────────────────────────────┤
│ L3 Body（Sans · caption / 索引）    │
└────────────────────────────────────┘
```

---

## 3. 版式原型 → Travelogue 映射

| Folio 屏 | 块 / pattern | folio 档位 |
|----------|--------------|------------|
| Cover | `cover-hero` + `trip-meta` 增强 | lite+ |
| Foreword | `foreword-spread` | full |
| Plate I | **`screen-plate`** | lite+ |
| Index | **`trip-index`** | full |
| Spread | **`screen-spread`** | full |
| Selected | **`featured-grid`** | full |
| Colophon | **`epilogue-screen`** | lite+ |

Press / More 页 **不借鉴**。

---

## 4. folio 档位

| 档位 | 包含 |
|------|------|
| `off` | 现版 |
| `lite` | Cover 分层 + `screen-plate` + epilogue 大字号 |
| `full` | lite + index + foreword-spread + spread + featured-grid |

| profile | folio |
|---------|-------|
| legacy / performance | off |
| default_hybrid | lite |
| magazine | full |

---

## 5. 新增 pattern / block（规划）

### 5.1 `screen-plate`

- 1 slot · landscape/panorama · full-bleed  
- `.plate-meta-top` / `.plate-meta-bot`  
- caption **框外** `.plate-caption`  
- 素材：附录 A `userTier: featured` 或章 hero  

### 5.2 其他 block

| block | 说明 |
|-------|------|
| `trip-index` | 四列文字目录；锚点 `#ch-xx` |
| `foreword-spread` | 1:2 分栏；首章 lead |
| `screen-spread` | 1 图 + 文案栏 + pull quote |
| `featured-grid` | 4 列 portrait 卡片；**与 screens 去重** |
| `epilogue-screen` | display 大字 + epilogue |

### 5.3 manifest 扩展（规划）

`screen-plate` · `screen-spread` 加入 `manifest.json` screens 白名单。

---

## 6. 设计 Token

```css
:root[data-folio="on"] {
  --folio-paper: #faf8fc;
  --folio-ink: #2d1f3a;
  --folio-accent: var(--screen-tone, #c8956c);
  --folio-meta-font: ui-monospace, monospace;
  --folio-display-font: var(--font-serif, Georgia, serif);
  --folio-ease: cubic-bezier(0.19, 1, 0.22, 1);
}
```

纸感 overlay：opacity ≤0.06；不抢照片。

---

## 7. Curate 规则（与附录 A）

| 规则 | 说明 |
|------|------|
| 章首 plate | featured 横/全景 → `screen-plate` |
| featured-grid | featured≥4 且 folio full |
| grid 与 screens | **同一 asset 不可重复** |
| plate 占 1 screen 槽 | 替换原首屏 pattern，不增屏数 |

`curation.folioPlan`（规划）：

```json
{ "index": true, "foreword": true, "featuredGrid": true, "plateAssetIds": [] }
```

---

## 8. 表面

| 表面 | folio |
|------|-------|
| index.html web | profile 驱动 |
| mobile / longshot | **off** |
| present | plate **页码 meta** 可开 |
| share zip | **off** |

---

## 9. 验收（附录 C）

| ID | 通过条件 |
|----|----------|
| AC-FO-01 | lite · plate + metadata 带 |
| AC-FO-02 | featured → screen-plate |
| AC-FO-03 | full · trip-index 可跳章 |
| AC-FO-04 | featured≥4 → grid；无 mobile |
| AC-FO-05 | folio off → golden 回归 |
| AC-FO-06 | longshot smoke PASS |
| AC-FO-07 | manifest 白名单 |
| AC-FO-08 | 无 featured → hero fallback |

→ **AC-EXP-05、AC-EXP-11**

---

## 10. Epic E7 任务

| 任务 | 说明 |
|------|------|
| folio lite CSS | Cover + plate + epilogue |
| screen-plate 模板 | hbs + planner |
| folio full blocks | index · spread · grid |
| render 注入 | `data-folio="on"` |

---

## 11. 实现锚点

`journal.css` · `manifest.json` · `screen_planner.py` · `render/engine.py`

---

## 12. 开放问题

1. 中文 display 断行：narrate vs render heuristic → E7 前定  
2. Index desc：lead 首句 vs curate 自动生成 → 倾向 **chapterPlan**  
3. Plate 编号：罗马数字 vs 「第 N 章」→ 倾向 **中文章序**
