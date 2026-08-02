# 文档归档候选清单（DOC · hygiene P1）

> Generated **2026-08-02** · **Do not `git mv` without maintainer confirmation.**  
> 本清单只列候选，不搬家。脚本归档见同目录 [ARCHIVE-CANDIDATES.md](./ARCHIVE-CANDIDATES.md)。

扫描范围：`docs/**/*.md` 文首约 60 行内 `| **DOC-STATUS** |` / `| **状态** |` / `| **Status** |`，以及 `docs/` 根上未标注的 `PRD|IMPLEMENTATION|ACCEPTANCE-PHASE*`。

状态口径与 [DOC-STATUS.md](../DOC-STATUS.md) 一致：`active` / `superseded` / `archive`（另见文内 `Closed` / `frozen` / `Done`）。

---

## 汇总

| 档 | 含义 | 数量 | 建议动作 |
|----|------|------|----------|
| **A · 强候选** | 文首已标 Closed / archive / superseded / frozen | **12**（去重后） | **A1 已迁** `2026/qfx-cqa/`；其余见 §A2/A3 |
| **B · Done 待确认** | 文首 `Done`，尚未统一标 archive | **14** | 先补 DOC-STATUS，再决定是否迁 |
| **C · Phase 未标注** | Phase 合同无 Closed/DOC-STATUS | **58** | 先批量盖章（archive 或 active），再搬 |
| **Hold** | Conditional Closed / 仍作现行引用 | **4+** | **禁止归档** |

---

## A · 强候选（可优先搬）

### A1 · Closed（修复包 / 审计包）· **已迁 2026-08-02**

> 正文：[`2026/qfx-cqa/`](./2026/qfx-cqa/) · 根路径留 stub，旧链不断。

| 文档 | 证据 | 现状 |
|------|------|------|
| [PRD-QUALITY-FIXPACK-V1.md](./2026/qfx-cqa/PRD-QUALITY-FIXPACK-V1.md) | DOC-STATUS **Closed** | ✅ archived · stub [`../PRD-QUALITY-FIXPACK-V1.md`](../PRD-QUALITY-FIXPACK-V1.md) |
| [IMPLEMENTATION-QUALITY-FIXPACK-V1.md](./2026/qfx-cqa/IMPLEMENTATION-QUALITY-FIXPACK-V1.md) | **Closed** | ✅ archived · stub |
| [ACCEPTANCE-QUALITY-FIXPACK-V1.md](./2026/qfx-cqa/ACCEPTANCE-QUALITY-FIXPACK-V1.md) | **Closed** | ✅ archived · stub |
| [PRD-CODE-QUALITY-AUDIT-FIXPACK-V1.md](./2026/qfx-cqa/PRD-CODE-QUALITY-AUDIT-FIXPACK-V1.md) | **closed** | ✅ archived · stub |
| [IMPLEMENTATION-CODE-QUALITY-AUDIT-FIXPACK-V1.md](./2026/qfx-cqa/IMPLEMENTATION-CODE-QUALITY-AUDIT-FIXPACK-V1.md) | **closed** | ✅ archived · stub |
| [ACCEPTANCE-CODE-QUALITY-AUDIT-FIXPACK-V1.md](./2026/qfx-cqa/ACCEPTANCE-CODE-QUALITY-AUDIT-FIXPACK-V1.md) | **Closed** | ✅ archived · stub |

### A2 · archive / superseded

| 文档 | 证据 | 备注 |
|------|------|------|
| [PRD-MVP.md](../PRD-MVP.md) | DOC-STATUS **archive** | 已在 DOC-STATUS 登记 |
| [adr/006-media-engines-integration.md](../adr/006-media-engines-integration.md) | DOC-STATUS **superseded** → ADR-007 | ADR 可原地留 superseded，或迁 archive 并在 adr 索引留指针 |
| [PRD-GALLERY-NARRATIVE-RHYTHM-V1.md](../PRD-GALLERY-NARRATIVE-RHYTHM-V1.md) | 状态 **Superseded in direction** → Highlight Gallery | 建议标正式 superseded 后再迁 |
| [PRD-PHASE8-photo-semantic-clustering.md](../PRD-PHASE8-photo-semantic-clustering.md) | Draft · **Superseded by ADR-012 + Phase 12** | |

