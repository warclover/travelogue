# P19 · 人评盲评组织指南（AC-P19-07）

> 北极星 Gate：**8 本 golden 中 P19 候选 vs P16 baseline 人评胜率 ≥ 60%（≥6/8）**；「故事更清楚」≥ 60%；Share Intent ≥ 4/5 ≥ 60%。

## 1. 样本与评审人数

| 项 | 要求 |
|----|------|
| Trip 集 | `docs/acceptance-records/p19-golden-trips.json` 中 **8 本 primary**（BSP 专项 `demo-d66fe642a9` 可选第 9 本） |
| 评审人数 | ≥ 3 人，互不讨论 |
| 对比方式 | Pairwise 盲评（左右随机 A/B，填表前不告知哪版是 P19） |

## 2. 生成对比成稿

### 自动化（推荐）

```bash
# P16 baseline（左/右随机之一）
python scripts/book_quality_baseline.py --out .cache/book-quality/baseline

# P19 候选（当前分支默认配置；subset/highlight 默认关）
python scripts/book_quality_baseline.py --p19-candidate --out .cache/book-quality/p19

# 仅签名/指标、跳过 HTML 渲染
python scripts/book_quality_baseline.py --skip-render
python scripts/book_quality_baseline.py --p19-candidate --skip-render --out .cache/book-quality/p19
```

每本 trip 的 `index.html` 位于：

- Baseline：`trips/<tripId>/index.html`（baseline 脚本会写入并渲染）
- 或缓存目录：`.cache/book-quality/baseline/<tripId>/` 下的 summary

**盲评打开方式**：对每本 trip，将 baseline 与 p19 两版 `index.html` 用不同浏览器 profile 或本地静态服务打开；URL 路径随机标为 A/B。

### VLM judge（辅助，不作 Gate 依据）

```bash
python scripts/book_quality_vlm_judge.py --mock
# 配置 API 后去掉 --mock，结果写入 .cache/book-quality/judge/
```

人评结果归档至 `docs/acceptance-records/p19-judge-calibration.json`；与 judge 一致率写入 AC-P19-01。

## 3. 评审表

复制模板：`docs/acceptance-records/p19-human-blind-review.template.json`

每位评审人每本 trip 填写：

| 字段 | 说明 |
|------|------|
| `overallWinner` | `A` / `B` / `tie`（映射回 baseline/candidate 时记录 `mapping`) |
| `storyClarity` | 哪版「故事更清楚」 |
| `shareIntent` | 1–5，更愿意分享哪版 |
| 五维度 | rhythm / whitespace / crop / monotony / book_like（与 judge 对齐） |

汇总后计算：

- `humanPairwiseWinRate` = candidate 胜 / 可裁决本数
- `tripsWon` = candidate 胜出的 trip 数（primary 8 本）
- `storyClarityPreferCandidatePct`
- `shareIntent4PlusPct`

## 4. 与自动化 Gate 的关系

| 自动化（已跑） | 人评 Gate |
|----------------|-----------|
| `p19_rhythm_audit` 违规 = 0 | 不替代盲评 |
| screens 签名 vs P16 baseline 零 diff | 减法回归；与感知质量无关 |
| subset 中位削减 30%（planner only） | 「故事更清楚」需人评 |
| curate P95 可能超标 | 性能 Gate 独立（AC-P19-08） |

一键重跑自动化：`python scripts/p19_golden_gate_run.py`

## 5. 归档检查清单

- [ ] `p19-human-blind-review.json`（从 template 复制填写）
- [ ] `p19-judge-calibration.json` 更新 summary
- [ ] `p19-final.json` AC-P19-07 字段
- [ ] `p19-sprint-gates.json` S6 `humanBlindWinRateActual`
