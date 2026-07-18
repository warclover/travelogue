# TPC W3 · 手写模板包入库记录

| 属性 | 内容 |
|------|------|
| 日期 | 2026-07-18 |
| 关联 | [PRD-TEMPLATE-CONTRACT-V1](../PRD-TEMPLATE-CONTRACT-V1.md) §5.1 / AC-TPC-02 / AC-TPC-06 |
| 状态 | **experimental 入库** · 待狗粮并排签核后升 beta |

## 模板清单（4）

| ID | Mix | 靶点 |
|----|-----|------|
| `screen-mosaic-4-1l3p-rail` | L1P3 | 混向空洞 |
| `screen-mosaic-5-2p3l-rail` | L3P2 | 混向空洞（接替 deprecated 2p3l-equal） |
| `screen-mosaic-4-2l2p-weighted` | L2P2 | 加权棋盘品味（无文案层） |
| `screen-mosaic-4-hero-70-sidebar` | L4P0 | 非对称 ~70% hero + 侧栏 |

均带齐：`mix` / `constraints.eligibility` / `usage` / `rollout.percent=100` / `status=experimental`。

## 校验

```bash
python -m travelogue.layout_templates.cli validate --semantic -v
python -m travelogue.layout_templates.cli export --sync-journal
pytest tests/unit/layout_engine/test_template_contract_w3.py -q
```

## AC-TPC-04② 桥接删除

**本波不删** `main_eligibility.py`：hero-70 仍双写 `mainSlotPolicy` 以兼容未开 contract 的路径；既有 hero YAML 尚未全量迁 `eligibility`。删除条件：狗粮无回归 + 等价 fixture 绿 + CI grep 无 `mainSlotPolicy` 残留——另开 PR。

## 狗粮建议

`template_contract.enabled=true` 狗粮周，并排对照 off；重点看 1L3P / 2P3L 窗与 hero-70 页。
