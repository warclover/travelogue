# Travelogue · 技术架构（MVP）

| 属性 | 内容 |
|------|------|
| **文档版本** | v0.1 |
| **阶段** | P0 本地工坊 |
| **关联** | `CHARTER.md`、`AGENT-ARCHITECTURE.md`、`DATA-MODEL.md` |
| **更新日期** | 2026-05-22 |

---

## 1. 架构目标

| 目标 | 手段 |
|------|------|
| 版式稳定 | 模板 + manifest；Agent 只改 JSON |
| 可测试 | ingest/curate/render 可单测；schema 校验 |
| 可恢复 | `trip.json` + 文件系统即状态 |
| 低耦合 | Agent 经 Orchestrator 调用，不互调 |
| 本地优先 | 无服务端；可选外部 LLM/地理 API |

---

## 2. 逻辑架构

```mermaid
flowchart TB
  subgraph ui [UI 层 P0]
    CLI[CLI travelogue]
    Skill[Cursor Skills 可选]
  end

  subgraph orch [编排层]
    O[Orchestrator]
    SM[Pipeline 状态机]
  end

  subgraph agents [Agent 层]
    A0[media_lab / ingest]
    A1[curator]
    A2[storyteller]
    A3[publisher render+validate]
  end

  subgraph core [核心服务]
    TS[TripService]
    VAL[Schema + Manifest Validator]
  end

  subgraph storage [存储]
    FS[(trips/tripId/)]
  end

  subgraph external [外部]
    LLM[LLM API]
    FF[ffmpeg]
    GEO[Geocode API 可选]
  end

  CLI --> O
  Skill --> O
  O --> SM
  O --> A0 & A1 & A2 & A3
  A0 & A1 & A2 & A3 --> TS
  A2 --> LLM
  A0 --> FF
  A0 --> GEO
  A3 --> VAL
  TS --> FS
```

---

## 3. 技术选型（P0 默认）

| 层次 | 选型 | 理由 |
|------|------|------|
| 语言 | **Python 3.11+** | EXIF、图像、CLI 生态成熟 |
| 编排 CLI | `typer` 或 `click` | 子命令清晰 |
| JSON Schema | `jsonschema` | 对齐 `trip.schema.json` |
| 模板渲染 | **Handlebars**（pybars3 或 Node 子进程） | 逻辑与表现分离 |
| 图像 | Pillow + pillow-heif | HEIC 支持 |
| 视频 | ffmpeg CLI | 裁切循环片段 |
| 配置 | `config.yaml` + 环境变量覆盖 | 本地 Key 不入库 |
| UI 壳 | **延后**（Tauri / Web） | P0 先 CLI |

---

## 4. 仓库目录（当前实现）

> 早期设计中的 `agents/`、`runner.py` 已落地为 `curation/`、`media/`、`services/narrate.py`、`render/`。Agent 2 为规则 stub（无 LLM）；ffmpeg 尚未接入 Python。

```
travelogue/
├── docs/
├── schemas/
├── templates/visual-journal/   # journal.hbs + journal.css + manifest.json
├── travelogue/                 # Python 包
│   ├── cli.py
│   ├── config.py
│   ├── curation/               # curate, bucket_planning, chapter_titles, screen_planner, …
│   ├── media/                  # Agent 0（ingest, image_ops, …）
│   ├── services/               # validate, narrate(stub), layout, manifest_limits
│   ├── render/                 # Agent 3（pybars3 → journal.hbs）
│   ├── export/
│   ├── orchestrator/
│   └── demo/
├── scripts/
├── tests/
├── trips/                      # 运行时（.gitignore）
├── config.yaml.example
└── pyproject.toml
```

---

## 5. 模块职责

### 5.1 TripService

- 创建 trip 目录与初始 `trip.json`  
- 原子写入（写临时文件再 rename）  
- 列出 `trips/`、加载、更新 `updatedAt`  

### 5.2 Orchestrator

- 解析 CLI：`travelogue trip new|ingest|curate|narrate|render|export|status`  
- 检查 `pipeline.status` 是否允许调用目标 Agent  
- 记录 `pipeline.runs[]`  
- 失败时保留上一稳定状态  

### 5.3 Agent 0 · media_lab

- 输入：`source/` 路径或 batch  
- 输出：更新 `assets[]`、`pipeline.status → ingest_ready`  
- 依赖：Pillow、ffmpeg、可选 geocoder  

