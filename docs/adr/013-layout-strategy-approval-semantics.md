# ADR-013：LSE 排版策略 L2 审批语义

| 属性 | 内容 |
|------|------|
| **状态** | 已采纳 |
| **日期** | 2026-06-07 |
| **关联** | PRD-PHASE17 §5.3、AC-P17-07、`travelogue/templating/config_governance.py` |

## 背景

PRD 要求 L2 权重变更「双人审批」。现网 `config_governance.approve_router_change` 实现为：

- `len(approvals) >= 2`
- `approver != operator`（不可 self-approve）

即：**提议人（operator）+ 至少 2 名不同审批人** 共 3 人参与，而非字面「2 人双人」。

LSE 复用同一治理平台扩展 `layout_strategy_*` patch 键时，须明确验收以**代码语义**为准，避免产品与实现漂移。

## 决议

1. **AC-P17-07 验收口径**：L2 `layout_strategy_weights` / `penalties` / `rollout` patch 生效条件 = 现网 `approve` 语义（operator + ≥2 approvers，approver≠operator）。
2. **不修改** `>= 2` 阈值为字面双人，除非产品另开 ADR 修订。
3. **文档措辞**：PRD/Studio UI 使用「多人审批（提议人不可自批）」；避免单独写「双人」造成误解。
4. **L0 标注**：新增 5 个 `layout_strategy_*` 键在 `_apply_approved_patch` 的分支属 **代码发版**，非纯配置。

## 后果

- Studio 审批 UI 灰显 self-approve；须展示已有 approvals 计数。
- 运营 SOP：调权需至少 2 位与 operator 不同的 admin/operator 批准。
- 测试：`tests/test_config_governance.py`（或 W2 新增）须覆盖 layout_strategy patch 分支。

## 参考

- W0 审计 · IMPLEMENTATION-PHASE17 §5 治理
- `config_governance.py` · `approve_router_change`
