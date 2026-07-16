# AAD 验收补齐记录 · 2026-07-16

| 属性 | 内容 |
|------|------|
| **分支** | `arch/algo-deepening-v1` |
| **PRD** | [PRD-ARCH-ALGO-DEEPENING-V1](../PRD-ARCH-ALGO-DEEPENING-V1.md) v1.1 |
| **范围** | 对照缺口清单：AC-04/11/12/03 Studio、M4/M5 加深、M7 模板 |

## 门禁结果

| AC | 状态 | 证据 |
|----|------|------|
| AC-AAD-01/02 | ✅ | must-green 含 LTE + cluster_cli |
| AC-AAD-03 | ✅ | CLI 负例 + Studio `test_ac_aad_03_studio_rejects_absolute_escape` / 正例 `finds_existing_trip` |
| AC-AAD-04 | ✅（钉死列表） | [aad-must-green-nodeids.txt](./aad-must-green-nodeids.txt) · `python scripts/run_aad_must_green.py` → **39 passed** |
| AC-AAD-10 | ✅ | `run_curate` 壳 ≤80 |
| AC-AAD-11 | ✅ | `tests/unit/curation/test_aad_curate_stages.py` |
| AC-AAD-12 | ✅ | `tests/unit/curation/test_aad_curate_signature_ab.py`（layout_snapshot 双跑） |
| AC-AAD-13 | ✅ | cur→LE **5** · LE→cur **0** |
| AC-AAD-20 | ✅（默认关） | signature_ab + flag 单测；剔除字段：用 snapshot 仅比 pattern/slots |
| AC-AAD-21 | ✅ | 预算尽 → `BUDGET_EXHAUSTED`；decisionLog 含 `utility` |
| AC-AAD-22 | 部分 | 双跑签名稳定（strict 路径未单独加压测） |
| AC-AAD-23 | ✅ | PrefixBeam 环内 `incremental=True` + 共享 `IncrementalScoreState` |
| AC-AAD-24 / M7 | 📋 模板 | [aad-holdback.template.json](./aad-holdback.template.json) · [aad-holdback-album-list.md](./aad-holdback-album-list.md)；**盲评未执行；默认开=否** |
| AC-AAD-25/26 | ✅ | mosaic + beam 经 `combine_utility`；`lint_layout_contract_surface` 绿 |
| AC-AAD-30 | ✅ | purpose_overall lint |
| AAD-12 注册表 | ⏸ | P2 机会主义，本批未抽 |

## 仍开放（人工）

1. 填写 holdback 相册清单 N≥8 并盲评 → `aad-holdback-YYYY-MM-DD.json`  
2. PrefixBeam **默认开** 另 PR（平局≠开）  
3. 可选：全量 `pytest tests/unit/{layout_engine,curation,media}` 作为 AC-04 增强证据  
