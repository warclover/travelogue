# CSC W3 · 结构化债务表（shim / legacy 双路径）

| 属性 | 内容 |
|------|------|
| **计量** | 文件名 legacy* / docstring `shim →`（非全文 rg） |
| **条目数** | **24** |
| **棘轮** | `python scripts/lint_csc_debt_table.py`（只降不升） |

| 文件 | 类型 |
|------|------|
| `travelogue/curation/aspect_buckets.py` | shim_docstring |
| `travelogue/curation/asset_subject.py` | shim_docstring |
| `travelogue/curation/burst_utils.py` | shim_docstring |
| `travelogue/curation/collage_routing.py` | shim_docstring |
| `travelogue/curation/decision_log.py` | shim_docstring |
| `travelogue/curation/degradation.py` | shim_docstring |
| `travelogue/curation/editorial_4mix.py` | shim_docstring |
| `travelogue/curation/editorial_portrait_row.py` | shim_docstring |
| `travelogue/curation/intent_hints.py` | shim_docstring |
| `travelogue/curation/layout_candidates.py` | shim_docstring |
| `travelogue/curation/screen_layout_state.py` | shim_docstring |
| `travelogue/curation/search_budget.py` | shim_docstring |
| `travelogue/curation/solo_scoring.py` | shim_docstring |
| `travelogue/curation/subject_tagging.py` | shim_docstring |
| `travelogue/curation/usage_rules/context.py` | shim_docstring |
| `travelogue/curation/usage_rules/evaluator.py` | shim_docstring |
| `travelogue/curation/usage_rules/registry.py` | shim_docstring |
| `travelogue/curation/usage_rules/tiebreak.py` | shim_docstring |
| `travelogue/layout_engine/mosaic/_legacy_generated.py` | legacy_filename |
| `travelogue/layout_engine/mosaic/legacy.py` | legacy_filename |
| `travelogue/layout_engine/mosaic/legacy_specs.py` | legacy_filename |
| `travelogue/layout_engine/render_contract.py` | shim_docstring |
| `travelogue/layout_templates/legacy_bridge.py` | legacy_filename |
| `travelogue/layout_templates/legacy_codegen.py` | legacy_filename |

> 删除无调用 shim 或退役 legacy 模块后重跑 `--update-baseline`；新增债务须 `--allow-growth` 并附理由。
