# Travelogue · 错误码

| 属性 | 内容 |
|------|------|
| **文档版本** | v0.1 |
| **格式** | `E_<域>_<名称>` |
| **关联** | `CLI-SPEC.md`、`VALIDATION-RULES.md` |
| **更新日期** | 2026-05-28 |

---

## 1. 使用约定

- CLI 失败时：`stderr` 输出 `[E_CODE] 人类可读说明`。  
- `--json` 时：`{ "error": "E_CODE", "message": "...", "path": "chapters[0].items[1]" }`。  
- 日志文件可记 code，**禁止**记录 API Key、精确 GPS。

---

## 2. 错误码表

### 通用

| 代码 | HTTP式 | 说明 |
|------|--------|------|
| `E_TRIP_NOT_FOUND` | — | tripId 目录不存在 |
| `E_TRIP_INVALID_JSON` | — | trip.json 无法解析 |
| `E_CONFIG_MISSING` | — | 无 config.yaml 且缺必需 env |
| `E_DEPENDENCY_MISSING` | 3 | ffmpeg / pillow-heif 等未安装 |

### 流水线 `E_PIPELINE_*`

| 代码 | 说明 |
|------|------|
| `E_PIPELINE_ORDER` | 当前 status 不允许该命令 |
| `E_PIPELINE_LOCKED` | 结构或文案已锁，需先 unlock 或专用子命令 |
| `E_PIPELINE_BATCH_CONFLICT` | 结构已锁但有未处理 pendingAssets |

### 校验 `E_VALIDATE_*`

| 代码 | 说明 |
|------|------|
| `E_VALIDATE_SCHEMA` | 不符合 trip.schema.json |
| `E_VALIDATE_MANIFEST` | 不符合 manifest 业务规则 |
| `E_VALIDATE_LIMIT` | 字数/数量超限 |
| `E_VALIDATE_REF` | assetId 引用不存在 |

### 导入 `E_INGEST_*`

| 代码 | 说明 |
|------|------|
| `E_INGEST_EMPTY` | 目录无支持的媒体 |
| `E_INGEST_LIMIT_PHOTOS` | 超过 maxPhotosPerTrip |
| `E_INGEST_LIMIT_VIDEOS` | 超过 maxVideosPerTrip |
| `E_INGEST_VIDEO_TOO_LONG` | 源视频 >15s |
| `E_INGEST_FILE_CORRUPT` | 单文件失败（警告继续，不阻断） |
| `E_INGEST_HEIC` | HEIC 解码失败 |

### 策展 `E_CURATE_*`

| 代码 | 说明 |
|------|------|
| `E_CURATE_NO_ASSETS` | 无可用 asset |
| `E_CURATE_CHAPTER_COUNT` | 无法凑足 3–5 章 |

### 叙事 `E_NARRATE_*`

| 代码 | 说明 |
|------|------|
| `E_NARRATE_API` | LLM 调用失败 |
| `E_NARRATE_PARSE` | 模型输出非合法 JSON patch |
| `E_NARRATE_RETRY_EXHAUSTED` | 自动修复超过 2 次 |

### 渲染/导出 `E_RENDER_*` / `E_EXPORT_*`

| 代码 | 说明 |
|------|------|
| `E_RENDER_TEMPLATE` | 模板文件缺失 |
| `E_RENDER_ASSET_MISSING` | displayFile 不存在 |
| `E_EXPORT_PRIVACY` | 未 `--confirm-privacy` |
| `E_EXPORT_NOT_RENDERED` | 无 index.html |

### Studio / 长图 `E_STU_*` / `E_LNG_*`（Phase 2）

