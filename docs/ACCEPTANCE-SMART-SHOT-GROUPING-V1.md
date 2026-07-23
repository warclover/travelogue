# ACCEPTANCE · 智能分镜 SSG V1

| 属性 | 内容 |
|------|------|
| **PRD** | [PRD-SMART-SHOT-GROUPING-V1.md](./PRD-SMART-SHOT-GROUPING-V1.md) **v0.2.1** |
| **实施** | [IMPLEMENTATION-SMART-SHOT-GROUPING-V1.md](./IMPLEMENTATION-SMART-SHOT-GROUPING-V1.md) |
| **更新日期** | 2026-07-23 |

## M0 / M1 自动化

| AC | 断言 | 命令 / 状态 |
|----|------|-------------|
| AC-SSG-01～03 | 投影 / 软切 | `pytest tests/unit/curation/test_shot_grouping.py` |
| AC-SSG-04 / 19 | 切条跨组硬拒 · 混拼不误杀 | `pytest tests/unit/layout_engine/test_shot_group_gate.py` |
| AC-SSG-06 | burst > shotGroup run | `pytest tests/unit/curation/test_burst_priority.py tests/unit/curation/test_shot_grouping.py` |
| AC-SSG-07 | enabled=false 清空 | test_enabled_false_clears_groups |
| AC-SSG-18 | stage 字面量 + `shotGroupingMs` | `test_run_trip_clustering_stage_when_enabled` |

## M2 / M3

| AC | 状态 |
|----|------|
| AC-SSG-10 / 12 / 13 / 14 | ✅ 单测 `tests/unit/curation/test_look_split.py`（向量注入，无实机 CLIP） |
| AC-SSG-11 / 16 数值门 / cache 狗粮 | ☐ PR-E / 狗粮 |
| AC-SSG-15 mosaic 契约 | 继承 M1 gate（look 与 scene 同 `shotGroupId` 语义） |
| AC-SSG-05 / 11 数值门 | ☐ 狗粮 / golden |
| AC-SSG-17 | ☐ M3 · `look.enabled=false` 已单测 |

## 狗粮

见 [config-ssg-dogfood.example.yaml](./config-ssg-dogfood.example.yaml)（vision on）。
