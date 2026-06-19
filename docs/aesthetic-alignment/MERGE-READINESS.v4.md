# Merge Readiness · feat/aesthetic-alignment → master

> 准备日期：2026-06-19 · 目标：v4 分层精选 pilot + G3 默认 `ml_calibrate=true`

## 分支概览

| 项 | 值 |
|----|-----|
| 源分支 | `feat/aesthetic-alignment` |
| 目标 | `master` |
| 相对 master 提交 | 5（含 studio cover fix + AA pilot + v4 signoff + DS-3 + sc00 labels） |
| 最新 HEAD | `d56c079` + 本准备 commit |

## 门禁矩阵（AC-SC-*）

| AC | 状态 | 依据 |
|----|------|------|
| AC-SC-00 | ⚠️ **waiver** | general 10/20 · group 29/30 · [ac-sc-00-waiver.v4.json](../acceptance-records/ac-sc-00-waiver.v4.json) |
| AC-SC-01 | ✅ | 各层 blend SRCC > rules |
| AC-SC-02 | ✅ | weighted Δ **0.142** ≥ 0.10 |
| AC-SC-03 | ✅ **waiver** | 3/5 strict · 58.9% · [purpose-pairwise-waiver.v4.json](../acceptance-records/purpose-pairwise-waiver.v4.json) |
| AC-SC-04 | ✅ | 三本 dogfood albumProfile · [aesthetic-dogfood-validation.v4.json](../acceptance-records/aesthetic-dogfood-validation.v4.json) |
| AC-SC-05/06 | ✅ | 继承 AA M4 + 开关回退 |

## 代码变更摘要

- **G3 默认**：`AppConfig.aesthetic.ml_calibrate=true` · v4 pilot blends · album-relative · cover/hero presets
- **DS-3**：4 类 `profileTemplates` + `tripKindMap` · `purposeProfileKind` 解析
- **Portrait**：`portrait_analyze` + subjectClarity 注入 · defect 惩罚 · Studio 展示
- **Studio**：stratumPreference · albumProfile · aesthetic 抽屉
- **脚本/验收**：stratified signoff · purpose pairwise · blind review · dogfood recurate

## 本地验证（2026-06-19）

```bash
# Lint（CI 同款）
python -m ruff check travelogue tests scripts

# AA 单元测试
python -m pytest tests/test_aesthetic_*.py tests/test_album_profile.py tests/test_portrait_analyze.py -q

# 分层 signoff（需 pyiqa）
python scripts/aesthetic_stratified_signoff.py \
  --corpus docs/acceptance-records/aesthetic-alignment-corpus.merged.v4.json \
  --labels docs/acceptance-records/aesthetic-human-labels.merged.v4.json \
  --write docs/acceptance-records/aesthetic-stratified-signoff.v4.json \
  --write-calibration docs/acceptance-records/aesthetic-stratum-calibration.merged.v4.json \
  --defer-strata none

# Dogfood G3 recurate（需本机 trips/）
python scripts/aesthetic_dogfood_recurate_g3.py
```

| 检查 | 结果 |
|------|------|
| ruff | ✅ All checks passed |
| test_aesthetic_* (42) | ✅ |
| PR-fast pytest（本地 3.14） | 658 pass · 3 fail（`test_food_grid` · `test_layout_density` ×2 — **与 AA 无关**，待 CI 3.11 确认） |
| dogfood recurate v4 | ✅ [aesthetic-g3-dogfood-recurate.v4.json](../acceptance-records/aesthetic-g3-dogfood-recurate.v4.json) |
| dogfood validation v4 | ✅ AC-SC-04 |

## Merge 前人工清单

- [ ] **Studio 抽检** 三本 dogfood cover/hero（东澳 / 锡兰 / 张智慧）视觉可接受
- [ ] 确认生产 `config.yaml` **不提交**；默认已走 AppConfig，MLLM 仍 `enabled: false`
- [ ] Reviewer 知晓 **双 waiver**：AC-SC-00 + AC-SC-03
- [ ] 川藏/仙本那 purpose ~42% 列入 post-merge 监控

## 回滚

见 [SIGNOFF-G3-DEFAULT-ML.md](./SIGNOFF-G3-DEFAULT-ML.md) §6：

```yaml
aesthetic:
  ml_calibrate: false
  mllm:
    enabled: false
```

recurate 目标 trip → `quality.aesthetic.source` 回到 `rules`。

## PR 要点（复制用）

**Title:** `feat(aesthetic): stratified curation pilot v4 with G3 ml_calibrate default`

**Summary:**
- Land v4 stratified curation pilot: stratum blend, purpose profiles (DS-3 templates), portrait subjectClarity
- Change AppConfig default to G3 pilot (`ml_calibrate=true`); MLLM remains opt-in
- Acceptance: AC-SC-01/02/04/05/06 pass; AC-SC-03 + AC-SC-00 under documented waivers

**Test plan:**
- [ ] CI green (lint + test-pr + test-integration)
- [ ] Spot-check Studio dogfood albums cover/hero
- [ ] `pytest tests/test_aesthetic_*.py -q`

## Post-merge

1. GAP-15：PRD Draft → Approved
2. landscape/underwater purpose 模板 tune
3. GAP-06 Portrait M1（MediaPipe）
4. AC-SC-00 扩 trip 补标或 PRD min-n 修订

## 关联 signoff

- [SIGNOFF-PILOT-FREEZE.v4.md](./SIGNOFF-PILOT-FREEZE.v4.md)
- [aesthetic-g3-signoff.v4.json](../acceptance-records/aesthetic-g3-signoff.v4.json)
- [aesthetic-alignment-rollout-log.json](../acceptance-records/aesthetic-alignment-rollout-log.json)
