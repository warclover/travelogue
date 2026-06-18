# 分层精选 Pilot · 配置冻结 Sign-off（v3）

> 分支：`feat/aesthetic-alignment`  
> PRD：[PRD-STRATIFIED-CURATION.md](../PRD-STRATIFIED-CURATION.md)  
> 语料：`aesthetic-human-labels.merged.v3.json`（332 张 · 4 trip）  
> **冻结日期**：2026-06-18  
> **结论**：自动化门禁 **AC-SC-01/02/04/05/06 通过**；人工 pairwise **AC-SC-03 通过（东澳 product waiver）**。Pilot 配置 **已冻结** · G1c **closed**。

---

## 1. 冻结配置

权威快照：[aesthetic-pilot-config.freeze.v3.yaml](../acceptance-records/aesthetic-pilot-config.freeze.v3.yaml)

| 项 | 冻结值 | 说明 |
|----|--------|------|
| stratum_blend_only | `[landscape, person]` | food 搁置 |
| stratum_blend_only_by_purpose.hero | `[landscape]` | hero 不用 person blend |
| person / landscape blend | 0.6 | merged v3 网格 |
| use_album_relative | true | p75 · clamp 0.7–1.3 |
| presets.cover.subjectClarity | **0.55** | 张智慧 person 网格；landscape 册见 0.45 校准档 |
| mllm.shortlist_purposes | **`[moment]`** | cover/hero **不**走 MLLM blend（pairwise 根因修复） |
| portrait_lite_enabled | true | PC-M1 §6.3 有 portrait 信号时替代 |

代码依赖（已合入分支）：

- `resolve_learned_blend(..., purpose=)` + `stratum_blend_only_by_purpose`
- `purpose_overall` / `_blend_mllm_overall`：purpose 不在 shortlist 时跳过 MLLM

---

## 2. AC-SC 验收矩阵

| ID | 判据 | 状态 | 证据 |
|----|------|------|------|
| **AC-SC-00** | min-n 分层样本 | **通过** | food 搁置 · landscape+person 达标 |
| **AC-SC-01** | 每层 blend Δ SRCC | **通过** | person Δ=+0.133 · [signoff.v3.json](../acceptance-records/aesthetic-stratified-signoff.v3.json) |
| **AC-SC-02** | 加权 Δ ≥ 0.10 | **通过** | weighted Δ=0.131 |
| **AC-SC-03** | ≥3 本 purpose pairwise ≥60% | **通过（waiver）** | 2/3 strict + **东澳 50% 产品接受** · 辅助合并 75% |
| **AC-SC-04** | albumProfile | **通过** | 三本 dogfood 已写入 |
| **AC-SC-05** | 继承 AC-AA-04~08 | **通过** | |
| **AC-SC-06** | 开关回退 | **通过** | |

### AC-SC-03 · canonical 整本 person-pilot（调权后）

| tripId | profile | canonical 轮次 | 胜率 | 状态 |
|--------|---------|----------------|------|------|
| demo-fc8b3a5c08 | landscape_heavy | person-pilot seed45 | **60.0%** | ✅ |
| demo-1a737d6205 | mixed_portrait | **person-pilot-v2** seed47 | **66.7%** | ✅ |
| demo-2025-6 | mixed_travel | person-pilot-v2 seed47 | **50.0%** | ⚠️ **waiver 接受** |

明细：[purpose-pairwise-signoff.v3.json](../acceptance-records/purpose-pairwise-signoff.v3.json)

**东澳 waiver（2026-06-18）**：整本 canonical 50% 未达 60%；产品接受继续。依据：分 purpose 合并 75%、语料 asset-071 误 ingest 已 `layoutEligible=false`、v5–v7 无突破。

**辅助（非主门禁）**

| 说明 | 胜率 |
|------|------|
| 东澳 分 purpose 合并（cover v2 + hero-recheck） | 75% |
| 东澳 hero-recheck seed46 | 83.3% |
| 张智慧 cover-recheck seed46 | 100%（5/5 可比） |

---

## 3. 调权历程摘要

| 问题 | 根因 | 修复 |
|------|------|------|
| 东澳 hero person-pilot 1/6 | MLLM 抬高 landscape 图 hero 分 | hero 移出 MLLM shortlist + hero landscape-only blend |
| 张智慧 cover 1/4 + tie | MLLM 抬高 cover aligned | cover 移出 MLLM shortlist · subjectClarity 0.55 |
| 锡兰 hero 4 tie | 初轮 topPick 未分化 | person-pilot + hero-recheck |

校准归档：

- [aesthetic-purpose-calibration.hero-dongao.v3.json](../acceptance-records/aesthetic-purpose-calibration.hero-dongao.v3.json)
- [aesthetic-purpose-calibration.cover-zhang.v3.json](../acceptance-records/aesthetic-purpose-calibration.cover-zhang.v3.json)
- [aesthetic-purpose-calibration.cover-landscape.v3.json](../acceptance-records/aesthetic-purpose-calibration.cover-landscape.v3.json)

---

## 4. 搁置与后续

| 项 | 状态 |
|----|------|
| demo-53cda5151f（food） | 搁置 |
| **东澳 AC-SC-03** | **waiver 接受** · canonical 50% · 辅助 75% |
| **G3 默认 ml_calibrate** | **待联签** · [SIGNOFF-G3-DEFAULT-ML.md](./SIGNOFF-G3-DEFAULT-ML.md)（AC-SC 已关 · 代码默认未改） |
| MediaPipe Py 3.11 | 待环境 · 提升 portrait 信号 |
| per-profile cover subjectClarity | 可选：landscape 0.45 / portrait 0.55 分册 |

---

## 5. 复现命令

```bash
# SRCC signoff
python scripts/aesthetic_stratified_signoff.py

# purpose pairwise 导出
python scripts/aesthetic_purpose_pairwise_export.py \
  --trip-id demo-2025-6 --trip-dir trips/demo-2025-6 \
  --suffix person-pilot-v2 --seed 47

# 计分
python scripts/aesthetic_purpose_pairwise_export.py \
  --score judged.json \
  --template docs/acceptance-records/purpose-pairwise.demo-XXX.json \
  --suffix person-pilot-v2
```

---

## 6. 签字

| 角色 | 日期 | 备注 |
|------|------|------|
| 工程 | 2026-06-18 | 配置冻结 · signoff 归档 |
| 产品/作者 | 2026-06-18 | 东澳 AC-SC-03 waiver · 继续后续任务 |
