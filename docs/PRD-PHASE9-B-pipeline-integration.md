# Phase 9 · 附录 B · 管线集成与配置

| 属性 | 内容 |
|------|------|
| **主文档** | [PRD-PHASE9.md](./PRD-PHASE9.md) |
| **代号** | P9-B |
| **文档版本** | v0.9.1 |
| **更新** | 2026-06-02 |

---

## 1. 管线顺序（权威）

### 1.1 单次 ingest 批内

```text
0.  M30-0a 前置：layout_eligible_assets() 读 asset.layoutEligible（见 §2.2）
1.  scan_image_paths / scan_tiered_image_paths（max_photos 限制解码候选）
2.  per-photo loop: decode → dedupe(burst/phash) → build asset
3.  ★ apply_photo_cull(trip)          ← 全 trip assets re-cull
4.  apply_layout_eligibility_marks     ← 低清；featured 可豁免
5.  persist trip.json + ingest_stats
6.  clustering / curate               ← 仅 layoutEligible=true
```

step 4 结束后需在 `cullSummary` 回写低清后的最终口径：

- `finalLayoutEligibleCount`
- `finalNonFeaturedEligibleCount`
- `finalNonFeaturedKeepRatio`
- `finalFloorNotMet`

### 1.2 增量 ingest

每次 `_finalize_ingest_assets` 对 **`trip["assets"]` 全量** 执行 step 3–4（D-P9-10）。  
不因 `ingestBatchId` 仅 cull 新批次。

### 1.3 Studio Job

仍 4 stage；cull 耗时并入 ingest。

---

## 2. 模块边界

| 模块 | 文件 | 职责 |
|------|------|------|
| **M30-0a** | `curate.py` 等 | 统一 `layoutEligible` 过滤 |
| Cull 引擎 | `curation/photo_cull.py` | Pass 1–4 |
| Ingest 挂钩 | `media/ingest.py` | `_finalize` 内调用 cull |
| 低清 | `curation/asset_quality.py` | featured 低清豁免 |
| Studio | `web/studio_pipeline.py` | stats / hint |

### 2.1 M30-0a · `layout_eligible_assets`（W1 阻塞前置）

**修订后契约**：

```python
def layout_eligible_assets(trip: dict) -> list[dict]:
    return [
        a for a in trip.get("assets") or []
        if a.get("type", "image") != "video"
        and a.get("layoutEligible", True) is not False
    ]
```

**须同步检查**（grep `layoutEligible` / `excludedLowRes`）：

- `travelogue/curation/curate.py`
- `travelogue/curation/clustering.py`
- `travelogue/curation/degradation.py`
- `cover_eligible_assets` 等（已部分读 `layoutEligible`）

`excludedLowResAssetIds` / `excludedByCullAssetIds` **保留**作摘要；**权威字段**为 `asset.layoutEligible`。

### 2.2 `apply_photo_cull`

```python
def apply_photo_cull(
    trip: dict,
    assets: list[dict] | None = None,
    *,
    cfg: AppConfig | None = None,
    ingest_stats: dict | None = None,
) -> dict:
    """全 trip re-cull。异常 fail-open（D-P9-14）。Returns cullSummary."""
```

---

## 3. 与 Phase 3 聚类

- `ClusteringLayer.run` 输入经 `layout_eligible_assets` 过滤  
- embed **仅** layoutEligible 资产  
- NR-P9-01：clustering off + cull on → curate smoke

---

## 4. 配置规格

```yaml
cull:
  enabled: true
  mode: rules                 # W1 默认 rules；W2 再开 auto
  keep_ratio_floor: 0.80
  min_keep: 15
  featured_exempt: true
  featured_hard_exclude: false
  featured_exempt_low_res: true # 与 ingest featured 策略一致
  max_photos_warn_only: true
  sharpness_absolute_min: 0.0
  blur_percentile: 2            # W1 Pass 1 · P2 分位
  hard_exclude_media_classes: [screenshot, thumbnail, reupload]
  ml:                           # W2
    aesthetic_metric: topiq_nr
    portrait_face_aesthetic: true
    allow_cpu_ml: false         # auto 无 GPU 不跑 ml
    device: auto
```

**W1 默认**：`cull.mode: rules`（config.yaml.example 已对齐）。

---

## 5. Fail-open · 降级

| 条件 | 行为 |
|------|------|
| `cull.enabled=false` | skip |
| 任意异常 in `apply_photo_cull` | D-P9-14（fail-open + 清理 cull 历史 excludeReason） |
| pyiqa 缺失（W2） | P0 公式 |

---

## 6. CLI（W2 可选）

```bash
travelogue cull trips/my-trip --recalc
travelogue cull trips/my-trip --dry-run
```

W1 **可不实现** CLI；Pass 2 recalc 语义预留。

---

## 7. 性能预算

| 档位 | 200 张 |
|------|--------|
| W1 P0 | +5–15s CPU |

---

## 8. 验收

见 [ACCEPTANCE-PHASE9.md](./ACCEPTANCE-PHASE9.md) §2 AC-P9-01、07、08、09。

---

## 9. 修订记录

| 版本 | 日期 | 说明 |
|------|------|------|
| v0.9.1 | 2026-06-02 | M30-0a · 全 trip re-cull · W1 mode=rules |
| v0.9.0 | 2026-06-02 | 初稿 |
