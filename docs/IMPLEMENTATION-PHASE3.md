# PRD-PHASE3 · 实施任务清单

| 属性 | 内容 |
|------|------|
| **权威 PRD** | [PRD-PHASE3.md](./PRD-PHASE3.md) v0.3.3 Kickoff |
| **验收** | [ACCEPTANCE-PHASE3.md](./ACCEPTANCE-PHASE3.md) v0.3.3 |
| **ADR** | [adr/007-native-clustering.md](./adr/007-native-clustering.md) v0.2 |
| **排版对齐** | [智能排版V2.md](./智能排版V2.md) Layer 1.5 · P1 |
| **更新** | 2026-05-28 |

---

## 全局门禁（每个 Phase 3 PR）

| # | 门禁 |
|---|------|
| **NR-P3-01** | `clustering.enabled=false` 时与 Phase 2 **documented equivalent**（PRD §12.1 · ACCEPTANCE §3） |
| **NR-P3-02** | `python -m pytest tests/ -q` **0 失败**（vision 测试可用 `@pytest.mark.vision` optional） |
| **NR-P3-03** | Phase 3 产出的 trip 在 clustering off 下 **可 serve / export-longshot** |

---

## 阶段总览

| 里程碑 | 交付 |
|--------|------|
| **M12-0** | 算法 Spike · golden fixtures · [clustering-algorithm-matrix.md](./spikes/clustering-algorithm-matrix.md) |
| **M12** | **P3-Lite**：§13.3 P0 包（geo + curate + decision_log + CACHE-05 + Studio） |
| **M12.5** | F-CLU-CACHE-01～03 增量策略（可与 M13 并行） |
| **M13** | **P3-Full**：scene_clusters + vision + layout + **AC-P3-C09** + I-G2 报告 |
| **M14** | 权重调参 · WORKSHOP 附录 · cache 清理 CLI（可选） |

**Phase 3 v1.0 完成**：M12-0 Go + M12 + M13 + AC-P3-C01～**C09** + NR-P3-01/02/03 + **UX-P3-01～07**

---

## M12-0 · 算法 Spike（W0 · 编码前）

| # | 任务 | 产出 | 状态 |
|---|------|------|------|
| M12-0-1 | 选定 3 套 golden trip（有 GPS / 无 GPS / 混合场景） | `tests/fixtures/clustering/` | ☐ |
| M12-0-2 | 人工标注 geo event 边界（spreadsheet 或 JSON） | `*-segments-golden.json` | ☐ |
| M12-0-3 | 跑通 Recasa 参考输出对比（**只读验证**，不集成） | matrix §3 | ☐ |
| M12-0-4 | CLIP 选型（PyTorch vs ONNX）与 eps/min_samples 敏感性 | matrix §4 | ☐ |
| M12-0-5 | 填写 matrix Go/No-Go + **§3.5 偏差白名单**（若需） | 签字 | ☐ |
| M12-0-6 | **关闭 OQ-P3-03** CLIP 选型 | matrix §4 | ☐ |
| M12-0-7 | 本文件 + ACCEPTANCE §3 review | IMPLEMENTATION review | ☐ |

**出口**：SP-C01～**05** 全 Go → 启动 M12 编码。

---

## M12 · P3-Lite（W1–2）

### M12-1 · 配置与 feature flag

