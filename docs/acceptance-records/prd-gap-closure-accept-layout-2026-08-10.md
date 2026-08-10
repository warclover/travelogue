# PRD 缺口收口 · 采纳章重排 / OQ-SAS-02 / AC-ACP-10

**日期**：2026-08-10  
**分支**：`fix/prd-gap-closure-accept-layout`  
**关联**：PRD-ACP §5.3 · PRD-SAS OQ-SAS-02 · AC-ACP-10/15/17 · SHD-ACP-01

## 交付

| 缺口 | 收口 |
|------|------|
| 采纳建议未触发章布局重跑 | `layout_accept.apply_accepted_suggestion_to_chapter` + accept handler `202` job；FE `pollJobUntilDone` + 预览重载 |
| OQ-SAS-02 正式包藏「高级」 | `capabilities.aiOpsAdminEnabled`（frozen 默认 false；`TRAVELOGUE_AI_OPS=1` 可开） |
| AC-ACP-10 六类统计可验 | `test_ac_acp_10_ops_summary_six_agents_nonzero_after_calls` |
| AC-ACP-15/17 · SHD-ACP-01 | 异步不阻塞断言 · Judge 源码禁 SearchBudget · ε 方法纪要勾选 |

## 自动化

```powershell
python -m pytest tests/unit/ai/test_layout_accept.py tests/unit/ai/test_unlock_gate.py tests/unit/ai/test_acp_gap_closure.py tests/unit/ai/test_mosaic_judge_post_compose.py tests/unit/web/test_sas_ai_sheet_wiring.py tests/unit/web/handlers/test_studio_handlers_config_static.py -q
```

## 狗粮手验（建议）

1. 开闸 trip：生成排版建议 → Sheet「采纳」→ toast「已按建议更新该章版面」→ 该章版式变化、他章不动。  
2. frozen/`aiOpsAdminEnabled=false`：Sheet 无「高级」；`?aiOps=1` 或 env 可显。  
3. `/ai-ops-admin`：六类 Agent 行可见（开发进程灌调用后非零）。
