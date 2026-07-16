# Travelogue · 文档索引

| 属性 | 内容 |
|------|------|
| **产品代号** | Travelogue（游记智能体） |
| **文档体系** | P0 立项 + P0.5 工程执行 + **Phase 2–22** + Studio 首页 v2/M21 + 算法 V2 |
| **更新日期** | 2026-07-16 |

---

## 阅读顺序（新人）

1. [CHARTER.md](./CHARTER.md) → [PRD-MVP.md](./PRD-MVP.md)（MVP · 已冻结）→ [PRD-PHASE2.md](./PRD-PHASE2.md) → [PRD-PHASE3.md](./PRD-PHASE3.md)（Curate 聚类）→ [PRD-PHASE4.md](./PRD-PHASE4.md)（编辑意图 · 杂志心智）→ [PRD-PHASE5.md](./PRD-PHASE5.md)（整体优化 · 做深做透）→ [PRD-PHASE6.md](./PRD-PHASE6.md)（稳态与治理）→ [PRD-PHASE6-ART-OPTIMIZATION.md](./PRD-PHASE6-ART-OPTIMIZATION.md)（艺术专项）→ [PRD-PHASE7.md](./PRD-PHASE7.md)（管线性能）  
2. [AGENT-ARCHITECTURE.md](./AGENT-ARCHITECTURE.md)  
2b. [PRD-LAYOUT.md](./PRD-LAYOUT.md)（排版布局子系统 · Agent 1.5）  
3. [DATA-MODEL.md](./DATA-MODEL.md) + [schemas/trip.schema.json](../schemas/trip.schema.json)  
4. [TEMPLATE-visual-journal.md](./TEMPLATE-visual-journal.md) + [golden.html](../templates/visual-journal/golden.html)  
5. **开发前必读 P0.5**（§下）  
6. [TECH-ARCHITECTURE.md](./TECH-ARCHITECTURE.md) → [DEVELOPMENT.md](./DEVELOPMENT.md)  
7. [ACCEPTANCE.md](./ACCEPTANCE.md)（**单轨验收入口** · Phase 5 发布闸门）→ 按需 [ACCEPTANCE-PHASE2～5](./ACCEPTANCE-PHASE5.md)

---

## Phase 2 · Studio 与可分享体验

| 文档 | 说明 |
|------|------|
| [PRD-PHASE2.md](./PRD-PHASE2.md) | **Phase 2 产品需求**（Studio + export-longshot + 交付物层级） |
| [IMPLEMENTATION-PHASE2.md](./IMPLEMENTATION-PHASE2.md) | **实施任务清单**（M8–M11 · 进度跟踪） |
| [ACCEPTANCE-PHASE2.md](./ACCEPTANCE-PHASE2.md) | Phase 2 验收（AC-P2-01～06） |
| [adr/004-studio-hub-server.md](./adr/004-studio-hub-server.md) | Hub Server vs 单 trip serve |
| [adr/005-longshot-server-side.md](./adr/005-longshot-server-side.md) | Playwright + longshot.js 服务端长图 |

阅读顺序：**PRD-PHASE2** → **IMPLEMENTATION-PHASE2** → ADR-004/005 → 开发时同步 **CLI-SPEC** / **WORKSHOP** / **SHARING**。

---

## Phase 3 · Curate 聚类（原生算法）

| 文档 | 说明 |
|------|------|
| [PRD-PHASE3.md](./PRD-PHASE3.md) | **Phase 3 产品需求** v0.3.3 Kickoff |
| [adr/007-native-clustering.md](./adr/007-native-clustering.md) | 原生聚类架构决策 v0.2（**当前有效**） |
| [adr/006-media-engines-integration.md](./adr/006-media-engines-integration.md) | 双引擎方案（**Superseded**） |
| IMPLEMENTATION-PHASE3.md | 实施任务清单（M12–M14 · **v0.3.3**） |
| ACCEPTANCE-PHASE3.md | Phase 3 验收（**v0.3.3**） |
| docs/spikes/clustering-algorithm-matrix.md | M12-0 算法 Spike（**v0.1 已写**） |

**前置**：Phase 2 ≥ M8b + M9 可用。**代号**：Curate 聚类。**注意**：与 [SHARING.md](./SHARING.md) 中小程序鉴权轨道无关（后者为 **分享 Phase 4**）。

阅读顺序：**PRD-PHASE3** v0.3.3 Kickoff → ADR-007 v0.2 → [智能排版V2.md](./智能排版V2.md) P1 → [IMPLEMENTATION-PHASE3.md](./IMPLEMENTATION-PHASE3.md) → [ACCEPTANCE-PHASE3.md](./ACCEPTANCE-PHASE3.md) → [PRD-STUDIO-HOMEPAGE.md](./PRD-STUDIO-HOMEPAGE.md) §19。

---

## Phase 4 · 编辑意图（Intent Layer + G1）

| 文档 | 说明 |
|------|------|
| [PRD-PHASE4.md](./PRD-PHASE4.md) | **Phase 4 产品需求** v0.4.3（意图层 · 导入 panel · 预览 drawer · 附录 A–C） |
| [IMPLEMENTATION-PHASE4.md](./IMPLEMENTATION-PHASE4.md) | 实施任务清单（M15–M19 · 含真实完成度核查） |
| [ACCEPTANCE-PHASE4.md](./ACCEPTANCE-PHASE4.md) | Phase 4 验收（AC-P4-01～09 · A11Y · P-EVAL） |

**前置**：Phase 2 Studio 可完成导入→预览→长图；Phase 3 建议已合入（成功页可展示行程段数）。**代号**：P4-Intent。**注意**：与分享轨道「小程序 Phase 4」区分。

阅读顺序：**PRD-PHASE4** → **IMPLEMENTATION-PHASE4** → 附录 A 精选上传 → **ACCEPTANCE-PHASE4**。

---

## Phase 5 · 整体优化（Polish · 做深做透）

