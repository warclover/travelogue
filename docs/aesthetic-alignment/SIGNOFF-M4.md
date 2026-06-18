# M4 · 人类审美对齐 Sign-off

> 分支：`feat/aesthetic-alignment`  
> PRD：[PRD-AESTHETIC-ALIGNMENT.md](../PRD-AESTHETIC-ALIGNMENT.md)  
> 语料：`trips/demo-2025-6` · 109 张 · 人类标签已冻结  
> **结论**：工程链路 **G0 通过**；**未达 AC-AA-02 全量门槛**，默认配置保持 rules-only，按 [ROLLOUT.md](./ROLLOUT.md) 灰度启用。

---

## 1. 实测 SRCC 汇总（demo-2025-6）

| 方案 | overall SRCC | Δ vs rules 0.2548 |
|------|-------------|-------------------|
| rules 基线（M0） | 0.2548 | — |
| rules + nima uniform blend 0.38 | 0.2855 | +0.0307 |
| + stratum blend | 0.2870 | +0.0322 |
| + portrait_lite | 0.2726 | +0.0178 |
| + MLLM 真实（qwen-vl-max × 8） | **0.2744** | +0.0196 |
| MLLM oracle 上界 | 0.2913 | +0.0365 |

图位 purpose SRCC（全栈 + 真实 MLLM）：

| purpose | SRCC |
|---------|------|
| cover | 0.2541 |
| hero | **0.2796** |
| moment | 0.2710 |

Acceptance records：`docs/acceptance-records/aesthetic-m2-stratum.demo-2025-6.json`、`aesthetic-m3-eval.demo-2025-6.json`

---

## 2. AC-AA 验收矩阵

| ID | 判据 | 状态 | 证据 |
|----|------|------|------|
| **AC-AA-00** | 标签集 ≥150、可复跑 SRCC | **部分** | 109/109 冻结；样本 <150，待扩语料 |
| **AC-AA-01** | learned SRCC > rules | **通过** | blend 后 0.2855 > 0.2548 |
| **AC-AA-02** | overall SRCC ≥0.6 或 +0.15 | **未通过** | 最佳 +0.037（oracle）；门槛 +0.15 |
| **AC-AA-03** | 封面/hero/瞬间盲评胜率 ≥60% | **待测** | 需 pairwise 人工盲评（非 SRCC 代理） |
| **AC-AA-04** | MLLM 失败 fail-open | **通过** | `aesthetic_mllm.py` + 单元测试 |
| **AC-AA-05** | MLLM 二次运行一致 | **通过** | 2026-06-18 复跑：cached=8, calls=0 |
| **AC-AA-06** | MLLM 调用 ≤ max_calls | **通过** | 8 ≤ 20（demo 短名单） |
| **AC-AA-07** | 坏片不进重点位 | **继承** | 沿用 cull + cover 闸口；Portrait PRD 后续 |
| **AC-AA-08** | 关闭开关回退现网 | **通过** | `ml_calibrate=false` / `mllm.enabled=false` 测试 |

---

## 3. 自动化（工程）

- [x] `pytest tests/test_aesthetic_*.py` — **42 passed**（2026-06-18）
- [x] M0 盲评 + SRCC CLI 可复跑
- [x] M2 `--by-stratum` 校准 + acceptance JSON
- [x] M3 DashScope 真实调用 8/8 + cache 命中
- [x] curate hook `apply_aesthetic_alignment`

---

## 4. 灰度与全量

| 阶段 | 配置 | 说明 |
|------|------|------|
| **G0** | 作者 dogfood | demo-2025-6 全链路实测完成 |
| **G1** | `config-aesthetic-alignment.example.yaml` G1 | ml + stratum；**mllm 默认关** |
| **G2** | 同文件 G2 | 作者 trip 开 mllm（需 DASHSCOPE） |
| **G3** | AC-AA-02 达标后 | 改代码默认 + 全量 |

Rollout 日志：[`../acceptance-records/aesthetic-alignment-rollout-log.json`](../acceptance-records/aesthetic-alignment-rollout-log.json)

---

## 5. 已知限制

1. 单语料 109 张、作者自标，泛化待 ≥150 多题材扩样。
2. `portrait_lite` 在 group 主导语料略降 SRCC，默认仍开、可 `--no-portrait-lite` 关闭。
3. MLLM 真实分低于 oracle，blend/短名单策略可继续调。
4. DeepSeek 供文本 LLM；视觉 MLLM 走百炼 `qwen-vl-max`（`.env` 需 `DASHSCOPE_API_KEY`）。

---

## 6. 签字栏

| 角色 | 姓名 | 日期 | 备注 |
|------|------|------|------|
| 作者 / PM | | | G0 dogfood |
| 工程 | | | 42 tests + acceptance JSON |
| QA | | | AC-AA-03 盲评待排 |
