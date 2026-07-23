# SSG PR-E · look `deltaThreshold` 标定纪要

| 属性 | 内容 |
|------|------|
| **日期** | 2026-07-23 |
| **PRD** | [PRD-SMART-SHOT-GROUPING-V1.md](../PRD-SMART-SHOT-GROUPING-V1.md) · AC-SSG-11 |
| **Fixture** | `tests/fixtures/shot-grouping/outfit-change-synthetic/` |
| **状态** | **Locked** · synthetic golden（实拍狗粮可再 ±0.05 一次） |

## 结论

| 参数 | 锁定值 |
|------|--------|
| `shotGrouping.look.deltaThreshold` | **0.28** |
| `shotGrouping.look.sustainFrames` | **2** |
| 边界 F1 门 | **≥0.70**（fixture 达标） |

## 算法修订（写回实现）

距离改为相对**当前造型参考帧**（段首），而非仅相邻帧：

1. Δ(ref, cur) ≥ threshold → 进入候选 streak  
2. streak 达 `sustainFrames` → 提交新 look（候选全部进入新组）  
3. streak 中断（回到低 Δ）→ 候选吸回当前 look（防单帧闪烁）

这样 `A,A,B,B` 可切开，且单帧 flash 不会误切。

## 验证

```bash
pytest tests/unit/curation/test_look_threshold_calibration.py tests/unit/curation/test_look_split.py -q
```

±0.05 扫描中，锁定值 0.28 落在 F1≥0.70 胜出集合内。

## 后续

- 实拍换装狗粮到位后可再 spike 一次（PRD 允许 ±0.05）并改版号  
- AC-SSG-16 cache 实机路径随狗粮验收  
