# Travelogue · CLI 规范

| 属性 | 内容 |
|------|------|
| **命令名** | `travelogue` |
| **文档版本** | v0.5 |
| **实现状态** | P0/P1 核心命令已实现；**Phase 2** `studio` / `export-longshot` / `serve --studio` **已实现**（P5-12.3 同步）；**Longshot 2.0** `--platform` 已实现 |
| **关联** | `AGENT-ARCHITECTURE.md`、`DEVELOPMENT.md`、`ERROR-CODES.md`、[PRD-PHASE2.md](./PRD-PHASE2.md)、[PRD-LONGSHOT-2.0.md](./PRD-LONGSHOT-2.0.md)、[ACCEPTANCE.md](./ACCEPTANCE.md) |
| **更新日期** | 2026-07-09 |

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
| **`studio`** | Studio | — | 启动工作台 HTTP |
| **`serve --studio`** | Studio | — | trips 根目录 Hub |
| **`export-longshot`** | 3 | `rendered`+ | 服务端长图 PNG |

**禁止**：在 `structure_locked` 之前调用 `narrate`（返回 `E_PIPELINE_ORDER`）。

### 2.2 Phase 2 · Studio 与长图（**已实现**）

| 命令 | 说明 | 等价 |
|------|------|------|
| **`studio`** | 启动 Studio 工作台 | `serve <trips_dir> --studio` |
| **`studio --pick-folder PATH`** | 先 pipeline，再 serve，再打开预览 | PATH 必填（脚本/CI） |
| **`studio --pick-folder-dialog`** | Windows 原生文件夹选择后再 pipeline | 桌面用户推荐 |
| **`export-longshot <trip>`** | Playwright 服务端长图 PNG | 见 §3.13 · ADR-005 |

#### `travelogue studio`

| 选项 | 说明 |
|------|------|
| `--pick-folder PATH` | 相册绝对路径；先跑 pipeline 再进入 serve |
| `--pick-folder-dialog` | Windows IFileDialog 选文件夹（Phase 4+） |
| `--demo-album` | 导入内置 demo 相册后 serve |
| `--port` / `-p` | 默认 **8766** |
| `--host` | 默认 `127.0.0.1` |
| `--allow-lan` | 非 loopback 绑定 · **所有**变更与敏感 GET（含 `/{tripId}/*` 静态资源）需 `X-Studio-Token`（Header / Cookie / `?studio_token=`） |
| `--no-open` | 不自动打开浏览器 |
| `--title` / `--place` | pipeline 默认杂志名/地点 |
| `--trips-dir` | trips 根目录（默认 `config.trips_dir`） |
| `--config` | 指定 config.yaml |

**入口脚本**：`scripts/start-studio.bat`（双击启动 · 等价 `python -m travelogue studio`，并默认 `TRAVELOGUE_STUDIO_TRUST_LOCAL_ALBUM=1` 以便本机文件夹导入）。

**环境变量**

| 变量 | 默认 | 说明 |
|------|------|------|
| `TRAVELOGUE_STUDIO_TRUST_LOCAL_ALBUM` | `0` | 为 `1` 时，loopback 下允许 `albumPath` 指向 uploads/demo/trips 以外的本机目录（文件夹选择器 / JSON 导入）。LAN 模式始终仅允许 uploads/demo。 |

**默认 Web pipeline**（`run_studio_pipeline`）：ingest → clustering → curate → narrate → render · Job 进度经 `StudioHooks` · `stageHint` 人话预估。

**进度**：Job 返回 `stageIndex` / `stageCount` / **`stageHint`**；ingest 子进度 `processed/total`（P5-I1）。

#### `travelogue serve` 扩展

| 选项 | 说明 |
|------|------|
| `--studio` | 启用 Studio 路由（`/`、`/__travelogue/*`）+ trip 子路径 |
| `--allow-lan` | 局域网访问 + token 鉴权（GET/POST/PATCH/DELETE 敏感路由） |
| `--trips-dir` | path 为 tripId 时解析 trips 根 |

无 `--studio` 时行为与 MVP **单 trip 预览**一致；**仅允许 loopback 绑定**（非 `127.0.0.1`/`localhost`/`::1` 会拒绝启动），写接口（`save-copy` / `promote-tier`）亦仅本机。

#### `travelogue export-longshot <trip>`（§3.13）

| 选项 | 说明 |
|------|------|
| `--format` / `-f` | `png`（默认）\| `jpeg` |
| `--scale` | CLI 默认 **`1`**；Studio HTTP / UI 默认 **`2`**（推荐）；最大 `3` |
| `--chapter` | 仅第 N 章（1-based） |
| `-o` / `--out` | 单文件输出路径（不分段时） |
| `--port` / `-p` | 临时 HTTP（0=随机） |

**捕获宽度**：**428px** × scale（P5-L1 · 弃 390 默认）。

**分段（P5-L2）**：预估单张 **>20MB** 或高度超阈值 → 按章 `{title}-ch{nn}.png` · Job 返回 `userHint`。

**依赖**：`pip install playwright` + Chromium（Studio 启动时可 warm）。

#### Studio HTTP（`serve --studio` · 单端口 8766）

