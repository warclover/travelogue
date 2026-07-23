# IMPLEMENTATION · 智能分镜 SSG V1

| 属性 | 内容 |
|------|------|
| **PRD** | [PRD-SMART-SHOT-GROUPING-V1.md](./PRD-SMART-SHOT-GROUPING-V1.md) **v0.2.1** |
| **分支** | `feature/smart-shot-grouping-v1` |
| **状态** | **Conditional Closed** · PR-A～F 自动化交付完成；实拍盲评另填 |
| **更新日期** | 2026-07-23 |

## 列车

| PR | 内容 | 状态 |
|----|------|------|
| **PR-A / M0** | PRD SUP 回写 · ACCEPTANCE · schema · dogfood yaml · fixture 契约 | ✅ |
| **PR-B / M1** | stage · 投影 · run_sort · mosaic 门 · config | ✅ |
| **PR-C / M1** | telemetry · CLI `cluster reshotgroup` · stage 回归 | ✅ |
| **PR-D / M2** | 主脸 look · CLIP torso · cache · 组内拆分 | ✅ |
| **PR-E / M2** | 阈值标定 · `deltaThreshold=0.28` · sustain 参考帧语义 | ✅ |
| **PR-F / M3** | 同组 anti-slice · AC-05/16/17 · 狗粮 GUIDE · 默认 on Hold | ✅ |

## 关键代码

| 模块 | 路径 |
|------|------|
| 投影 | `travelogue/curation/shot_grouping.py` |
| look 纯逻辑 | `travelogue/curation/look_split.py` |
| look 指标 | `travelogue/curation/look_metrics.py` |
| 外观向量 | `travelogue/vision/look_appearance.py` |
| 换装 golden | `tests/fixtures/shot-grouping/outfit-change-synthetic/` |
| mosaic 门 | `layout_engine/mosaic/shot_group_gate.py` · `shot_group_metrics.py` · `candidates.py` |
| 配置 | `travelogue/config/shot_grouping.py` |
| stage | `orchestrator/run.py` · `domain/pipeline_view.py` |
| CLI | `travelogue/cli/cluster.py` · `reshotgroup` |
| 屏序 | `curation/cluster_run_sort.py` |

## 结案文档

| 文档 | 说明 |
|------|------|
| [ssg-m3-closeout-2026-07-23.md](./acceptance-records/ssg-m3-closeout-2026-07-23.md) | M3 结案 |
| [ssg-local-dogfood-GUIDE.md](./acceptance-records/ssg-local-dogfood-GUIDE.md) | 本机狗粮 |
| [ssg-default-on-decision-2026-07-23.md](./acceptance-records/ssg-default-on-decision-2026-07-23.md) | 默认 on **Hold** |
| [ssg-look-threshold-calibration-2026-07-23.md](./acceptance-records/ssg-look-threshold-calibration-2026-07-23.md) | PR-E 锁参 |

## 合同补丁（已会签）

见 PRD §3.1 · D-SSG-17b～27 · [ssg-dev-feasibility](./acceptance-records/ssg-dev-feasibility-2026-07-23.md)。
