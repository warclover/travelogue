# QFX · God-module 棘轮留痕上调（2026-07-23）

| 属性 | 内容 |
|------|------|
| **决策** | [PRD-QUALITY-FIXPACK-V1](../PRD-QUALITY-FIXPACK-V1.md) **D-QFX-02** · AC-QFX-02 |
| **基线文件** | [csc-w2b-god-module-ratchet-baseline.json](./csc-w2b-god-module-ratchet-baseline.json) |
| **PR** | `fix/qfx-pr-a-m1-hemostasis`（PR-A） |
| **性质** | 小幅留痕上调（非空搬 keep-all 降行） |

## 变更

| 文件 | 旧 ceiling | 新 ceiling | Δ |
|------|------------|------------|---|
| `travelogue/curation/curate.py` | 1940 | 1945 | +5 |
| `travelogue/web/studio_pipeline.py` | 1127 | 1154 | +27 |

## 归因

- **`studio_pipeline.py`（+27，主因）**：NAS / 日更合入后管道编排增长；与 keep-all 门控行数无关。QFX 预处理抽离（T-QFX-02）落地前，以棘轮留痕锁定现况，禁止无审继续膨胀。
- **`curate.py`（+5）**：keep-all / 低清相关旁路增量；探查结论：门控本身约数行，**禁止**把「搬六行到新文件」当本波降耦银弹。完整降耦走策展预处理模块（PR-B/C）。

## 退出条件（后续）

- PR-B/C：抽出预处理后重新跑 `lint_csc_god_module_ratchet.py`；能降则降 ceiling；仍超则再留痕并更新本文。
- 本留痕 **不** 替代 AC-13/26（真实图 / 幂等清标）。
