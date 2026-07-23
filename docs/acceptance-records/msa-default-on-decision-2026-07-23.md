# MSA · 默认 `slot_adaptation.enabled` 决策（AC-11 / O-05）

| 属性 | 内容 |
|------|------|
| **日期** | 2026-07-23 |
| **决策** | **保持默认 `false`（fail-closed）** |
| **依据** | PR-A/B 自动化已绿；三类画像 **实册盲评尚未签核**（AC-09） |
| **关联** | [GUIDE](./msa-local-dogfood-GUIDE.md) · [盲评模板](./msa-blind-review-TEMPLATE.md) · [ACCEPTANCE](../ACCEPTANCE-MOSAIC-SLOT-ADAPTATION-V1.md) |

## 决议

1. 仓库 / `config.yaml.example` 继续 `mosaic.slot_adaptation.enabled: false`。  
2. 本机狗粮用 [`config-msa-dogfood.example.yaml`](../config-msa-dogfood.example.yaml) 显式打开。  
3. **仅当** AC-09 日期版盲评记录勾选通过后，另开 PR 改默认 true，并更新本文为「启用」修订。  
4. 不通过或未评：永久可保持 off；功能路径仍可用 dogfood 配置验证。

## 状态

| 项 | 状态 |
|----|------|
| AC-11 决策记录已落盘 | ✅ 本文（hold off） |
| AC-09 盲评签核 | ☐ 待手测 |
| 默认改为 true | ☐ 未做 |
