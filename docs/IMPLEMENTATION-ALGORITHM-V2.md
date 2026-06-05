# 算法优化 V2.0 实施清单

| 属性 | 内容 |
|------|------|
| **PRD** | [PRD-ALGORITHM-OPTIMIZATION-V2.md](./PRD-ALGORITHM-OPTIMIZATION-V2.md) v2.0.0-rc |
| **评审** | [algorithm-v2-prd-review-2026-06-05.md](./acceptance-records/algorithm-v2-prd-review-2026-06-05.md) |
| **状态** | Phase A/B/C 已落地 · **默认 v2**（开发期直切，无灰度） |

---

## 1. 已交付代码

| 模块 | 路径 | 说明 |
|------|------|------|
| Cover V2 模型 | `travelogue/curation/cover_scoring_v2.py` | logit、features、explain、hero |
| 路由集成 | `travelogue/curation/curate_scoring.py` | `scoring_version` / `pool` 透传 |
| Curate 写入 | `travelogue/curation/curate.py` | `sync_trip_covers` 读 config |
| Sharpness V2 | `travelogue/media/sharpness.py` | Laplacian + ROI；OpenCV 失败回退 PIL |
| 归一化清晰度 | `travelogue/curation/asset_quality.py` | `normalized_sharpness` |
| Ingest | `travelogue/media/ingest.py` | `sharpness_version=v2` 时写 v2 + legacy |
| Heuristic C-A | `travelogue/vision/clip_encoder.py` | percentile sharp + `heuristic-v1-quality-bucket` |
| 配置 | `travelogue/config.py` · `config.yaml.example` | `cover_scoring_version` · `sharpness_version` |

---

## 2. 脚本与测试

| 项 | 路径 |
|----|------|
| V2 单测 | `tests/test_cover_scoring_v2.py` |
| Sharpness V2 | `tests/test_sharpness_v2.py` |
| Fixture | `tests/fixtures/cover_v2_quality_priority.json` |
| Kendall τ | `scripts/cover_scoring_v2_kendall.py` |
| Sprint 2 门禁 | `tests/test_cover_scoring_v2_gates.py` |
| Kendall fixture | `tests/fixtures/cover_v2_kendall_albums.json` |
| 标定骨架 | `scripts/cover_scoring_calibrate.py` |
| C-B 门禁 | `tests/test_heuristic_v2_gates.py` |
| Sharpness 迁移 | `scripts/migrate_sharpness_v2.py` |
| V2 验收记录 | `scripts/algorithm_v2_signoff.py` |

---

## 3. 默认配置

出厂默认 `cover_scoring_version: v2`、`sharpness_version: v2`。回退 v1：

```yaml
curate:
  cover_scoring_version: v1
ingest:
  sharpness_version: v1
```

---

## 4. 待办（v2.1 / 后续）

- [x] Phase C-B：heuristic 18 维向量 + cache fingerprint / schema 失效
- [x] Phase D 骨架：Bradley-Terry proxy 标定 + feature export（`cover_scoring_calibrate.py`）
- [ ] Phase D 发布：真实盲评样本标定权重并人工 approve
- [x] `cover_candidates` 全量透传 `scoring_version`
- [x] `algorithm-v2-signoff.json` 模板 + 自动化门禁（A-M1/A-M7）；人工 A-M3 待填
- [x] `demo verify` quick 套件纳入 V2 测试 + `algorithm_profile` v2 字段
- [x] `docs/reports/algorithm-v2-kendall.md` 报告（合成 10 本；真实 trip 待素材）

---

## 5. 任务拆分（工程）

### Sprint 1（已完成）

- [x] `extract_cover_features` + `cover_score_v2`
- [x] feature flag + curate 路由
- [x] `sharpness_score_v2` + ingest 写入
- [x] heuristic 诚实降级（C-A）
- [x] 单测 + fixture CV2-01/02

### Sprint 1.5（测试修复 · 2026-06-05）

- [x] P0 sharpness_v2 纯色图 v1 floor 兜底
- [x] P1 aesthetic 权重（w_aesthetic=0.18，启用时 w_sharp cap 0.12）
- [x] P1 集成测试 F1–F5 修复
- [x] P1 CV2-01～06 fixture + 单测
- [x] P2 Kendall 脚本 tripDir 加载
- [x] pick_chapter_hero 透传 hero_pool（v2 percentile）

### Sprint 2（发布前）

- [x] A-M1 Kendall τ ≥ 0.85（合成 10 本，mean=1.0）
- [x] A-M4 explain top4 贡献 ≥ 0.65×logit
- [x] A-M7 ΔcoverId ≤ 3/10（合成 10 本，Δ=0）
- [x] B-M5 burst 选最清晰 + 缩放后顺序稳定
- [x] `test_v2_demotes_low_date_confidence_vs_v1`（CV2-04 预期反转，不计入 τ）
- [x] Kendall 脚本默认读合成 fixture + `--write-report`
- [x] `docs/reports/algorithm-v2-kendall.md`
- [x] Phase C-B C-M1/C-M2 自动化门禁
- [x] Phase D proxy LOO accuracy（合成相册，D-M1 骨架）
- [ ] R0' 盲评 10 本真实相册（需 `trips/mao` 等素材落地 + 填 `judgeVerdict`）
- [x] 默认 v2（开发期直切）
