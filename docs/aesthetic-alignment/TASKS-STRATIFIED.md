# 分层精选 · 任务清单（Stratified Curation）

> PRD：[PRD-STRATIFIED-CURATION.md](../PRD-STRATIFIED-CURATION.md)  
> Rubrics：[RUBRICS-v1.md](./RUBRICS-v1.md)  
> 数据契约：[DATA-CONTRACT.md](./DATA-CONTRACT.md)  
> 继承 AA 工程：[TASKS.md](./TASKS.md) · [GAP-TASKS.md](./GAP-TASKS.md)  
> 分支：`feat/aesthetic-alignment`  
> 状态键：`[ ]` 待做 · `[~]` 进行中 · `[x]` 完成

---

## 背景与起点

| 项 | 状态 |
|----|------|
| merged v3 标签 | **332** 张（109+146+60+17）· `aesthetic-human-labels.merged.v3.json` **frozen** |
| GAP-01 语料 ≥150 | [x] |
| GAP-02 pooled AC-AA-02 | [ ] 未达标；改走 **AC-SC-02** 分层门禁 |
| 分层 blend 单 trip | 东澳 +0.036、锡兰 +0.22 |
| landscape / food 样本 | landscape **207**；food **17 搁置** |

---

## P0 · 标准冻结（约 1 周）

> 出口：文档 + 验收模板就绪；**不改** `AppConfig` 默认。

| ID | 任务 | 状态 | 产出 |
|----|------|------|------|
| P0-1 | 分层精选 PRD | [x] | `docs/PRD-STRATIFIED-CURATION.md` |
| P0-2 | 分类 rubric 冻结 | [x] | `docs/aesthetic-alignment/RUBRICS-v1.md` |
| P0-3 | 本任务清单 | [x] | 本文档 |
| P0-4 | 更新 AA PRD 交叉引用 + AC 映射 | [x] | `PRD-AESTHETIC-ALIGNMENT.md` §13 |
| P0-5 | 分层 signoff JSON 模板 | [x] | `aesthetic-stratified-signoff.template.json` |
| P0-6 | 更新 GAP-TASKS / SIGNOFF-M4 指向 AC-SC-* | [x] | GAP-TASKS §0 |
| P0-7 | 盲评 HTML：展示 rubric 摘要 + **可改 stratum** | [x] | `build_blind_review_html` v3 |
| P0-8 | 标签 schema 文档：`stratumAuto` / `defectTags` 预留 | [x] | [DATA-CONTRACT.md](./DATA-CONTRACT.md) |

**P1 命令**

```bash
# 东澳 stratum 审计 + 批量修正
python scripts/aesthetic_stratum_audit.py --trip-dir trips/demo-2025-6 \
  --labels docs/acceptance-records/aesthetic-human-labels.demo-2025-6.json --apply \
  --write-audit docs/acceptance-records/aesthetic-stratum-audit.demo-2025-6.json

# 合并 + 冻结 + 分层 baseline
python scripts/aesthetic_merge_labels.py --freeze

# 跨 trip blend 网格 + AC-SC signoff
python scripts/aesthetic_stratified_signoff.py

# dogfood 三本 · landscape pilot
python scripts/aesthetic_dogfood_validation.py --persist-profiles

# AC-SC-03 purpose pairwise（cover+hero 各 6 组 / 册）
python scripts/aesthetic_purpose_pairwise_export.py

# P2-4 cover × landscape 网格 + 东澳 cover 复核
python scripts/aesthetic_purpose_calibrate_merged.py --export-dongao-cover
```

**P0 命令（已有）**

```bash
python scripts/aesthetic_merged_eval.py \
  --corpus docs/acceptance-records/aesthetic-alignment-corpus.v2.json \
  --labels docs/acceptance-records/aesthetic-human-labels.merged.v2.json \
  --write docs/acceptance-records/aesthetic-m2-merged.v2.json
```

---

## P1 · 分层标注协议（约 2–3 周）

> 出口：**全局校准库 v3** 达 AC-SC-00；定向补 landscape / food。

