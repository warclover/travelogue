# ADR-004 · Studio 模式：扩展 serve，单进程单端口

| 属性 | 内容 |
|------|------|
| **状态** | 已采纳（**v0.3.1 修订**，取代 v0.1 双服务方案） |
| **日期** | 2026-05-27 |
| **决策者** | 产品 + 技术负责人 |
| **影响范围** | `travelogue/web/serve.py`、`cli.py`、Phase 2 Studio |
| **关联** | [PRD-PHASE2.md](../PRD-PHASE2.md) §7、§9、[API-MINIAPP.md](../API-MINIAPP.md) |
| **修订** | v0.1 曾决策独立 `StudioHubServer`（8765）；评审后 **撤销**，改为 `--studio` 扩展现有 serve |

---

## 背景

1. MVP 已有 `travelogue serve <trip>`：`TripPreviewHandler` + `save-copy` / `promote-tier` + 自动重渲染。  
2. Phase 2 需要：工作台首页、pipeline Job、import API、最简 `studio.html`。  
3. v0.1 方案新增独立 Hub（8765）与 serve（8766）并存 → **评审结论**：Phase 2 单机场景过度设计；双端口、trip 路径委托、双 Handler 维护成本高于收益。  
4. 云端 Job 模型（P3）仍需要对齐，但 **本地不必提前拆服务**。

---

## 决策

### D1 · 不新建 Hub Server；扩展 `serve` 为 Studio 模式

| 项 | 决定 |
|----|------|
| **CLI** | `travelogue studio` ≡ `travelogue serve <trips_dir> --studio`（糖衣命令） |
| **单 trip 调试** | `travelogue serve trips/<id>` **不变**（无 `--studio`） |
| **默认端口** | **8766**（与现有 serve 一致；**不再**使用 8765） |
| **绑定** | 默认 `127.0.0.1` only |
| **实现** | 在 `TripPreviewHandler`（或同级 Handler）上增加 Studio 路由；**不**新建 `studio_server.py` 独立服务 |

**理由**：一个进程、一个端口、一套路由；`save-copy` / `promote-tier` **零路径前缀映射**。

---

### D2 · URL 路由表（`--studio` 模式）

`<trips_dir>` 默认为 `config.trips_dir`（通常 `./trips`）。

| 方法 | 路径 | 行为 |
|------|------|------|
| `GET` | `/` | `templates/studio/studio.html`（M8 最简；M10 增强） |
| `GET` | `/__travelogue/trips` | 扫描 `<trips_dir>` 最近 trip JSON 列表 |
| `POST` | `/__travelogue/import` | 启动 import Job（JSON 或 multipart 上传） |
| `GET` | `/__travelogue/status?jobId=` | Job 状态 |
| `POST` | `/__travelogue/longshot` | 启动 longshot Job（M9） |
| `POST` | `/__travelogue/reveal` | 在文件夹中显示（M9；body `{ path }`） |
| `POST` | `/__travelogue/cancel` | 取消 Job（**M10**；body `{ jobId }`） |
| `GET` | `/{tripId}/index.html` | 静态文件：`<trips_dir>/{tripId}/` |
| `POST` | `/{tripId}/__travelogue/save-copy` | **现有** inline edit（路径不变） |
| `POST` | `/{tripId}/__travelogue/promote-tier` | **现有** tier promote |

