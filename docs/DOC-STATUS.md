# 文档状态机（CSC W3c · D-CSC-06）

| 属性 | 内容 |
|------|------|
| **状态** | **active**（本页即状态登记入口） |
| **日期** | 2026-08-02（导读刷新；登记表仍按合入增量扩） |
| **PRD** | [PRD-COMPLETION-SURFACE-CONVERGENCE-V1.md](./PRD-COMPLETION-SURFACE-CONVERGENCE-V1.md) §7.3 |
| **归档候选** | [archive/DOC-ARCHIVE-CANDIDATES.md](./archive/DOC-ARCHIVE-CANDIDATES.md) |

---

## 状态枚举

| 状态 | 含义 | 读者默认动作 |
|------|------|----------------|
| **active** | 当前有效；实施与验收以此为准 | 优先阅读 / 可引用 |
| **superseded** | 已被更新文档取代；保留历史 | 跟链接去新文；勿新开实施 |
| **archive** | 历史冻结；不再演进 | 仅考古 / 对照 |

标注方式（任选其一，与本登记表一致即可）：

1. 文首表格增加一行 `| **DOC-STATUS** | active |`  
2. 或 HTML 注释：`<!-- DOC-STATUS: superseded -->`

W3c **不要求**一次清库；本波先钉机制 + ≥5 篇示范，后续按 PR 扩表。

---

## 现行导读（D-CSC-06 · 2026-08 刷新）

按此顺序读「现在有效」的合同，避免误读 superseded / archive。索引页同步：[README.md](./README.md) §现行导读。

1. [CHARTER.md](./CHARTER.md)  
2. [TECH-ARCHITECTURE.md](./TECH-ARCHITECTURE.md)（现行工程骨架）→ [DEVELOPMENT.md](./DEVELOPMENT.md)  
3. 活跃 ADR（例：[adr/007-native-clustering.md](./adr/007-native-clustering.md)；索引 [adr/README.md](./adr/README.md)）  
4. [ACCEPTANCE.md](./ACCEPTANCE.md) → 特性验收如 [ACCEPTANCE-COMPLETION-SURFACE-CONVERGENCE-V1.md](./ACCEPTANCE-COMPLETION-SURFACE-CONVERGENCE-V1.md)  
5. 完工与用户面：[PRD-FINISH-THIS-TRIP-V1.md](./PRD-FINISH-THIS-TRIP-V1.md) / [PRD-COMPLETION-SURFACE-CONVERGENCE-V1.md](./PRD-COMPLETION-SURFACE-CONVERGENCE-V1.md) / [PRD-NO-AI-SURFACE-V1.md](./PRD-NO-AI-SURFACE-V1.md)  
6. 布局 / 算法现行：[PRD-ALGORITHM-OPTIMIZATION-V3.md](./PRD-ALGORITHM-OPTIMIZATION-V3.md)（主题包 MTSO / MSA / MEGC / SSG 见本表）  
7. 归档候选（**不搬家**）：[archive/DOC-ARCHIVE-CANDIDATES.md](./archive/DOC-ARCHIVE-CANDIDATES.md)

---

## 归档策略（P1 · 清单先行）

| 档 | 动作 |
|----|------|
| **Closed / archive / superseded** | 可进入搬家 PR；见候选清单 §A（**A1 QFX+CQA 已迁** [`archive/2026/qfx-cqa/`](./archive/2026/qfx-cqa/)） |
| **frozen** | 默认原地保留，索引标明即可 |
| **Done（未盖 DOC-STATUS）** | 先盖章再迁；见 §B |
| **Phase 未标注** | 先批量盖章；见 §C |
| **Conditional Closed** | **禁止归档**（例：SSG） |

本波只维护清单与导读；`git mv` 另开 PR，且需 maintainer 确认。

---

## 示范登记（≥5）

