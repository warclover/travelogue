# ACCEPTANCE · 完工表面积收敛 CSC V1

| 属性 | 内容 |
|------|------|
| **DOC-STATUS** | **active** |
| **PRD** | [PRD-COMPLETION-SURFACE-CONVERGENCE-V1.md](./PRD-COMPLETION-SURFACE-CONVERGENCE-V1.md) §10 |
| **实施** | [IMPLEMENTATION-COMPLETION-SURFACE-CONVERGENCE-V1.md](./IMPLEMENTATION-COMPLETION-SURFACE-CONVERGENCE-V1.md) |
| **日期** | 2026-07-22 |
| **分支** | `feat/csc-w0-recipe` |

---

## 0. 钉定基线数字

| 指标 | W0 钉定 | 目标 |
|------|---------|------|
| L1 结果旋钮 | **3** | ≤10 |
| 债务表条目 | **24** | 只降不升 |
| facade 深 import | **0** | 0 容忍 |
| 默认 True / False | **97 / 53** | 快照锁定；禁一键翻转 |
| 首趟 L1 设置点击 | **≤2** | AC-CSC-13 |
| intentional 版式 DIFF | **空表** | [csc-w0-diff-empty.md](./acceptance-records/csc-w0-diff-empty.md) |

---

## 1. 工程 AC

| ID | 验收项 | 状态 | 证据 |
|----|--------|------|------|
| **AC-CSC-01** | `studio_default` 启用集合快照单测 | **Pass** | `tests/unit/orchestrator/test_happy_path_recipe.py` · `lint_csc_recipe_baseline.py` |
| **AC-CSC-02** | facade 外新增深 import → CI 失败 | **Pass** | `lint_layout_engine_facade.py`（挂 CI） |
| **AC-CSC-03** | 基线入库；债务 ceiling 可跑 | **Pass** | W0 JSON + `lint_csc_debt_table.py` |
| **AC-CSC-04** | L1 ≤10（排除 L0） | **Pass** | `L1_RESULT_KEYS` 长度 3 |
| **AC-CSC-05** | curate：AAD 证明 **或** ≥3 薄边界 + 禁堆料 | **Pass（棘轮+薄边界）** | 见 §1.1；大拆仍归 AAD |
| **AC-CSC-06** | 主路径 e2e 不依赖 admin | **Pass（静态）** | 首页无 admin 链；实机 HAR 见 dogfood 勾选 |
| **AC-CSC-07** | README 现行区含 CSC | **Pass** | `docs/README.md` + [DOC-STATUS](./DOC-STATUS.md) |
| **AC-CSC-08** | W2 结构改动附 DIFF | **Pass** | DIFF 空表 |
| **AC-CSC-12** | `studio_pipeline` 禁堆料棘轮 | **Pass** | `lint_csc_god_module_ratchet.py` |

### 1.1 AC-CSC-05 · curate 薄边界（≥3）

| # | 可识别子步骤 | 入口符号 |
|---|--------------|----------|
| 1 | preflight / cull cohort | `_curate_preflight` · `stage_refresh_cull_cohort` |
| 2 | aesthetic align | `_stage_aesthetic_align` |
| 3 | resolve buckets | `_stage_resolve_buckets` |
| 4 | chapters compose | `_stage_build_chapters_compose` |
| 5 | finalize | `_stage_finalize` |

CSC 独有闸：`curate.py` / `studio_pipeline.py` 行数 ceiling（只降不升 / 有意增长须 `--allow-growth`）。

---

## 2. 产品 / 测评 AC

| ID | 验收项 | 状态 | 证据 |
|----|--------|------|------|
| **AC-CSC-09** | 短文 ≤3 分钟复述无黑话 | **Pass** | [三题记录](./acceptance-records/csc-w1-dogfood-three-questions-2026-07-22.md) · 帮助 H0 |
| **AC-CSC-10** | Advanced 不影响首趟主 CTA | **Pass** | 实验区二次折叠；F-CSC |
| **AC-CSC-11** | ≥5 篇文档状态标注 | **Pass** | [DOC-STATUS.md](./DOC-STATUS.md)（≥6） |
| **AC-CSC-13** | L1 点击 ≤2 | **Pass**（合入前轻测 = 0） | [pre-merge smoke](./acceptance-records/csc-pre-merge-smoke-2026-07-22.md) |
| **AC-CSC-14** | 首趟 0 次 admin | **Pass**（DOM + performance 资源） | 同上 |

---

## 3. 明确不验

算法分上升；文档总行数绝对值；全文 `legacy` 字符串降幅。

---

## 4. CI 命令（PR）

```powershell
python scripts/lint_layout_engine_facade.py
python scripts/lint_csc_god_module_ratchet.py
python scripts/lint_csc_debt_table.py
python scripts/lint_csc_recipe_baseline.py
python -m pytest tests/unit/orchestrator/test_happy_path_recipe.py -q
```

---

## 5. 结案条件（CSC V1 Closed）

1. 本文件工程 AC 全绿（已）。  
2. 产品 AC：Q1–Q3 桌面/静态已过；实机狗粮勾选建议补签后宣布 Closed。  
3. Parking（不挡 V1 Closed 工程面）：shim 删除批 · AAD curate 大拆 · pipeline 机会主义抽取。