| 文档 | 说明 |
|------|------|
| [PRD-PHASE5.md](./PRD-PHASE5.md) | **Phase 5 产品需求** v0.5.4（**双路径交付** · 长图 A + 卷轴 B · Tier 0–4） |
| [IMPLEMENTATION-PHASE5.md](./IMPLEMENTATION-PHASE5.md) | Phase 5 实施任务清单（M20–M23） |
| [ACCEPTANCE-PHASE5.md](./ACCEPTANCE-PHASE5.md) | Phase 5 验收（UX-P5-80-01 · UX-P5-SCROLL-01） |
| [PRD-PREVIEW-REFINE-V1.md](./PRD-PREVIEW-REFINE-V1.md) | 预览精修体验 V1（验货默认 · 更新版面 · 导出拦截） |
| [PRD-PREVIEW-REFINE-UX-V1.1.md](./PRD-PREVIEW-REFINE-UX-V1.1.md) | **精修可用性优化 V1.1**（模式≠面板 · 情境对齐 · 导出门面收敛）· **Conditional Go** |
| [IMPLEMENTATION-PREVIEW-REFINE-UX-V1.1.md](./IMPLEMENTATION-PREVIEW-REFINE-UX-V1.1.md) | 精修可用性 V1.1 实施清单（M1–M3 代码就绪） |
| [ACCEPTANCE-PREVIEW-REFINE-UX-V1.1.md](./ACCEPTANCE-PREVIEW-REFINE-UX-V1.1.md) | 精修可用性 V1.1 验收清单（手测待补签） |
| [acceptance-records/preview-refine-ux-v1.1-review-2026-07-14.md](./acceptance-records/preview-refine-ux-v1.1-review-2026-07-14.md) | 精修可用性 V1.1 跨职能评审纪要 |
| [acceptance-records/preview-refine-ux-v1.1-s1-2026-07-14.md](./acceptance-records/preview-refine-ux-v1.1-s1-2026-07-14.md) | 精修可用性 V1.1 · S1 新手脚本手测记录 |
| [acceptance-records/preview-refine-ux-v1.1-dogfood-retest-2026-07-14.md](./acceptance-records/preview-refine-ux-v1.1-dogfood-retest-2026-07-14.md) | 精修可用性 V1.1 · 多角色复测（Playwright） |
| [wireframes/preview-refine-ux-v1.1-wireframe.html](./wireframes/preview-refine-ux-v1.1-wireframe.html) | 精修可用性 V1.1 评审线框 |
| [PRD-PREVIEW-EXPORT-FACADE-V1.md](./PRD-PREVIEW-EXPORT-FACADE-V1.md) | **预览导出门面 V1** v1.1 · Reliability 条件 Go |
| [IMPLEMENTATION-PREVIEW-EXPORT-FACADE-V1.md](./IMPLEMENTATION-PREVIEW-EXPORT-FACADE-V1.md) | 导出门面 V1 实施清单 |
| [ACCEPTANCE-PREVIEW-EXPORT-FACADE-V1.md](./ACCEPTANCE-PREVIEW-EXPORT-FACADE-V1.md) | 导出门面 V1 验收 |
| [acceptance-records/preview-export-facade-v1-review-2026-07-11.md](./acceptance-records/preview-export-facade-v1-review-2026-07-11.md) | 导出门面 V1 跨职能评审纪要 |
| [PRD-UX-TRUST-V1.md](./PRD-UX-TRUST-V1.md) | **试用反馈信任闭环 V1**（文案门禁 · 验货壳 · Share 只读 · 续跑加严 · 平台话术） |
| [ACCEPTANCE-UX-TRUST-V1.md](./ACCEPTANCE-UX-TRUST-V1.md) | 信任闭环 V1 验收 |
| [IMPLEMENTATION-UX-TRUST-V1.md](./IMPLEMENTATION-UX-TRUST-V1.md) | 信任闭环 V1 实施清单 |
| [IMPLEMENTATION-UX-TRUST-V1.md](./IMPLEMENTATION-UX-TRUST-V1.md) | 信任闭环 V1 实施清单 |
| [acceptance-records/ux-trust-v1-review-2026-07-11.md](./acceptance-records/ux-trust-v1-review-2026-07-11.md) | 信任闭环 V1 跨职能评审纪要 · Conditional Go |
| [PRD-HELP-ONBOARDING-V1.md](./PRD-HELP-ONBOARDING-V1.md) | **帮助与情境引导系统 V1** **v1.1.1**（Conditional Go · MF 已回写 · FirstSuccess 方案 A · 可见 tip · 发群兜底 · 可开 W0） |
| [IMPLEMENTATION-HELP-ONBOARDING-V1.md](./IMPLEMENTATION-HELP-ONBOARDING-V1.md) | 帮助系统 V1 · W0–W3 落地说明（V1 编码收口） |
| [wireframes/help-onboarding-v1-wireframe.html](./wireframes/help-onboarding-v1-wireframe.html) | 帮助系统 V1 评审线框 · F1–F10（W1：F1–F3/F7） |
| [acceptance-records/help-onboarding-v1-review-2026-07-14.md](./acceptance-records/help-onboarding-v1-review-2026-07-14.md) | 帮助系统 V1 跨职能评审纪要 · Conditional Go · MF 已回写 |
| [PRD-REFINE-FEEDBACK-LOOP-V1.md](./PRD-REFINE-FEEDBACK-LOOP-V1.md) | **精修意图可感知闭环 V1** **v0.1.3**（Conditional Go · M1+M2+P0+M3 · scope=tier） |
| [IMPLEMENTATION-REFINE-FEEDBACK-LOOP-V1.md](./IMPLEMENTATION-REFINE-FEEDBACK-LOOP-V1.md) | 精修反馈闭环 · M1+M2+P0+M3 落地说明 |
| [ACCEPTANCE-REFINE-FEEDBACK-LOOP-V1.md](./ACCEPTANCE-REFINE-FEEDBACK-LOOP-V1.md) | 精修反馈闭环验收 · AC-FEED + P0 + M3 |
| [wireframes/refine-feedback-loop-v1-wireframe.html](./wireframes/refine-feedback-loop-v1-wireframe.html) | 精修反馈闭环评审线框 · F-BE-01 / F-FEAT-01～03 |

**前置**：Phase 4 M15–M19 代码主线已收口。**代号**：P5-Polish。**决策**：D1–D6 见 PRD §2.2（D4/D5 暂缓）。

阅读顺序：**PRD-PHASE5** →（启动实施时）**IMPLEMENTATION-PHASE5** → **ACCEPTANCE-PHASE5**。  
预览导出加固：**PRD-PREVIEW-REFINE-V1**（已落地）→ **PRD-PREVIEW-REFINE-UX-V1.1**（Conditional Go · 可开 M1）→ **PRD-PREVIEW-EXPORT-FACADE-V1** → **PRD-UX-TRUST-V1**。  
首访帮助：**PRD-HELP-ONBOARDING-V1** **v1.1.1**（Conditional Go · FirstSuccess 方案 A · 脉冲+可见 tip · 发群三要素兜底 · 对齐精修 V1.1「完成≠更新版面」；不做全站 tour）。  
精修反馈闭环：**PRD-REFINE-FEEDBACK-LOOP-V1** **v0.1.3**（Conditional Go · B′+3a · M1+M2+P0+M3 `scope=tier`；线框见 refine-feedback-loop-v1-wireframe）。

---

## 桌面安装与分发（Desktop Installer）