| ID | 任务 | 状态 | 产出 |
|----|------|------|------|
| P1-0 | **锡兰 v3 全标 146** | [x] | `aesthetic-human-labels.demo-fc8b3a5c08.v3.json` frozen · baseline `aesthetic-baseline.demo-fc8b3a5c08.v3.json` |
| P1-1 | corpus v3 配额模板 | [x] | `aesthetic-alignment-corpus.v3.json` |
| P1-1b | **张智慧精选** ingest + 分层抽样 ~60 | [x] | `aesthetic-human-labels.demo-1a737d6205.json` frozen · baseline `aesthetic-baseline.demo-1a737d6205.json` |
| P1-2 | 定向招募 **landscape 50** 张标签 | [~] | 锡兰 v3 全标含 landscape 119 层 |
| P1-3 | 定向招募 **food 30** 张标签 | [-] | **搁置** · `demo-53cda5151f` 17 frozen 待用 |
| P1-4 | 合并 v3 标签集 | [x] | `aesthetic-human-labels.merged.v3.json` frozen · 332 张 |
| P1-5 | 分层 baseline 报告（每层 SRCC） | [x] | `aesthetic-baseline-stratified.v3.json` |
| P1-6 | 单册验收集协议（20–40 张 / 按 profile） | [x] | `aesthetic-validation-protocol.v3.json` |
| P1-7 | 纯风景册 + 纯人像册各 1 本试标 | [~] | 张智慧 `demo-1a737d6205` portrait backfill 216/223 · 待 frozen 试标记录 |

**全局库 v3 目标配额**

| stratum | 目标 | 现有（v2） | 缺口 |
|---------|------|------------|------|
| group | 50 | ~127* | 已够（*merged 内） |
| person | 40 | ~25 | ~15 |
| landscape | 50 | ~35* | ~15（可从锡兰再抽） |
| food | 30 | ~0 | **30** |
| general | 20 | ~11 | ~9 |

---

## P2 · 分类校准与相册内排序（约 3–4 周）

> 出口：AC-SC-01/02 达标；跨 trip **统一** stratum blend。

| ID | 任务 | 状态 | 产出 |
|----|------|------|------|
| P2-1 | **跨 trip 统一** stratum blend 网格（v3 全局库） | [x] | `run_stratum_blend_calibration_merged()` · `aesthetic-stratum-calibration.merged.v3.json` |
| P2-2 | `albumProfile` 计算 + 写入 `trip.curation` | [x] | `album_profile.py` · curate 挂钩 |
| P2-3 | album-relative 分位乘数 `score / P75(stratum)` | [x] | `stratum_score_percentiles` · `relative_purpose_score` |
| P2-4 | purpose 权重：stratum × purpose 网格（或分层 purpose 校准） | [x] | `aesthetic-purpose-calibration.cover-landscape.v3.json` · cover 调权已写入 `config.yaml` |
| P2-5 | MLLM 短名单：profile-aware 候选池 | [x] | `build_mllm_shortlist` · `profile_priority_strata` |
| P2-6 | 分层 signoff 脚本（输出 AC-SC 表） | [x] | `scripts/aesthetic_stratified_signoff.py` · `aesthetic-stratified-signoff.v3.json` |
| P2-7 | config `aesthetic.stratified.*` 接入 | [x] | `aesthetic_stratified.py` · `stratum_blend_only` · example yaml |
| P2-8 | dogfood ≥3 本不同 profile（风景/人像/混合） | [x] | `aesthetic-dogfood-validation.v3.json` · AC-SC-03 自动化 proxy 未过 |

**P2 依赖**：P1 v3 标签；landscape/food 样本 ≥20 才可拟合该层 blend。

---

## P3 · 合影 / 人像质量闭环（与 Portrait PRD）

| ID | 任务 | 状态 | 产出 |
|----|------|------|------|
| P3-1 | Portrait M1（睁眼 / 脸锐度） | [~] | `portrait_analyze.py` · `portrait_backends.py` · §6.3 subjectClarity · backfill 脚本 |
| P3-2 | 标签 `defectTags`：closed_eyes / blur_face | [x] | 盲评 HTML · `build_blind_review_html` |
| P3-3 | group/person 重点位硬降权 | [x] | `portrait_cover_defect_penalty` · cover + hero logit |
| P3-4 | AC-PC 缺陷率 vs 基线 | [x] | `portrait_defect_metrics.py` · `aesthetic_portrait_defect_signoff.py` |

