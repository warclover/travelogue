# ACP W2.5 · Mosaic Judge 产品/算法对齐纪要

**日期**：2026-08-10  
**状态**：Accepted（按 PRD v0.3 D-ACP-15 冻结语义落地接线）  
**关联**：PRD-AI-CAPABILITY-PLATFORM-V1 §5.4 / §8 W2.5 / AC-ACP-17 / SHD-ACP-01

## 1. 确认事项

| 议题 | 结论 |
|------|------|
| 角色 | Judge 从「beam 内决策者」降级为「排版结束后的事后复核」 |
| 调用时机 | `compose_trip` + `drain_mosaic_capture` 之后；**禁止**进入 `try_mosaic_window` / SearchBudget 热路径 |
| 候选约束 | `chosenCandidateId` ∈ 第一阶段 `top3Patterns`（AC-ACP-08） |
| 未赶上渲染 | 维持第一阶段确定性赢家；`overriddenFromFirstPass=false` |
| 默认开关 | `ai_capability.mosaic_judge.enabled=false`（NR） |
| 缩略图 VLM | V1 仍用文本摘要复核；像素缩略图留待 dogfood 后再开 |

## 2. SHD-ACP-01 阈值方法

- 用既有 `mosaicDecisionLog` / raw `top3Scores` 统计 top1−top2 分差分布。
- 同时统计「分差 < ε 的窗口数 / trip」。
- 默认 `tie_epsilon=0.03`；校准脚本：`python -m travelogue.ai.eval.tie_epsilon_stats`（或单测 fixture）。
- Judge 独立上限：`mosaic_judge.max_calls_per_trip`（默认 4）。

## 3. 验收锚点

- AC-ACP-08 / AC-ACP-09 / AC-ACP-17（SearchBudget 开/关逐位一致）
- 接线模块：`travelogue.ai.agents.mosaic_judge.run_post_compose_mosaic_judge`