| 文档 | 说明 |
|------|------|
| [PRD-DESKTOP-LLM-SETUP-V1.md](./PRD-DESKTOP-LLM-SETUP-V1.md) | **桌面首启能力分层与写作引擎配置 V1**（L0 开箱 · L1 自带 Key）**v1.1 Conditional Go** |
| [PRD-DESKTOP-L0-GUIDANCE-HARDENING-V1.md](./PRD-DESKTOP-L0-GUIDANCE-HARDENING-V1.md) | **无 Key 主路径加固与首启预期管理**（死循环修复 · 友好引导）**Draft · W1/W2 ✅** |
| [IMPLEMENTATION-DESKTOP-L0-GUIDANCE-HARDENING-V1.md](./IMPLEMENTATION-DESKTOP-L0-GUIDANCE-HARDENING-V1.md) | W1–W3 实施对照（含 Resume 断点） |
| [acceptance-records/l0-resume-flow-fix-2026-07-15.md](./acceptance-records/l0-resume-flow-fix-2026-07-15.md) | Resume 断点修复 · T1–T7 手工矩阵 |
| [IMPLEMENTATION-DESKTOP-LLM-SETUP-V1.md](./IMPLEMENTATION-DESKTOP-LLM-SETUP-V1.md) | 实施清单（W1a–W3 ✅ · 狗粮/实机冒烟待人工） |
| [ACCEPTANCE-DESKTOP-LLM-SETUP-V1.md](./ACCEPTANCE-DESKTOP-LLM-SETUP-V1.md) | 验收 |
| [adr/019-desktop-user-data-llm-secrets.md](./adr/019-desktop-user-data-llm-secrets.md) | LLM secrets 落盘（复用 ADR-018 `user_data_dir`） |
| [wireframes/desktop-llm-setup-v1-wireframe.html](./wireframes/desktop-llm-setup-v1-wireframe.html) | 线框 F1–F3/F5 |
| [acceptance-records/desktop-llm-setup-v1-review-2026-07-15.md](./acceptance-records/desktop-llm-setup-v1-review-2026-07-15.md) | 跨职能评审 · Conditional Go |
| [acceptance-records/desktop-llm-setup-v1-packaging-smoke-2026-07-15.md](./acceptance-records/desktop-llm-setup-v1-packaging-smoke-2026-07-15.md) | 打包冒烟模板（发布门） |
| [PRD-DESKTOP-INSTALLER-V1.md](./PRD-DESKTOP-INSTALLER-V1.md) | **桌面可安装版 V1**（绿色便携包 · Windows 安装包 · frozen 路径 · 长图双轨 · 三道发布门） |
| [IMPLEMENTATION-DESKTOP-INSTALLER-V1.md](./IMPLEMENTATION-DESKTOP-INSTALLER-V1.md) | 实施清单（M-INS-0a/0b/0c → Gate A/B/C） |
| [ACCEPTANCE-DESKTOP-INSTALLER-V1.md](./ACCEPTANCE-DESKTOP-INSTALLER-V1.md) | 验收（冒烟 · Gate A/B/C 矩阵） |
| [adr/018-desktop-installer-layout.md](./adr/018-desktop-installer-layout.md) | ADR：onedir · 数据目录 · worker · 长图双轨 · 单实例退出 |

**前置**：Phase 2 M11 骨架（`packaging/travelogue-studio.spec` · `travelogue.desktop`）已存在。  
**代号**：Desktop Installer V1（分发）· Desktop LLM Setup V1（首启能力分层）。  
**阅读顺序**：先读 **[PRD-DESKTOP-LLM-SETUP-V1](./PRD-DESKTOP-LLM-SETUP-V1.md)** → 若处理无 Key 死循环/首启预期则读 **[PRD-DESKTOP-L0-GUIDANCE-HARDENING-V1](./PRD-DESKTOP-L0-GUIDANCE-HARDENING-V1.md)** → **[PRD-DESKTOP-INSTALLER-V1](./PRD-DESKTOP-INSTALLER-V1.md)** → [ADR-018](./adr/018-desktop-installer-layout.md) / [ADR-019](./adr/019-desktop-user-data-llm-secrets.md) → IMPLEMENTATION / ACCEPTANCE；关联 [PRD-PHASE2.md](./PRD-PHASE2.md) M11 · G-P2-05 · [PRD-HELP-ONBOARDING-V1.md](./PRD-HELP-ONBOARDING-V1.md) · [PRD-WEBSITE-MARKETING.md](./PRD-WEBSITE-MARKETING.md) `/install`。

---

## Phase 6 · 稳态与艺术优化（Stability + Art）

| 文档 | 说明 |
|------|------|
| [PRD-PHASE6.md](./PRD-PHASE6.md) | **Phase 6 主 PRD**（质量闭环 · 业务指标 · 灰度回滚 · 合规治理） |
| [PRD-PHASE6-ART-OPTIMIZATION.md](./PRD-PHASE6-ART-OPTIMIZATION.md) | **艺术卷轴子 PRD**（叙事分段/节奏/审美/多样性） |
| [IMPLEMENTATION-PHASE6.md](./IMPLEMENTATION-PHASE6.md) | 实施任务清单（M24–M26 + M25-ART） |
| [ACCEPTANCE-PHASE6.md](./ACCEPTANCE-PHASE6.md) | 验收标准（AC-P6 + BR-P6 + ART-AC） |
| [reports/phase6-week1-execution-plan.md](./reports/phase6-week1-execution-plan.md) | Week 1 到天执行计划（M24） |
| [reports/phase6-ab-eval.md](./reports/phase6-ab-eval.md) | A/B 评测报告模板 |
| [reports/phase6-art-rubric.md](./reports/phase6-art-rubric.md) | 艺术主观评分模板 |

开发准备建议顺序：**PRD-PHASE6** → **IMPLEMENTATION-PHASE6** → **ACCEPTANCE-PHASE6** → `scripts/phase6_*.py`。

---

## Phase 7 · 管线性能（Performance）

| 文档 | 说明 |
|------|------|
| [PRD-PHASE7.md](./PRD-PHASE7.md) | **Phase 7 产品需求**（ingest/CLIP/流水线/layout 等价加速 · NR-P7） |
| [IMPLEMENTATION-PHASE7.md](./IMPLEMENTATION-PHASE7.md) | 实施任务清单（M27–M29 · 3 周波次） |
| [ACCEPTANCE-PHASE7.md](./ACCEPTANCE-PHASE7.md) | 验收标准（AC-P7 · NR-P7 · G0–G3） |
| [config-phase7.example.yaml](./config-phase7.example.yaml) | P7 benchmark / 验收 config 快照 |
| [reports/phase7-g0-preflight-checklist.md](./reports/phase7-g0-preflight-checklist.md) | G0 离线预检 |
| [reports/phase7-perf-baseline.md](./reports/phase7-perf-baseline.md) | P6 vs P7 性能对比报告模板 |