### 5.4 Agent 1 · curator

- 输入：`ingest_ready` 的 trip  
- 输出：`chapters[]`、`coverCandidates`、`structure_draft`  
- 无 LLM 路径必须可运行  

### 5.5 Agent 2 · storyteller

- 输入：`structure_locked`  
- 输出：`meta`、章/卡文案、`copy_draft`  
- 依赖：LLM；输出经 Validator  

### 5.6 Agent 3 · publisher

- **validate**：schema + manifest 规则  
- **render**：`trip.json` + `journal.hbs` → `index.html`  
- **export**：zip、`preview.jpg`、EXIF 剥离副本  

---

## 6. 数据流

```
本地文件夹
  → [A0] source/ + assets/ + assets meta in trip.json
  → [G1 用户] structure_locked
  → [A2] 文案 fields
  → [G2 用户] copy_locked
  → [A3] index.html + journal.css
  → [G3 用户] privacy.confirmedAt
  → [A3] zip + preview.jpg → exported
```

---

## 7. 校验双层

| 层 | 工具 | 内容 |
|----|------|------|
| L1 结构 | `jsonschema` | `schemas/trip.schema.json` |
| L2 业务 | `validate.py` | manifest limits、pattern 序列、视频不在封面章 |

Agent 2 失败：L1/L2 错误列表 → 自动重试 prompt（≤2 次）。

---

## 8. 渲染器设计

- **输入**：`trip.json`、`templateId`、`assets/`  
- **模板**：由 `golden.html` 抽块为 `journal.hbs`；CSS 复制为 `journal.css`  
- **输出**：`index.html` 内相对路径；`<html data-layout="...">`  
- **图片**：优先 `<img srcset>`（见 `ADAPTIVE-LAYOUT.md`）  
- **禁止**：运行时拼接无约束 HTML 字符串作为终稿  

---

## 9. 配置

`config.yaml`（见 `config.yaml.example`）：

| 键 | 说明 |
|----|------|
| `trips_dir` | 默认 `./trips` |
| `llm.provider` | openai / anthropic / … |
| `llm.model` | 可配置 |
| `llm.api_key_env` | 环境变量名 |
| `ffmpeg.path` | 可执行路径 |
| `geocode.enabled` | 默认 false |

**安全**：`config.yaml` 加入 `.gitignore`；仓库只保留 `.example`。

---

## 10. 外部依赖

| 依赖 | 必需 | 用途 |
|------|------|------|
| Python 3.11+ | ✅ | 主运行时 |
| ffmpeg | ✅（含视频时） | 视频循环 |
| LLM API | ✅（叙事阶段） | Agent 2 |
| Node.js | 可选 | 若 Handlebars 用 Node 子进程 |
| 地理 API | ❌ | 城市反查 |

---

## 11. 日志与可观测

- 每 trip：`trips/{id}/runs/run-{ts}.json`（可选详细日志）  
- CLI 标准输出：阶段名、耗时、警告（无 EXIF 等）  
- 不记录 API Key、不记录精确 GPS 到日志  

---

## 12. 与 PRD 模块映射

| PRD 模块 | 技术模块 |
|----------|----------|
| F-ING-* | Agent 0 |
| F-CUR-* | Agent 1 |
| F-NAR-* | Agent 2 |
| F-VID-* | Agent 0（ffmpeg） |
| F-EXP-* | Agent 3 |
| F-TRIP-* | TripService + Orchestrator |

---

## 13. 非功能

| 类别 | 实现要点 |
|------|----------|
| 性能 | ingest 并行缩图；渲染 <5s（30 图） |
| 兼容 | 输出 HTML 测 Chrome / Safari / 微信 |
| 可维护 | 模板版本与 `trip.version` 解耦记录 |
| 测试 | schema 样例 fixture；golden HTML 快照对比（可选） |

---

## 14. 开放技术项（P0 内决策）

| ID | 问题 | 默认 |
|----|------|------|
| TQ-01 | Handlebars 用 Python 还是 Node | Python pybars3，不行再 Node |
| TQ-02 | ASR 供应商 | MVP 可粘贴 transcript |
| TQ-03 | 预览 server | `python -m http.server` 文档化 |

---

## 15. 版本历史

| 版本 | 日期 | 说明 |
|------|------|------|
| v0.1 | 2026-05-19 | P0 技术架构初稿 |
