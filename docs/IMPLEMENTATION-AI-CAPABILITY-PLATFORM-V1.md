# IMPLEMENTATION · AI Capability Platform V1（ACP）

| 属性 | 内容 |
|------|------|
| **文档版本** | **v1.0.0** |
| **对应 PRD** | [PRD-AI-CAPABILITY-PLATFORM-V1.md](./PRD-AI-CAPABILITY-PLATFORM-V1.md) **v0.3.1** |
| **验收** | [ACCEPTANCE-AI-CAPABILITY-PLATFORM-V1.md](./ACCEPTANCE-AI-CAPABILITY-PLATFORM-V1.md) |
| **合入** | master（`9b32604e`…`b0321f79`） |
| **更新日期** | 2026-08-10 |

## 0. 切拍（已交付）

| 波次 | 内容 | 状态 |
|------|------|------|
| W1a | `travelogue/ai/` 骨架 · title_art · narrate 接入 | ✅ |
| W1b | aesthetic_mllm 拆分 · cover_engine layers | ✅ |
| W2 | Intent Brief · ops admin | ✅ |
| W2.5 | Mosaic Judge 二阶段对齐（Accepted） | ✅ |
| W3 | Layout Critic · Mosaic Judge skeleton | ✅ |
| W4 | unlock_gate · 统一盲评 | ✅ |
| Gap | Judge 接线 · G1 建议/反馈 · 超时/cache/埋点 · AC-15/16/17 | ✅ |

## 1. 包地图

| 模块 | 路径 |
|------|------|
| Agents | `travelogue/ai/agents/`（intent_brief · layout_critic · mosaic_judge · title_art · …） |
| Gate / budget / cache | `travelogue/ai/gate.py` · `budget.py` · `cache.py` |
| Telemetry / unlock | `travelogue/ai/telemetry.py` · `eval/unlock_gate.py` · `eval/blind_review.py` |
| HTTP | `travelogue/web/studio_handlers/ai_ops_handlers.py` |
| Studio 消费 | SAS Sheet · `chapter-panel.js` · `studio_entry.py` |

## 2. 铁律（实施）

1. Advisory-only：Critic/Judge/Intent **不得**静默改 `chapters[]`/`screens[]`（SHD-ACP-03）。  
2. Fail-open：超时/无 Key/解析失败不阻断导入→预览。  
3. D-ACP-14：`ai_capability` ∧ `aiSurfaceEnabled` ∧ 有效 Key。  
4. D-ACP-15：Judge **不**进 beam 热路径。  
5. D-ACP-17：narrate **不**物理搬家，只接入预算/缓存/遥测。

## 3. 残留

| 项 | 说明 |
|----|------|
| AC-ACP-10 | 需一次全 Agent 开启的 dogfood trip 填 ops |
| OQ-AIR-01 | 样本 ≥ 门槛后再出 go/no-go |
| cover_engine→render ignore 抽离 | W1b 备注 pending，非主里程碑 |