**前置**：Phase 6 G0 离线 AC 通过；`phase6-quality-eval.json` 基线已登记。**代号**：P7-Perf · 极速管线。

阅读顺序：**PRD-PHASE7** → **IMPLEMENTATION-PHASE7** → **ACCEPTANCE-PHASE7** → `scripts/phase7_*.py`（W1 编码）。

---

## Phase 8 · 照片语义聚类（Semantic Tagging · 规划归档）

| 文档 | 说明 |
|------|------|
| [PRD-PHASE8-photo-semantic-clustering.md](./PRD-PHASE8-photo-semantic-clustering.md) | 11 大类 taxonomy · **Superseded → ADR-012 + Phase 12** |

**实施权威**：[PRD-PHASE12.md](./PRD-PHASE12.md) · [adr/012-semantic-tagging-p8-p12-split.md](./adr/012-semantic-tagging-p8-p12-split.md)

---

## Phase 9 · 排版前闸口（Quality Gate）

| 文档 | 说明 |
|------|------|
| [PRD-PHASE9.md](./PRD-PHASE9.md) | **Phase 9 总览**（减噪+精选 · ≥80% · featured 豁免） |
| [PRD-PHASE9-A-quality-gate-algorithm.md](./PRD-PHASE9-A-quality-gate-algorithm.md) | 算法规格 Pass 1–4 |
| [PRD-PHASE9-B-pipeline-integration.md](./PRD-PHASE9-B-pipeline-integration.md) | 管线顺序 · config |
| [PRD-PHASE9-C-data-model.md](./PRD-PHASE9-C-data-model.md) | trip.json · schema |
| [PRD-PHASE9-D-studio-ux.md](./PRD-PHASE9-D-studio-ux.md) | Importing hint · 完成摘要（无被筛 UI） |
| [PRD-PHASE9-E-subject-bridge.md](./PRD-PHASE9-E-subject-bridge.md) | Wave 3 · subjectClass 桥接 |
| [IMPLEMENTATION-PHASE9.md](./IMPLEMENTATION-PHASE9.md) | 实施任务 M30 |
| [ACCEPTANCE-PHASE9.md](./ACCEPTANCE-PHASE9.md) | W1/W2/W3 验收 |

**前置**：Phase 7 ingest 基线。**代号**：P9-QualityGate · **W1 可独立发版**。

阅读顺序：**PRD-PHASE9** → P9-A～E → **IMPLEMENTATION-PHASE9** → **ACCEPTANCE-PHASE9**。

---

## Phase 10 · Food Grid 组屏

| 文档 | 说明 |
|------|------|
| [PRD-PHASE10-food-grid.md](./PRD-PHASE10-food-grid.md) | mundane 食物/标识 **grid 屏** · screen_planner |
| [IMPLEMENTATION-PHASE10.md](./IMPLEMENTATION-PHASE10.md) | 实施任务（**12/12 Done**） |
| [ACCEPTANCE-PHASE10.md](./ACCEPTANCE-PHASE10.md) | 验收 |

**前置**：Phase 9 Wave 3（subject 桥接）。

---

## Phase 11 · 轻文案（decorLine）

| 文档 | 说明 |
|------|------|
| [PRD-PHASE11-copy-optimization.md](./PRD-PHASE11-copy-optimization.md) | 章级单句点缀 · copyIntent 锚点 |
| [IMPLEMENTATION-PHASE11.md](./IMPLEMENTATION-PHASE11.md) | M11-W1/W2 代码 · W3 观测骨架 |
| [ACCEPTANCE-PHASE11.md](./ACCEPTANCE-PHASE11.md) | AC-P11-01～10 |

**状态**：W1/W2 已合入 · 盲评 AC-P11-04 待人工。

---

## Phase 12 · 质量闸口增强

| 文档 | 说明 |
|------|------|
| [PRD-PHASE12.md](./PRD-PHASE12.md) | L1 语义 · category_coherence · 人像细粒度信号 |
| [IMPLEMENTATION-PHASE12.md](./IMPLEMENTATION-PHASE12.md) | M40 任务清单 |

**ADR**：[012-semantic-tagging-p8-p12-split.md](./adr/012-semantic-tagging-p8-p12-split.md)（L1 权威归 P12 · L2 暂缓）。

---

## Phase 13 · 模板系统化

| 文档 | 说明 |
|------|------|
| [PRD-PHASE13.md](./PRD-PHASE13.md) | 智能路由 · 模板治理 · event-recap 试点 |
| [IMPLEMENTATION-PHASE13.md](./IMPLEMENTATION-PHASE13.md) | M50 · Gate Ready |

---

## Phase 14 · 双模式导入（快速分享 / 精细制作）

| 文档 | 说明 |
|------|------|
| [PRD-PHASE14.md](./PRD-PHASE14.md) | 双 Tab · travelNotes · 成功页分流 |
| [IMPLEMENTATION-PHASE14.md](./IMPLEMENTATION-PHASE14.md) | M14.0–M14.4 |
| [ACCEPTANCE-PHASE14.md](./ACCEPTANCE-PHASE14.md) | AC-P14-01～12 |
| [PHASE14-PRD-COVERAGE.md](./PHASE14-PRD-COVERAGE.md) | PRD 对照完成度 |

关联：[PRD-FINE-CRAFT-LAYOUT-DENSITY.md](./PRD-FINE-CRAFT-LAYOUT-DENSITY.md) · [PRD-M14-shelf-save-longshot.md](./PRD-M14-shelf-save-longshot.md)

---

## Phase 15 · Photo Mosaic 演进

| 文档 | 说明 |
|------|------|
| [PRD-PHASE15-photo-mosaic-evolution.md](./PRD-PHASE15-photo-mosaic-evolution.md) | 统一候选评分 · 多窗 mosaic |
| [IMPLEMENTATION-PHASE15.md](./IMPLEMENTATION-PHASE15.md) | P15-S0～S3 |
| [ACCEPTANCE-PHASE15.md](./ACCEPTANCE-PHASE15.md) | 离线闸门 |

---

## Phase 16 · 布局模板引擎（LTE）

| 文档 | 说明 |
|------|------|
| [PRD-PHASE16-layout-template-engine.md](./PRD-PHASE16-layout-template-engine.md) | pattern YAML 注册 · 几何治理 · MCS 消费 |
| [DESIGN-PHASE16-layout-template-engine.md](./DESIGN-PHASE16-layout-template-engine.md) | 工程形态与模块边界 |
| [GUIDE-PHASE16-layout-template-engine.md](./GUIDE-PHASE16-layout-template-engine.md) | 操作指南 |
| [LTE-ADMISSION-LAYOUT-TEMPLATES.md](./LTE-ADMISSION-LAYOUT-TEMPLATES.md) | 轻量 admission · 复用 templating 平台 |

---

## Phase 17 · 智能排版引擎（LSE）

