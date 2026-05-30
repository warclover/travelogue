# Phase 6 · Benchmark 数据集台账

| 属性 | 内容 |
|------|------|
| **阶段** | P6-Stability |
| **关联 PRD** | [PRD-PHASE6.md](../PRD-PHASE6.md) §15 |
| **更新日期** | 2026-05-30 |

---

## 1. 数据集版本

| 字段 | 值 |
|------|----|
| 当前版本 | `benchmark-p6-v0.2-ci-fixtures` |
| 上一版本 | — |
| 负责人 | Phase 6 工程 |
| 冻结日期 | 2026-05-30 |

---

## 2. 覆盖矩阵（CI 首轮）

| 维度 | 最小要求 | 当前数量 | 是否达标 |
|------|----------|----------|----------|
| 城市/建筑 | 5 套 | 1（golden-kyoto-gps） | ☐ |
| 自然/风景 | 5 套 | 0 | ☐ |
| 人像/合影 | 5 套 | 0 | ☐ |
| 弱 GPS/无 GPS | 5 套 | 1（golden-no-gps） | ☐ |
| 连拍高密度 | 5 套 | 0 | ☐ |
| 夜景/弱光 | 5 套 | 0 | ☐ |

> CI fixture 用于回归与 G0 预检；完整 5×6 矩阵需后续导入真实 trip 集。

---

## 3. 清单（逐套）

| 数据集 ID | 场景标签 | 张数 | 标注状态 | 用途 |
|-----------|----------|------|----------|------|
| golden-kyoto-gps | 城市/GPS/事件边界 | 见 manifest | segments-golden | AC-P6-03 |
| golden-mixed-scenes | 混合场景/聚类 | 18 | segments-golden | AC-P6-02/03 |
| golden-no-gps | 弱 GPS | 见 manifest | segments-golden | 聚类回归 |
| synthetic-gps | 合成 GPS | 见 manifest | segments-golden | AC-P6-03 |
| golden-gap-edge | 午餐间隔/GPS | 6 | segments-golden | AC-P6-03 |
| golden-cluster-noise | 聚类噪声对比 | 23 | — | AC-P6-02 |

路径根目录：`tests/fixtures/clustering/` · `schemas/fixtures/trip.linzhi_screens.json`

---

## 4. 标注规范与一致性

- 事件边界：与 `segments-golden.json` 对齐，fixed vs auto gap 作为 P5/P6 proxy。
- 聚类：DBSCAN（P5）vs HDBSCAN（P6），噪声率加权平均。
- 布局：linzhi fixture 上 P5/P6 longshot 模拟对比 repeat streak。
- 盲评样本需去除版本标签偏见（AC-P6-04 独立流程）。

---

## 5. 版本变更记录

| 日期 | 变更 | 影响 |
|------|------|------|
| 2026-05-30 | 模板创建 | Phase 6 开发准备 |
| 2026-05-30 | v0.2 新增 gap-edge / cluster-noise；adaptive gap 修复；G0 自动化 AC 全绿（除盲评） |
