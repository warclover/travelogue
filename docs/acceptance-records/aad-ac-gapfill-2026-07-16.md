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
| AC-AAD-04 | ✅（钉死列表） | [aad-must-green-nodeids.txt](./aad-must-green-nodeids.txt) · `python scripts/run_aad_must_green.py` → **46 passed** |
| AC-AAD-04 全量增强 | ⚠ | 本地 `layout_engine+curation+media`：**1435 passed / 5 failed / 21 skipped**（非 AAD 回归：cover v4 样式/Playwright 超时、`test_intent_plan`；CI 点数耗尽未跑 Actions） |
| AC-AAD-10 | ✅ | `run_curate` 壳 ≤80 |
| AC-AAD-11 | ✅ | `tests/unit/curation/test_aad_curate_stages.py` |
| AC-AAD-12 | ✅ | `tests/unit/curation/test_aad_curate_signature_ab.py`（layout_snapshot 双跑） |
| AC-AAD-13 | ✅ | cur→LE **5** · LE→cur **0** |
| AC-AAD-20 | ✅（默认关） | signature_ab + flag 单测；剔除字段：用 snapshot 仅比 pattern/slots |
| AC-AAD-21 | ✅ | 预算尽 → `BUDGET_EXHAUSTED`；decisionLog 含 `utility` |
| AC-AAD-22 | ✅ | `test_aad_ac_boost::test_ac_aad_22_deterministic_strict_double_run` |
| AC-AAD-23 | ✅ | PrefixBeam IncrementalScoreState + cache key prefix 探针 |
| AC-AAD-24 / M7 | 📋 骨架 | [aad-holdback-2026-07-16.json](./aad-holdback-2026-07-16.json)：**默认开=否 / Gate-Q No-Go**；盲评待填 N≥8 |
| AC-AAD-25/26 | ✅ | weights_hash 变更 + combine_utility AST 探针 |
| AC-AAD-30 | ✅ | purpose_overall lint |
| AAD-12 注册表 | ✅ 最小片 | `mosaic/pattern_specials.py` + 单测 |

## 仍开放（人工）

1. 填写 holdback 相册清单 N≥8 并盲评 → 更新 `aad-holdback-2026-07-16.json`  
2. PrefixBeam **默认开** 另 PR（平局≠开）  
3. UX-AAD-02 Studio 成册观感（flag 关）；UX-AAD-03 dogfood（flag 开）  
4. CI：本波 GitHub Actions 点数耗尽，**以本地 must-green / 全量套件为准**  