---

## P4 · 产品化（持续）

| ID | 任务 | 状态 | 产出 |
|----|------|------|------|
| P4-1 | Studio 展示 stratum / purpose 分 / critique | [x] | GAP-16 · `studio_aesthetic.py` + preview-toolbar |
| P4-2 | 展示 albumProfile + 选图说明 | [x] | `albumProfile` in `/aesthetic` + entry summary |
| P4-3 | 用户微调「更偏风景 / 更偏人像」| [x] | `stratumPreference` · preset overlay · Studio chips |
| P4-4 | G3 默认开关（`ml_calibrate=true`）| [~] | [SIGNOFF-G3-DEFAULT-ML.md](./SIGNOFF-G3-DEFAULT-ML.md) · 待联签 · 代码未改 |

---

## 验收对照（AC-SC-*）

| AC | 任务依赖 | 状态 |
|----|----------|------|
| AC-SC-00 | P1-4 | [x] food 搁置跳过 · landscape+person 达 min-n |
| AC-SC-01 | P2-1, P1-5 | [x] person Δ=+0.133 · normalize_human_score 修复后重跑 |
| AC-SC-02 | P2-1, P2-6 | [x] weighted Δ=0.131 |
| AC-SC-03 | P2-8, P0-7 pairwise | [x] | **2/3 strict + 东澳 waiver** · G1c closed · 2026-06-18 |
| AC-SC-04 | P2-2 | [x] | albumProfile 已写入三本 dogfood |
| AC-SC-05 | 已实现 AA M4 | [x] |
| AC-SC-06 | 已实现 AA 开关回退 | [x] |

---

## 建议实施顺序

```text
P0 文档+盲评UI ──► P1 补 landscape/food 语料
        │                    │
        └──────► P2 统一 blend + albumProfile + 分层 signoff
                              │
        P3 Portrait ──────────┴──► P4 Studio + G3
```

**可并行**：P0-7 盲评 UI · P2-2 albumProfile（不依赖新语料）· P3 与 P1 后半并行。

---

## Pilot 配置冻结（2026-06-18）

- Signoff：[SIGNOFF-PILOT-FREEZE.v3.md](./SIGNOFF-PILOT-FREEZE.v3.md)
- 配置快照：[aesthetic-pilot-config.freeze.v3.yaml](../acceptance-records/aesthetic-pilot-config.freeze.v3.yaml)
- Pairwise：[purpose-pairwise-signoff.v3.json](../acceptance-records/purpose-pairwise-signoff.v3.json)
- **G3 默认 ml_calibrate**：AC-SC-03 已关（含东澳 waiver）；G3 改默认仍须 PRD 单列 signoff

---

## 修订记录

| 日期 | 说明 |
|------|------|
| 2026-06-18 | 初版：P0–P4 任务；与 merged v2 现状对齐 |
| 2026-06-18 | Pilot 配置冻结 · AC-SC-03 2/3 · 东澳阻塞 |
| 2026-06-18 | 东澳 AC-SC-03 product waiver · G1c passed · AC-SC 全矩阵关闭 |
| 2026-06-18 | P4-1/P4-2 Studio 分层审美展示 · GAP-16 closed |
| 2026-06-18 | P2-5 profile-aware MLLM 短名单 · P4-3 stratumPreference preset |
| 2026-06-18 | P0-8 DATA-CONTRACT · stratumAuto / defectTags schema |
| 2026-06-18 | P3-2 盲评 HTML defectTags 勾选导出 |
| 2026-06-18 | P3-3 cover/hero portrait defect penalty（闭眼+糊脸） |
| 2026-06-18 | P3-4 portrait defect dogfood signoff 脚本 |
| 2026-06-18 | G3 signoff 草案 SIGNOFF-G3-DEFAULT-ML.md |
