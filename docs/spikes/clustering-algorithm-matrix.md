# M12-0 · Curate 聚类算法 Spike 矩阵

| 属性 | 内容 |
|------|------|
| **文档版本** | v0.3 |
| **状态** | Draft · 待 M12-0 实测签字 |
| **关联 PRD** | [PRD-PHASE3.md](../PRD-PHASE3.md) v0.3.3 §4.5 |
| **更新日期** | 2026-05-28 |

---

## 1. Spike 目标

在 **不集成** Recasa / PhotoMapAI 的前提下，验证原生算法能否满足：

| ID | 通过标准 |
|----|----------|
| **SP-C01** | geo events 与 golden **一致率 ≥70%**（有 GPS trip） |
| **SP-C02** | scene cluster 簇数合理（5–40）；无 mega-cluster |
| **SP-C03** | curate 章数始终 **3–5** |
| **SP-C04** | mao / maomi / linzhi **NR-P3-01** + I-G1 不劣化 |
| **SP-C05** | 同 fixture 双跑：`curation.clustering` **hash 一致**（G-P3-C08） |

---

## 2. Golden Trip 清单

| Trip ID | 路径 / 来源 | 张数 | GPS | 标注内容 | 状态 |
|---------|-------------|------|-----|----------|------|
| `golden-kyoto-gps` | 待填：`tests/fixtures/clustering/kyoto/` | ~200 | ✅ | 人工 event 边界 JSON | ☐ |
| `golden-local-no-gps` | 待填：微信另存册（如 mao） | ~150 | ❌ | 期望 `date_fallback` | ☐ |
| `golden-mixed-scenes` | 待填：多场景旅行 | ~300 | ✅ | event + 主题簇抽检 | ☐ |

**产出目录**：`tests/fixtures/clustering/{tripId}/`

```
{tripId}/
├── assets-manifest.json      # assetId, takenAt, geo, path
├── segments-golden.json      # 人工标注 event 边界
├── clusters-golden.json      # 可选 · M13 主题簇抽检
└── README.md                 # 采集说明、EXIF 脱敏备注
```

---

## 3. Geo Event 算法（P3-Lite）

### 3.1 参考来源