> Studio 模式下 Handler 的 `directory` 按请求路径动态解析到对应 trip 子目录；`/`` 与 `/__travelogue/*` 走 Studio 逻辑，其余走现有 trip 静态 + API 逻辑。

---

### D3 · `--pick-folder` 时序

**先 pipeline，再 serve，再打开预览**（避免空工作台干等）：

```text
travelogue studio --pick-folder PATH
  → 同步/Job：run_studio_pipeline(PATH)
  → 成功后：serve <trips_dir> --studio [--open]
  → webbrowser.open /{tripId}/index.html
```

若用户仅 `travelogue studio`（无 pick-folder）：直接启动 `--studio` serve + 打开 `/` 工作台。

---

### D4 · Job 状态机（字段对齐云端，HTTP 不拆服务）

Job JSON **字段名** 仍对齐 `API-MINIAPP.md` §6，便于 P3 迁移：

| 字段 | 说明 |
|------|------|
| `jobId` | `job-{uuid}` |
| `type` | `import` \| `longshot` |
| `status` | `queued` \| `running` \| `succeeded` \| `failed` \| `cancelled`（**M10**） |
| `stage` | `ingest` \| `curate` \| `narrate` \| `render` \| `longshot` |
| `stageIndex` | 1–4（import pipeline）或 1–1（longshot） |
| `stageCount` | 4 或 1 |
| `error` | `{ code, message }`；`message` 为用户中文 |
| `result` | `previewUrl`、`tripId`、`tripDir`、`outputs[]` |

**进度模型（Phase 2）**：仅 **离散 stage**（「2/4 正在排版（约 30 秒）…」），含 **`stageHint`** 预估时间字段；**不做** ingest 内部 0–100% 连续进度（避免重构 pipeline API）。

Job 在后台线程执行；同一时刻 **1 个 import Job**。

---

### D5 · pipeline 调用链

**不得** shell 拼接 `workshop-pipeline.ps1`。

```text
run_demo_from_album(..., render=False)
→ run_trip(from_stage=lock_structure, until=rendered, skip_locked=True, narrate_provider=stub)
→ render_trip_surfaces(draft)
```

封装于 `studio_pipeline.py`（或 `web/studio_pipeline.py`）。

---

### D6 · 文件夹导入

| 路径 | 机制 |
|------|------|
| **M8 CLI** | `--pick-folder PATH` **必填路径**；M8 不做原生对话框 |
| **M8 studio.html** | **优先** 粘贴路径；**备选** `webkitdirectory` → `trips/_uploads/{jobId}/`（须上传 progress） |
| **M11 exe（P2）** | Windows IFileDialog |

**上传清理（D6b）**：

| 时机 | 动作 |
|------|------|
| Job **succeeded** | 删除 `trips/_uploads/{jobId}/` |
| Job **failed** | 保留 24h；启动时 sweep |
| Job **cancelled**（M10） | 同 failed |

浏览器 **不能** POST 本地 `D:\` 绝对路径。

---

### D7 · Pipeline 与 GIL

- Job 在后台 **线程**；ingest CPU 密集可能饿死 HTTP 轮询。  
- **M8**：pipeline 循环内 `time.sleep(0)`。  
- **M10**：pipeline 迁至子进程（`ProcessPoolExecutor`）。

---

## 后果

### 正面

- 单进程单端口；无 trip 路由委托 bug 温床。  
- 现有 serve 测试可扩展，而非并行维护两套服务。  
- Job JSON 仍可对齐云端。

### 负面

- `TripPreviewHandler` 职责增加；须用 `--studio` flag 清晰分支。  
- 动态 trip 目录路由比单 trip serve 略复杂。

### 缓解

- Studio 逻辑集中在 `studio_routes.py` / handler mixin，保持文件边界。  
- 无 `--studio` 时行为与 MVP **完全一致**（回归保障）。

---

## 备选方案（记录）

| 方案 | 结论 |
|------|------|
| v0.1 独立 Hub:8765 + serve:8766 | **撤销**（Phase 2 过度设计） |
| Tauri / Electron | Phase 2 不做 |
| 仅 CLI 无 Web UI | **否决**（AC-P2-01 需 M8 最简 studio.html） |

---

### D8 · Studio Chrome 注入（v0.3）

| 里程碑 | 行为 |
|--------|------|
| **M8** | `serve --studio` 对 allowlist 内 trip HTML 注入 `studio-chrome.js` |
| **M9** | chrome 增加最小「保存长图」+ longshot Job 轮询 + 成功路径面板 + `POST /reveal` |
| **M10** | chrome 替换为 `preview-toolbar.js`（完整 toolbar） |

**注入 allowlist（v0.3.1 · 验收必测）**：

| 注入 | 不注入 |
|------|--------|
| `/{tripId}/index.html` | `/{tripId}/index-longshot.html` |
| `/{tripId}/index-mobile.html` | 其他 `*.html`、CSS/JS/图片 |

实现：`TripPreviewHandler` 在 `--studio` 且路径匹配 allowlist 时，于 `</body>` 前注入 `<script src="/__studio/studio-chrome.js">`；逻辑集中在 `templates/studio/studio-chrome.js`。

**禁止**对 `index-longshot.html` 注入——该面为 P0 长图 capture 目标，Chrome 会污染 `<main>` 截图。

### D9 · 路由组织（v0.3.1）

Studio 逻辑 **不得**堆进 `serve.py` 的巨型 if-elif。采用 **`StudioMixin`** + `studio_routes.py` dispatcher：

```python
# studio_routes.py
class StudioMixin:
    studio_mode: bool = False
    def studio_dispatch_GET(self, path: str) -> bool: ...
    def studio_dispatch_POST(self, path: str) -> bool: ...
    def should_inject_studio_chrome(self, path: str) -> bool: ...

# serve.py
class TripPreviewHandler(StudioMixin, SimpleHTTPRequestHandler):
    def do_GET(self):
        if self.studio_mode and self.studio_dispatch_GET(self.path): return
        if self.studio_mode and self.should_inject_studio_chrome(...): ...
        super().do_GET()
```

---

## 相关决策（非本 ADR 修订）

Desktop 写作引擎密钥与用户级配置落在 **`user_data_dir`**（与 `trips_dir` 分裂），见 **[ADR-019](./019-desktop-user-data-llm-secrets.md)**。Studio 仍保持本 ADR 的单进程 `--studio`；不新增配置服务端口。

---

## 版本历史

| 版本 | 日期 | 说明 |
|------|------|------|
| v0.1 | 2026-05-27 | 初稿：独立 StudioHubServer |
| v0.2 | 2026-05-27 | 合并为 `serve --studio` 单进程 |
| v0.2.1 | 2026-05-27 | cancelled、upload 清理、GIL D7、cancel 路由 |
| v0.3 | 2026-05-27 | D8 Studio Chrome；stageHint；M9 长图 UI 注入 |
| v0.3.1 | 2026-05-27 | Chrome allowlist；D9 StudioMixin；reveal API |
| 注记 | 2026-07-15 | 交叉引用 ADR-019（user_data / LLM secrets） |
