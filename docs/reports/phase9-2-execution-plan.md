# Phase 9.2 执行计划（算法增强）

| 属性 | 内容 |
|------|------|
| 目标阶段 | Phase 9.2 |
| 范围 | P9 Quality Gate 算法增强（不改 UI 交互范式） |
| 计划周期 | 2 周（可按人力拉伸） |
| 关联文档 | `docs/PRD-PHASE9.md`、`docs/PRD-PHASE9-A-quality-gate-algorithm.md`、`docs/PRD-PHASE9-B-pipeline-integration.md`、`docs/PRD-PHASE9-C-data-model.md` |
| 输出物 | 评测基线、参数化能力、鲁棒性增强、可解释性增强 |

---

## 1. 背景与目标

在 Phase 9 已完成 W1/W3 落地后，P9 算法具备上线可用性，但仍存在三个提升空间：

1. **调优成本高**：Pass3 权重硬编码，调参需改代码。
2. **场景鲁棒性不足**：material-only 组在重算场景缺少兜底策略。
3. **评估闭环不完善**：缺少统一离线基线与 low-res 后最终口径对齐报告。

本计划聚焦建立“可测、可调、可回滚”的算法工程能力。

---

## 2. 里程碑总览

### Week 1（必须完成）

- M1：离线评测基线固化
- M2：Pass3 权重配置化
- M3：material-only 组可选严格模式

### Week 2（建议完成）

- M4：分桶阈值（media/subject 维度）
- M5：重复度惩罚因子
- M6：可解释性字段增强

### Backlog（后续）

- M7：ML 评分持久化缓存

---

## 3. 工作分解（WBS）

## M1 · 离线评测基线固化（P0）

**目标**
- 固定数据、固定指标、固定输出结构，建立每次算法改动后的可比基线。

**建议负责人**
- 算法工程（主）
- 测试工程（配合）

**代码与文件**
- 新增 `scripts/phase9_eval_baseline.py`
- 新增 `tests/test_phase9_eval_baseline.py`
- 输出 `docs/acceptance-records/phase9-eval-baseline.json`

**验收标准**
- 脚本可在无 ML 环境下运行并产出完整 JSON。
- JSON 至少包含：
  - `cull_keep_ratio_non_featured`
  - `final_keep_ratio_non_featured`
  - `excluded_by_reason`
  - `fail_open_rate`
  - `ingest_elapsed_ms`
- 同一输入重复运行两次，关键指标误差在可接受阈值内（按 deterministic 约束）。

**风险与回滚**
- 风险：fixture 波动导致基线漂移。
- 回滚：锁定 fixture 版本号，先冻结再接入 CI。

---

## M2 · Pass3 权重配置化（P0）

**目标**
- 将 Pass3 权重从硬编码迁移为配置驱动，支持灰度调参和快速回滚。

**建议负责人**
- 算法工程（主）
- 平台/配置维护（配合）

**代码与文件**
- 更新 `travelogue/config.py`（新增 cull 权重配置项）
- 更新 `config.yaml.example`（补默认值与注释）
- 更新 `travelogue/curation/photo_cull.py`（`_cull_score()` 读配置）
- 更新 `tests/test_photo_cull.py`（配置生效测试）

**验收标准**
- 默认配置下，与当前基线结果保持高一致（误差 < 1%）。
- 调整单一权重可观察到分数排序变化。
- 不破坏 `keep_ratio_floor` 和 `min_keep` 约束。

**风险与回滚**
- 风险：错误配置导致保留率异常。
- 回滚：保留默认权重快照，支持一键恢复。

---

## M3 · material-only 组可选严格模式（P0）

**目标**
- 为“重算/历史资产回放”场景提供组内择优兜底能力。

**建议负责人**
- 算法工程（主）
- 测试工程（配合）

**代码与文件**
- 更新 `travelogue/config.py`：`recalc_strict_groups`（默认 false）
- 更新 `travelogue/curation/photo_cull.py`：Pass2 material-only 分支可控启用
- 更新 `tests/test_photo_cull.py`：默认行为 + 开启行为双测

