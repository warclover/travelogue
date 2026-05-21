# Travelogue · 错误码

| 属性 | 内容 |
|------|------|
| **文档版本** | v0.1 |
| **格式** | `E_<域>_<名称>` |
| **关联** | `CLI-SPEC.md`、`VALIDATION-RULES.md` |
| **更新日期** | 2026-05-19 |

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

---

## 3. 版本历史

| 版本 | 日期 | 说明 |
|------|------|------|
| v0.1 | 2026-05-19 | 初稿 |