借鉴 [Recasa event_detector](https://github.com/yonie/recasa/blob/master/backend/app/services/event_detector.py)（MIT）思路，**非代码拷贝**。

### 3.2 参数矩阵（待实测勾选）

| 参数 | 默认值 | 候选 A | 候选 B | 备注 |
|------|--------|--------|--------|------|
| `eventTimeGapHours` | 4 | 3 | 6 | 连续照片最大间隔 |
| `minPhotosPerEvent` | 3 | 2 | 5 | 少于此不进 event |
| `locationProximityKm` | 5.5 | 3 | 10 | GPS 跳变子切分 |
| `mergeTimeGapHours` | 36 | 24 | 48 | stay 合并 |
| `mergeLocationKm` | 55 | 30 | 80 | 与上行配合 |
| `maxEventDays` | 4 | 3 | 7 | 合并后单 event 上限 |

### 3.3 SP-C01 实测记录

| Trip | 算法参数集 | 一致率 | 主要偏差 | 决议 |
|------|------------|--------|----------|------|
| golden-kyoto-gps | default | — | — | ☐ |
| golden-mixed-scenes | default | — | — | ☐ |

**一致率定义**：golden 段边界与算法段边界，按 asset 归属计算 **Jaccard ≥0.7** 的段占比。

### 3.4 与 Recasa 参考对比（可选）

| Trip | Recasa v1.5 docker 输出 | 原生 geo_events | 差异说明 |
|------|-------------------------|-----------------|----------|
| golden-kyoto-gps | 未跑 / 已跑 | — | 仅参考，不阻断 |

### 3.5 可接受偏差白名单（SP-C01 · 未达 70% 时）

若一致率 **<70%**，下列偏差类型可 **产品+技术联合签字** 接受；须写入本表「决议」列：

| 偏差类型 | 示例 | 可接受？ | 签字 |
|----------|------|----------|------|
| 同城相邻 event 合并为一段 | 上午/下午同一 metro 区 | ☐ 是 ☐ 否 | |
| 短停（<minPhotos）并入前后 stay | 服务区 2 张 | ☐ 是 ☐ 否 | |
| GPS 漂移导致假跳变 | 室内/隧道 | ☐ 是 ☐ 否 | |
| 人工按「天」切、算法按「stay」切 | 边界差 1 天 | ☐ 是 ☐ 否 | |

**No-Go**：若偏差不可接受且调参后仍 <60% → 推迟 geo_events，M12 仅 ship `date_fallback` + NR-P3-01。

---

## 4. Scene Cluster 算法（P3-Full）

### 4.1 参考来源

借鉴 PhotoMapAI：CLIP embedding → 聚类（生产路径 **不用 UMAP**；UMAP 仅 debug 可视化）。

### 4.2 模型选型

| 选项 | 体积 | CPU 400张 | GPU | 决议 |
|------|------|-----------|-----|------|
| OpenCLIP ViT-B/32 PyTorch | ~350MB | 待测 | 待测 | ☐ |
| ONNX 量化（若有） | 待测 | 待测 | N/A | ☐ |

**与智能排版 V2 P1 对齐**：最终选型 **必须** 与 [智能排版V2.md](../智能排版V2.md) `subjectClass` 共用 encoder。

### 4.3 聚类参数矩阵

| 参数 | 默认值 | 说明 |
|------|--------|------|
| `clusterEps` | 0.07 | DBSCAN eps（cosine 或 L2，实现定稿） |
| `clusterMinSamples` | 10 | DBSCAN min_samples |
| `timeoutSec` | 480 | 400 张 CPU soft cap |

### 4.4 SP-C02 实测记录

| Trip | 簇数 | 最大簇占比 | mega-cluster? | 决议 |
|------|------|------------|---------------|------|
| golden-mixed-scenes | — | — | — | ☐ |

---

## 5. Curate 章数（SP-C03）

| 输入 events 数 | merge/cap 后章数 | 通过 |
|----------------|------------------|------|
| 3 | 3 | ☐ |
| 8 | ≤5 | ☐ |
| 1 | ≥3（date_fallback 补足） | ☐ |

---

## 6. Layout 回归（SP-C04）

| 样本 | clustering off | P3-Lite | P3-Full | time_inversion | subject_run |
|------|----------------|---------|---------|----------------|-------------|
| mao | baseline | — | — | — | — |
| maomi | baseline | — | — | — | — |
| linzhi | baseline | — | — | — | — |

---

## 7. 确定性双跑（SP-C05）

| Trip | Run 1 hash | Run 2 hash | 一致 | 备注 |
|------|------------|------------|------|------|
| golden-kyoto-gps | — | — | ☐ | `clustering.deterministic=true` |
| golden-mixed-scenes | — | — | ☐ | CPU 路径 · 固定 seed |

**hash 范围**：`curation.clustering` JSON（segments + clusters，排除 `visionModel` 下载时间戳）。

---

## 8. Go / No-Go 签字

| 项 | 结果 | 签字人 | 日期 |
|----|------|--------|------|
| SP-C01 geo events | ☐ Go ☐ No-Go | | |
| SP-C02 scene clusters | ☐ Go ☐ No-Go ☐ Defer M13 | | |
| SP-C03 章数 cap | ☐ Go ☐ No-Go | | |
| SP-C04 layout 回归 | ☐ Go ☐ No-Go | | |
| SP-C05 确定性双跑 | ☐ Go ☐ No-Go | | |
| **总体 M12-0** | ☐ **Go → 启动 M12** ☐ **No-Go** | | |

**No-Go 预案**：

- SP-C01 失败 → 调参重测；仍失败则 **仅 ship date_fallback**（推迟 geo_events）
- SP-C02 失败 → M12 只 ship P3-Lite；P3-Full 推迟
- SP-C04 失败 → 阻断 M13 layout 接入，仅保留 segments hints
- SP-C05 失败 → 排查 non-deterministic op；**阻塞 M12 merge**（见 ADR-007 R2）

---

## 9. 版本历史

| 版本 | 日期 | 说明 |
|------|------|------|
| v0.1 | 2026-05-28 | 初稿 · 替代 engines-api-matrix |
| v0.2 | 2026-05-28 | 对齐 PRD v0.3.1：SP-C05 确定性双跑 |
| v0.3 | 2026-05-28 | §3.5 可接受偏差白名单（Kickoff） |
