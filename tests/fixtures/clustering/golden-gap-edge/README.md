# golden-gap-edge

CI golden · 同日午餐长间隔（6h）· 期望 **单事件**。

- **P5 proxy**：`eventGapMode=fixed` + `mergeTimeGapHours=0` → 4h 阈值误切两段 → F1 proxy 0
- **P6 proxy**：`eventGapMode=auto` → 自适应阈值 ≈6h → 单段 → F1 proxy 1.0

> Benchmark 评测时对该 fixture 使用 `merge_time_gap_hours=0`，以隔离 gap 自适应能力；生产默认 merge 仍由 `GeoClusterConfig` 控制。
