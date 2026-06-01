# Phase 7 · ONNX 推理加速 Spike（P7-F*）

| 属性 | 内容 |
|------|------|
| **状态** | No-Go（默认链路仍用 PyTorch OpenCLIP） |
| **日期** | 2026-06-01 |
| **关联** | [PRD-PHASE7.md](../PRD-PHASE7.md) §6.6 |

## 结论

- 未将 ONNX 纳入默认 Studio / curate 链路。
- 原因：INT8 导出与 OpenCLIP 权重对齐成本高；NR-P7 要求 ≥95% embedding hash 一致，需专项 benchmark 机时。
- 复现命令：`python scripts/phase7_onnx_compare.py`（无 ONNX 环境时退出码 2）。

## 后续若重启

1. 固定 250 张 fixture 相册 · S2 设备档。
2. 对比 PyTorch vs ONNX Runtime 耗时与 L2 距离。
3. 更新 [phase6-license-bom.md](./phase6-license-bom.md) 增量条目（P7-F3）。
