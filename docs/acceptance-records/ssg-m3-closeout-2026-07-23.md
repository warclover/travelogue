# SSG M3 · 结案记录（PR-F）

| 属性 | 内容 |
|------|------|
| **日期** | 2026-07-23 |
| **分支** | `feature/smart-shot-grouping-v1` |
| **状态** | **Conditional Closed** · 自动化门 ✅ · 实拍盲评待签核 |

## 交付清单

| 项 | 状态 |
|----|------|
| F-SSG-M3-01 狗粮 GUIDE + 盲评模板 | ✅ |
| F-SSG-M3-02 AC-17 可关 look / 全部分镜 | ✅ 单测 |
| F-SSG-M3-03 ACCEPTANCE / IMPL 闭环 | ✅ Conditional Closed |
| F-SSG-M3-04 默认 on 决策 | ✅ **Hold**（不改默认） |
| AC-SSG-05 假切条↓≥40% | ✅ 合成窗度量 + `sameGroupAntiSlice` 硬拒 |
| AC-SSG-16 look cache | ✅ roundtrip 单测 |
| AC-SSG-15 look mosaic 契约 | ✅ 单测 |

## 自动化命令

```powershell
python -m pytest tests/unit/curation/test_shot_grouping.py tests/unit/curation/test_look_split.py tests/unit/curation/test_look_threshold_calibration.py tests/unit/curation/test_look_cache_and_toggles.py tests/unit/layout_engine/test_shot_group_gate.py tests/unit/orchestrator/test_orchestrator_studio_profile.py -q
```

## 仍开放（不阻塞合码）

- 实拍盲评日期版（填 [ssg-blind-review-TEMPLATE](./ssg-blind-review-TEMPLATE.md)）  
- 实机 CLIP cache 狗粮路径抽查  
- 默认强制 vision on（另决策 PR）
