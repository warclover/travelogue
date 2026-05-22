# Travelogue · 文档索引

| 属性 | 内容 |
|------|------|
| **产品代号** | Travelogue（游记智能体） |
| **文档体系** | P0 立项 + P0.5 工程执行 |
| **更新日期** | 2026-05-19 |

---

## 阅读顺序（新人）

1. [CHARTER.md](./CHARTER.md) → [PRD-MVP.md](./PRD-MVP.md)  
2. [AGENT-ARCHITECTURE.md](./AGENT-ARCHITECTURE.md)  
2b. [PRD-LAYOUT.md](./PRD-LAYOUT.md)（排版布局子系统 · Agent 1.5）  
3. [DATA-MODEL.md](./DATA-MODEL.md) + [schemas/trip.schema.json](../schemas/trip.schema.json)  
4. [TEMPLATE-visual-journal.md](./TEMPLATE-visual-journal.md) + [golden.html](../templates/visual-journal/golden.html)  
5. **开发前必读 P0.5**（§下）  
6. [TECH-ARCHITECTURE.md](./TECH-ARCHITECTURE.md) → [DEVELOPMENT.md](./DEVELOPMENT.md)  
7. [ACCEPTANCE.md](./ACCEPTANCE.md)

---

## P0 · 立项与产品

| 文档 | 说明 |
|------|------|
| [CHARTER.md](./CHARTER.md) | 项目章程 |
| [PRD-MVP.md](./PRD-MVP.md) | 产品需求 |
| [AGENT-ARCHITECTURE.md](./AGENT-ARCHITECTURE.md) | 智能体流水线 |
| [DATA-MODEL.md](./DATA-MODEL.md) | 数据模型 |
| [TEMPLATE-visual-journal.md](./TEMPLATE-visual-journal.md) | 模板 PRD |
| [ADAPTIVE-LAYOUT.md](./ADAPTIVE-LAYOUT.md) | 终端自适应 |
| [TECH-ARCHITECTURE.md](./TECH-ARCHITECTURE.md) | 技术架构 |
| [DEVELOPMENT.md](./DEVELOPMENT.md) | 开发手册 |
| [WORKSHOP.md](./WORKSHOP.md) | **本地工坊**：一条龙脚本、验收与 Web screens 自检 |
| [老图.md](./老图.md) | **混册/老图/截图**：时间段分段、`mediaClass` 与编排原则 |
| [ACCEPTANCE.md](./ACCEPTANCE.md) | MVP 验收 |
| [SHARING.md](./SHARING.md) | **双轨分享**：微信群长图（P0）vs 小程序鉴权 HTML（P2） |
| [PRD-LAYOUT.md](./PRD-LAYOUT.md) | **排版布局 PRD**（专职 Agent 1.5 规划） |
| [web端模板.prd](./web端模板.prd) | **Web 端模板 PRD**（章/屏、16:9 舞台、pattern 库） |
| [web端模板升级计划.md](./web端模板升级计划.md) | **Web 升级实施计划**（layoutEngine legacy/screens） |
| [LAYOUT-PLANNER.md](./LAYOUT-PLANNER.md) | 排版算法细则（阈值、rowLayout、CSS） |

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
