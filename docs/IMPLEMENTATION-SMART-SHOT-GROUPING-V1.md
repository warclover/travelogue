# IMPLEMENTATION · 智能分镜 SSG V1

| 属性 | 内容 |
|------|------|
| **PRD** | [PRD-SMART-SHOT-GROUPING-V1.md](./PRD-SMART-SHOT-GROUPING-V1.md) **v0.2.1** |
| **分支** | `feature/smart-shot-grouping-v1` |
| **状态** | **In progress** · M1/M2 ✅ · PR-E 阈值已锁（synthetic）；M3 狗粮待续 |
| **更新日期** | 2026-07-23 |

## 列车

| PR | 内容 | 状态 |
|----|------|------|
| **PR-A / M0** | PRD SUP 回写 · ACCEPTANCE · schema · dogfood yaml · fixture 契约 | ✅ |
| **PR-B / M1** | stage · 投影 · run_sort · mosaic 门 · config | ✅ |
| **PR-C / M1** | telemetry · CLI `cluster reshotgroup` · stage 回归 | ✅ |
| **PR-D / M2** | 主脸 look · CLIP torso · cache · 组内拆分 | ✅ |
| **PR-E / M2** | 阈值标定 · `deltaThreshold=0.28` · sustain 参考帧语义 | ✅ |
| **PR-F / M3** | 狗粮盲评 | ☐ |

## 关键代码

| 模块 | 路径 |
|------|------|
| 投影 | `travelogue/curation/shot_grouping.py` |
| look 纯逻辑 | `travelogue/curation/look_split.py` |
| look 指标 | `travelogue/curation/look_metrics.py` |
| 外观向量 | `travelogue/vision/look_appearance.py` |
| 换装 golden | `tests/fixtures/shot-grouping/outfit-change-synthetic/` |
| 标定纪要 | [ssg-look-threshold-calibration-2026-07-23.md](./acceptance-records/ssg-look-threshold-calibration-2026-07-23.md) |
| 配置 | `travelogue/config/shot_grouping.py` |
| stage | `orchestrator/run.py` · `domain/pipeline_view.py` |
| CLI | `travelogue/cli/cluster.py` · `reshotgroup` |
| 屏序 | `curation/cluster_run_sort.py` |
| mosaic 门 | `layout_engine/mosaic/shot_group_gate.py` · `candidates.py` · `clone_detection.py` |
| 测试 | `tests/unit/curation/test_shot_grouping.py` · `test_look_split.py` · `tests/unit/layout_engine/test_shot_group_gate.py` |

## 合同补丁（已会签）

见 PRD §3.1 · D-SSG-17b～27 · [ssg-dev-feasibility](./acceptance-records/ssg-dev-feasibility-2026-07-23.md)。
