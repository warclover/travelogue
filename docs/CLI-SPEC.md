# Travelogue · CLI 规范

| 属性 | 内容 |
|------|------|
| **命令名** | `travelogue` |
| **文档版本** | v0.1 |
| **实现状态** | P0/P1 核心命令已实现（见 §2 表） |
| **关联** | `AGENT-ARCHITECTURE.md`、`DEVELOPMENT.md`、`ERROR-CODES.md`、[API-MINIAPP.md](./API-MINIAPP.md)（小程序 HTTP 对照） |
| **更新日期** | 2026-05-19 |

---

## 1. 总则

- 所有子命令以 **`tripId`** 为第一位置参数（`trip new` 除外）。  
- 默认读写目录：`config.yaml` → `trips_dir`（默认 `./trips`）。  
- 成功退出码 **0**；预期失败 **1**；参数错误 **2**；环境缺失（ffmpeg/Key）**3**。  
- 人类可读输出走 **stderr**；机器可读 JSON 用 `--json`（可选，P1）。

### 1.1 如何调用（Windows 常见）

`pip install -e .` 会安装控制台脚本 `travelogue.exe` 到 Python 的 `Scripts` 目录。若 PowerShell 报 **「无法将 travelogue 项识别为 cmdlet…」**，说明该目录不在 `PATH` 上。

**推荐（无需改 PATH）：**

```powershell
python -m travelogue <子命令> …
```

与 `python -m travelogue.cli …` 等价。下文示例仍写作 `travelogue …`；本地请自行替换，或把 `Scripts` 加入 PATH（见 `DEVELOPMENT.md` §4.1）。

---

## 2. 命令一览

| 命令 | Agent | 前置 `pipeline.status` | 成功后 status |
|------|-------|------------------------|---------------|
| `trip new` | — | — | `draft_ingest` |
| `trip list` | — | — | — |
| `ingest` | 0 | `draft_ingest` \| 增量 | `ingest_ready` |
| `curate` | 1 | `ingest_ready` \| `structure_draft` | `structure_draft` |
| `narrate` | 2 | `structure_locked` | `copy_draft` |
| `lock structure` / `lock copy` | — | 见 §3.5 | 锁定闸口 |
| `status` | — | 任意 | — |
| `lock structure` | — | `structure_draft` | `structure_locked` |
| `narrate` | 2 | `structure_locked` \| `copy_draft` | `copy_draft` |
| `lock copy` | — | `copy_draft` | `copy_locked` |
| `render` | 3 | `copy_locked` \| `rendered` | `rendered` |
| `export` | 3 | `rendered` | `exported` |
| `validate` | — | 任意 | — |
| `layout` | 1.5 | `structure_draft`+（已有 assets） | 更新 `chapters` / `curation` |
| **`demo <album>`** | 0+1.5+3 | — | `structure_draft`（+`rendered` 若未 `--no-render`） |
| `demo from-album` | （同上，别名） | — | 同上 |
| `status` | — | 任意 | — |
| `run` | 0–3 | 见 `--from` | 链式推进 |

**禁止**：在 `structure_locked` 之前调用 `narrate`（返回 `E_PIPELINE_ORDER`）。

### 2.1 `travelogue run <tripId> --from <stage>`

从指定阶段执行到下一人工闸口或 `--until`。

| 选项 | 说明 |
|------|------|
| `--from ingest\|curate\|narrate\|render\|export` | 起始阶段 |
| `--until structure\|copy\|rendered\|exported` | 停在哪一闸口 |
| `--skip-locked` | 若已 `copy_locked` 仅 render，不重复 narrate |

**手改 JSON 后续跑**：

```powershell
# G1 删章、写 memoryAnchors 后
travelogue validate kyoto-2025-04 --level all
travelogue lock structure kyoto-2025-04
travelogue run kyoto-2025-04 --from narrate --until copy

# G3 前只改 caption
travelogue validate kyoto-2025-04
travelogue render kyoto-2025-04
```