| 文档 | 说明 |
|------|------|
| [PRD-PHASE17-layout-strategy-engine.md](./PRD-PHASE17-layout-strategy-engine.md) | **智能排版引擎 LSE** v0.17.6 · P17-Core/Plus/B · 跨职能 + CTO/算法 + 前端 + 开发负责人评审已纳入 |
| [IMPLEMENTATION-PHASE17.md](./IMPLEMENTATION-PHASE17.md) | 实施清单：融合设计 · W0 三项审计 · adapter 参数收束 · 阶段交付（分支 `feature/phase17-lse`） |
| [PRD-PHASE17-research-stub.md](./PRD-PHASE17-research-stub.md) | P17-B：生成式 composite · 7 张 4P+3L（LTE 扩展） |

**前置**：Phase 16 LTE 默认路径稳定。**代号**：LSE。**原则**：最小用户干扰 · 后台自动出结果。**与 LTE 分工**：LSE 管组屏决策与调参；LTE 管 pattern 几何。

阅读顺序：**PRD-PHASE17** v0.17.6 → `IMPLEMENTATION-PHASE17`（已建）→（W0 待补）`lse_strategy.schema.json` + `DESIGN-PHASE17`

---

## Phase 18–22 · 成书质量 · 存储纪律

| 文档 | 说明 |
|------|------|
| [观感提升路线图.md](./观感提升路线图.md) | LSE 冻结 · 选片/模板/盲评优先级 |
| [ROADMAP-PHASE18-BOOK-QUALITY.md](./ROADMAP-PHASE18-BOOK-QUALITY.md) | Phase 18 BQP 项目级路线图 |
| [PRD-PHASE18-layout-effect-improvement.md](./PRD-PHASE18-layout-effect-improvement.md) | 版式观感专项 |
| [PRD-PHASE21-mosaic-density-budget.md](./PRD-PHASE21-mosaic-density-budget.md) | 拼图密度预算 · ☑ 已合入 |
| [IMPLEMENTATION-PHASE21.md](./IMPLEMENTATION-PHASE21.md) | P21 实施清单 |
| [PRD-PHASE22-storage-platform.md](./PRD-PHASE22-storage-platform.md) | **存储平台纪律** · Approved · 待 Kickoff |
| [IMPLEMENTATION-PHASE22.md](./IMPLEMENTATION-PHASE22.md) | P22 实施清单 |
| [ACCEPTANCE-PHASE22.md](./ACCEPTANCE-PHASE22.md) | P22 验收 |
| [adr/008-trip-storage-boundaries.md](./adr/008-trip-storage-boundaries.md) | trip.json 写入边界 · **Accepted** |
| [PRD-MEDIA-REFERENCE-STORAGE-V1.md](./PRD-MEDIA-REFERENCE-STORAGE-V1.md) | **媒体存储省盘与引用模式 V1** **v0.2.0**（W0–W2 已落地 · 待狗粮出口） |
| [IMPLEMENTATION-MEDIA-REFERENCE-STORAGE-V1.md](./IMPLEMENTATION-MEDIA-REFERENCE-STORAGE-V1.md) | MRS V1 实施清单 · 分支 `feature/media-reference-storage-v1` |
| [acceptance-records/media-reference-storage-v1-review-2026-07-15.md](./acceptance-records/media-reference-storage-v1-review-2026-07-15.md) | MRS V1 跨职能评审纪要 · 架构/开发/产品/算法/测试 · Conditional Go |
| [acceptance-records/media-reference-storage-v1-dogfood-checklist.md](./acceptance-records/media-reference-storage-v1-dogfood-checklist.md) | MRS V1 狗粮 5 步出口清单（合入前手测） |
| [reports/integration-sprint-checklist-2026-06-13.md](./reports/integration-sprint-checklist-2026-06-13.md) | **Integration Sprint** · 收口/验证/还债 |

---

## Studio 首页 v2 · M20 / M21

| 文档 | 说明 |
|------|------|
| [PRD-STUDIO-HOMEPAGE-v2.md](./PRD-STUDIO-HOMEPAGE-v2.md) | Bento 双交付 · Import Wizard · 书架 |
| [PRD-STUDIO-HOMEPAGE-v2.1-OPTIMIZATION.md](./PRD-STUDIO-HOMEPAGE-v2.1-OPTIMIZATION.md) | v2.1 体验优化 · CTA 层级 · bench 三分法 |
| [PRD-STUDIO-HOMEPAGE-v2.2-OPTIMIZATION.md](./PRD-STUDIO-HOMEPAGE-v2.2-OPTIMIZATION.md) | **v2.2 体验优化（Draft）** · 窄屏出口 · 首屏视觉权重 · 书架检索 |
| [PRD-IMPORT-SHEET-v3-WIZARD.md](./PRD-IMPORT-SHEET-v3-WIZARD.md) | Import Wizard v3 · 两步向导 + 智能默认（文件名历史遗留 Sheet） |
| [PRD-IMPORT-WIZARD-A1-DELTA.md](./PRD-IMPORT-WIZARD-A1-DELTA.md) | **方案 A.1 增量规格** · P0/P1/P2 体验补丁 |
| [IMPLEMENTATION-IMPORT-WIZARD-A1.md](./IMPLEMENTATION-IMPORT-WIZARD-A1.md) | **v3+A.1 实施清单** · M-A1-0～5 任务勾选 |
| [IMPLEMENTATION-IMPORT-SHEET-RETIRE.md](./IMPLEMENTATION-IMPORT-SHEET-RETIRE.md) | **旧 Sheet 退役** · P0～P4 ✅ |
| [wireframes/import-wizard-v3.html](./wireframes/import-wizard-v3.html) | Wizard v3 线框 |
| [wireframes/import-wizard-a1.html](./wireframes/import-wizard-a1.html) | **A.1 增量线框** · 进阶折叠 / 信任行 / 关闭确认 |
| [archive/import-sheet/](./archive/import-sheet/) | 已退役 Sheet 线框（v1 / 双模式 / 弹窗对比） |
| [PRD-M21-studio-homepage-v3-retirement.md](./PRD-M21-studio-homepage-v3-retirement.md) | v3 退役 · v2 唯一入口 |
| [studio-homepage-v2/](./studio-homepage-v2/) | FEATURE-FLAG · RUNBOOK · OPEN-QUESTIONS |

---

## 封面专项 · V4 / V5 / V6 / Bookends

