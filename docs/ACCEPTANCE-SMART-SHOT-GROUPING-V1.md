# ACCEPTANCE · 智能分镜 SSG V1

| 属性 | 内容 |
|------|------|
| **PRD** | [PRD-SMART-SHOT-GROUPING-V1.md](./PRD-SMART-SHOT-GROUPING-V1.md) **v0.2.1** |
| **实施** | [IMPLEMENTATION-SMART-SHOT-GROUPING-V1.md](./IMPLEMENTATION-SMART-SHOT-GROUPING-V1.md) |
| **状态** | **Conditional Closed**（实拍盲评待日期版） |
| **更新日期** | 2026-07-23 |

## 自动化门

| AC | 断言 | 命令 / 状态 |
|----|------|-------------|
| AC-SSG-01～03 | 投影 / 软切 | `pytest tests/unit/curation/test_shot_grouping.py` |
| AC-SSG-04 / 19 | 切条跨组硬拒 · 混拼不误杀 | `test_shot_group_gate.py` |
| AC-SSG-05 | 假切条窗↓≥40% | `test_fake_slice_reduction_at_least_40pct` + `sameGroupAntiSlice` |
| AC-SSG-06 | burst > shotGroup run | `test_burst_priority` / `test_shot_grouping` |
| AC-SSG-07 | enabled=false 清空 | `test_enabled_false_clears_groups` |
| AC-SSG-10 / 12～14 | look 边界 / flash / 无脸 | `test_look_split.py` |
| AC-SSG-11 | look F1≥0.70 @ 0.28 | `test_look_threshold_calibration.py` |
| AC-SSG-15 | look 同 mosaic 契约 | `test_look_kind_same_mosaic_contract` |
| AC-SSG-16 | appearance cache | `test_look_cache_and_toggles.py` |
| AC-SSG-17 | 可关 look / 全部分镜 | `test_look_cache_and_toggles.py` |
| AC-SSG-18 | stage + `shotGroupingMs` | `test_orchestrator_studio_profile.py` |

## 狗粮 / 决策

| 项 | 状态 |
|----|------|
| 本机 GUIDE | [ssg-local-dogfood-GUIDE.md](./acceptance-records/ssg-local-dogfood-GUIDE.md) |
| 盲评模板 | [ssg-blind-review-TEMPLATE.md](./acceptance-records/ssg-blind-review-TEMPLATE.md) |
| 默认 on | **Hold** · [ssg-default-on-decision-2026-07-23.md](./acceptance-records/ssg-default-on-decision-2026-07-23.md) |
| M3 结案 | [ssg-m3-closeout-2026-07-23.md](./acceptance-records/ssg-m3-closeout-2026-07-23.md) |
| 配置样例 | [config-ssg-dogfood.example.yaml](./config-ssg-dogfood.example.yaml) |

```powershell
python -m pytest tests/unit/curation/test_shot_grouping.py tests/unit/curation/test_look_split.py tests/unit/curation/test_look_threshold_calibration.py tests/unit/curation/test_look_cache_and_toggles.py tests/unit/layout_engine/test_shot_group_gate.py tests/unit/orchestrator/test_orchestrator_studio_profile.py -q
```
