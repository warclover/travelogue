# PA · 照片审美评价体系 — 执行任务清单

| 属性 | 内容 |
|------|------|
| **版本** | v0.1 |
| **日期** | 2026-06-05 |
| **关联设计** | [DESIGN-PHOTO-AESTHETIC-EVALUATION.md](../DESIGN-PHOTO-AESTHETIC-EVALUATION.md) |
| **门禁** | 改 `trip.json` 字段须同步 `schemas/trip.schema.json`；scoring 改动须跑相应测试（见 [QUALITY-GATE.md](../QUALITY-GATE.md)） |

> 任务编号 `PA-T##`。规模：S（<0.5d）/ M（0.5–1.5d）/ L（>1.5d）。状态：⬜ 待办 / 🟦 进行 / ✅ 完成。
> **关键路径**：T01 → T02 → T03 → T04 → (T06/T07/T08) → T09。T05/T10/T11 可并行；T12+ 为可选增强。

---

## 阶段 PA-1 · 通用美学/质量分（路径 A · 零依赖）

### PA-T01 · 数据模型与 schema ✅ S
- **目标**：定义 `quality.aesthetic` 结构并落到 schema。
- **涉及**：`schemas/trip.schema.json`（新增 `aesthetic` 定义：`version/source/overall/confidence/dims{}/signals{}/critique`）。
- **产出**：schema 校验通过；提供 1 个 fixture 样例。
- **依赖**：无。
- **验收**：`python scripts/validate_trip.py … --level all` 通过。

### PA-T02 · 曝光/影调指标 ✅ M
- **目标**：新增直方图类指标（动态范围、过/欠曝占比、中间调居中度）。
- **涉及**：新增 `travelogue/media/exposure_metrics.py`，函数 `histogram_stats(img) → {dynamicRange, clipHighRatio, clipLowRatio, midtoneCenter}`。复用 ingest 已有的灰度缩略图，避免二次解码。
- **依赖**：无（PIL）。
- **验收**：单测覆盖纯黑/纯白/正常曝光样张；耗时纳入 `pipeline.timings`。

### PA-T03 · 色彩和谐 + 光影指标 ✅ M
- **目标**：补 `colorHarmony`（主色 k-means + `delta_e_cie76` 和谐窗）与 `lighting`（亮度梯度 `lumaGradient` + 反差 `contrast`）。
- **涉及**：扩展 `travelogue/media/color_metrics.py`（复用 `delta_e_cie76`/`triangular_score`）；光影可并入 `exposure_metrics.py` 或新增 `lighting_metrics.py`。
- **依赖**：T02（共享缩略图管线）。
- **验收**：单色/互补/杂乱配色样张得分符合预期；逆光/平光样张 `lighting` 有区分度。

### PA-T04 · Layer 1 合成器 ✅ M
- **目标**：把 signals 合成五维 `dims` 与 `overall/confidence`，写入 `quality.aesthetic`。
- **涉及**：新增 `travelogue/curation/aesthetic_score.py`，函数 `compute_aesthetic(asset) → dict`、`build_aesthetic_explain(asset)`（仿 `build_cover_explain`）。构图维度复用 `curate_scoring._subject_center_norm/_axis_rule_of_thirds_score`。
- **依赖**：T01–T03。
- **验收**：所有维度 ∈[0,1]；缺信号时 fail-open 给 `confidence` 折扣不崩。

### PA-T05 · ingest 接线 + 缓存 ✅ M
- **目标**：在导入时填充 `quality.aesthetic.signals`，合成层可在 ingest 或 curate 阶段调用。
- **涉及**：`travelogue/media/ingest.py`（`:383` 算色彩处同批补 signals；`:416` 写 `quality` 处挂 `aesthetic`）。缓存沿用 `contentSig`（参考 `phase9_aesthetic.json` 机制）。
- **依赖**：T02–T04。
- **验收**：重复导入命中缓存；`meanLuma` 统一从 `quality.meanLuma` 读取（注意现存 `color.meanLuma` 兼容读法）。

### PA-T06 · 配置开关 ✅ S
- **目标**：`config.py` 增加 `aesthetic.*`（enabled / source / weights / use_purpose_presets）。
- **涉及**：`travelogue/config.py` + 一份 `docs/config-pa.example.yaml`。
- **依赖**：T04。
- **验收**：关开关后回退到旧行为；默认 `enabled=true, source=rules`。

---

## 阶段 PA-2 · 用途专属分接入（首页 / 拼图主图）

