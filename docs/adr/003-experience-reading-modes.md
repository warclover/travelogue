# ADR-003 · 阅读体验：三模式、Hybrid 与配置收敛

| 属性 | 内容 |
|------|------|
| **状态** | 已采纳 |
| **日期** | 2026-05-27 |
| **决策者** | 产品 + 技术负责人 |
| **影响范围** | Agent 0/1/3、模板 JS/CSS、render、`trip.json` export、文档体系 |
| **关联** | [PRD-EXPERIENCE.md](../PRD-EXPERIENCE.md)、[experience-matrix.yaml](../experience-matrix.yaml) |

---

## 背景

1. 四份体验相关 PRD（双文件夹、呼吸感、Folio 版式、阅读模式）配置与路线图分散，易 drift。  
2. 用户需要 **滑动浏览 / 全屏放映 / 长图分享** 三种读法，但必须共用同一 `screens[]` 序列。  
3. 林芝级 trip（78 屏）不能采用整站 slideshow deck；需 Hybrid（scroll 主干 + 可选增强）。  
4. longshot 导出与 inline-edit 与 Lenis/scrub 存在几何冲突，需统一 teardown 规则。

---

## 决策

### D1 · 文档结构：1 主 PRD + 3 附录 + 1 矩阵

| 文档 | 职责 |
|------|------|
| [PRD-EXPERIENCE.md](../PRD-EXPERIENCE.md) | 三模式、Hybrid、profile、路线图、总 AC |
| [PRD-EXPERIENCE-附录A-精选上传.md](../PRD-EXPERIENCE-附录A-精选上传.md) | ingest/curate · `userTier` |
| [PRD-EXPERIENCE-附录B-滚动动效.md](../PRD-EXPERIENCE-附录B-滚动动效.md) | scroll · breath 档位与技术 |
| [PRD-EXPERIENCE-附录C-Folio版式.md](../PRD-EXPERIENCE-附录C-Folio版式.md) | folio 版式 · pattern/block |
| [experience-matrix.yaml](../experience-matrix.yaml) | profile 与降级（机器可读） |

原文件名（`双文件夹.md` 等）保留 **重定向 stub**，不删链。

---

### D2 · 三阅读模式与屏序契约

| 模式 | ID | 入口 | 硬约束 |
|------|-----|------|--------|
| 浏览 | `scroll` | `index.html` 默认 | 主模式 |
| 放映 | `present` | toolbar「放映」· `screenplay.js` | 1 screen = 1 slide |
| 长图 | `longshot` | `index-longshot.html` / 保存长图 | screens 按 slot 展平（**已由 [ADR-020](./020-narrative-contract.md) D5 修订**：默认尊重 `preserveGroup`；仅显式 `false` 时拆屏） |

**屏序**：`trip.chapters[].screens[]` 为唯一顺序源；present/longshot **禁止**独立排序。

---

### D3 · 配置收敛：`export.reading.profile`

| 项 | 决定 |
|----|------|
| **权威命名空间** | `trip.export.reading` |
| **用户可见** | `profile`：`legacy` \| `performance` \| `default_hybrid` \| `magazine` |
| **高级 override** | `reading.scroll.breath` / `folio` / `snap` 等 |
| **废弃别名（1 版本）** | 顶层 `export.breathMode` → `reading.scroll.breath`；解析器兼容后移除 |
| **`userTier`** | **保留**在 `assets[]`；**不**并入 `export.reading` |

**默认**：

| 场景 | profile |
|------|---------|
| 工坊 draft · web | `default_hybrid` |
| share zip | `performance` |
| mobile / longshot 面 | 强制 scroll 增强 off（见 matrix） |

---

### D4 · 合并前开放问题 — 拍板结论

| # | 问题 | **决定** |
|---|------|----------|
| 1 | featured 图能否在 grid 与 screens 各出现一次 | **否**。`featured-grid` 仅索引/导航；正文由 `screen-plate` 等承担；curate 去重 |
| 2 | 默认 profile | **`default_hybrid`** = snap proximity + breath soft + folio lite |
| 3 | share zip 是否降档 | **是** → `performance`（等同 legacy） |
| 4 | mobile 是否开 breath/folio | **12 个月内否**；仅 web `index.html` |
| 5 | present 默认 2s/屏 | **保持**；写入 `reading.present.dwellMs`，可 per-trip 覆盖 |
| 6 | GSAP 进 repo | **E7/E8 再议**；E2（Hybrid 最小包）**禁止**硬依赖 GSAP |
| 7 | 双文件夹是否 G1 必须 | **否**；G1 可选；G2 serve 可升格 `userTier` |
| 8 | URL hash 深链 | **P3 可选** `#present/12`；非 MVP |

---

### D5 · 实施 Epic 顺序（取代四套 P0/P1）

| Epic | 内容 | 阻塞关系 |
|------|------|----------|
| E0 | 屏序契约 + AC-EXP-01 | — |
| E1 | config 壳 + profile 解析 | — |
| E2 | Hybrid 最小包：snap + breath soft + folio lite + toolbar 文案 | 不依赖 userTier |
| E3 | present ↔ scroll sync | — |
| E4 | longshot teardown 统一 API | **须与 E2 同发或紧接** |
| E5 | 双文件夹 ingest + curate 加权 | 内容质量 |
| E6 | breath flow + present featured-only | 可选 |
| E7 | folio full（index/spread/grid） | 可选 |
| E8 | breath cinematic + gallery pin | 独立；林芝慎用 |

---

### D6 · 与子 PRD 能力边界

| 层 | Owner | 文档 |
|----|-------|------|
| L0 素材意图 | Agent 0/1 | 附录 A |
| L1 阅读范式 | 产品 + Agent 3 | 主 PRD |
| L2 版式 skin | Agent 3 | 附录 C |
| L2 滚动动效 | Agent 3 | 附录 B |

**不修改** [PRD-LAYOUT.md](../PRD-LAYOUT.md) 的 screens 算法 FR；Folio 仅增 presentation pattern。

---

## 后果

### 正面

- 单一配置面与验收表；工坊/分享行为可预测。  
- 三模式一致性可自动化（林芝 regression）。  
- 附录可并行维护，主 PRD 控制在决策层。

### 负面 / 缓解

- 文档迁移期存在双链 → 旧文件 stub 保留 1 个里程碑。  
- `export.reading` 字段需同步 schema + DATA-MODEL → E1 一并完成。

---

## 实现清单

- [x] `trip.schema.json` · `export.reading` · `folioPlan` · `userTierSummary`
- [x] `config.yaml` · `render.reading`
- [x] `render/engine.py` 注入 `window.__TRAVELOGUE_READING__`
- [x] `breath.js` / folio CSS · profile 驱动
- [x] `longshot.js` · `breath.teardown()` 钩子
- [x] pytest · AC-EXP-01～03 · AC-EXP-10/12 · P0–P4 子集
- [x] 更新 [DATA-MODEL.md](../DATA-MODEL.md)、[TEMPLATE-SURFACES.md](../TEMPLATE-SURFACES.md)（体验字段见主 PRD / matrix）
- [x] 废弃别名 `export.breathMode` / `folioMode` · `reading_profile.py` 解析

---

## 相关 ADR

- [ADR-001](./001-delivery-and-media.md) · zip 交付、longShot 默认 true  
- [ADR-002](./002-smart-layout-v2-integration.md) · beam 与 legacy 等价护栏
