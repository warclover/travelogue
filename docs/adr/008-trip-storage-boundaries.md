# ADR-008 · trip.json 存储边界与 Document/Blob 分离

| 属性 | 内容 |
|------|------|
| **状态** | **Accepted**（PRD v0.22.1 评审闭合 · 2026-06-11） |
| **日期** | 2026-06-11 |
| **决策者** | 首席架构 / Phase 22 |
| **关联 PRD** | [PRD-PHASE22-storage-platform.md](../PRD-PHASE22-storage-platform.md) v0.22.0 |
| **取代/补充** | [ADR-001](./001-delivery-and-media.md) SSOT、[ADR-006](./006-media-engines-integration.md) 遥测分离 |

---

## 背景

Travelogue 以 **`trip.json` + 文件系统** 为 SSOT，无关系型业务主库。Phase 15–21 在 curate/layout 层快速迭代，带来：

1. 调试字段易写入 trip，体积膨胀；
2. 多种 cache 目录缺乏统一失效与清理；
3. Studio 与 CLI 可能并发写同一 trip；
4. P2 托管需要 document/blob 边界，但不应现在拆表。

Phase 22 需要 **成文的存储边界**，避免「file-as-DB」退化为「JSON 垃圾堆」。

---

## 决策

### 1. SSOT 不变

- **`trip.json` 仍是唯一业务真相源**。
- Agent / Studio **不得**引入第二份可写 chapters/assets 副本（除 render 输出 HTML）。

### 2. trip.json 写入分类

#### 2.1 允许（Document · 用户/管线状态）

- `version`, `tripId`, `templateId`, `exportLayout`, `export`, `meta`（含 **`revision`**）
- `intent`, `userNotes`, `privacy`, `pipeline`（含 **`stageFingerprints` 摘要**）
- `assets[]`（元数据：id、路径引用、quality、dimensions；**非** embedding）
- `chapters[]`, `coverAssetId`, `coverCandidates`
- `curation` **摘要**：`orientationSummary`, `clustering`（segments/clusters 摘要）, `layoutDensityMeta`, **`layoutDecisionLogDigest` + `layoutDecisionLogCount`**
- **禁止** `curation.layoutDecisionLog[]` 全量数组（见 §7 清退）

#### 2.2 禁止（Blob / Derived / Telemetry）

| 数据 | 落点 |
|------|------|
| CLIP embedding | `trips/{id}/.cluster-cache/embeddings.npz` |
| 审美 CV cache | `trips/{id}/cache/phase_pa_aesthetic.json` |
| LLM raw / prompt cache | `trips/{id}/.cache/narrate/` |
| 全量 layout/mosaic decision log | `trips/{id}/runs/layout-decisions.jsonl` |
| 单次 pipeline trace | `trips/{id}/runs/run-{ulid}.json` |
| Studio 行为 telemetry | `~/.travelogue/telemetry/*.jsonl` |
| 跨 trip geocode | `trips/.geocode-cache.json` |

**Lint**：CI / `scripts/lint_trip_json.py` 拦截已知禁止顶层键；512 KiB 警告、2 MiB 失败（可配置）。

### 3. revision 乐观锁

- 字段：`meta.revision: integer`，每次成功 `TripService.save` +1。
- Studio 写接口支持 `expectedRevision`；冲突 → HTTP **409** `E_TRIP_REVISION_CONFLICT`。
- CLI 可选 `--expect-revision`；pipeline 单进程默认不强制。

**理由**：比文件锁更轻；比 PostgreSQL 事务更贴本地单文件模型。

### 4. Cache Registry

- 代码注册表 `CacheRegistry` 为 **唯一** 缓存路径/失效文档源。
- `purge_trip(trip_dir)` 在删除相册时级联清理 trip 级 cache；geocode 全局 cache 除外。

### 5. Library Index 非 SSOT

- SQLite 默认 **`{trips_dir}/.travelogue/library.db`**；主键 `(workspace_root, trip_id)`。
- JSON fallback：`trips/_library/index.json`。
- 冲突时 **以 trip.json 为准**；index 可 full reconcile 重建。

### 6. revision bump 分离

- **用户/API 写**（intent、tier、chapters/copy）：`bump_revision=True`。
- **pipeline 系统写**（`stageFingerprints`、`pipeline.status` 中间态）：`bump_revision=False`。

### 7. layoutDecisionLog 清退（P22-W1）

| 阶段 | trip.json | runs/ |
|------|-----------|-------|
| dual-write | digest + count；可选保留旧数组一版 | append jsonl 全量 |
| 读者切换 | 仅 digest | chapter_explain 读 jsonl |
| 终态 | 无 `layoutDecisionLog[]` | 权威来源 |

### 8. Document / Blob / Derived 三层（P2 预埋）

| 层 | 本地 | 云端（未来） |
|----|------|--------------|
| **Document** | `trip.json` | Object snapshot `trips/{id}/snapshots/{rev}.json` |
| **Blob** | `source/`, `assets/` | S3/R2 `assets/{contentHash}` |
| **Derived** | `index.html`, longshot PNG | CDN 或按需生成 |

- `trip.json` **永久** 作为 import/export 交换格式。
- P22 **不实现** 上传；仅约定路径与 optional `assets[].contentHash`。

---

## 拒绝的方案

| 方案 | 原因 |
|------|------|
| PostgreSQL 作业务主库 | P0–P1 无多用户查询需求；双写 trip.json 与表 |
| chapters/screens 拆表 | 破坏 Agent 只改 JSON；curate 重写成本高 |
| 全量 CRDT 协同 | 产品未定义多人编辑；复杂度过高 |
| 把 embedding 写入 trip.assets | 体积与 schema 爆炸 |

---

## 后果

### 正面

- trip 体积可控；git diff / zip 分享更可靠；
- 并发写可检测；增量 pipeline 有 fingerprint 锚点；
- P2 托管可映射到 object snapshot，无需推翻 curate。

### 负面

- 开发者需查 ADR 再新增 trip 字段；
- Studio 客户端需处理 409 重试；
- library index 可能漂移，需 reconcile 运维习惯。

---

## 合规

- 延续 ADR-006：**行为 telemetry 永不进 trip.json**。
- 分享 trip zip 前，`runs/` 与 `.cache/` 可选 strip（已有 privacy 闸口扩展点）。

---

## 版本历史

| 版本 | 日期 | 说明 |
|------|------|------|
| v0.2 | 2026-06-11 | Accepted · PRD v0.22.1 评审闭合 |
| v0.1 | 2026-06-11 | Proposed · Phase 22 Kickoff |