### PA-T07 · U-COVER 接入 overall ✅ M
- **目标**：封面打分纳入美感比乘子。
- **涉及**：`curate_scoring._quality_multiplier`（增 `aesthetic_multiplier`，clamp[0.7,1.3]）；`effective_cover_score` 透传；`build_cover_explain` 增加因子标签。
- **依赖**：T04、T06。
- **验收**：`tests/` 封面相关用例更新通过；盲评 A/B 新封面 ≥ 旧选择。

### PA-T08 · U-HERO 接入 overall ✅ M
- **目标**：拼图主图/章节英雄排序键由 `sharpness` 改为 `aesthetic.overall`（sharpness 作 tiebreak）。
- **涉及**：`curate_scoring.hero_score`、`mosaic/hero.pick_main_for_pattern`、`screen_planner._pick_main_landscape_id`、`mosaic/scorer._main_quality_penalty`（阈值可改读 overall）。
- **依赖**：T04。
- **验收**：`tests/test_layout_scoring.py` / mosaic 相关用例通过；主图人评不劣化。

---

## 阶段 PA-3 · 单张强调（U-SOLO，新增能力）

### PA-T09 · U-SOLO 评分器 ✅ L
- **目标**：新增单张强调选择器：`solo_score = overall × 光影 × 留白 × uniqueness × (1−dup)`。
- **涉及**：新增 `travelogue/curation/solo_scoring.py`；`uniqueness` 用 `layout_scoring.score_tone_continuity` 的 ΔE 工具（无 CLIP 时）。排版调用点：`screen_planner` / `mosaic` 选定整屏大图处。
- **依赖**：T04、T08。
- **验收**：与封面/主图不重复；单张强调命中率人评提升。

### PA-T10 · 解释输出对接 Studio ✅ S
- **目标**：把 `build_aesthetic_explain` 的 top-3 因子透出到 Studio 展示。
- **涉及**：`web/studio_*` 对应 entry/telemetry 字段（参考 QUALITY-GATE telemetry 章）。
- **依赖**：T04。
- **验收**：Studio 能看到每图分项因子。

### PA-T11 · 算法清单登记 ✅ S
- **目标**：把新指标/文件登记进算法清单。
- **涉及**：`docs/algorithm-inventory.md` §1.4 + §2.1/§2.4 增行。
- **依赖**：T02–T09 相应完成。
- **验收**：清单与代码一致。

---

## 阶段 PA-4 · ML 校准（路径 B · 可选 external）

### PA-T12 · topiq 校准接入挑选 ✅ M
- **目标**：`overall = 0.6·rules + 0.4·topiq`，在 curate 阶段默认可用（不止 cull）。
- **涉及**：`photo_cull_ml.apply_aesthetic_scores` 复用；`aesthetic_score.compute_aesthetic` 读取 `aestheticScore` 做 blend；config `ml_calibrate`。
- **依赖**：T04；环境含 `pyiqa+torch`。
- **验收**：overall 与人评 SRCC 提升；无 torch 时 fail-open 到纯规则。

---

## 阶段 PA-5 · MLLM 点评（路径 C · 可选 external）

### PA-T13 · MLLM 分项打分 + 一句点评 ⬜ L
- **目标**：批量调多模态大模型出 `dims` + ≤40 字中文点评，仅对 cull 通过的候选池调用。
- **涉及**：仿 `services/llm_*` 范式新增 `services/aesthetic_critique.py`；强约束 JSON；缓存键 `contentSig+model+promptVersion`；fail-open 回退路径 A。
- **依赖**：T04、T06。
- **验收**：点评可读性人评达标；成本可控（候选池限流 + 缓存）；失败不阻断成册。

---

## 验收度量（贯穿）

| 指标 | 方法 | 关联任务 |
|------|------|----------|
| overall–人评相关性 | 标注子集 Spearman SRCC | T04 / T12 |
| 择优盲评 | U-COVER/HERO/SOLO top-1 vs 旧逻辑 2 选 1 | T07 / T08 / T09 |
| 稳健性 | 缺信号 / 无 OpenCV / 无 torch fail-open | T04 / T05 / T12 |
| 性能 | Layer1 单图 CPU 增量进 `pipeline.timings` | T02 / T05 | `ingestStats.elapsedMs.aesthetic` |

**验收脚本**：`scripts/pa_aesthetic_acceptance.py`（SRCC + U-COVER/HERO/SOLO 盲评导出）

---

## 建议执行顺序（两周内可交付 PA-1+PA-2）

1. **W1**：T01 → T02 → T03 → T04 → T05 → T06（打通 Layer 1，零依赖可跑）。
2. **W2**：T07 + T08（首页/主图接入）→ T11 登记 → 盲评 A/B。
3. **后续按需**：T09（单张强调）→ T10（Studio 展示）→ T12（ML 校准）→ T13（MLLM 点评）。