| 文档 | 说明 |
|------|------|
| [PRD-COVER-OPTIMIZATION-V4.md](./PRD-COVER-OPTIMIZATION-V4.md) | Icon Dock + 右下书名卡 `card-br` |
| [ACCEPTANCE-COVER-OPTIMIZATION-V4.md](./ACCEPTANCE-COVER-OPTIMIZATION-V4.md) | V4 验收 |
| [IMPLEMENTATION-COVER-OPTIMIZATION-V4.md](./IMPLEMENTATION-COVER-OPTIMIZATION-V4.md) | V4 实施清单 |
| [PRD-COVER-STYLES-V5.md](./PRD-COVER-STYLES-V5.md) | **封面多样式 V5** · 三款 Web 皮肤 + 创建时分配 |
| [ACCEPTANCE-COVER-STYLES-V5.md](./ACCEPTANCE-COVER-STYLES-V5.md) | V5 验收 |
| [IMPLEMENTATION-COVER-STYLES-V5.md](./IMPLEMENTATION-COVER-STYLES-V5.md) | V5 实施清单 |
| [acceptance-records/cover-styles-prd-review-2026-06-15.md](./acceptance-records/cover-styles-prd-review-2026-06-15.md) | V5 跨职能评审纪要 |
| [wireframes/cover-styles-v5-split-mat.html](./wireframes/cover-styles-v5-split-mat.html) | `split-mat` 线框 |
| [wireframes/cover-styles-v5-magazine-head.html](./wireframes/cover-styles-v5-magazine-head.html) | `magazine-head` 线框 |
| [PRD-COVER-STYLES-V6.md](./PRD-COVER-STYLES-V6.md) | **封面多样式 V6** · 五款 Opening + Cover Style Engine + 图×样式联合 |
| [ACCEPTANCE-COVER-STYLES-V6.md](./ACCEPTANCE-COVER-STYLES-V6.md) | V6 验收 |
| [IMPLEMENTATION-COVER-STYLES-V6.md](./IMPLEMENTATION-COVER-STYLES-V6.md) | V6 实施清单 |
| [PRD-BOOKENDS-ENGINE-V1.md](./PRD-BOOKENDS-ENGINE-V1.md) | **Bookends Engine V1**（**v0.2.1** · 开发决议已合入）· 封面–封底引擎 + 成对约束 |
| [adr/017-bookends-engine.md](./adr/017-bookends-engine.md) | ADR-017 · Bookends 挂点 / 锁 / 压字分期 / B2a·b |
| [IMPLEMENTATION-BOOKENDS-ENGINE-V1.md](./IMPLEMENTATION-BOOKENDS-ENGINE-V1.md) | Bookends 实施清单（B0→B1→B2a→B2b） |
| [ACCEPTANCE-BOOKENDS-ENGINE-V1.md](./ACCEPTANCE-BOOKENDS-ENGINE-V1.md) | Bookends 验收追踪（B1 起勾选） |
| [acceptance-records/bookends-prd-review-2026-07-13.md](./acceptance-records/bookends-prd-review-2026-07-13.md) | Bookends PRD 跨职能评审纪要（产品/架构/算法/UIUX/体验/视觉/流程） |

阅读顺序：**PRD-COVER-OPTIMIZATION-V4** → **V5** → **V6** → **[PRD-BOOKENDS-ENGINE-V1](./PRD-BOOKENDS-ENGINE-V1.md)** → ADR-017 → IMPLEMENTATION → ACCEPTANCE。

---

## 算法优化 V2

| 文档 | 说明 |
|------|------|
| [PRD-ALGORITHM-OPTIMIZATION-V2.md](./PRD-ALGORITHM-OPTIMIZATION-V2.md) | 封面 logit · sharpness v2 |
| [IMPLEMENTATION-ALGORITHM-V2.md](./IMPLEMENTATION-ALGORITHM-V2.md) | Sprint 1/2 · R0' 盲评待素材 |

---

## Phase 7 子专项 · RAW 拦截

| 文档 | 说明 |
|------|------|
| [PRD-PHASE7-RAW-GATE.md](./PRD-PHASE7-RAW-GATE.md) | RAW 不支持策略：检测即拦截、提示先转 JPG 后重试 |
| [IMPLEMENTATION-PHASE7-RAW-GATE.md](./IMPLEMENTATION-PHASE7-RAW-GATE.md) | 实施任务清单（RG-M1~M3） |
| [ACCEPTANCE-PHASE7-RAW-GATE.md](./ACCEPTANCE-PHASE7-RAW-GATE.md) | 验收标准（AC-RAW-01~05） |
| [FAQ-RAW-IMPORT.md](./FAQ-RAW-IMPORT.md) | RAW 导入 FAQ 与用户指引 |

---

## P0 · 立项与产品

| 文档 | 说明 |
|------|------|
| [CHARTER.md](./CHARTER.md) | 项目章程 |
| [PRD-MVP.md](./PRD-MVP.md) | MVP 产品需求（**已冻结**） |
| [PRD-PHASE2.md](./PRD-PHASE2.md) | **Phase 2**：Studio 工作台 + 服务端长图 + 交付物层级 |
| [AGENT-ARCHITECTURE.md](./AGENT-ARCHITECTURE.md) | 智能体流水线 |
| [DATA-MODEL.md](./DATA-MODEL.md) | 数据模型 |
| [TEMPLATE-visual-journal.md](./TEMPLATE-visual-journal.md) | 模板 PRD |
| [ADAPTIVE-LAYOUT.md](./ADAPTIVE-LAYOUT.md) | 终端自适应 |
| [TECH-ARCHITECTURE.md](./TECH-ARCHITECTURE.md) | 技术架构 |
| [DEVELOPMENT.md](./DEVELOPMENT.md) | 开发手册 |
| [WORKSHOP.md](./WORKSHOP.md) | **本地工坊**：Phase 2 推荐 Studio；开发者 workshop 脚本 |
| [老图.md](./老图.md) | **混册/老图/截图**：时间段分段、`mediaClass` 与编排原则 |
| [ACCEPTANCE.md](./ACCEPTANCE.md) | **单轨验收入口**（MVP 附录 + Phase 2–21 · 闸门 P5+P6+P21 回归） |
| [SHARING.md](./SHARING.md) | **双轨分享**：服务端长图（Phase 2 主路径）vs 小程序鉴权 HTML（P3） |
| [PRD-LAYOUT.md](./PRD-LAYOUT.md) | **排版布局 PRD**（专职 Agent 1.5 规划） |
| [web端模板.prd](./web端模板.prd) | **Web 端模板 PRD**（章/屏、16:9 舞台、pattern 库） |
| [web端模板升级计划.md](./web端模板升级计划.md) | **Web 升级实施计划**（layoutEngine legacy/screens） |
| [LAYOUT-PLANNER.md](./LAYOUT-PLANNER.md) | 排版算法细则（阈值、rowLayout、CSS） |
| [PRD-EXPERIENCE.md](./PRD-EXPERIENCE.md) | **阅读体验 PRD**：三模式 · Hybrid · `export.reading` · 路线图 E0–E8 |
| [IMPLEMENTATION-EXPERIENCE.md](./IMPLEMENTATION-EXPERIENCE.md) | **实施任务清单**（E0–E8 逻辑顺序 · 进度跟踪） |
| [experience-matrix.yaml](./experience-matrix.yaml) | 阅读 profile / 降级矩阵（机器可读） |

