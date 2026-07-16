# IMPLEMENTATION · 媒体存储省盘与引用模式 V1

| 属性 | 内容 |
|------|------|
| **PRD** | [PRD-MEDIA-REFERENCE-STORAGE-V1.md](./PRD-MEDIA-REFERENCE-STORAGE-V1.md) **v0.2.0** |
| **评审** | [acceptance-records/media-reference-storage-v1-review-2026-07-15.md](./acceptance-records/media-reference-storage-v1-review-2026-07-15.md) |
| **分支** | `feature/media-reference-storage-v1` |
| **更新日期** | 2026-07-16 |

---

## 切片

| 切片 | 内容 | 状态 |
|------|------|------|
| **W0** | PRD v0.2 · 本 IMPLEMENTATION · ERROR-CODES | ✅ |
| **W1a** | `copy_source_files` · schema `sourceRef`/`media` · 串行 ingest · `resolve_source_path` | ✅ |
| **W1b** | 并行 ingest worker/merge · 二次解码读原路径 | ✅ |
| **W1c** | 安全/深度清理 API · 占用估算 · 设置「存储与磁盘」UI | ✅ |
| **W2** | remount + source-status · 导出 Facade 阻断 · ADR-008 · F-ING-02a/b · zip 泄漏断言 | ✅ |

---

## 并行 ingest 技术简报（BLK-02）

| 点 | 做法 |
|----|------|
| Worker | `WorkerIngestConfig.copy_source_files`；`force_materialize`（demo/upload）强制写 provisional JPEG |
| Commit | `_commit_provisional_blobs(..., copy_source_files=)` 可跳过 source move |
| Merge | mediaClass/美学：先 trip `source/{id}.jpg`，否则 `result.source_path` |
| Entry | 复制模式写 `sourceFile`+`sourceRef`；引用模式仅 `sourceRef` |

---

## 关键路径

| 区域 | 文件 |
|------|------|
| Resolve | `travelogue/media/source_resolve.py` |
| Cleanup | `travelogue/media/storage_cleanup.py` |
| Config | `travelogue/config/ingest.py` · `loader.py` · `studio.py` |
| Ingest | `ingest.py` · `ingest_worker.py` · `ingest_parallel.py` |
| Reexport / CLIP | `reexport.py` · `vision/clip_encoder.py` |
| API | `web/studio_handlers/storage_handlers.py` · `paths.py` · `studio_dispatch.py` |
| UI | `studio-home-v2.html` · `homepage-v2/storage-settings.js` · `settings-panel.js` |
| Schema | `schemas/trip.schema.json` |
| Tests | `tests/unit/media/test_source_resolve_storage.py` · `tests/unit/export/test_export_no_absolute_paths.py` |

---

## API

| Method | Path | 说明 |
|--------|------|------|
| GET | `/__travelogue/storage/usage` | 占用估算 |
| POST | `/__travelogue/storage/cleanup` | `{ safe, deepSource, acceptDerivativesOnly, tripIds?, devScratch? }` |
| POST | `/__travelogue/storage/remount` | `{ tripId, albumPath }` |
| PATCH | `/__travelogue/config` | `{ ingest: { copySourceFiles } }` |

---

## W2 补充路径

| 项 | 落地 |
|----|------|
| source-status | `GET /__travelogue/trips/{id}/source-status` |
| 导出闸 | `longshot.js` `maybeSourceMissingGate` · Task Dock 栈位 · handler 409 安全网 |
| remount UI | 导出阻断 Modal → pick-folder → `POST .../storage/remount` |
| ADR / AC / DATA-MODEL | 已回写 |
| zip 泄漏 | `tests/unit/export/test_export_no_absolute_paths.py` |

## P1 收口（合入前补齐）

| 项 | 落地 |
|----|------|
| 导入向导引用/上传文案 +「更改存储设置」 | `import-wizard.js` · `studio-home-v2.html` |
| 设置页 trip `storageMode` 纯文字 | `storage-settings.js` · source-status |
| DLLM 三组交叉引用 | `PRD-DESKTOP-LLM-SETUP-V1.md` §4.3 |
| remount `content_changed` UI | `longshot.js` 阻断 + toast |
| incremental 失败码 | ingest `errorCode=E_MEDIA_INCREMENTAL_SOURCE` |

## P2 收口

| 项 | 落地 |
|----|------|
| AC-MRS-02b 并行引用自动化 | `test_parallel_reference_ingest_skips_source_jpeg` |
| 书架占用超阈值角标 | `shelf.js` 「磁盘占用较高」→ 打开存储设置 |
| incremental 警告透出 UI | `StudioPipelineResult.media_warn` → first-success toast |

## 可选后续

1. 设置清理改用产品 Dialog（替代 `window.confirm`）  
2. 批量 remount 多 trip 共享 albumRoot  
3. 「引用 → 重新物化 source」反向向导  
4. 狗粮 5 步出口勾选（评审纪要 §8）  
