# PRD-PHASE2 · 实施任务清单

| 属性 | 内容 |
|------|------|
| **权威 PRD** | [PRD-PHASE2.md](./PRD-PHASE2.md) v0.3.1 |
| **验收** | [ACCEPTANCE-PHASE2.md](./ACCEPTANCE-PHASE2.md) v0.3.1 |
| **ADR** | [adr/004](./adr/004-studio-hub-server.md) v0.3.1、[adr/005](./adr/005-longshot-server-side.md) v0.3.1 |
| **更新** | 2026-05-27 |

---

## 全局门禁（每个 Phase 2 PR）

| # | 门禁 |
|---|------|
| **NR-P2-01** | `python -m pytest tests/ -q` **0 失败** |
| **NR-P2-02** | 无 `--studio` 时 serve 与 MVP 一致 |

---

## 阶段总览

| 里程碑 | 交付 |
|--------|------|
| **M8a** | serve + Job + pipeline + CLI/bat（架构跑通） |
| **M8b** | studio.html + Chrome allowlist + stageHint 分档 |
| **M9** | export-longshot + 长图 UI + reveal + browser 单例 |
| **M10** | trip 列表、toolbar、cancel、stub 图注 |
| **M11** | P2 backlog · exe |

**Phase 2 完成**：M8a+M8b+M9+M10 + AC-P2-01a/b～06 + NR-P2-01

---

## M8a · 架构跑通（W1）

### M8a-1 · serve `--studio` + StudioMixin