| 方法 | 路径 | 说明 |
|------|------|------|
| `GET` | `/` | Studio 首页 |
| `GET` | `/__travelogue/trips` | trip 列表 |
| `GET` | `/__travelogue/trips/{id}/entry` | 预览深链 · peakScreenId |
| `GET` | `/__travelogue/status?jobId=` | import / longshot / narrate Job |
| `GET` | `/__travelogue/config` | 分析选项 · layout.scoring 等 |
| `PATCH` | `/__travelogue/config` | 持久化 config.yaml 白名单字段 |
| `GET` | `/__travelogue/chapter-layout?tripId=` | 分章 + 排版 explain |
| `POST` | `/__travelogue/import` | JSON 或 multipart 上传 |
| `POST` | `/__travelogue/longshot` | `{ tripId, scale? }` → Job |
| `POST` | `/__travelogue/narrate` | LLM 文案 Job |
| `POST` | `/__travelogue/reveal` | 资源管理器定位文件 |
| `POST` | `/__travelogue/cancel` | 取消活跃 Job |
| `POST` | `/__travelogue/export` | share zip（需隐私确认） |
| `POST` | `/__travelogue/pick-folder` | Windows 文件夹选择 |
| `POST` | `/__travelogue/trips/{id}/curate` | 强制重跑 curate |
| `PATCH` | `/__travelogue/trips/{id}/intent` | 杂志名 · userNotes |
| `PATCH` | `/__travelogue/trips/{id}/pipeline` | G1 确认 · `continuePipeline` |
| `POST` | `/{tripId}/__travelogue/save-copy` | 预览内联改字 / 锚点 |
| `POST` | `/{tripId}/__travelogue/promote-tier` | ★ 标为精选 |
| `POST` | `/{tripId}/__travelogue/rerender` | 应用排版重渲染 |
| `GET` | `/{tripId}/…` | trip 静态资源 · preview 注入 toolbar |

**import body（JSON）**：`{ "albumPath", "title?", "place?", "userNotes?", "planText?", "force": false }` — `E_DEMO_EXISTS` 时 UI 确认后 **`force: true`** 重试。

**上传清理**：Job succeeded → 删 `trips/_uploads/{jobId}/`；failed 保留 24h。

详见 [adr/004-studio-hub-server.md](./adr/004-studio-hub-server.md) v0.3。

**Preview Chrome**：`index.html` / `index-mobile.html` 注入 `preview-toolbar.js` + `studio-modal.js`（`?share=1` / `mode=share` **不**注入 · P5-S7）。

---

### 2.3 `travelogue run <tripId> --from <stage>`

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

### 3.12 `travelogue studio`（已实现 · Phase 2/5）

见 [§2.2](#22-phase-2--studio-与长图已实现)。常用：

```powershell
python -m travelogue studio
python -m travelogue studio --pick-folder-dialog
python -m travelogue studio --pick-folder D:\Photos\trip --no-open
```

---

### 3.13 `travelogue export-longshot <trip>`（已实现 · Phase 2/5 · Longshot 2.0）

Playwright 捕获 `index-longshot.html`（须已 `render` 且 sidecar 存在）。

```powershell
python -m travelogue export-longshot demo-雨后京都
python -m travelogue export-longshot demo-雨后京都 --scale 2 -o out.png
python -m travelogue export-longshot demo-雨后京都 --chapter 2
# Longshot 2.0 · 平台化（见 SHARING §2.5 / PRD-LONGSHOT-2.0）
python -m travelogue export-longshot demo-雨后京都 --platform wechat_moments --scale 2
python -m travelogue export-longshot demo-雨后京都 --platform xiaohongshu --slide-count 6 --pad-mode letterbox
python -m travelogue export-longshot demo-雨后京都 --platform instagram --slide-count 4
python -m travelogue export-longshot demo-雨后京都 --platform weibo --slide-count 6
python -m travelogue export-longshot demo-雨后京都 --platform douyin_cover
python -m travelogue export-longshot demo-雨后京都 --platform custom --width 720 --height 960 --slide-count 3
```

| 选项 | 说明 |
|------|------|
| `--platform` | `wechat_chat`（默认）· `wechat_moments` · `xiaohongshu` · `instagram` · `weibo` · `douyin_cover` · `custom` |
| `--slide-count` | aspect-fit 张数（xhs 1–18 / ins 1–10 / weibo 1–9 / custom 1–18）；省略 = auto；朋友圈 / 抖音封面忽略 |
| `--pad-mode` | `letterbox`（默认）· `smart_crop`（需 `studio.longshot2.smart_crop.enabled`；`douyin_cover` 默认 smart_crop） |
| `--width` / `--height` | 仅 `--platform custom`；默认 1080×1440；范围 64–4096 × 64–8192 |
| `--scale` | 1–3；平台模式降 scale 会重采 boundary + 重截图 |
| `--chapter` | 仅 `wechat_chat`；平台模式忽略 |

失败码：`E_EXPORT_LONGSHOT` / `E_LNG2_*`（见 `ERROR-CODES.md`）。Studio 内等价 `POST /__travelogue/longshot`（可带 `platform` / `slideCount` / `padMode`）。

Telemetry（本地 jsonl）：`longshot_export_start` / `_success` / `_fail` · `~/.travelogue/telemetry/studio-homepage-events.jsonl`。

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
| v0.2.1 | 2026-05-27 | cancel、force import、upload 清理、bat 入口 |
| v0.3 | 2026-05-27 | stageHint；Studio scale=2 默认；Studio Chrome |
| v0.3.1 | 2026-05-27 | reveal API；--trips-dir；409 body |
| v0.4 | 2026-05-30 | **P5-12.3**：studio/export-longshot 已实现 · HTTP 路由补全 · 428px/20MB 长图 · preview-toolbar |
| v0.5 | 2026-07-09 | Longshot 2.0：`--platform` / `--slide-count` / `--pad-mode` · SHARING §2.5 |
