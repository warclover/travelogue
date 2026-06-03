# Phase 12.1 发布闸门检查单（冻结版）

| 属性 | 内容 |
|------|------|
| 适用阶段 | P12.1（稳定收敛，不扩功能） |
| 负责人 | 项目负责人 / 发布值班 |
| 更新日期 | 2026-06-03 |
| 关联 | `docs/PRD-PHASE12.md` · `docs/IMPLEMENTATION-PHASE12.md` · `docs/ACCEPTANCE-PHASE9.md` §5.1 |

---

## 1) 建议阈值表（可直接落配置）

> 原则：默认保守、优先稳定、保持 P9 floor 语义。

| 配置键 | 建议值 | 说明 |
|-------|--------|------|
| `cull.portrait_quality_enabled` | `true` | 开启分支化评分总线 |
| `cull.face_ratio_portrait_min` | `0.15` | 人像分支阈值 |
| `cull.face_ratio_gray_low` | `0.10` | 灰区下界 |
| `cull.face_ratio_gray_high` | `0.20` | 灰区上界 |
| `cull.score_branch_weight_portrait` | `0.15` | 人像分支融合权重 |
| `cull.score_branch_weight_landscape` | `0.15` | 风光分支融合权重 |
| `cull.score.threshold` | `0.00` | 默认关闭额外阈值裁剪 |
| `cull.score.topk_ratio` | `1.00` | 默认关闭额外 Top-K 裁剪 |
| `layout.scoring.weights.category_coherence` | `0.00` | 先 shadow 观测，后灰度开启 |

---

## 2) 冻结窗口（Day 1-3）

- [ ] 仅保留 2-3 组候选参数，不再新增参数维度。
- [ ] 生成候选配置文件（建议：`config.phase12.1.candidate-*.yaml`）。
- [ ] 确认回退开关可用（`cull.mode=rules` 可一键降级）。

通过标准：

- [ ] 误杀率不高于 P9 基线。
- [ ] 至少一个场景（人像/风光）Top-K 命中率提升，另一项不明显退化。

---

## 3) 回归窗口（Day 4-7）

建议命令：

```bash
pytest tests/test_photo_cull.py tests/test_layout_scoring.py tests/test_subject_tagging_bridge.py -q
pytest tests/test_ingest_enrichment.py tests/test_food_grid.py tests/test_layout_search.py -q
python -m travelogue demo verify
```

通过标准：

- [ ] 回归全绿。
- [ ] `l3_fail_open_rate.max == 0`（正常批次）。
- [ ] `l2_branch_fallback_rate.avg` 在目标阈值内（建议 `<= 0.35`）。
- [ ] `cpuMs` 无异常抬升（相对当前基线可解释）。

---

## 4) 验收记录产物（Day 8-11）

执行：

```bash
python scripts/phase9_golden_cull_signoff.py --all --write docs/acceptance-records/phase9-golden-cull-signoff.json
python scripts/phase9_eval_baseline.py --golden docs/acceptance-records/phase9-golden-cull-signoff.json --quality docs/acceptance-records/phase9-quality-gate.json --write docs/acceptance-records/phase9-eval-baseline.json
```

核对字段：

- [ ] `phase9-golden-cull-signoff.json` 含 `mlFallbackRateL1` / `branchFallbackRateL2` / `branchFallbackByReasonL2` / `failOpenRateL3` / `cpuMs`。
- [ ] `phase9-eval-baseline.json` 含 `l1_ml_fallback_rate` / `l2_branch_fallback_rate` / `l2_branch_fallback_by_reason` / `l3_fail_open_rate`。

---

## 5) 发布日 Gate（Day 12-14）

- [ ] PRD、实施、验收入口字段口径一致（命名完全一致）。
- [ ] 保留降级预案：`cull.mode=rules`。
- [ ] 发布前 24h 无新增功能改动（仅文档/阈值微调）。
- [ ] 发布后首批观察窗口完成并记录结论。

发布结论：

- [ ] Go（允许发布）
- [ ] No-Go（继续观察）

备注：

- 观察摘要：
- 需要回滚项：

