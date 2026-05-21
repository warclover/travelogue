# ADR-001 · 交付形态、媒体体积、视觉标签、状态机与封面

| 属性 | 内容 |
|------|------|
| **状态** | 已采纳 |
| **日期** | 2026-05-19 |
| **决策者** | 项目负责人 |
| **影响范围** | Agent 0/2/3、PRD、schema、导出与分享 |

---

## 背景

1. 「单文件 HTML」若采用 Base64 内嵌 30 图 + 3 视频，体积可达 15–20MB，在微信 WebView 易卡顿。  
2. Agent 2 仅见 EXIF/城市时，文案易沦为导游式流水账。  
3. G1/G3 人工闸口要求 CLI 可挂起、手改 `trip.json` 后断点续跑，避免重复消耗 Token。  
4. 9:16 `preview.jpg` 是分享漏斗第一屏，需确定性高颜值生成。

---

## 决策

### D1 · 交付物：Zip 离线包为主，非 Base64 单文件

| 项 | 决定 |
|----|------|
| **MVP 主交付** | `index.html` + `journal.css` + `assets/`（相对路径） |
| **分享单元** | `trip-{id}.zip`，解压即开 |
| **对外表述** | 「一页故事 / 一个 zip」，不强调「仅一个 .html 文件」 |
| **Base64 自包含 HTML** | **不做** MVP 默认；P2 可选 `export --self-contained` |
| **引流** | 先发 `preview.jpg`（9:16），再发 zip 或托管链接 |

**理由**：相对路径 + zip 在体积、内存、微信体验上优于巨型单 HTML；与 `srcset`、多档 WebP 一致。

---

### D2 · Agent 0：强制压缩 + 可选视觉语义标签

| 项 | 决定 |
|----|------|
| **图片** | 强制 WebP 多档（800/1600，可选 2400）；质量 ~82 |
| **视频** | ffmpeg 3–8s 循环；宽约 1280；目标 **≤1.5MB/段** |
| **整包** | zip 目标 **≤25MB**（30 图 + 3 视频，可配置） |
| **视觉标签** | Agent 0 写入 `assets[].tags[]`（3–5 个推荐），**不写正文** |
| **标签来源** | P0：启发式/文件名；P0.5+：本地 CLIP；P1：本地 VLM（如 Moondream2） |
| **云端 Vision** | MVP 默认 **不用**（隐私与成本） |

**理由**：体积在 ingest 阶段控制；标签补足 Agent 2「看不见图」问题，且可本地运行。

---

### D3 · G1：记忆锚点 + 现有 pipeline 状态机

| 项 | 决定 |
|----|------|
| **SSOT** | 仅 `trip.json`；Orchestrator 内 **State Manager** |
| **状态字段** | 沿用 `pipeline.status`（非 v0.1 的 `ingested/curated` 字符串） |
| **G1 增量** | `chapters[].curation.memoryAnchors[]`（每章 0–3 条，用户原话） |
| **手改后** | L2 校验；`lock structure`；不自动重跑 ingest |
| **续跑** | `travelogue` 分阶段子命令 + `run --from <stage>`（见 CLI-SPEC） |
| **改字** | G3 前改 JSON → 仅 `render`；`edited: true` 防覆盖 |

**用户心智 ↔ 状态对照**：

| 用户理解 | `pipeline.status` |
|----------|-------------------|
| 已导入 | `ingest_ready` |
| 策展待确认 | `structure_draft` |
| G1 已过 | `structure_locked` |
| 文案待确认 | `copy_draft` |
| G2 已过 | `copy_locked` |
| 已出页 | `rendered` |
| 已导出 | `exported` |

---

### D4 · 封面 preview.jpg：Pillow 固定版式（P1 可 Playwright）

| 项 | 决定 |
|----|------|
| **MVP** | Python Pillow：9:16、1080×1920 |
| **素材** | `coverAssetId` + `cropMobile` 或 9:16 裁切 |
| **文案** | `meta.hook` 或 `meta.title` + `meta.places[0]` + 日期 |
| **风格** | 杂志感：大图、留白、衬线地名、一句金句 |
| **P1** | 可选 Playwright 截封面 HTML 节点，与 golden 像素对齐 |

---

## 后果

### 正面

- 微信端加载与分享体积可控。  
- Agent 2 输入含 tags + anchors，叙事更个性化。  
- 开发可按阶段实现、可测试、可 resume。  

### 负面 / 代价

- 离线「单文件」优雅感让位于「单 zip」。  
- 本地 VLM/CLIP 增加可选依赖与 ingest 耗时。  
- 需维护 schema 字段与校验规则。

---

## 实现清单（文档与代码）

- [x] 本 ADR  
- [x] 更新 `CHARTER.md`、`PRD-MVP.md` 交付表述  
- [x] 更新 `DATA-MODEL.md`、`trip.schema.json`（`memoryAnchors`、`tagsSource`）  
- [x] 更新 `MEDIA-PIPELINE.md`、`NARRATIVE-PROMPTS.md`  
- [x] 更新 `RENDER-CONTRACT.md`（Pillow 封面）  
- [x] 更新 `CLI-SPEC.md`（`run --from`）  
- [ ] 代码：ingest 体积预算、tags 生成、Pillow preview、State Manager  

---

## 相关文档

- `MEDIA-PIPELINE.md` §体积预算、§视觉标签  
- `NARRATIVE-PROMPTS.md` §brief 扩展  
- `AGENT-ARCHITECTURE.md` §G1  
- `RENDER-CONTRACT.md` §preview.jpg  
