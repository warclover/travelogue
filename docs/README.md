# Travelogue · 文档索引

| 属性 | 内容 |
|------|------|
| **产品代号** | Travelogue（游记智能体） |
| **文档体系** | P0 立项 + P0.5 工程执行 + **Phase 2–17** + Studio 首页 v2/M21 + 算法 V2 |
| **更新日期** | 2026-06-07 |

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

**前置**：Phase 4 M15–M19 代码主线已收口。**代号**：P5-Polish。**决策**：D1–D6 见 PRD §2.2（D4/D5 暂缓）。

阅读顺序：**PRD-PHASE5** →（启动实施时）**IMPLEMENTATION-PHASE5** → **ACCEPTANCE-PHASE5**。

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

## Studio 首页 v2 · M20 / M21

| 文档 | 说明 |
|------|------|
| [PRD-STUDIO-HOMEPAGE-v2.md](./PRD-STUDIO-HOMEPAGE-v2.md) | Bento 双交付 · Import Sheet · 书架 |
| [PRD-M21-studio-homepage-v3-retirement.md](./PRD-M21-studio-homepage-v3-retirement.md) | v3 退役 · v2 唯一入口 |
| [studio-homepage-v2/](./studio-homepage-v2/) | FEATURE-FLAG · RUNBOOK · OPEN-QUESTIONS |

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
| [ACCEPTANCE.md](./ACCEPTANCE.md) | **单轨验收入口**（MVP 附录 + Phase 2–5 索引 · 当前闸门 Phase 5） |
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

## 版本记录

| 日期 | 变更 |
|------|------|
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