State Manager 规则见 `AGENT-ARCHITECTURE.md` §3 与 `adr/001`。

---

## 3. 命令详述

### 3.1 `travelogue trip new <tripId>`

创建游记项目。

| 选项 | 说明 |
|------|------|
| `--from <path>` | 本地照片/视频目录；若提供则链式调用 ingest |
| `--title <text>` | 预填 `meta.title`（可选） |
| `--force` | 目录已存在时覆盖空 trip（危险，需确认） |

**行为**：

1. 创建 `trips/{tripId}/`、`source/`、`assets/`、`runs/`。  
2. 写入初始 `trip.json`（`version: 0.2`，`pipeline.status: draft_ingest`）。  
3. `--from` 时继续执行 `ingest`。

**示例**：

```powershell
travelogue trip new kyoto-2025-04 --from D:\Photos\Kyoto
```

---

### 3.2 `travelogue trip list`

列出 `trips_dir` 下所有 trip：`tripId`、`pipeline.status`、`meta.title`、`updatedAt`。

---

### 3.3 `travelogue ingest <tripId>`

| 选项 | 说明 |
|------|------|
| `--from <path>` | 本次导入目录（默认 `source/` 扫描新增） |
| `--batch-id <id>` | 指定批次 ID；默认时间戳 `batch-YYYYMMDD-HHMM` |
| `--no-dedupe` | 跳过去重（含 md5 / phash / 连拍） |
| `--no-crop` | 不生成 9:16/16:9 裁切图 |
| `--config` | 指定 `config.yaml`（`webp_widths`、`phash_threshold` 等） |

**行为**：见 `MEDIA-PIPELINE.md`。完成后 `pipeline.status = ingest_ready`。终端输出导入报告（跳过原因、日期来源、构图统计）。

### 3.3a `travelogue media reexport <tripId>`

从 `source/` 按当前 `focalPoint`、`aspectKind` 与章节 slot（封面/scroll）**重导出 WebP**，不改 `chapters`。

| 选项 | 说明 |
|------|------|
| `--asset/-a` | 仅重导出指定 asset id（可重复） |
| `--config` | 读取 `ingest.webp_widths` / `generate_crops` |

改完 `trip.json` 里的 `focalPoint` 或跑完 `layout` 后执行。

---

### 3.4 `travelogue curate <tripId>`

| 选项 | 说明 |
|------|------|
| `--no-llm` | 章标题仅用规则/地名，不调 LLM |
| `--incremental` | 仅处理 `pendingAssets` |

**行为**：写入 `chapters[]`、`coverCandidates`、`coverAssetId`（提案）。`structure_draft`。

---

### 3.5 `travelogue lock structure <tripId>`

| 选项 | 说明 |
|------|------|
| `--cover <assetId>` | 指定封面（须在 candidates 或 assets 内） |

设置 `pipeline.locks.structure = true`，`pipeline.status = structure_locked`。

---

### 3.5a `travelogue layout <tripId>`（已实现）

在已有 `trip.json` 上重跑 **Agent 1.5 排版师**：按 `assets[].aspectKind` 与 `exportLayout` 重写 `chapters[].items[]`，写入 `curation.orientationSummary`。

| 选项 | 说明 |
|------|------|
| `--layout mobile\|web\|auto` | 覆盖 `exportLayout`（默认 `mobile`） |
| `--render` | 保存后重渲染 draft `index.html` |
| `--no-validate` | 跳过后续校验 |

**不改动**：封面 `coverAssetId`、像素文件、文案字段。

```powershell
travelogue layout demo-雨后京都 --layout web --render
```

算法见 `docs/LAYOUT-PLANNER.md`。

---

### 3.6 `travelogue narrate <tripId>`

| 选项 | 说明 |
|------|------|
| `--tone relaxed\|documentary` | 覆盖 `meta.tone` |
| `--field <path>` | 仅重生成单字段，如 `meta.hook` |
| `--dry-run` | 打印 brief 不调 API |

