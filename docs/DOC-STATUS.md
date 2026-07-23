# 文档状态机（CSC W3c · D-CSC-06）

| 属性 | 内容 |
|------|------|
| **状态** | **active**（本页即状态登记入口） |
| **日期** | 2026-07-22 |
| **PRD** | [PRD-COMPLETION-SURFACE-CONVERGENCE-V1.md](./PRD-COMPLETION-SURFACE-CONVERGENCE-V1.md) §7.3 |

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

## 现行导读（D-CSC-06）

按此顺序读「现在有效」的合同，避免误读 superseded / archive：

1. [CHARTER.md](./CHARTER.md)  
2. [TECH-ARCHITECTURE.md](./TECH-ARCHITECTURE.md)（现行工程骨架）  
3. 活跃 ADR（例：[adr/007-native-clustering.md](./adr/007-native-clustering.md)）  
4. [ACCEPTANCE.md](./ACCEPTANCE.md) 索引 → 特性验收如 [ACCEPTANCE-COMPLETION-SURFACE-CONVERGENCE-V1.md](./ACCEPTANCE-COMPLETION-SURFACE-CONVERGENCE-V1.md)  
5. [PRD-FINISH-THIS-TRIP-V1.md](./PRD-FINISH-THIS-TRIP-V1.md) / [PRD-COMPLETION-SURFACE-CONVERGENCE-V1.md](./PRD-COMPLETION-SURFACE-CONVERGENCE-V1.md)

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
| [PRD-QUALITY-FIXPACK-V1.md](./PRD-QUALITY-FIXPACK-V1.md) | **Closed** | 日更质量修复包 QFX **v0.2.1** · Closed（[Acceptance](./ACCEPTANCE-QUALITY-FIXPACK-V1.md) · [评审](./acceptance-records/quality-fixpack-v1-review-2026-07-22.md)） |
| [PRD-COMMERCIALIZATION-MVP-V1.md](./PRD-COMMERCIALIZATION-MVP-V1.md) | **active** | 商业化 MVP **CMZ** **v0.1.0**（Draft · 买断 + 离线许可 + 导出墙） |
| [PRD-MOSAIC-TEMPLATE-SELECTION-OPTIMIZATION-V1.md](./PRD-MOSAIC-TEMPLATE-SELECTION-OPTIMIZATION-V1.md) | **active** | 拼图模板选型与使用优化 **MTSO** **v0.2.0**（Conditional Go · 可 Kickoff M1 · [评审](./acceptance-records/mtso-mosaic-template-selection-v1-review-2026-07-23.md)） |
| [acceptance-records/mtso-mosaic-template-selection-v1-review-2026-07-23.md](./acceptance-records/mtso-mosaic-template-selection-v1-review-2026-07-23.md) | **active** | MTSO 七席联评 · Conditional Go · BLK-01～08 · 可 Kickoff M1 |
| [acceptance-records/mtso-dev-feasibility-2026-07-23.md](./acceptance-records/mtso-dev-feasibility-2026-07-23.md) | **active** | MTSO 开发负责人实施前可行性 · SUP 默认已认可 |
| [IMPLEMENTATION-MOSAIC-TEMPLATE-SELECTION-OPTIMIZATION-V1.md](./IMPLEMENTATION-MOSAIC-TEMPLATE-SELECTION-OPTIMIZATION-V1.md) | **active** | MTSO 实施 **v0.2.0** · PR-A～C2 ✅ · PR-D 进行中 |
| [ACCEPTANCE-MOSAIC-TEMPLATE-SELECTION-OPTIMIZATION-V1.md](./ACCEPTANCE-MOSAIC-TEMPLATE-SELECTION-OPTIMIZATION-V1.md) | **active** | MTSO 验收 · AC-01～10/13（AC-11/12 待狗粮盲评） |
| [acceptance-records/mtso-local-dogfood-GUIDE.md](./acceptance-records/mtso-local-dogfood-GUIDE.md) | **active** | MTSO 本机短狗粮 GUIDE |
| [acceptance-records/mtso-mosaic-template-selection-v1-review-TEMPLATE.md](./acceptance-records/mtso-mosaic-template-selection-v1-review-TEMPLATE.md) | **active** | MTSO 七席评审纪要**模板**（结案见日期版） |
| [PRD-MOSAIC-SLOT-ADAPTATION-V1.md](./PRD-MOSAIC-SLOT-ADAPTATION-V1.md) | **active** | 拼图槽位自适应 **MSA** **v0.2.0**（Conditional Go · 可 Kickoff M0 · [评审](./acceptance-records/msa-mosaic-slot-adaptation-v1-review-2026-07-23.md)） |
| [IMPLEMENTATION-MOSAIC-SLOT-ADAPTATION-V1.md](./IMPLEMENTATION-MOSAIC-SLOT-ADAPTATION-V1.md) | **active** | MSA 实施 **v0.1.0** · M0 ✅ · M1 未 Kickoff |
| [ACCEPTANCE-MOSAIC-SLOT-ADAPTATION-V1.md](./ACCEPTANCE-MOSAIC-SLOT-ADAPTATION-V1.md) | **active** | MSA 验收 · AC-01～11（含 05v/05p）· W0 门已齐 |
| [acceptance-records/msa-mosaic-slot-adaptation-v1-review-2026-07-23.md](./acceptance-records/msa-mosaic-slot-adaptation-v1-review-2026-07-23.md) | **active** | MSA 七席联评 · Conditional Go · BLK-01～08 |
| [acceptance-records/msa-mosaic-slot-adaptation-v1-review-TEMPLATE.md](./acceptance-records/msa-mosaic-slot-adaptation-v1-review-TEMPLATE.md) | **active** | MSA 七席评审纪要**模板**（结案见日期版） |
| [IMPLEMENTATION-QUALITY-FIXPACK-V1.md](./IMPLEMENTATION-QUALITY-FIXPACK-V1.md) | **Closed** | QFX 实施 Closed · PR-A/B/C/C2/D 已合 master |
| [ACCEPTANCE-QUALITY-FIXPACK-V1.md](./ACCEPTANCE-QUALITY-FIXPACK-V1.md) | **Closed** | QFX AC-01～27 结案勾选 · `quality_fixpack_gate` |
| [acceptance-records/quality-fixpack-v1-review-2026-07-22.md](./acceptance-records/quality-fixpack-v1-review-2026-07-22.md) | **active** | QFX 七席跨职能评审 · Conditional Go · 系统根因与根本解法 |
| [PRD-NO-AI-SURFACE-V1.md](./PRD-NO-AI-SURFACE-V1.md) | **active** | NAS 用户面现行合同（**v0.2.3** · status 403 + config 投影收口 · Conditional Go） |
| [IMPLEMENTATION-NO-AI-SURFACE-V1.md](./IMPLEMENTATION-NO-AI-SURFACE-V1.md) | **active** | NAS 实施 **v0.2.2** · status 403 · config 投影 · 对齐 QFX |
| [ACCEPTANCE-NO-AI-SURFACE-V1.md](./ACCEPTANCE-NO-AI-SURFACE-V1.md) | **active** | NAS 验收 AC-NAS-01～17 · OUT-01～05 指针 · v0.1.2 e2e/DOC 勾选 |
| [acceptance-records/no-ai-surface-v1-review-2026-07-22.md](./acceptance-records/no-ai-surface-v1-review-2026-07-22.md) | **active** | NAS 跨职能评审 · Conditional Go · MF 已回写 PRD v0.2 |
| [acceptance-records/no-ai-surface-v1-e2e-doc-closeout-2026-07-22.md](./acceptance-records/no-ai-surface-v1-e2e-doc-closeout-2026-07-22.md) | **active** | NAS e2e/DOC-NAS-02 收口 · 2026-07-22 |
| [PRD-DESKTOP-LLM-SETUP-V1.md](./PRD-DESKTOP-LLM-SETUP-V1.md) | **active（engineering）** | 写作引擎工程栈仍有效；**用户面由 NAS supersede** |
| [PRD-WRITING-ENGINE-API-HARDENING-V1.md](./PRD-WRITING-ENGINE-API-HARDENING-V1.md) | **active（engineering）** | WEA 配置加固仍有效；默认 UI 入口由 NAS 关闭 |
| [UI-DETAIL-CONTRACT-V0.md](./UI-DETAIL-CONTRACT-V0.md) | **frozen** | Studio 弹窗家族细节合同 · Wave1–10 样式落地 |
| [UI-DETAIL-SURFACE-INVENTORY-V0.md](./UI-DETAIL-SURFACE-INVENTORY-V0.md) | **active** | UI Detail 表面清单 / 波次索引 |
| [adr/006-media-engines-integration.md](./adr/006-media-engines-integration.md) | **superseded** | 双引擎方案 → 见 ADR-007 |
| [PRD-MVP.md](./PRD-MVP.md) | **archive** | MVP 已冻结；产品演进见后续 Phase PRD |

---

## 维护

- 新 PRD / IMPLEMENTATION 合入时：在本表加一行，并在文首标 `DOC-STATUS`。  
- 取代旧文时：旧文改 `superseded`，并写清继任链接；本表同步。  
- 索引：[README.md](./README.md) 顶部「文档状态」链到本页。
