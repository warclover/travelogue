# Travelogue · 文档索引

| 属性 | 内容 |
|------|------|
| **产品代号** | Travelogue（游记智能体） |
| **文档体系** | P0 立项 + P0.5 工程执行 + **Phase 2 Studio** + **Phase 3 Curate 聚类** |
| **更新日期** | 2026-05-27 |

---

## 阅读顺序（新人）

1. [CHARTER.md](./CHARTER.md) → [PRD-MVP.md](./PRD-MVP.md)（MVP · 已冻结）→ [PRD-PHASE2.md](./PRD-PHASE2.md) → [PRD-PHASE3.md](./PRD-PHASE3.md)（Curate 聚类 · 第三阶段）  
2. [AGENT-ARCHITECTURE.md](./AGENT-ARCHITECTURE.md)  
2b. [PRD-LAYOUT.md](./PRD-LAYOUT.md)（排版布局子系统 · Agent 1.5）  
3. [DATA-MODEL.md](./DATA-MODEL.md) + [schemas/trip.schema.json](../schemas/trip.schema.json)  
4. [TEMPLATE-visual-journal.md](./TEMPLATE-visual-journal.md) + [golden.html](../templates/visual-journal/golden.html)  
5. **开发前必读 P0.5**（§下）  
6. [TECH-ARCHITECTURE.md](./TECH-ARCHITECTURE.md) → [DEVELOPMENT.md](./DEVELOPMENT.md)  
7. [ACCEPTANCE.md](./ACCEPTANCE.md)（MVP）→ [ACCEPTANCE-PHASE2.md](./ACCEPTANCE-PHASE2.md)（Phase 2）

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

**前置**：Phase 2 ≥ M8b + M9 可用。**代号**：Curate 聚类。**注意**：与 [SHARING.md](./SHARING.md) 中小程序 **P3** 轨道无关，后者规划为 Phase 4。

阅读顺序：**PRD-PHASE3** v0.3.3 Kickoff → ADR-007 v0.2 → [智能排版V2.md](./智能排版V2.md) P1 → [IMPLEMENTATION-PHASE3.md](./IMPLEMENTATION-PHASE3.md) → [ACCEPTANCE-PHASE3.md](./ACCEPTANCE-PHASE3.md) → [PRD-STUDIO-HOMEPAGE.md](./PRD-STUDIO-HOMEPAGE.md) §19。

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
| [ACCEPTANCE.md](./ACCEPTANCE.md) | MVP 验收 |
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
| [CLI-SPEC.md](./CLI-SPEC.md) | CLI 命令契约 |
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
