# ACP W4 · AIR 解冻门槛首份建议报告

**日期**：2026-08-10  
**状态**：计算器已落地（AC-ACP-11）  
**关联**：PRD-AI-CAPABILITY-PLATFORM-V1 §5.5 / OQ-AIR-01

## 1. 说明

本文件由 `travelogue.ai.eval.unlock_gate` 对 fixture 埋点计算生成，**不**自动改写 `aiSurfaceEnabled`。  
Live 计算：`GET /__travelogue/ai/unlock-gate`（聚合本机 Studio jsonl + ACP ops）。

## 2. 真实狗粮量级（当前不足）

# AIR 解冻门槛建议报告

- 裁决：**insufficient-data**
- 数据源：fixture:w4-bootstrap

| KPI | 样本 n | 比率 | 门槛 |
|-----|--------|------|------|
| 配置转化 | 5 | 60.0% | ≥40.0% |
| narrate 成功 | 4 | 75.0% | ≥70.0% |
| 渠道复制 | 6 | 33.3% | ≥30.0% |

- 理由：三路 KPI 分母均 < 30（对齐 CTS G-CTS-05 样本精神 / SHD-ACP-05）

## 3. AC-ACP-11 合成 fixture（门槛达标示例）

# AIR 解冻门槛建议报告

- 裁决：**go**
- 数据源：fixture:ac-acp-11

| KPI | 样本 n | 比率 | 门槛 |
|-----|--------|------|------|
| 配置转化 | 40 | 50.0% | ≥40.0% |
| narrate 成功 | 40 | 80.0% | ≥70.0% |
| 渠道复制 | 40 | 40.0% | ≥30.0% |

- 理由：all AIR KPI floors met

## 4. 使用方式

```bash
# 读本机漏斗
curl -H "X-Studio-Token: $TOKEN" http://127.0.0.1:8766/__travelogue/ai/unlock-gate

# 用 fixture 复现 AC-ACP-11
curl -X POST -H "Content-Type: application/json" -H "X-Studio-Token: $TOKEN" \
  http://127.0.0.1:8766/__travelogue/ai/unlock-gate \
  -d "{\"configOpens\":40,\"configCompletions\":20,\"narrateAttempts\":40,\"narrateSuccesses\":32,\"copyOpportunities\":40,\"copySuccesses\":16}"
```