### 阅读体验附录（PRD-EXPERIENCE）

| 文档 | 说明 |
|------|------|
| [PRD-EXPERIENCE-附录A-精选上传.md](./PRD-EXPERIENCE-附录A-精选上传.md) | 双文件夹 · `userTier` · curate 加权 |
| [PRD-EXPERIENCE-附录B-滚动动效.md](./PRD-EXPERIENCE-附录B-滚动动效.md) | 呼吸感 · Lenis · breath profile |
| [PRD-EXPERIENCE-附录C-Folio版式.md](./PRD-EXPERIENCE-附录C-Folio版式.md) | Folio 九屏 · screen-plate · featured-grid |

> 旧稿 [双文件夹.md](./双文件夹.md)、[页面互动呼吸感.md](./页面互动呼吸感.md)、[Folio版式借鉴.md](./Folio版式借鉴.md)、[阅读模式融合.md](./阅读模式融合.md) 已重定向至上述体系。

---

## P0.5 · 工程执行（开代码前）

| 文档 | 说明 |
|------|------|
| [CLI-SPEC.md](./CLI-SPEC.md) | CLI 命令契约（**v0.4** · studio / export-longshot 已实现） |
| [ERROR-CODES.md](./ERROR-CODES.md) | 错误码 |
| [VALIDATION-RULES.md](./VALIDATION-RULES.md) | L1 Schema + L2 Manifest |
| [MEDIA-PIPELINE.md](./MEDIA-PIPELINE.md) | Agent 0 媒体管线 |
| [NARRATIVE-PROMPTS.md](./NARRATIVE-PROMPTS.md) | Agent 2 叙事提示 |
| [RENDER-CONTRACT.md](./RENDER-CONTRACT.md) | Agent 3 渲染映射 |
| [DEFINITION-OF-DONE.md](./DEFINITION-OF-DONE.md) | 里程碑 Done |
| [TESTING.md](./TESTING.md) | 测试策略 |
| [API-MINIAPP.md](./API-MINIAPP.md) | 小程序 / 云端 HTTP 契约（设计稿） |
| [PRD-MINIAPP-P1.md](./PRD-MINIAPP-P1.md) | 小程序 P1 · 混合云长图交付（Draft） |
| [PRD-MINIAPP-PHOTO-PICK-V1.md](./PRD-MINIAPP-PHOTO-PICK-V1.md) | **小程序选图 V1** · 双主权（我来选 / 交给应用挑） |

### ADR（架构决策）

| 文档 | 说明 |
|------|------|
| [adr/README.md](./adr/README.md) | ADR 索引 |
| [adr/001-delivery-and-media.md](./adr/001-delivery-and-media.md) | 交付 zip、体积、视觉标签、状态机、封面 |
| [adr/003-experience-reading-modes.md](./adr/003-experience-reading-modes.md) | 三阅读模式 · Hybrid · `export.reading.profile` · Epic 顺序 |

### Fixtures

| 文件 | 流水线阶段 |
|------|------------|
| [trip.ingest_ready.json](../schemas/fixtures/trip.ingest_ready.json) | Agent 1 输入 |
| [trip.structure_locked.json](../schemas/fixtures/trip.structure_locked.json) | Agent 2 输入 |
| [trip.copy_locked.json](../schemas/fixtures/trip.copy_locked.json) | Agent 3 输入 |
| [trip.example.json](../schemas/fixtures/trip.example.json) | 综合样例 |
| [trip.phase10_food_grid.json](../schemas/fixtures/trip.phase10_food_grid.json) | Phase 10 食物组屏人工验收 fixture |

校验：

```powershell
python scripts/validate_trip.py schemas/fixtures/trip.copy_locked.json --level all
```

---

## P1 · 计划补充

| 文档 | 说明 |
|------|------|
| `PRIVACY-SECURITY.md` | 隐私专篇（与 `SHARING.md` 路径 B 衔接） |
| `CLI-UX.md` | 本地 UI 与 G0–G3 |
| `ROADMAP.md` | 版本节奏 |
| `docs/adr/` | 架构决策记录 |

---

## 现行有效文档（架构治理 · M-C3）

> 历史 Phase PRD/验收仍保留在仓库中供查阅；**实施与运维以本节 + ADR 为准**。  
> 完整脚本清单见 [scripts/README.md](../scripts/README.md)（`python scripts/gen_scripts_registry.py` 刷新）。

### 主 PRD / 架构 SSOT

| 文档 | 说明 |
|------|------|
| [PRD-ARCH-OPTIMIZATION.md](./PRD-ARCH-OPTIMIZATION.md) | 架构优化还债 PRD v1.1 |
| [PRD-ARCH-OPT-WS1-MERGE-FIX.md](./PRD-ARCH-OPT-WS1-MERGE-FIX.md) | WS1 合并闸门修复 PRD（feedback / LSE baseline / CI） |
| [PRD-STABLE-QUALITY-HARDENING-V1.md](./PRD-STABLE-QUALITY-HARDENING-V1.md) | **稳定期质量硬化与体验优化 v1.1**（**Done** · PR #12 · [结案](./acceptance-records/stable-qh-closeout-2026-07-15.md)） |
| [PRD-LONGSHOT-COOPERATIVE-CANCEL-V1.md](./PRD-LONGSHOT-COOPERATIVE-CANCEL-V1.md) | **长图 Job 真协作取消 V1**（**Done** · [狗粮](./acceptance-records/lcc-cancel-dogfood-2026-07-15.md)） |
| [PRD-ARCH-ALGO-DEEPENING-V1.md](./PRD-ARCH-ALGO-DEEPENING-V1.md) | **架构收敛与算法加深 V1.1**（执行分支 `arch/algo-deepening-v1` · [评审纪要](./acceptance-records/aad-prd-review-2026-07-15.md)） |
| [ARCH-OPT-STATUS.md](./ARCH-OPT-STATUS.md) | 里程碑状态追踪（实施期 SSOT） |
| [PROMPTS-ARCH-OPTIMIZATION.md](./PROMPTS-ARCH-OPTIMIZATION.md) | Agent 执行提示词 |
| [TECH-ARCHITECTURE.md](./TECH-ARCHITECTURE.md) | 技术架构（M-B0 v0.9 增量；M-D1 后全量更新） |
| [GLOSSARY.md](./GLOSSARY.md) | Studio 命名消歧（classic / Import Wizard v3 / Preview v3） |
| [TESTING.md](./TESTING.md) | 测试分层与 CI job 说明 |

### ADR（架构决策 · 现行）