| # | 任务 | 模块 | 状态 |
|---|------|------|------|
| M12-1a | `ClusteringConfig` + `VisionConfig` + `config.yaml.example` | `config.py` | ☐ |
| M12-1b | `clustering.enabled`（true/false/**auto**）、`segmentCurateMode` | `config.py` | ☐ |
| M12-1c | 默认 **`enabled=auto`**、`vision.enabled=false`；off 时 skip ClusteringLayer | `studio_pipeline.py` | ☐ |
| M12-1d | `clustering.deterministic=true` + 固定 seed 路径 | `clustering.py` | ☐ |

### M12-2 · geo_events

| # | 任务 | 模块 | 状态 |
|---|------|------|------|
| M12-2a | `detect_geo_events(assets, cfg) -> list[GeoSegment]` | `curation/geo_events.py` | ☐ |
| M12-2b | 时间窗切分 + GPS 跳变 + stay 合并 | 同上 | ☐ |
| M12-2c | 段命名（location + date span） | 同上 | ☐ |
| M12-2d | 封面候选启发式（sharpness + face bbox） | 同上 | ☐ |
| M12-2e | 无 GPS → 返回空 + `segmentMode=date_fallback` | 同上 | ☐ |
| M12-2f | 单元测试 + golden | `tests/test_geo_events.py` | ☐ |

### M12-3 · ClusteringLayer 接入

| # | 任务 | 模块 | 状态 |
|---|------|------|------|
| M12-3a | `ClusteringLayer.run(trip, assets)` | `curation/clustering.py`（新） | ☐ |
| M12-3b | ingest 后调用；写 `curation.clustering` + `asset.eventId` | `studio_pipeline.py` 或 `ingest.py` | ☐ |
| M12-3c | ingest `stageHint` 按 PRD §6.4.2 写入 | `studio_pipeline.py` | ☐ |

### M12-7 · Studio 前端（PRD §6.4）

| # | 任务 | 模块 | 状态 |
|---|------|------|------|
| M12-7a | D′ 折叠「高级 · 分析选项」HTML + CSS | `studio.html` · `studio.css` | ☐ |
| M12-7b | `GET/PATCH /__travelogue/config`（PRD §9.5） | `serve.py` | ☐ |
| M12-7c | 首页加载时回显 clustering/vision 当前值 | `studio.js` | ☐ |
| M12-7d | T+30s 慢提示（Phase 2 回归 · §6.4.4 L1） | `studio.js` | ☐ |
| M12-7e | `#studio-shell-slot-p3` 保持空 · 无引擎灯 | `studio.html` | ☐ |

### M12-4 · curate 消费

| # | 任务 | 模块 | 状态 |
|---|------|------|------|
| M12-4a | `build_buckets_from_clustering`（PRD §8.1 伪代码） | `curation/curate.py` | ☐ |
| M12-4b | `merge_small_events` + `cap_segments(3–5)` | `curation/bucket_planning.py` 或新 helper | ☐ |
| M12-4c | 章 title / coverCandidates hints | `curate.py` | ☐ |
| M12-4d | `date_fallback` 与 Phase 2 双跑测试 | `tests/test_curate_clustering.py` | ☐ |
| M12-4e | burst 优先级：`burstGroupId` > cluster run > 时间 | `screen_planner.py` / curate | ☐ |
| M12-4e2 | burst 优先级单测（F-CLU-CUR-05） | `tests/test_burst_priority.py` | ☐ |
| M12-4f | `decision_log`（PRD §9.6） | `curation/decision_log.py` | ☐ |
| M12-4g | M12 reingest **全量**重算 embed（无增量） | `clustering.py` | ☐ |

### M12-5 · 数据模型与校验

| # | 任务 | 模块 | 状态 |
|---|------|------|------|
| M12-5a | [DATA-MODEL.md](./DATA-MODEL.md) §3.4 同步 | docs | ☐ |
| M12-5b | `trip.schema.json` optional `curation.clustering` | `schemas/` | ☐ |
| M12-5c | validate L1 忽略 optional 子树 | 现有 validator | ☐ |

### M12-6 · cache 与确定性（M12 子集）

| # | 任务 | 模块 | 状态 |
|---|------|------|------|
| M12-6a | F-CLU-CACHE-**05** 损坏 npz 重算 | `vision/cache.py` · `clustering.py` | ☐ |
| M12-6b | 双跑确定性（AC-P3-C08） | `tests/test_clustering_deterministic.py` | ☐ |
| M12-6c | NR-P3-01 回归套件（ACCEPTANCE §3） | `tests/test_clustering_regression.py` | ☐ |

**M12 出口**：AC-P3-C01 · C04 · C06 · C07 · C08 · PRD §13.2 E1～E8

---

## M12.5 · 增量 cache（W2–3 · 可选缓冲）

| # | 任务 | 模块 | 状态 |
|---|------|------|------|
| M125-1 | F-CLU-CACHE-01 mtime / asset 数失效 | `vision/cache.py` | ☐ |
| M125-2 | F-CLU-CACHE-02 增量 <10% embed + 全 trip DBSCAN | `clustering.py` | ☐ |
| M125-3 | F-CLU-CACHE-03 ≥30% / forceRecluster 全量 | `clustering.py` · `cli.py` | ☐ |
| M125-4 | `tests/test_cluster_cache.py` | tests | ☐ |

---

## M13 · P3-Full（W3–4）

### M13-1 · vision 模块

| # | 任务 | 模块 | 状态 |
|---|------|------|------|
| M13-1a | `[vision]` optional extra in `pyproject.toml` | `pyproject.toml` | ☐ |
| M13-1b | `ClipEncoder` lazy load + model download | `vision/clip_encoder.py` | ☐ |
| M13-1c | `EmbeddingCache` → `trips/{id}/.cluster-cache/` | `vision/cache.py` | ☐ |
| M13-1d | 未安装 vision → `E_CLUSTER_VISION_MISSING` 降级 | `clustering.py` | ☐ |

### M13-2 · scene_clusters

| # | 任务 | 模块 | 状态 |
|---|------|------|------|
| M13-2a | `compute_scene_clusters(assets, embeddings, cfg)` | `curation/scene_clusters.py` | ☐ |
| M13-2b | DBSCAN on embeddings（UMAP debug only） | 同上 | ☐ |
| M13-2c | 写 `asset.sceneClusterId` + `curation.clustering.clusters[]` | `clustering.py` | ☐ |
| M13-2d | medoid 选取 | `scene_clusters.py` | ☐ |
| M13-2e | timeout → `E_CLUSTER_VISION_TIMEOUT` | `clustering.py` | ☐ |
| M13-2f | golden + `@pytest.mark.vision` | `tests/test_scene_clusters.py` | ☐ |
| M13-2g | **单次 forward**：embedding + subjectClass logits | `vision/clip_encoder.py` | ☐ |

### M13-3 · layout 消费（对齐智能排版 V2 P1）

| # | 任务 | 模块 | 状态 |
|---|------|------|------|
| M13-3a | `sceneClusterMode: run_aware` 段内 run | `screen_planner.py` | ☐ |
| M13-3b | `subject_run` 评分项启用 cluster | `layout/scoring.py` | ☐ |
| M13-3c | 黄金样本 I-G2 回归 | `tests/test_layout_golden.py` | ☐ |
| M13-3d | AC-P3-C09 全量 layout guard | `tests/test_layout_golden.py` | ☐ |
| M13-3e | **I-G2 报告模板** 填写（mao/maomi/linzhi） | `docs/reports/` 或 matrix 附录 | ☐ |

### M13-4 · 性能

| # | 任务 | 模块 | 状态 |
|---|------|------|------|
| M13-4a | 400 张 CPU 计时脚本 | `scripts/phase3_cluster_bench.py` | ☐ |
| M13-4b | GPU 路径 optional 文档 | WORKSHOP 附录 | ☐ |

### M13-5 · Studio 前端（PRD §6.4 · P3-Full）

| # | 任务 | 模块 | 状态 |
|---|------|------|------|
| M13-5a | 场景分析三态 + stageHint（场景/首次下载） | `studio.js` · pipeline | ☐ |
| M13-5b | T+3min / T+8min 慢提示（§6.4.4 L2/L3） | `studio.js` | ☐ |
| M13-5c | wireframe Importing hint 变体 3 条 | `wireframes/studio-homepage-wireframe.html` | ☐ |

**M13 出口**：AC-P3-C02 · C03 · C05 · **C09** · **UX-P3-04～07**

---

## M14 · 增强（可选 · W5）

| # | 任务 | 模块 | 状态 |
|---|------|------|------|
| M14-1 | config 权重调参指南 | WORKSHOP.md | ☐ |
| M14-2 | `.cluster-cache` 清理 CLI | `cli.py` | ☐ |
| M14-3 | migrate-on-load：`curation.insights` strip | `serve.py` | ☐ |
| M14-4 | 预览「为什么这样分章」（§6.4.8） | preview-toolbar | ☐ |
| M14-5 | vision 降级 Toast | `studio.js` | ☐ |
| M14-6 | F-CLU-CACHE-04 pendingAssets **文档 + CLI stub** | docs · `cli.py` | ☐ |

---

## 模块接口签名（M12-0 定稿输入）

```python
# travelogue/curation/geo_events.py
@dataclass
class GeoSegment:
    id: str
    name: str
    start_date: date
    end_date: date
    location: str | None
    asset_ids: list[str]

def detect_geo_events(
    assets: list[dict],
    *,
    event_time_gap_hours: float = 4,
    min_photos_per_event: int = 3,
    location_proximity_km: float = 5.5,
    merge_time_gap_hours: float = 36,
    merge_location_km: float = 55,
    max_event_days: int = 4,
) -> list[GeoSegment]: ...


# travelogue/curation/scene_clusters.py
@dataclass
class SceneCluster:
    id: int
    label: str
    asset_ids: list[str]
    medoid_asset_id: str | None

def compute_scene_clusters(
    assets: list[dict],
    embeddings: np.ndarray,
    *,
    eps: float = 0.07,
    min_samples: int = 10,
) -> list[SceneCluster]: ...


# travelogue/curation/clustering.py
class ClusteringLayer:
    def run(self, trip: dict, assets: list[dict], trip_dir: Path, cfg: AppConfig) -> None:
        """写入 trip['curation']['clustering'] 与 per-asset fields."""
```

---

## 测试清单

| 套件 | 命令 | 说明 |
|------|------|------|
| geo golden | `pytest tests/test_geo_events.py -q` | M12 必跑 |
| curate clustering | `pytest tests/test_curate_clustering.py -q` | M12 必跑 |
| NR-P3-01 | `pytest tests/test_clustering_regression.py -q` | PRD §12.1 · ACCEPTANCE §3 |
| burst priority | `pytest tests/test_burst_priority.py -q` | M12 · F-CLU-CUR-05 |
| deterministic | `pytest tests/test_clustering_deterministic.py -q` | M12 · AC-P3-C08 |
| cache incremental | `pytest tests/test_cluster_cache.py -q` | **M12.5** |
| vision | `pytest -m vision -q` | CI optional / nightly |
| layout golden | `pytest tests/test_layout_golden.py -q` | M13 |

---

## 版本历史

| 版本 | 日期 | 说明 |
|------|------|------|
| v0.3.0 | 2026-05-28 | 原生 Curate 聚类实施清单（替代 v0.2 引擎/Orchestrator 版） |
| v0.3.1 | 2026-05-28 | decision_log/cache 升 M12；auto config；deterministic；burst guard；C08/C09 测试 |
| v0.3.2 | 2026-05-28 | M12-7/M13-5 Studio 前端；§6.4 UX |
| v0.3.3 | 2026-05-28 | M12.5 cache 切割；§9.5 API；NR-P3-01 §12.1；E3/C09 分离；Kickoff |
