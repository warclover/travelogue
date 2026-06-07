# Phase 16 · 曝光负债调权 Runbook（§9.4）

| 属性 | 内容 |
|------|------|
| **适用** | LTE 布局模板 `base_weight` 运行时调权（不改 YAML） |
| **审批** | 双人复核（proposer ≠ approver，共 2 票） |
| **入口** | Studio `/templates-admin` · CLI `phase16_template_eval.py` |

## 1. 生成提案

```bash
python scripts/phase16_template_eval.py \
  --trips-dir tests/fixtures/phase16-dogfood \
  --json-out /tmp/phase16-eval.json
```

查看 `exposureDebtProposals[]`：每项含 `templateId`、`currentBaseWeight`、`suggestedBaseWeight`、`actualExposureShare`、`targetExposureShare`。

## 2. 提交待审批

**CLI**

```bash
python scripts/phase16_template_eval.py \
  --trips-dir tests/fixtures/phase16-dogfood \
  --propose --operator admin-1
```

**Studio**

1. 打开 `/templates-admin`（loopback 或 `layout_templates_internal`）
2. 刷新列表，在「曝光负债调权提案」表格确认提案
3. 点击「提交调权提案」
4. 「待审批配置变更」与曝光区会显示 `待审批曝光调权 N 项（cfg-x 0/2）`

## 3. 双人审批

```bash
python scripts/phase16_template_eval.py --approve cfg-1 --approver admin-2
python scripts/phase16_template_eval.py --approve cfg-1 --approver admin-3
```

或在 Studio「待审批配置变更」中点击「审批」，输入第二名、第三名审批人 ID（不可与 proposer 相同）。

## 4. 生效与回滚

- 通过后写入 `runtime.layout_template_base_weights` + `layout_template_base_weights_meta`
- MCS 经 `lte_adapter.template_base_weight()` 读取
- 回滚：再次 propose 反向权重 patch，或手动 `runtime` PATCH（需同样双人审批）

## 5. 门禁

- CI：`phase16_template_eval.py --strict-ac15` 使用 `tests/fixtures/phase16-dogfood`
- 禁止自动 apply；`approvalRequired: true` 为硬约束