**验收标准**
- 默认关闭时行为与当前一致。
- 开启后 material-only 组收敛为单代表。
- `excludedByReason.duplicate_group` 计数符合预期。

**风险与回滚**
- 风险：在普通流程误开导致“过筛”。
- 回滚：开关默认 false，CI 加入配置校验。

---

## M4 · 分桶阈值（P1）

**目标**
- 减少单一 blur 阈值对特定场景（夜景/人像/室内）误伤。

**建议负责人**
- 算法工程

**代码与文件**
- 更新 `travelogue/curation/photo_cull.py`（按 mediaClass 或 subject bucket 分桶计算阈值）
- 更新 `tests/test_photo_cull.py`（混合场景回归）

**验收标准**
- 代表性夜景/人像 fixture 误杀率下降。
- 全体保留率不低于当前基线。

---

## M5 · 重复度惩罚因子（P1）

**目标**
- 在 Pass3 评分中引入轻量同质化惩罚，提高入池多样性。

**建议负责人**
- 算法工程

**代码与文件**
- 更新 `travelogue/curation/photo_cull.py`（score 增加重复度项）
- 更新 `config.yaml.example`（惩罚系数）
- 更新测试（组内排序变化验证）

**验收标准**
- 同组高相似素材保留更集中。
- 不影响 floor 达标逻辑。

---

## M6 · 可解释性增强（P1）

**目标**
- 让每个剔除决策可追踪、可复盘。

**建议负责人**
- 算法工程（主）
- 产品/QA（校验可读性）

**代码与文件**
- 更新 `travelogue/curation/photo_cull.py`
- 新增或扩展字段：`quality.cullExplain`（字符串或对象）
- 更新 `schemas/trip.schema.json`
- 更新 `docs/PRD-PHASE9-C-data-model.md`

**验收标准**
- 被剔除资产可查看主要决策依据（阈值/分值/分组信息）。
- 输出结构向后兼容。

---

## M7 · ML 评分持久化缓存（Backlog）

**目标**
- 降低重复导入/重算中的 ML 推理成本。

**建议负责人**
- 算法工程

**代码与文件**
- 新增 cache 文件（建议在 trip 目录）
- 更新 `travelogue/curation/photo_cull_ml.py`
- 新增缓存命中/失效测试

**验收标准**
- 二次运行命中率显著提升。
- 推理耗时明显下降。

---

## 4. 验收矩阵（P9.2）

| ID | 验收点 | 通过标准 |
|----|--------|----------|
| AC-P9.2-01 | 基线脚本稳定输出 | 固定 fixture 可重复产出 |
| AC-P9.2-02 | 权重配置化 | 默认等价、调参可见 |
| AC-P9.2-03 | strict group 开关 | 默认不变、开启生效 |
| AC-P9.2-04 | 分桶阈值收益 | 关键场景误杀下降 |
| AC-P9.2-05 | 重复度惩罚 | 同质化下降且 floor 不破 |
| AC-P9.2-06 | explain 字段 | 剔除原因可追溯 |

---

## 5. 发布与回滚策略

- **发布策略**
  - 先合入 M1~M3（能力建设），再灰度启用 M4~M6。
  - 所有新策略默认保守（开关关闭或默认弱权重）。

- **回滚策略**
  - 通过配置恢复默认权重/关闭增强项，无需回滚代码。
  - 保留 `phase9-eval-baseline.json` 作为回滚后对照基线。

---

## 6. 协作分工建议

- **算法工程**：M1~M6 实现与参数校准
- **后端工程**：配置/Schema/流水线兼容
- **测试工程**：回归矩阵、基线稳定性、性能对比
- **产品/数据**：评测口径确认与异常样本标注

---

## 7. 交付清单（Done 定义）

满足以下条件视为 P9.2 完成：

1. M1~M3 全绿（必须项）
2. 至少完成 M4 或 M6 其中之一（增强项）
3. `phase9-eval-baseline.json` 入库并可复现
4. 关键测试通过且无新增 P1 回归