| 代码 | 说明 | Studio 用户文案（中文） |
|------|------|-------------------------|
| `E_STU_JOB_NOT_FOUND` | 无效 jobId | 任务不存在或已过期，请重新开始 |
| `E_STU_IMPORT_BUSY` | 已有 import Job 运行 | 正在处理上一本游记，请稍候 |
| `E_STU_UPLOAD_FAILED` | 浏览器上传写入失败 | 上传失败，请检查磁盘空间后重试 |
| `E_LNG_PLAYWRIGHT` | 未安装 playwright/chromium | 无法生成长图。请运行：pip install 'travelogue[playwright]' && playwright install chromium |
| `E_LNG_NO_LONGSHOT` | 无 index-longshot.html | 请先完成渲染，或检查 export.longShot 配置 |
| `E_LNG_CAPTURE_FAILED` | captureMainToBlob 失败 | 长图生成失败，请重试（M10+ 可按章导出） |
| `E_STUDIO_REVEAL_DENIED` | reveal 路径不在 trips 根下 | 无法打开该文件 |
| `E_STUDIO_AUTH` | 非 loopback 绑定缺少 `X-Studio-Token` | Studio 请求未授权 |
| `E_STUDIO_BODY_TOO_LARGE` | JSON/multipart 超过上限 | 请求体过大 |
| `E_STUDIO_ALBUM_DENIED` | LAN 模式下 JSON 任意 `albumPath` | 不允许从该路径导入 |
| `E_STUDIO_JOB_BUSY` | 已有 import / longshot / narrate Job | 正在处理上一任务，请稍候 |
| `E_STUDIO_CANCELLED` | 用户取消 Job | 已取消 |
| `E_STUDIO_UPLOAD_EMPTY` | multipart 无文件 | 未收到任何照片文件 |
| `E_STUDIO_PIPELINE` | 导入子进程或 pipeline 异常 | 导入失败，请重试 |
| `E_LLM_AUTH` | 未配置 LLM API Key | 未配置 LLM API Key，无法生成杂志感文案 |
| `E_EXPORT_PRIVACY` | Studio zip 未 confirmPrivacy | 导出 zip 需要确认隐私设置 |

### Demo / ingest 用户文案（Studio 映射）

| 代码 | Studio 用户文案（中文） |
|------|-------------------------|
| `E_INGEST_TOO_FEW` / `E_DEMO_TOO_FEW` | 至少需要 4 张照片，请换一个文件夹 |
| `E_INGEST_EMPTY` | 文件夹里没有找到照片 |
| `E_DEMO_NOT_DIR` | 所选路径不是文件夹 |
| `E_DEMO_EXISTS` | 该游记已存在 | **409** body 含 `existingTripId`；确认后 `POST import` + `"force": true` |
| `E_INGEST_HEIC` | 发现 HEIC 照片无法读取。请安装 pillow-heif 或转换为 JPG |

### 聚类 `E_CLUSTER_*`（Phase 3 · Curate 聚类）

| 代码 | 说明 | Studio 用户文案（中文） | 行为 |
|------|------|-------------------------|------|
| `E_CLUSTER_VISION_MISSING` | 未安装 `[vision]` extra 或模型不可用 | （无弹窗）场景分析不可用，已按日期排版。 | 降级 P3-Lite |
| `E_CLUSTER_VISION_TIMEOUT` | CLIP/聚类超时 | 场景分析耗时较长，已跳过主题分组。 | 跳过 scene；继续 pipeline |
| `E_CLUSTER_GEO_EMPTY` | 无有效 GPS/日期，无法 geo 分段 | （无弹窗）照片缺少位置信息，已按日期分段。 | fallback `time_segments` |
| `E_CLUSTER_CACHE_CORRUPT` | embeddings cache 损坏 | 正在重新分析照片… | 删 cache 自动重算 |

> Phase 3 聚类错误 **默认 fail-open**：记录日志 + 降级，**不** 阻断 ingest/curate 主路径（NR-P3-01）。

---

## 3. 版本历史

| 版本 | 日期 | 说明 |
|------|------|------|
| v0.1 | 2026-05-19 | 初稿 |
| v0.2 | 2026-05-27 | Phase 2 Studio / longshot 错误码 |
| v0.2.1 | 2026-05-27 | E_DEMO_EXISTS 确认流 + force 参数 |
| v0.3.1 | 2026-05-27 | E_DEMO_EXISTS 409 body；E_LNG_CAPTURE_FAILED 文案 |
| v0.3.2 | 2026-05-27 | M10 Studio Job 错误码；E_LLM_AUTH；E_STUDIO_REVEAL_DENIED |
| v0.4.0 | 2026-05-28 | Phase 3 Curate 聚类：`E_CLUSTER_*`；废止 v0.2 洞察/引擎错误码 |
