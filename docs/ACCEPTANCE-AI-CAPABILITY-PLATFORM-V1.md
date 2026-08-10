# ACCEPTANCE · AI Capability Platform V1（ACP）

| 属性 | 内容 |
|------|------|
| **对应 PRD** | [PRD-AI-CAPABILITY-PLATFORM-V1.md](./PRD-AI-CAPABILITY-PLATFORM-V1.md) **v0.3.1** |
| **实施** | [IMPLEMENTATION-AI-CAPABILITY-PLATFORM-V1.md](./IMPLEMENTATION-AI-CAPABILITY-PLATFORM-V1.md) |
| **评审** | [acceptance-records/acp-ai-capability-platform-v1-review-2026-08-10.md](./acceptance-records/acp-ai-capability-platform-v1-review-2026-08-10.md) |
| **更新日期** | 2026-08-10 |

> 代码已合入 master（W1a～W4 + gap closure）。本表对照单测与狗粮勾选；**不**要求默认开启各 Agent。

## 自动化

```powershell
python -m pytest tests/unit/ai -q
```

## AC 勾选

| ID | 断言摘要 | 结果 | 证据 |
|----|----------|------|------|
| AC-ACP-01 | narrate 零回归（接入非搬迁） | ☑ | W1a + 既有 narrate 测 |
| AC-ACP-02 | title_art / CAL 零回归 | ☑ | title_art agent 包一层 |
| AC-ACP-03 | PA-MLLM 行为可回归 | ☑ | aesthetic 拆分测 |
| AC-ACP-04 | aesthetic→curation ignore 清理方向 | ☑ | W1b |
| AC-ACP-05 | Intent 关时 NR | ☑ | intent_brief disabled fallback |
| AC-ACP-06 | Intent 失败回落规则 | ☑ | fail-open 测 |
| AC-ACP-07 | Critic patternId 白名单 | ☑ | `test_layout_critic_*` |
| AC-ACP-08 | Judge 候选命中集合 | ☑ | mosaic_judge 测 |
| AC-ACP-09 | Agent 异常 fail-open | ☑ | 各 agent exception 测 |
| AC-ACP-10 | ops-admin ≥6 类统计 | ☐ | **需 dogfood 全开 trip** |
| AC-ACP-11 | unlock_gate 确定性 | ☑ | `test_unlock_gate.py` |
| AC-ACP-12 | agents 无默认像素/base64 | ☑ | 静态/单测 |
| AC-ACP-13 | cover_engine layers | ☑ | W1b |
| AC-ACP-14 | CI 零外呼 | ☑ | Mock / gate 测 |
| AC-ACP-15 | 关/超时不拖导入预览 | ☑ | gap closure |
| AC-ACP-16 | 三方 AND 零外呼 | ☑ | gate 测 |
| AC-ACP-17 | Judge 不侵入 SearchBudget 一阶段 | ☑ | gap / judge 测 |
| SHD-ACP-03 | 建议未采纳时 chapters/screens 不变 | ☑ | `test_shd_acp_03_*` |

## 开放

| 项 | 状态 |
|----|------|
| OQ-AIR-01 解冻建议 | unlock 现网样本不足 → `insufficient-data`；续狗粮 |
| Mosaic 缩略图 VLM | W2.5：V1 文本摘要 |