| 文档 | 说明 |
|------|------|
| [adr/README.md](./adr/README.md) | ADR 索引（含 008 revision 锁 · 015 LSE 迁移 · 016 Longshot 草案） |

### 运行手册 / 运维

| 文档 | 说明 |
|------|------|
| [DEVELOPMENT.md](./DEVELOPMENT.md) | 本地开发与调试 |
| [studio-homepage-v2/README.md](./studio-homepage-v2/README.md) | Studio 首页 v2 文档 hub |
| [studio-homepage-v2/RUNBOOK-HOLDBACK.md](./studio-homepage-v2/RUNBOOK-HOLDBACK.md) | Holdback 灰度 / 回滚 |
| [studio-homepage-v2/RUNBOOK-DOGFOOD.md](./studio-homepage-v2/RUNBOOK-DOGFOOD.md) | Dogfood 观察 |
| [QUALITY-GATE.md](./QUALITY-GATE.md) | CI 质量门禁与脚本入口 |

### 历史归档

| 路径 | 说明 |
|------|------|
| [docs/archive/](./archive/) | 退役文档（M-C3 机制） |
| [docs/archive/ARCHIVE-CANDIDATES.md](./archive/ARCHIVE-CANDIDATES.md) | 可归档 `phaseN_*` 脚本候选清单 |
| [scripts/archive/](../scripts/archive/) | 退役脚本（确认后 `git mv`） |

---

## 版本记录

| 日期 | 变更 |
|------|------|
| 2026-07-16 | 开工 [PRD-ARCH-ALGO-DEEPENING-V1](./PRD-ARCH-ALGO-DEEPENING-V1.md) 分支 `arch/algo-deepening-v1`（M1 基线）；评审纪要 [aad-prd-review-2026-07-15.md](./acceptance-records/aad-prd-review-2026-07-15.md) |
| 2026-07-16 | [PRD-MEDIA-REFERENCE-STORAGE-V1](./PRD-MEDIA-REFERENCE-STORAGE-V1.md) W0–W2 落地（引用 ingest · 清理 · remount · 导出阻断）；待狗粮出口 |
| 2026-07-15 | LCC V1 **Done**：长图协作取消合入 `master`；狗粮 [lcc-cancel-dogfood-2026-07-15.md](./acceptance-records/lcc-cancel-dogfood-2026-07-15.md) |
| 2026-07-15 | Stable-QH **结案**：[closeout](./acceptance-records/stable-qh-closeout-2026-07-15.md)；补充试用 [supplemental](./acceptance-records/stable-qh-supplemental-trial-2026-07-15.md)；下一波 [长图协作取消](./PRD-LONGSHOT-COOPERATIVE-CANCEL-V1.md) |
| 2026-07-15 | Stable-QH M1–M5 落地验收：[acceptance-records/stable-qh-2026-07-15.md](./acceptance-records/stable-qh-2026-07-15.md)；QUALITY-GATE 增稳定期 AC 命令 |
| 2026-07-15 | [PRD-STABLE-QUALITY-HARDENING-V1](./PRD-STABLE-QUALITY-HARDENING-V1.md) 升 **v1.1.0**（合入六席 BLK-01..08 · Ready for Kickoff） |
| 2026-07-15 | 新增 [PRD-STABLE-QUALITY-HARDENING-V1.md](./PRD-STABLE-QUALITY-HARDENING-V1.md)（稳定期 16 失败归因 + 体验硬化可落地方案） |
| 2026-07-15 | 稳定期修复 PRD 六席评审纪要：[acceptance-records/stable-qh-prd-review-2026-07-15.md](./acceptance-records/stable-qh-prd-review-2026-07-15.md)（有条件通过） |
| 2026-07-15 | 索引补 [PRD-DESKTOP-L0-GUIDANCE-HARDENING-V1.md](./PRD-DESKTOP-L0-GUIDANCE-HARDENING-V1.md)（无 Key 主路径加固 · 首启预期 · 失败可继续） |
| 2026-07-15 | 索引补 [PRD-DESKTOP-LLM-SETUP-V1.md](./PRD-DESKTOP-LLM-SETUP-V1.md)（桌面首启 L0/L1 · 写作引擎配置 · 无 Key 长图兜底） |
| 2026-07-14 | 桌面安装版：PRD v1.1.1 + [ADR-018](./adr/018-desktop-installer-layout.md) + [IMPLEMENTATION](./IMPLEMENTATION-DESKTOP-INSTALLER-V1.md) + [ACCEPTANCE](./ACCEPTANCE-DESKTOP-INSTALLER-V1.md) |
| 2026-07-14 | 精修反馈闭环：PRD v0.1.2 + IMPLEMENTATION + ACCEPTANCE + 线框索引 |
| 2026-07-13 | Bookends：PRD v0.2.1 + [ADR-017](./adr/017-bookends-engine.md) + IMPLEMENTATION + ACCEPTANCE 索引 |
| 2026-07-11 | 索引补 [PRD-DESKTOP-INSTALLER-V1.md](./PRD-DESKTOP-INSTALLER-V1.md)（Windows 可安装版 · Gate A/B/C） |
| 2026-06-13 | 索引补 Phase 18–22 · Integration Sprint · ACCEPTANCE v1.3 闸门对齐 |
| 2026-06-06 | 索引补 Phase 11–15 · M21 · Algorithm V2 · ADR-012 |
| 2026-05-30 | 新增 Phase 7 管线性能 PRD 索引 |
| 2026-05-30 | 新增 Phase 6 与艺术专项文档索引 |
| 2026-05-19 | P0 文档包 |
| 2026-05-19 | P0.5 工程执行文档 + validate 脚本 + fixtures |
| 2026-05-19 | ADR-001：交付/媒体/标签/状态机/封面 |
| 2026-05-27 | PRD-EXPERIENCE v1.0：三模式 + Hybrid + 三附录 + ADR-003 + experience-matrix |
| 2026-05-27 | PRD-PHASE2 **v0.2.1**：跨文档一致性补丁（SHARING 双轨、250 张、bat、cancel/upload/GIL） |
| 2026-05-27 | PRD-PHASE2 **v0.3.1**：M8a/b；Chrome allowlist；reveal API；开发准入补丁 |
| 2026-05-28 | PRD-PHASE3 **v0.3.3 Kickoff**：NR-P3-01 §12.1、M12 切割、config API §9.5、M12.5 cache |
| 2026-05-28 | PRD-PHASE3 **v0.3.2**：§6.4 Studio 前端；UX-P3-01～10 |
| 2026-05-28 | PRD-PHASE3 **v0.3.0**：战略 pivot 原生 Curate 聚类；ADR-007 替代 ADR-006 |
| 2026-05-27 | PRD-PHASE3 **v0.2.0**：评审修订（compose 双容器、路径策略、测试、M12-0）— 已由 v0.3 废止 |