| 文档 | DOC-STATUS | 说明 |
|------|-------------|------|
| [PRD-COMPLETION-SURFACE-CONVERGENCE-V1.md](./PRD-COMPLETION-SURFACE-CONVERGENCE-V1.md) | **active** | CSC 产品合同 |
| [IMPLEMENTATION-COMPLETION-SURFACE-CONVERGENCE-V1.md](./IMPLEMENTATION-COMPLETION-SURFACE-CONVERGENCE-V1.md) | **active** | CSC 实施清单 |
| [ACCEPTANCE-COMPLETION-SURFACE-CONVERGENCE-V1.md](./ACCEPTANCE-COMPLETION-SURFACE-CONVERGENCE-V1.md) | **active** | CSC 验收合同 |
| [acceptance-records/csc-root-cause-cure-2026-07-22.md](./acceptance-records/csc-root-cause-cure-2026-07-22.md) | **active** | Recipe 根治决议 |
| [adr/007-native-clustering.md](./adr/007-native-clustering.md) | **active** | 原生聚类（当前有效） |
| [PRD-POST-MERGE-UX-FIXPACK-V1.md](./PRD-POST-MERGE-UX-FIXPACK-V1.md) | **active** | CSC+SFI 合入后 UX 修复包 v0.2 |
| [IMPLEMENTATION-POST-MERGE-UX-FIXPACK-V1.md](./IMPLEMENTATION-POST-MERGE-UX-FIXPACK-V1.md) | **active** | 合入后修复包 · RCA + 实施清单 |
| [ACCEPTANCE-POST-MERGE-UX-FIXPACK-V1.md](./ACCEPTANCE-POST-MERGE-UX-FIXPACK-V1.md) | **active** | PMX 验收合同 |
| [acceptance-records/post-merge-ux-trial-2026-07-22.md](./acceptance-records/post-merge-ux-trial-2026-07-22.md) | **active** | 合入后完整 UX 走查 + 冒烟底稿 |
| [UI-DETAIL-CONTRACT-V0.md](./UI-DETAIL-CONTRACT-V0.md) | **frozen** | Studio UI 细节审计尺子（Wave1–10 收口） |
| [acceptance-records/ui-detail-wave2-settings-sheet-2026-07-22.md](./acceptance-records/ui-detail-wave2-settings-sheet-2026-07-22.md) | **active** | Wave2 Settings+Sheet |
| [acceptance-records/ui-detail-wave3-preview-chrome-2026-07-22.md](./acceptance-records/ui-detail-wave3-preview-chrome-2026-07-22.md) | **active** | Wave3 Preview chrome+Help |
| [acceptance-records/ui-detail-wave4-wait-tips-2026-07-22.md](./acceptance-records/ui-detail-wave4-wait-tips-2026-07-22.md) | **active** | Wave4 wait-tips tip-tone |
| [acceptance-records/ui-detail-wave5-cap-narrow-lightbox-2026-07-22.md](./acceptance-records/ui-detail-wave5-cap-narrow-lightbox-2026-07-22.md) | **active** | Wave5 Cap+Narrow+Lightbox |
| [acceptance-records/ui-detail-wave6-bench-wizard-carousel-2026-07-22.md](./acceptance-records/ui-detail-wave6-bench-wizard-carousel-2026-07-22.md) | **active** | Wave6 Bench+Wizard+Carousel |
| [acceptance-records/ui-detail-wave7-home-tokens-2026-07-22.md](./acceptance-records/ui-detail-wave7-home-tokens-2026-07-22.md) | **active** | Wave7 Homepage tokens |
| [acceptance-records/ui-detail-wave8-shelf-dev-loading-2026-07-22.md](./acceptance-records/ui-detail-wave8-shelf-dev-loading-2026-07-22.md) | **active** | Wave8 Shelf+Dev+Loading |
| [acceptance-records/ui-detail-wave9-overlay-toast-2026-07-22.md](./acceptance-records/ui-detail-wave9-overlay-toast-2026-07-22.md) | **active** | Wave9 Overlay+Toast |
| [acceptance-records/ui-detail-wave10-wizard-help-closeout-2026-07-22.md](./acceptance-records/ui-detail-wave10-wizard-help-closeout-2026-07-22.md) | **active** | Wave10 Wizard+Help+Closeout |
| [acceptance-records/ui-detail-wave11-runtime-2026-07-22.md](./acceptance-records/ui-detail-wave11-runtime-2026-07-22.md) | **active** | Wave11 Runtime+Contract freeze |
| [PRD-KEEP-ALL-PHOTOS-V1.md](./PRD-KEEP-ALL-PHOTOS-V1.md) | **active** | P9-F3 全部保留模式（**v0.1.3** · 回填仍执行 · 跳低清仅显式 keep_all） |
| [archive/2026/qfx-cqa/PRD-QUALITY-FIXPACK-V1.md](./archive/2026/qfx-cqa/PRD-QUALITY-FIXPACK-V1.md) | **archive**（Closed） | QFX **v0.2.1** · 已迁（根 stub · [Acceptance](./archive/2026/qfx-cqa/ACCEPTANCE-QUALITY-FIXPACK-V1.md) · [评审](./acceptance-records/quality-fixpack-v1-review-2026-07-22.md)） |
| [PRD-COMMERCIALIZATION-MVP-V1.md](./PRD-COMMERCIALIZATION-MVP-V1.md) | **active** | 商业化 MVP **CMZ** **v0.1.0**（Draft · 买断 + 离线许可 + 导出墙） |
| [PRD-MOSAIC-TEMPLATE-SELECTION-OPTIMIZATION-V1.md](./PRD-MOSAIC-TEMPLATE-SELECTION-OPTIMIZATION-V1.md) | **active** | 拼图模板选型与使用优化 **MTSO** **v0.2.0**（Conditional Go · 可 Kickoff M1 · [评审](./acceptance-records/mtso-mosaic-template-selection-v1-review-2026-07-23.md)） |
| [acceptance-records/mtso-mosaic-template-selection-v1-review-2026-07-23.md](./acceptance-records/mtso-mosaic-template-selection-v1-review-2026-07-23.md) | **active** | MTSO 七席联评 · Conditional Go · BLK-01～08 · 可 Kickoff M1 |
| [acceptance-records/mtso-dev-feasibility-2026-07-23.md](./acceptance-records/mtso-dev-feasibility-2026-07-23.md) | **active** | MTSO 开发负责人实施前可行性 · SUP 默认已认可 |
| [IMPLEMENTATION-MOSAIC-TEMPLATE-SELECTION-OPTIMIZATION-V1.md](./IMPLEMENTATION-MOSAIC-TEMPLATE-SELECTION-OPTIMIZATION-V1.md) | **active** | MTSO 实施 **v0.2.0** · PR-A～C2 ✅ · PR-D 进行中 |
| [ACCEPTANCE-MOSAIC-TEMPLATE-SELECTION-OPTIMIZATION-V1.md](./ACCEPTANCE-MOSAIC-TEMPLATE-SELECTION-OPTIMIZATION-V1.md) | **active** | MTSO 验收 · AC-01～10/13（AC-11/12 待狗粮盲评） |
| [acceptance-records/mtso-local-dogfood-GUIDE.md](./acceptance-records/mtso-local-dogfood-GUIDE.md) | **active** | MTSO 本机短狗粮 GUIDE |
| [acceptance-records/mtso-mosaic-template-selection-v1-review-TEMPLATE.md](./acceptance-records/mtso-mosaic-template-selection-v1-review-TEMPLATE.md) | **active** | MTSO 七席评审纪要**模板**（结案见日期版） |
| [PRD-SMART-SHOT-GROUPING-V1.md](./PRD-SMART-SHOT-GROUPING-V1.md) | **active** | 智能分镜 **SSG** **v0.2.1** · Conditional Closed（实拍盲评另填） |
| [IMPLEMENTATION-SMART-SHOT-GROUPING-V1.md](./IMPLEMENTATION-SMART-SHOT-GROUPING-V1.md) | **active** | SSG 实施 · PR-A～F ✅ |
| [ACCEPTANCE-SMART-SHOT-GROUPING-V1.md](./ACCEPTANCE-SMART-SHOT-GROUPING-V1.md) | **active** | SSG 验收 · Conditional Closed |
| [acceptance-records/ssg-m3-closeout-2026-07-23.md](./acceptance-records/ssg-m3-closeout-2026-07-23.md) | **active** | SSG M3 结案 |
| [acceptance-records/ssg-local-dogfood-GUIDE.md](./acceptance-records/ssg-local-dogfood-GUIDE.md) | **active** | SSG 本机狗粮指南 |
| [acceptance-records/ssg-default-on-decision-2026-07-23.md](./acceptance-records/ssg-default-on-decision-2026-07-23.md) | **active** | SSG 默认 on **Hold** |
| [acceptance-records/ssg-look-threshold-calibration-2026-07-23.md](./acceptance-records/ssg-look-threshold-calibration-2026-07-23.md) | **active** | SSG PR-E · deltaThreshold=0.28 锁定 |
| [acceptance-records/ssg-smart-shot-grouping-v1-review-2026-07-23.md](./acceptance-records/ssg-smart-shot-grouping-v1-review-2026-07-23.md) | **active** | SSG 七席联评 · Conditional Go · BLK-01～08 |
| [acceptance-records/ssg-dev-feasibility-2026-07-23.md](./acceptance-records/ssg-dev-feasibility-2026-07-23.md) | **active** | SSG 开发可行性 · SUP-01～10 **已会签** |
| [acceptance-records/ssg-smart-shot-grouping-v1-review-TEMPLATE.md](./acceptance-records/ssg-smart-shot-grouping-v1-review-TEMPLATE.md) | **active** | SSG 七席评审纪要**模板**（结案见日期版） |
| [acceptance-records/ssg-blind-review-TEMPLATE.md](./acceptance-records/ssg-blind-review-TEMPLATE.md) | **active** | SSG 盲评记录模板 |
| [PRD-MOSAIC-SLOT-ADAPTATION-V1.md](./PRD-MOSAIC-SLOT-ADAPTATION-V1.md) | **active** | 拼图槽位自适应 **MSA** **v0.2.0**（Conditional Go · 可 Kickoff M0 · [评审](./acceptance-records/msa-mosaic-slot-adaptation-v1-review-2026-07-23.md)） |
| [IMPLEMENTATION-MOSAIC-SLOT-ADAPTATION-V1.md](./IMPLEMENTATION-MOSAIC-SLOT-ADAPTATION-V1.md) | **active** | MSA 实施 · M0～PR-C + gap-close ✅ · 默认仍 off · AC-09 待盲评 |
| [ACCEPTANCE-MOSAIC-SLOT-ADAPTATION-V1.md](./ACCEPTANCE-MOSAIC-SLOT-ADAPTATION-V1.md) | **active** | MSA 验收 · AC-01～08/10/11 ✅ · AC-09 待实册盲评 |
| [PRD-MOSAIC-EQUAL-GRID-CONTRACT-V1.md](./PRD-MOSAIC-EQUAL-GRID-CONTRACT-V1.md) | **active** | 等权拼图几何合同 **MEGC** **v0.2.0**（Conditional Go · 可 Kickoff M0/M1 · [评审](./acceptance-records/megc-equal-grid-contract-v1-review-2026-07-31.md)） |
| [IMPLEMENTATION-MOSAIC-EQUAL-GRID-CONTRACT-V1.md](./IMPLEMENTATION-MOSAIC-EQUAL-GRID-CONTRACT-V1.md) | **active** | MEGC 实施 · M0 ✅ · PR-A 可 Kickoff · M3 延期 |
| [ACCEPTANCE-MOSAIC-EQUAL-GRID-CONTRACT-V1.md](./ACCEPTANCE-MOSAIC-EQUAL-GRID-CONTRACT-V1.md) | **active** | MEGC 验收 · AC-01～10 · W0 七席门 ✅ |
| [acceptance-records/megc-equal-grid-contract-v1-review-2026-07-31.md](./acceptance-records/megc-equal-grid-contract-v1-review-2026-07-31.md) | **active** | MEGC 七席联评 · Conditional Go · BLK-01～08 |
| [acceptance-records/megc-dev-feasibility-2026-07-31.md](./acceptance-records/megc-dev-feasibility-2026-07-31.md) | **active** | MEGC 开发负责人实施前可行性 · PR-A Go · PR-B 待 SUP |
| [acceptance-records/megc-equal-grid-contract-v1-review-TEMPLATE.md](./acceptance-records/megc-equal-grid-contract-v1-review-TEMPLATE.md) | **active** | MEGC 七席评审纪要**模板** |
| [config-megc-dogfood.example.yaml](./config-megc-dogfood.example.yaml) | **active** | MEGC 本机狗粮配置样例（默认勿开） |
| [acceptance-records/msa-contain-visual-contract-BLK06.md](./acceptance-records/msa-contain-visual-contract-BLK06.md) | **active** | MSA BLK-06 contain 杂志纸色视觉合同 |
| [acceptance-records/msa-local-dogfood-GUIDE.md](./acceptance-records/msa-local-dogfood-GUIDE.md) | **active** | MSA 本机狗粮 GUIDE |
| [acceptance-records/msa-blind-review-TEMPLATE.md](./acceptance-records/msa-blind-review-TEMPLATE.md) | **active** | MSA 盲评记录模板 |
| [acceptance-records/msa-default-on-decision-2026-07-23.md](./acceptance-records/msa-default-on-decision-2026-07-23.md) | **active** | MSA 默认 on 决策 · **hold off** |
| [acceptance-records/msa-mosaic-slot-adaptation-v1-review-2026-07-23.md](./acceptance-records/msa-mosaic-slot-adaptation-v1-review-2026-07-23.md) | **active** | MSA 七席联评 · Conditional Go · BLK-01～08 |
| [acceptance-records/msa-mosaic-slot-adaptation-v1-review-TEMPLATE.md](./acceptance-records/msa-mosaic-slot-adaptation-v1-review-TEMPLATE.md) | **active** | MSA 七席评审纪要**模板**（结案见日期版） |
| [archive/2026/qfx-cqa/IMPLEMENTATION-QUALITY-FIXPACK-V1.md](./archive/2026/qfx-cqa/IMPLEMENTATION-QUALITY-FIXPACK-V1.md) | **archive**（Closed） | QFX 实施 · PR-A/B/C/C2/D 已合 master |
| [archive/2026/qfx-cqa/ACCEPTANCE-QUALITY-FIXPACK-V1.md](./archive/2026/qfx-cqa/ACCEPTANCE-QUALITY-FIXPACK-V1.md) | **archive**（Closed） | QFX AC-01～27 · `quality_fixpack_gate` |
| [archive/2026/qfx-cqa/PRD-CODE-QUALITY-AUDIT-FIXPACK-V1.md](./archive/2026/qfx-cqa/PRD-CODE-QUALITY-AUDIT-FIXPACK-V1.md) | **archive**（Closed） | CQA · 根 stub 保留旧链 |
| [archive/2026/qfx-cqa/IMPLEMENTATION-CODE-QUALITY-AUDIT-FIXPACK-V1.md](./archive/2026/qfx-cqa/IMPLEMENTATION-CODE-QUALITY-AUDIT-FIXPACK-V1.md) | **archive**（Closed） | CQA 实施 |
| [archive/2026/qfx-cqa/ACCEPTANCE-CODE-QUALITY-AUDIT-FIXPACK-V1.md](./archive/2026/qfx-cqa/ACCEPTANCE-CODE-QUALITY-AUDIT-FIXPACK-V1.md) | **archive**（Closed） | CQA 验收 |
| [acceptance-records/quality-fixpack-v1-review-2026-07-22.md](./acceptance-records/quality-fixpack-v1-review-2026-07-22.md) | **active** | QFX 七席跨职能评审 · Conditional Go · 系统根因与根本解法 |
| [PRD-NO-AI-SURFACE-V1.md](./PRD-NO-AI-SURFACE-V1.md) | **active** | NAS 用户面现行合同（**v0.2.3** · status 403 + config 投影收口 · Conditional Go） |
| [IMPLEMENTATION-NO-AI-SURFACE-V1.md](./IMPLEMENTATION-NO-AI-SURFACE-V1.md) | **active** | NAS 实施 **v0.2.2** · status 403 · config 投影 · 对齐 QFX |
| [ACCEPTANCE-NO-AI-SURFACE-V1.md](./ACCEPTANCE-NO-AI-SURFACE-V1.md) | **active** | NAS 验收 AC-NAS-01～17 · OUT-01～05 指针 · v0.1.2 e2e/DOC 勾选 |
| [acceptance-records/no-ai-surface-v1-review-2026-07-22.md](./acceptance-records/no-ai-surface-v1-review-2026-07-22.md) | **active** | NAS 跨职能评审 · Conditional Go · MF 已回写 PRD v0.2 |
| [acceptance-records/no-ai-surface-v1-e2e-doc-closeout-2026-07-22.md](./acceptance-records/no-ai-surface-v1-e2e-doc-closeout-2026-07-22.md) | **active** | NAS e2e/DOC-NAS-02 收口 · 2026-07-22 |
| [PRD-AI-RETURN-V1.md](./PRD-AI-RETURN-V1.md) | **active** | **AIR** AI-Return **v0.1.0** Draft · 解冻最小包 · 三语气 · 渠道 pack v2 · 迟晒（承接 NAS §14） |
| [PRD-COVER-ART-DIRECTION-V1.md](./PRD-COVER-ART-DIRECTION-V1.md) | **active** | **CAD** 封面装帧导演 **v0.1.0** Draft · Mode A 默认真照片 · 禁假风景默认 |
| [PRD-DESKTOP-LLM-SETUP-V1.md](./PRD-DESKTOP-LLM-SETUP-V1.md) | **active（engineering）** | 写作引擎工程栈仍有效；**用户面由 NAS supersede**（解冻后由 AIR 重新激活用户面） |
| [PRD-WRITING-ENGINE-API-HARDENING-V1.md](./PRD-WRITING-ENGINE-API-HARDENING-V1.md) | **active（engineering）** | WEA 配置加固仍有效；默认 UI 入口由 NAS 关闭（AIR 解冻后恢复） |
| [UI-DETAIL-CONTRACT-V0.md](./UI-DETAIL-CONTRACT-V0.md) | **frozen** | Studio 弹窗家族细节合同 · Wave1–10 样式落地 |
| [UI-DETAIL-SURFACE-INVENTORY-V0.md](./UI-DETAIL-SURFACE-INVENTORY-V0.md) | **active** | UI Detail 表面清单 / 波次索引 |
| [adr/006-media-engines-integration.md](./adr/006-media-engines-integration.md) | **superseded** | 双引擎方案 → 见 ADR-007 |
| [PRD-MVP.md](./PRD-MVP.md) | **archive** | MVP 已冻结；产品演进见后续 Phase PRD |

---

## 维护

- 新 PRD / IMPLEMENTATION 合入时：在本表加一行，并在文首标 `DOC-STATUS`。  
- 取代旧文时：旧文改 `superseded`，并写清继任链接；本表同步。  
- 索引：[README.md](./README.md) 顶部「文档状态」链到本页。