| # | 任务 | 模块 | 状态 |
|---|------|------|------|
| M8a-1a | `serve(..., studio=True)` | `serve.py` | ☑ |
| M8a-1b | **`StudioMixin` + dispatcher**（ADR-004 D9） | `studio_routes.py` | ☑ |
| M8a-1c | Job + stageIndex/stageCount/**stageHint 分档** | `studio_jobs.py` | ☑ |
| M8a-1d | import 前统计照片数 → ingest hint（≤50/51–100/101–250） | `studio_pipeline.py` | ☑ |

**M8a-1d 不含 Chrome 注入**（M8b 再做）。

### M8a-2 · pipeline + CLI

| # | 任务 | 模块 | 状态 |
|---|------|------|------|
| M8a-2a | `run_studio_pipeline`；pin max_photos=250 | `studio_pipeline.py` | ☑ |
| M8a-2b | 后台线程 Job + GIL `sleep(0)` | `studio_jobs.py` | ☑ |
| M8a-2c | `travelogue studio` + `--pick-folder` + `--trips-dir` | `cli.py` | ☑ |
| M8a-2d | `scripts/start-studio.bat` | `scripts/` | ☑ |

### M8a-3 · API（最小）

| # | 任务 | 模块 | 状态 |
|---|------|------|------|
| M8a-3a | `POST /import`（`force`）· **`409` + existingTripId** | `studio_routes.py` | ☑ |
| M8a-3b | `GET /status`（含 stageHint） | `studio_routes.py` | ☑ |

**M8a 出口**：维护者 `studio --pick-folder PATH` → 浏览器预览；Job 轮询可见 stageHint。

---

## M8b · Studio Web（W2）

### M8b-1 · studio.html

| # | 任务 | 模块 | 状态 |
|---|------|------|------|
| M8b-1a | 粘贴路径表单（主） | `studio.html` | ☑ |
| M8b-1b | 备选 upload + XHR progress | `studio.js` | ☑ |
| M8b-1c | stage 轮询 + stageHint 展示 | `studio.js` | ☑ |
| M8b-1d | `E_DEMO_EXISTS` → confirm → `force:true` | `studio.js` | ☑ |
| M8b-1e | 最近 trip：`GET /trips` → **`trips[0]` 渲染 `<a href="/{id}/index.html">`** | `studio.html` | ☑ |
| M8b-1f | 空态文案 + **`assets/sample-longshot.jpg`**（golden trip 导出占位） | `studio.html` | ☑ |
| M8b-1g | >100 张 soft warning | `studio.js` | ☑ |

### M8b-2 · Studio Chrome（allowlist）

| # | 任务 | 模块 | 验收 | 状态 |
|---|------|------|------|------|
| M8b-2a | `should_inject_studio_chrome()` allowlist | `studio_routes.py` | ☑ |
| M8b-2b | 注入 `index.html` / `index-mobile.html` **仅** | `serve.py` | ☑ |
| M8b-2c | **`index-longshot.html` 不注入** | 同上 | pytest 截图无 Chrome | ☑ |
| M8b-2d | 返回工作台 + 编辑提示条 | `preview-toolbar.js` | ☑ |

### M8b-3 · API 补全

| # | 任务 | 模块 | 状态 |
|---|------|------|------|
| M8b-3a | `GET /trips` JSON | `studio_routes.py` | ☑ |
| M8b-3b | `_uploads` 清理 + 中文错误 | `studio_jobs.py` · `studio_errors.py` | ☑ |

**M8b 出口**：AC-P2-01a · AC-P2-03 · UX-P2-*

---

## M9 · 可分享闭环

| # | 任务 | 模块 | 状态 |
|---|------|------|------|
| M9-1a | P0 captureMainToBlob | `export/longshot.py` | ☑ |
| M9-1b | P1 screenshot fallback | `longshot.py` | ☑ |
| M9-1c | **`base_url` 分支**：Studio 用 8766；CLI 临时 HTTP | `longshot.py` | ☑ |
| M9-1d | **Playwright browser 单例**（60s idle close） | `longshot.py` | ☑ |
| M9-2a | 高度 >5000px / 章 >60 卡分段 | `longshot.py` | ☑ |
| M9-3a | CLI 默认 scale=1 | `cli.py` | ☑ |
| M9-4a | `POST /longshot` | `studio_routes.py` | ☑ |
| M9-5a | chrome 最小「保存长图」+ Job 轮询 | `preview-toolbar.js` | ☑ |
| M9-5b | 成功路径面板 + **`POST /reveal`** | `preview-toolbar.js` | ☑ |
| M9-5c | Studio UI 默认 scale=2 | `preview-toolbar.js` | ☑ |
| M9-6a | P2：按章 PNG 页码水印 | `longshot.py` | ☑ |

---

## M10 · 工作台成熟化

| # | 任务 | 模块 | 状态 |
|---|------|------|------|
| M10-1a | trip 列表 UI | `studio.html` | ☑ |
| M10-2a | `preview-toolbar.js` 替换 chrome | `templates/studio/` | ☑ |
| M10-2b | stale 长图提示 | `preview-toolbar.js` | ☑ |
| M10-3a | `POST /cancel` + `cancelled` | `studio_jobs.py` | ☑ |
| M10-3b | pipeline 子进程 | `studio_subprocess.py` | ☑ |
| M10-3c | 失败态「返回工作台 / 重试」 | `studio.html` | ☑ |
| M10-4a | **F-NAR-P2-04** stub 图注 | `narrate.py` | ☑ |
| M10-4b | stub hook 模板库 | `narrate.py` | ☑ |

---

## M11 · PyInstaller（P2 · backlog）

| # | 任务 | 状态 |
|---|------|------|
| M11-1 | spec + IFileDialog | ☑ |
| M11-2 | 内置 demo 试跑相册 | ☑ |

---

## 缺口补齐（2026-05-27）

| # | 任务 | 模块 | 状态 |
|---|------|------|------|
| GAP-1 | **F-NAR-P2-03** LLM 按钮 + `GET /config` + `POST /narrate` | `studio_routes.py` · `preview-toolbar.js` | ☑ |
| GAP-2 | **F-LNG-08** >30s 慢速提示 | `preview-toolbar.js` · `studio.js` | ☑ |
| GAP-3 | **F-LNG-09** scale=2「推荐 · 适合手机」 | `preview-toolbar.js` | ☑ |
| GAP-4 | **F-NAR-P2-01** 章 lead Day 格式 | `narrate.py` | ☑ |
| GAP-5 | **F-STU-14** `studio_stages.yaml` 外置 hint | `studio_stages.yaml` · `studio_stages.py` | ☑ |
| GAP-6 | **NR-P2-02** 非 studio serve 测试 | `test_studio_nr_p2_02.py` | ☑ |

**P2 backlog（已完成）**：F-LNG-13 页码水印 · preview.jpg 路径展示 · LS-P2-01 脚本

| # | 任务 | 模块 | 状态 |
|---|------|------|------|
| BL-1 | **F-LNG-13** 按章 PNG 页码水印 | `longshot.py` · `preview-toolbar.js` | ☑ |
| BL-2 | **preview.jpg** Studio 生成 + 路径展示 | `studio_pipeline.py` · `studio_trips.py` · toolbar | ☑ |
| BL-3 | **LS-P2-01** 稳定性脚本 | `scripts/phase2_longshot_stability.py` | ☑ |
| BL-4 | 自动化验收前置检查 | `scripts/phase2_studio_acceptance.py` | ☑ |

**仍须人工验收**：AC-P2-01a/b～06 · PF-P2-* 计时 · LS-P2-01 在 ≥5 真实 trip 上跑脚本

---

## 版本历史

| 版本 | 日期 | 说明 |
|------|------|------|
| v0.3 | 2026-05-27 | Studio Chrome；M9 长图 UI；stageHint |
| v0.3.1 | 2026-05-27 | M8a/b 拆分；allowlist；reveal；409 body；base_url |
| v0.3.2 | 2026-05-27 | 缺口补齐：LLM 按钮、慢速提示、stage YAML、NR-P2-02 |
| v0.3.3 | 2026-05-27 | backlog：页码水印、preview.jpg 路径、LS-P2-01 脚本 |
