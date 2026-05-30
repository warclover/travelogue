# Travelogue · Phase 6 验收标准

> **单轨入口建议**：[ACCEPTANCE.md](./ACCEPTANCE.md)

| 属性 | 内容 |
|------|------|
| **关联 PRD** | [PRD-PHASE6.md](./PRD-PHASE6.md) v0.6.2 |
| **关联子 PRD** | [PRD-PHASE6-ART-OPTIMIZATION.md](./PRD-PHASE6-ART-OPTIMIZATION.md) v0.1.0 |
| **关联实施** | [IMPLEMENTATION-PHASE6.md](./IMPLEMENTATION-PHASE6.md) |
| **代号** | P6-Stability · 智排稳态 |
| **更新日期** | 2026-05-30 |

---

## 1. 验收环境

- Windows 10/11 · Chrome/Edge 90+  
- `pip install -e ".[dev]"`  
- 启动：`python -m travelogue studio` 或 `start-studio.bat`  
- Benchmark 数据集：`benchmark-p6-v{n}`（必须登记版本）

---

## 2. 验收分层与门禁

| 层级 | 含义 | 必达 |
|------|------|------|
| **L0** | 核心算法与稳定性 | AC-P6-01/02/03/06/07 |
| **L1** | 用户感知质量 | AC-P6-04/05 |
| **L2** | 合规与治理 | AC-P6-08 |
| **L3** | 艺术卷轴专项 | ART-AC-01~05（至少通过 4 项） |

> 发布前必须 L0+L1+L2 全部通过。

---

## 3. 核心验收项（AC-P6）

| ID | 验收项 | 验收方法 | 通过条件 | 状态 |
|----|--------|----------|----------|------|
| **AC-P6-01** | HDBSCAN 默认路径稳定 | 20 套 benchmark 跑批 | 全量可运行，无阻断错误 | ☐ |
| **AC-P6-02** | 聚类噪声率改进 | 对比 P5 基线 | `cluster_noise_ratio` 下降 ≥15% | ☐ |
| **AC-P6-03** | 事件边界质量改进 | 标注集计算 F1 | `event_boundary_f1` 提升 ≥10% | ☐ |
| **AC-P6-04** | 封面偏好提升 | 盲评 A/B（P6 vs P5） | 偏好率 ≥60% | ☐ |
| **AC-P6-05** | 布局重复度下降 | 自动统计 + 抽检 | `layout_repeat_streak` 下降 ≥25% | ☐ |
| **AC-P6-06** | 性能不退化 | 1k 图压力测试 | 耗时退化 <10%，内存退化 <15% | ☐ |
| **AC-P6-07** | 可回滚验证 | 演练 Runbook | 30 分钟内可回退到 P5 行为 | ☐ |
| **AC-P6-08** | 合规门禁 | License BOM 审核 | BOM 完整且 L2 组件未进默认链路 | ☐ |

---

## 4. 业务验收项（BR-P6）

| ID | 指标 | 验收窗口 | 通过条件 | 状态 |
|----|------|----------|----------|------|
| **BR-P6-01** | 导出成功率 | 连续 7 天 | ≥98% | ☐ |
| **BR-P6-02** | 二次使用率 | 连续 14 天 | 相比 P5 +10% | ☐ |
| **BR-P6-03** | 7 日复访率 | 连续 14 天 | 相比 P5 +8% | ☐ |
| **BR-P6-04** | 分享转化率 | 连续 14 天 | 相比 P5 +12% | ☐ |

> 放量标准：BR-P6 至少 2 项改善，且关键指标无退化。

---

## 5. 验收用例

### TC-P6-01 场景聚类稳定性

| 项 | 规格 |
|----|------|
| 输入 | benchmark 20 套（覆盖城市/自然/人像/弱GPS/夜景） |
| 步骤 | 使用 `hdbscan` 默认配置执行全流程 |
| 期望 | 全部成功产出，不出现阻断异常 |

### TC-P6-02 事件分段准确性

| 项 | 规格 |
|----|------|
| 输入 | 人工标注边界样本集 |
| 步骤 | 运行 `gap_mode=auto` 与 P5 对比 |
| 期望 | `event_boundary_f1` 提升 ≥10% |

### TC-P6-03 封面盲评