### A3 · frozen（默认原地；可选归档）

| 文档 | 证据 | 备注 |
|------|------|------|
| [UI-DETAIL-CONTRACT-V0.md](../UI-DETAIL-CONTRACT-V0.md) | DOC-STATUS **frozen** | 尺子类合同，**建议先留根**，仅在索引标 frozen |
| [P17-LSE-处置建议.md](../P17-LSE-处置建议.md) | CAP 边界 FROZEN | 工程参考；迁前确认无活跃链接依赖 |

---

## B · Done 待确认（先盖章，再搬）

文首已写 **Done**，但多数未进 DOC-STATUS 登记表。建议统一改文首为 `DOC-STATUS: archive`（或 `active` 若仍作现行工程说明），再进入搬家 PR。

| 文档 | 证据摘要 |
|------|----------|
| [PRD-ASSERTION-HARDENING-V1.md](../PRD-ASSERTION-HARDENING-V1.md) | Done · 有结案 |
| [PRD-LONGSHOT-COOPERATIVE-CANCEL-V1.md](../PRD-LONGSHOT-COOPERATIVE-CANCEL-V1.md) | Done · 已合 master |
| [PRD-STABLE-QUALITY-HARDENING-V1.md](../PRD-STABLE-QUALITY-HARDENING-V1.md) | Done · PR #12 |
| [PRD-STUDIO-FE-TEST-HARDENING-V1.md](../PRD-STUDIO-FE-TEST-HARDENING-V1.md) | Done（本机） |
| [IMPLEMENTATION-STUDIO-FE-TEST-HARDENING-V1.md](../IMPLEMENTATION-STUDIO-FE-TEST-HARDENING-V1.md) | Done（本机） |
| [IMPLEMENTATION-IMPORT-SHEET-RETIRE.md](../IMPLEMENTATION-IMPORT-SHEET-RETIRE.md) | Done · P0～P4 |
| [ACCEPTANCE-PREVIEW-DELETE-GUARD-V1.md](../ACCEPTANCE-PREVIEW-DELETE-GUARD-V1.md) | 自动化门禁 Done |
| [IMPLEMENTATION-COPY-OPTIMIZATION.md](../IMPLEMENTATION-COPY-OPTIMIZATION.md) | P0–P4 Done |
| [IMPLEMENTATION-FINE-CRAFT-LAYOUT-DENSITY.md](../IMPLEMENTATION-FINE-CRAFT-LAYOUT-DENSITY.md) | Core/Hardening Done |
| [IMPLEMENTATION-DESKTOP-INSTALLER-V1.md](../IMPLEMENTATION-DESKTOP-INSTALLER-V1.md) | Smoke/Gate 准备 Done（安装主合同可能仍 active——迁前核对 PRD） |
| [IMPLEMENTATION-P9-F1.md](../IMPLEMENTATION-P9-F1.md) | Done |
| [IMPLEMENTATION-PHASE10.md](../IMPLEMENTATION-PHASE10.md) | Done |
| [IMPLEMENTATION-PHASE11.md](../IMPLEMENTATION-PHASE11.md) | W1/W2 Done |
| [IMPLEMENTATION-PHASE12.md](../IMPLEMENTATION-PHASE12.md) | W1/W2 Done |
| [PRD-PHASE9.md](../PRD-PHASE9.md) | W1 Done（整 Phase 是否 archive 另议） |

---

## C · Phase 合同未标注（58）

`docs/` 根上 `PRD|IMPLEMENTATION|ACCEPTANCE-PHASE*` 在文首 60 行内**未**出现 Closed / DOC-STATUS。  
多为历史 Phase 列车，**不宜直接搬**；建议下一 PR：

1. 批量盖 `DOC-STATUS: archive`（已合入且无继任合同的 Phase），或  
2. 对仍被 README「阅读顺序」引用的 Phase 2–5 盖 `archive` 并在导读改为「考古链」。

完整文件名列表（按字母序）：

<details>
<summary>展开 58 个 Phase 未标注文件</summary>