**行为**：见 `NARRATIVE-PROMPTS.md`。尊重 `edited: true`。

---

### 3.7 `travelogue lock copy <tripId>`

`pipeline.locks.copy = true`，`pipeline.status = copy_locked`。

---

### 3.8 `travelogue render <tripId>`

| 选项 | 说明 |
|------|------|
| `--mode draft\|share` | 默认 `draft` |
| `--layout auto\|mobile\|web` | 覆盖 `exportLayout` 仅本次渲染 |

**行为**：见 `RENDER-CONTRACT.md`。先 `validate`，失败不写入 HTML。

---

### 3.9 `travelogue export <tripId>`

| 选项 | 说明 |
|------|------|
| `--confirm-privacy` | 必填才写入 `privacy.confirmedAt` 并打包 |
| `--no-preview` | 跳过 `preview.jpg` |
| `--output <path>` | zip 输出路径，默认 `trips/{id}/trip-{id}.zip` |
| `--no-longshot` | 写入 `export.longShot=false`，zip 不含长图 bundle（默认 **含**） |

**前置**：`rendered` 或已存在 `index.html`；`--confirm-privacy` 时剥离 EXIF 展示图。

---

### 3.10 `travelogue validate <tripId>`

| 选项 | 说明 |
|------|------|
| `--level schema\|manifest\|all` | 默认 `all` |
| `--file <path>` | 校验任意 json，不读 trip 目录 |

等价脚本：`python scripts/validate_trip.py trips/{id}/trip.json`

---

### 3.11 `travelogue status <tripId>`

打印：`pipeline.status`、`locks`、资产数、章数、最后 `runs[]` 一条。

---

## 4. 推荐工作流

**一键 Demo（与下面分步同一套 ingest/curate/render）：**

```powershell
travelogue demo .\album --title "雨后京都" --layout mobile
travelogue status demo-雨后京都 --g1
```

**一键出可分享 zip（相册 → zip）：**

```powershell
travelogue demo .\album --title "雨后京都" --place 京都 --publish
# 等价分步：lock structure → narrate → export --confirm-privacy
travelogue run demo-雨后京都 --from lock_structure --until exported --confirm-privacy
```

**Demo 子命令：**

| 命令 | 说明 |
|------|------|
| `travelogue demo <album>` | 相册 → HTML（自动读 `config.demo.yaml` 若存在） |
| `travelogue demo <album> --publish` | 同上 + lock → narrate → share zip（`--confirm-privacy` 默认开） |
| `travelogue demo verify` | 4 个 fixture（含 `render_golden`）+ DOM 回归 + pytest 快套件 |
| `travelogue demo verify --album .\photos` | 再加真图 smoke |
| `travelogue demo verify --sync-reference` | 同步 `trips/_golden-reference/render-golden-demo/` |
| `travelogue demo verify --full` | 全量 `tests/` |
| `travelogue demo golden` | 预览 `golden.html`；缺 reference 时自动 materialize |
| `travelogue demo golden --sync-reference` | 强制从 fixture 生成 reference trip |

**分步（闸口 / 导出）：**

```powershell
travelogue trip new demo --from .\album
travelogue curate demo
# 人工编辑 trip.json 或后续 UI
travelogue lock structure demo --cover asset-001
travelogue narrate demo --tone relaxed
travelogue lock copy demo
travelogue render demo
travelogue export demo --confirm-privacy
```

---

## 5. 全局选项

| 选项 | 说明 |
|------|------|
| `--config <path>` | 指定 config.yaml |
| `--trips-dir <path>` | 覆盖 trips 根目录 |
| `-v` / `--verbose` | 详细日志 |
| `-q` / `--quiet` | 仅错误 |

---

## 6. 版本历史

| 版本 | 日期 | 说明 |
|------|------|------|
| v0.1 | 2026-05-19 | P0.5 CLI 规范初稿 |