| 项 | 规格 |
|----|------|
| 输入 | 同一批相册，P5 与 P6 导出版本 |
| 步骤 | 至少 5 人盲评 Top-1 偏好 |
| 期望 | P6 胜率 ≥60% |

### TC-P6-04 回滚演练

| 项 | 规格 |
|----|------|
| 输入 | 当前 P6 配置 |
| 步骤 | 按 PRD §14.3 执行回滚 4 步 |
| 期望 | 30 分钟内恢复 P5 行为且可导出 |

---

## 6. 艺术卷轴专项验收（ART-AC）

| ID | 对应子 PRD | 验收项 | 通过条件 | 状态 |
|----|------------|--------|----------|------|
| **ART-AC-01** | ART-A1/A2 | 章节“故事段落感” | `event_boundary_f1` 达标且叙事盲评 ≥4.0/5 | ☐ |
| **ART-AC-02** | ART-B1/B2/B3 | 阅读节奏感 | `gravity_rhythm_score` 提升 ≥15% | ☐ |
| **ART-AC-03** | ART-C1/C2/C3 | 首屏/章首杂志感 | 封面盲评胜率 ≥60% | ☐ |
| **ART-AC-04** | ART-D1/D2 | 去同质化 | `layout_repeat_streak` 下降 ≥25% 且多样性提升 | ☐ |
| **ART-AC-05** | ART-E1/E2 | 呼吸屏自然度 | “突兀感”负反馈 <10% | ☐ |

> 艺术专项放量条件：`ART-AC` 至少通过 4/5，且不得破坏 `AC-P6`。

---

## 7. 自动化与脚本建议

```powershell
python scripts/phase6_metrics_baseline.py
python scripts/phase6_event_boundary_eval.py
python scripts/phase6_cover_blind_review.py
python scripts/phase6_layout_rhythm_eval.py
python scripts/phase6_art_rubric_eval.py
python -m pytest tests/test_phase6_heuristic_vector.py -q
```

---

## 8. 灰度验收（G0-G3）

| 阶段 | 验收项 | 通过条件 |
|------|--------|----------|
| **G0** | 离线评测 | AC-P6-01~06 通过 |
| **G1** | 10% 灰度 | BR 指标无退化 |
| **G2** | 50% 灰度 | 至少 2 项 BR 指标改善 + ART-AC 达成 3/5 |
| **G3** | 全量 | 连续 7 天稳定且无 P0 事故 |

---

## 9. 失败判定与处置

| 失败条件 | 处置动作 |
|----------|----------|
| 导出成功率 <97%（24h） | 立即冻结灰度并评估回滚 |
| 性能退化 >15%（连续两天） | 停止放量，启动性能专项 |
| 封面盲评低于 P5 | 关闭新评分项，回退权重 |
| 艺术专项突兀反馈 >10% | 回退呼吸屏策略到固定间隔 |
| License BOM 不完整 | 阻塞发布 |

---

## 10. 验收记录文件

| 文件 | 用途 |
|------|------|
| `docs/acceptance-records/phase6-quality-eval.json` | 质量/性能结果 |
| `docs/acceptance-records/phase6-rollout-log.json` | 灰度与回滚日志 |
| `docs/reports/phase6-ab-eval.md` | 盲评与A/B报告 |
| `docs/reports/phase6-license-bom.md` | 合规审核记录 |
| `docs/reports/phase6-art-rubric.md` | 艺术专项主观评分记录 |

---

## 11. 签字页（发布前）

| 角色 | 负责人 | 结论 | 日期 |
|------|--------|------|------|
| 产品负责人 |  | 通过 / 拒绝 |  |
| 算法负责人 |  | 通过 / 拒绝 |  |
| 工程负责人 |  | 通过 / 拒绝 |  |
| QA 负责人 |  | 通过 / 拒绝 |  |
| 产品总监 |  | 最终放量 / 回退 |  |

---

## 12. 变更记录

| 日期 | 说明 |
|------|------|
| 2026-05-30 | 初稿：对齐 PRD v0.6.1，建立 AC/BR/Gate/Runbook 验收口径 |
| 2026-05-30 | 增补：对齐艺术子 PRD，新增 ART-AC-01~05 与放量条件 |