- ACCEPTANCE-PHASE10.md
- ACCEPTANCE-PHASE11.md
- ACCEPTANCE-PHASE13.md
- ACCEPTANCE-PHASE14.md
- ACCEPTANCE-PHASE15.md
- ACCEPTANCE-PHASE2.md
- ACCEPTANCE-PHASE22.md
- ACCEPTANCE-PHASE23.md
- ACCEPTANCE-PHASE3.md
- ACCEPTANCE-PHASE4.md
- ACCEPTANCE-PHASE5.md
- ACCEPTANCE-PHASE6.md
- ACCEPTANCE-PHASE7-RAW-GATE.md
- ACCEPTANCE-PHASE7.md
- ACCEPTANCE-PHASE9.md
- IMPLEMENTATION-PHASE13.md
- IMPLEMENTATION-PHASE14.md
- IMPLEMENTATION-PHASE15.md
- IMPLEMENTATION-PHASE16.md
- IMPLEMENTATION-PHASE17.md
- IMPLEMENTATION-PHASE2.md
- IMPLEMENTATION-PHASE21.md
- IMPLEMENTATION-PHASE22.md
- IMPLEMENTATION-PHASE23.md
- IMPLEMENTATION-PHASE3.md
- IMPLEMENTATION-PHASE4.md
- IMPLEMENTATION-PHASE5.md
- IMPLEMENTATION-PHASE6.md
- IMPLEMENTATION-PHASE7-RAW-GATE.md
- IMPLEMENTATION-PHASE7.md
- IMPLEMENTATION-PHASE9.md
- PRD-PHASE10-food-grid.md
- PRD-PHASE11-copy-optimization.md
- PRD-PHASE12.md
- PRD-PHASE13.md
- PRD-PHASE14.md
- PRD-PHASE15-benchmark.md
- PRD-PHASE15-photo-mosaic-evolution.md
- PRD-PHASE16-layout-template-engine.md
- PRD-PHASE17-layout-strategy-engine.md
- PRD-PHASE17-research-stub.md
- PRD-PHASE18-layout-effect-improvement.md
- PRD-PHASE2.md
- PRD-PHASE21-mosaic-density-budget.md
- PRD-PHASE22-storage-platform.md
- PRD-PHASE23-peak-moment.md
- PRD-PHASE3.md
- PRD-PHASE4.md
- PRD-PHASE5.md
- PRD-PHASE6-ART-OPTIMIZATION.md
- PRD-PHASE6.md
- PRD-PHASE7-RAW-GATE.md
- PRD-PHASE7.md
- PRD-PHASE9-A-quality-gate-algorithm.md
- PRD-PHASE9-B-pipeline-integration.md
- PRD-PHASE9-C-data-model.md
- PRD-PHASE9-D-studio-ux.md
- PRD-PHASE9-E-subject-bridge.md

</details>

---

## Hold · 禁止归档

| 文档 | 原因 |
|------|------|
| [PRD-SMART-SHOT-GROUPING-V1.md](../PRD-SMART-SHOT-GROUPING-V1.md) 及 SSG IMPL/ACCEPTANCE / closeout | **Conditional Closed** · DOC-STATUS 仍 **active** · 默认 on Hold |
| 一切文首 **active** / Draft / Conditional Go | 现行或在研合同 |
| [DOC-STATUS.md](../DOC-STATUS.md) 本身 | 状态机入口，永不归档 |

---

## 建议下一波执行顺序（仍不在本 PR）

1. ~~**A1**：QFX + CQA 六件套~~ → ✅ [`2026/qfx-cqa/`](./2026/qfx-cqa/)（根 stub）。  
2. **A2**：MVP + Phase8 superseded + Gallery rhythm（ADR-006 优先原地标 superseded）。  
3. **B**：逐个确认 Done → 盖 `archive` 后迁。  
4. **C**：Phase 批量盖章；README「新人阅读顺序」改为短现行链 + 「历史 Phase」折叠区。

刷新本清单：对文首状态字段再扫一遍即可；勿与 [ARCHIVE-CANDIDATES.md](./ARCHIVE-CANDIDATES.md)（脚本）混用。
