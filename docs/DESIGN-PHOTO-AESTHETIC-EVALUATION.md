# 照片审美评价体系设计文档（Photo Aesthetic Evaluation · PA）

| 属性 | 内容 |
|------|------|
| **版本** | v0.1（草案） |
| **日期** | 2026-06-05 |
| **代号** | PA（Photo Aesthetic） |
| **关联** | [algorithm-inventory.md](./algorithm-inventory.md) · [QUALITY-GATE.md](./QUALITY-GATE.md) · [cover-selection-plan.md](./cover-selection-plan.md) · [DESIGN-PHASE15-mosaic-system.md](./DESIGN-PHASE15-mosaic-system.md) |
| **状态** | 设计评审中 · 未排期实现 |

---

## §0 背景与目标

### 0.1 目标场景

对**用户指定文件夹中的照片**做审美/质量评价，并据此完成三类"择优"：

| 用途代号 | 场景 | 现有承接函数 |
|----------|------|--------------|
| **U-COVER** | 适合做首页 / 封面的照片 | `curate_scoring.pick_cover_asset_id` |
| **U-HERO** | 适合在拼图中作为主图（hero/main slot） | `mosaic/hero.pick_main_for_pattern` · `curate_scoring.pick_chapter_hero` |
| **U-SOLO** | 适合单张强调（整屏大图 / 跨页） | 暂无专属选择器（新增） |

### 0.2 评价维度

需要可解释地覆盖摄影学常用维度：**构图、曝光/影调、色彩、光影、主体清晰与突出**，并产出一个可排序的总分与置信度。

### 0.3 设计原则（与现有工程一致）

1. **默认零依赖可跑**：基座（PIL + 规则）必须给出完整评分；深度模型/MLLM 为可选增强（参照 `algorithm-inventory.md` §1 的 `native / hybrid / external` 分级）。
2. **幂等可缓存**：所有评分写入 `asset.quality.*`，复用 `phase9_aesthetic.json` 式的 content-sig 缓存。
3. **可解释**：每个评分都能反查 top 因子（沿用 `build_cover_explain` 的因子-标签模式）。
4. **确定性**：同输入同配置必同输出，便于 golden 回归。

---

## §1 现状基线（travelogue 当前能力与缺口）

### 1.1 底层质量信号（ingest 阶段）

| 维度 | 现状实现 | 字段 | 文件 |
|------|----------|------|------|
| 清晰度 | 边缘滤波方差（≈拉普拉斯方差测焦） | `quality.sharpness` | `media/sharpness.py` |
| 曝光 | 32×32 缩略图 sRGB 平均亮度 | `meanLuma` | `media/color_metrics.py` |
| 色彩 | 主色 → Lab → 彩度三角窗 | `dominantTone` | `media/color_metrics.py` |
| 主体 | Haar 人脸 → 焦点/显著框 | `focalPoint` · `salientBox` · `faceCount` | `media/subject_detect.py` |
| 媒体类型 | 截图/缩略图/转发启发式 | `mediaClass` | `media_classify.py` |
| ML 美学分 | pyiqa `topiq_nr`（**默认关，仅 cull 用**） | `quality.aestheticScore` | `photo_cull_ml.py` |

### 1.2 上层用途评分

- **剔除门** `photo_cull.run_photo_cull`：分辨率门 → 模糊百分位门 → burst/dedupe 组内选优 → top-k 配额；分人像/风景分支。
- **封面** `cover_score`：`画幅比例 × 媒体权重 × 清晰度比 × 人像降权 × 人脸构图 × 色彩丰富度 × 横竖偏好 × 三分法`。
- **章节英雄** `hero_score`：偏好宽幅横图、清晰、非截图。
- **拼图主图** `pick_main_for_pattern`：landscape 中按清晰度选。
- **拼图惩罚** `mosaic/scorer.score_candidate`：人脸裁切、`_main_quality_penalty`（用 `quality.sharpness`）、重复密度、几何/比例。

### 1.3 缺口分析

| 维度 | 现状 | 缺口 |
|------|------|------|
| 构图 | 仅"主体三分线位置 + 横竖比例" | 无引导线、对称、平衡、留白 |
| 曝光/影调 | 仅整图平均亮度 | 无动态范围、过/欠曝占比、直方图分布 |
| 色彩 | 仅"够不够鲜艳" | 无色彩和谐度、冷暖、调性 |
| 光影 | 基本缺失 | 无方向光/逆光/反差判断 |
| 总体美感 | 规则乘法分 + 可选 topiq | 未学习"人类审美偏好"；分项未结构化 |
| 单张强调 | 无专属评分 | U-SOLO 需新增 |

**结论**：现有体系强于"版式适配 + 工程稳健"，弱于"真实美感（光影/色彩/构图美学）"。本设计在**不破坏现有择优链路**的前提下补齐审美维度。

---

## §2 与专业点评类应用算法对比

| 能力 | 点评类应用（NIMA / PhotoEye / MLLM） | travelogue 现状 | 本设计取向 |
|------|--------------------------------------|------------------|------------|
| 总体审美分 | 学 AVA 人类打分分布，输出 1–10 + 置信 | 规则分 + 可选 topiq | 规则分项 + topiq 校准，可选 MLLM |
| 构图 | 神经网络隐式学习 | 三分 + 比例 | CV 显式分项（三分/留白/平衡）+ 可选模型 |
| 曝光/影调 | 学高光阴影/动态范围 | 平均亮度 | 新增直方图/动态范围 CV 指标 |
| 色彩 | 学和谐/调性 | 彩度 | 新增色彩和谐度（Lab 距离） |
| 光影 | 模型理解方向光/逆光 | 缺失 | 亮度梯度/明暗分区启发式 + 可选模型 |
| 可解释点评 | MLLM 生成自然语言 | 因子级解释 | 因子级解释 + 可选 MLLM 一句话点评 |
| 运行成本 | NIMA 端侧 / MLLM 需 GPU·API | CPU 毫秒级 | 基座 CPU，增强可选 |

> 取向：**用 CV 显式分项补齐"曝光/色彩/光影/构图"** 作为默认路径，把 `topiq_nr` 当作"总分校准器"，把 MLLM 当作"高质量增强 + 自然语言点评"的可选层。

---

## §3 评价体系设计（三层架构）

```
Layer 1  通用美学/质量分（每张照片一次，写 quality.aesthetic.*）
         ├─ 构图 composition
         ├─ 曝光 exposure
         ├─ 色彩 color
         ├─ 光影 lighting
         ├─ 主体 subjectClarity
         └─ 总分 overall + 置信 confidence
                │
Layer 2  用途专属分（= Layer1 分项 × 用途权重）
         ├─ U-COVER  首页/封面
         ├─ U-HERO   拼图主图
         └─ U-SOLO   单张强调
                │
Layer 3  多样性 / 叙事约束（复用现有：aspect·day 去重、burst 组、重复密度惩罚）
```

### 3.1 数据模型（写入 `asset.quality.aesthetic`）

> 同步 `schemas/trip.schema.json`（见 QUALITY-GATE 第 1 条）。所有字段 `[0,1]`，缺省 `null` 表示未评估。

```jsonc
"quality": {
  "sharpness": 1234.5,            // 既有
  "aestheticScore": 0.62,        // 既有 · topiq_nr 归一
  "aesthetic": {                  // 新增 · Layer 1 产物
    "version": "pa-v0.1",
    "source": "rules|rules+ml|mllm",
    "overall": 0.71,
    "confidence": 0.80,
    "dims": {
      "composition":    0.74,
      "exposure":       0.68,
      "color":          0.81,
      "lighting":       0.55,
      "subjectClarity": 0.66
    },
    "signals": {                  // 可解释的中间量（调试/解释用）
      "dynamicRange":   0.72,
      "clipHighRatio":  0.03,
      "clipLowRatio":   0.01,
      "colorHarmony":   0.78,
      "thirdsScore":    0.69,
      "negativeSpace":  0.41,
      "lumaGradient":   0.58
    },
    "critique": null               // 可选 · MLLM 一句话点评
  }
}
```

### 3.2 Layer 1：分项指标定义（默认 CV 路径）

每个分项最终归一到 `[0,1]`。下面给出**默认 native 实现**，括号内为可替换的增强实现。

#### (a) 构图 composition
- **三分法 thirdsScore**：复用 `_subject_center_norm` + `_axis_rule_of_thirds_score`（已存在于 `curate_scoring.py`）。
- **留白 negativeSpace**：主体框 `salientBox` 面积占比 → 适中留白得分（三角窗，peak≈主体占画面 15–35%）。
- **平衡 balance**：将缩略图四象限亮度/边缘能量做对称性比较（左右、上下方差越小越平衡）。
- 合成：`composition = 0.45·thirds + 0.30·balance + 0.25·negSpace`
- （增强：构图美学可由 MLLM 或 AADB 属性模型直接给分。）

#### (b) 曝光/影调 exposure
- 在 ingest 的 32×32 灰度缩略图上算**亮度直方图**：
  - `clipHighRatio` = 亮度 > 0.95 的像素比；`clipLowRatio` = 亮度 < 0.05 的像素比。
  - `dynamicRange` = (P95 − P5) 亮度差，归一。
- 合成：`exposure = clamp( 0.5·dynamicRange + 0.3·midtoneCenter + 0.2·(1 − clipHigh − clipLow) )`
  - `midtoneCenter` 复用现有 `meanLuma` 的"居中度"（`1 − |meanLuma − 0.5|·2`，已在 `_portrait_quality_score` 出现）。

#### (c) 色彩 color
- **饱和/丰富度**：复用 `color_richness_multiplier` / `dominant_tone_chroma_score`。
- **色彩和谐 colorHarmony**：对缩略图取主色 k-means（k=3–5），用 `delta_e_cie76`（已存在）衡量主色之间距离是否落在"和谐窗"（互补/邻近/单色调）。
- 合成：`color = 0.55·richness + 0.45·colorHarmony`

#### (d) 光影 lighting（新增启发式）
- **亮度梯度 lumaGradient**：缩略图水平/垂直亮度梯度的均值（方向光强度代理）。
- **明暗反差 contrast**：直方图标准差 / 高低分区亮度差。
- 合成：`lighting = clamp( 0.5·normGradient + 0.5·normContrast )`，对纯平光给低分、对有方向/层次的光给高分。
- （增强：MLLM 对"逆光/黄金时刻/伦勃朗光"语义判断显著更准。）

#### (e) 主体清晰与突出 subjectClarity
- `sharpness` 归一（复用 `_norm_sharpness`，按本批 lo/hi）。
- 主体-背景清晰对比：若有 `salientBox`，比较框内/框外边缘能量。
- 合成：`subjectClarity = 0.7·normSharp + 0.3·subjectContrast`

#### (f) 总分与置信
```
overall = Σ wᵢ · dimᵢ          // 默认 w = {comp .25, expo .20, color .20, light .15, subj .20}
若存在 aestheticScore(topiq)：
    overall = 0.6·overall + 0.4·aestheticScore     // 用学习模型校准规则分
confidence = f(信号完整度, mediaClass, 是否人脸/曝光极端)   // 用于争议度/兜底
```

> 权重 `w` 进配置（见 §6），首页/拼图主图可用不同的预设权重。

### 3.3 Layer 2：用途专属分

通用形式：`用途分 = aesthetic.overall × Π(用途适配乘子)`，乘子沿用现有乘法模型，便于灰度替换。

#### U-COVER（首页/封面）
在现有 `cover_score` 基础上，把"清晰度比乘子"升级为"美感比乘子"：
```
cover_score' = base(画幅)
             × media_weight × person_demote × face_bbox × color_richness × composition × thirds   // 现有
             × aesthetic_multiplier            // 新增：overall 相对本批中位数的比，clamp[0.7,1.3]
```
- 集成点：`curate_scoring._quality_multiplier` 增加 `aesthetic` 项；`effective_cover_score` 透传。

#### U-HERO（拼图主图）
```
hero_score' = aspect(宽幅偏好) × media_weight × aesthetic.overall × composition × subjectClarity
```
- 集成点：`hero_score` / `pick_chapter_hero` / `mosaic/hero.pick_main_for_pattern`（`_pick_main_landscape_id` 的排序键由 `sharpness` 改为 `aesthetic.overall`，sharpness 作 tiebreak）。

#### U-SOLO（单张强调）— 新增
单张大图最看重**情绪/光影/独特性 + 足够留白**，且不应与封面/主图重复：
```
solo_score = aesthetic.overall
           × (0.5 + 0.5·lighting)        // 光影加权
           × (0.6 + 0.4·negativeSpace)   // 留白足够才适合压字/跨页
           × uniqueness                  // 与同章其它图的 CLIP/色调距离（无 CLIP 时用 ΔE 代理）
           × (1 − dup_penalty)
```
- 建议新增 `curation/solo_scoring.py`，复用 `layout_scoring.score_tone_continuity` 的 ΔE 工具算 `uniqueness`。

### 3.4 Layer 3：多样性 / 叙事约束（复用现有）

| 约束 | 复用 |
|------|------|
| 封面候选 aspect/day 去重 | `cover_candidates` |
| burst/dedupe 组内选优 | `photo_cull._pass2_group_winners` |
| 拼图重复密度惩罚 | `mosaic/scorer._duplicate_density_penalty` |
| 节奏/连续 pattern 限制 | `ScreenLayoutPlannerState.can_emit_pattern` |

---

## §4 实现路径（分级，可叠加）

| 路径 | 实现 | 默认可用 | 依赖 | 价值 | 成本 |
|------|------|----------|------|------|------|
| **A · CV 分项** | §3.2 native 指标（曝光/色彩和谐/光影/构图） | ✅ | PIL（可选 numpy 加速） | 补齐四大维度，零成本 | 低 |
| **B · ML 校准** | 把 `topiq_nr` 在挑选场景默认开启，校准 overall | ❌ | pyiqa + torch | 总分更贴近人类偏好 | 中（GPU 优） |
| **C · MLLM 点评** | 批量调多模态大模型出分项 JSON + 一句点评 | ❌ | API Key / 本地 MLLM | 接近"摄影大师"，可展示给用户 | 高 |

建议顺序：**A → B → C**。A 即可显著改善择优质量且无新依赖；B/C 作为 `external` 增强，遵循 `algorithm-inventory.md` 分级。

### 4.1 路径 C 的 MLLM 接口（建议）
- 复用 `services/llm_*` 的调用与错误处理范式。
- 输出强约束 JSON（与 §3.1 `dims` 对齐）+ ≤40 字中文点评。
- 缓存键 = `contentSig + model + promptVersion`，沿用 `phase9_aesthetic.json` 机制，避免重复计费。
- 失败 fail-open 回退到路径 A 分数（对齐 `apply_photo_cull` 的 fail-open 设计）。

---

## §5 与现有代码的集成点

| 改动 | 文件 / 函数 | 说明 |
|------|-------------|------|
| 写入分项信号 | `media/ingest.py`（调用处） | 在算 `meanLuma/dominantTone` 同批补：直方图、动态范围、色彩和谐、亮度梯度 → `quality.aesthetic.signals` |
| 新增曝光指标 | `media/color_metrics.py` 或新增 `media/exposure_metrics.py` | `histogram_stats / dynamic_range / clip_ratios` |
| 新增 Layer 1 合成 | 新增 `curation/aesthetic_score.py` | 读 signals → 产出 `quality.aesthetic.dims/overall/confidence` |
| ML 校准接入挑选 | `photo_cull_ml.apply_aesthetic_scores` | 当前仅 cull 用；让 overall 校准默认在 curate 阶段可用 |
| 封面接入美感 | `curate_scoring._quality_multiplier` / `effective_cover_score` | 增加 `aesthetic_multiplier` |
| 主图接入美感 | `curate_scoring.hero_score` · `mosaic/hero.pick_main_for_pattern` · `screen_planner._pick_main_landscape_id` | 排序键 sharpness → overall（sharpness 兜底） |
| 单张强调 | 新增 `curation/solo_scoring.py` | U-SOLO 评分器 |
| 解释输出 | 仿 `build_cover_explain` | `build_aesthetic_explain`，给分项 top 因子 |
| Schema | `schemas/trip.schema.json` | 新增 `quality.aesthetic` 定义 |
| 算法清单 | `docs/algorithm-inventory.md` §1.4 / §2 | 登记新指标与文件 |

---

## §6 配置开关（建议挂在 `config.py`）

```yaml
aesthetic:
  enabled: true               # Layer 1 总开关（A 路径）
  source: "rules"             # rules | rules+ml | mllm
  weights:                    # overall 维度权重
    composition: 0.25
    exposure: 0.20
    color: 0.20
    lighting: 0.15
    subjectClarity: 0.20
  ml_calibrate: false         # B 路径：用 topiq 校准 overall
  ml_calibrate_blend: 0.4
  mllm:                       # C 路径
    enabled: false
    model: ""
    prompt_version: "pa-1"
    max_critique_chars: 40
  use_purpose_presets: true   # cover/hero/solo 各用不同 weights 预设
```

---

## §7 分阶段落地计划

| 阶段 | 范围 | 交付 | 验收 |
|------|------|------|------|
| **PA-1** | 路径 A 分项指标 + Layer 1 合成 + schema | `aesthetic_score.py` + ingest 接线 | golden trip 上分项分布合理；CPU 耗时 < ingest 既有预算 |
| **PA-2** | U-COVER / U-HERO 接入 overall | 改 `_quality_multiplier` / hero 排序键 | 盲评：新封面/主图 ≥ 旧选择（A/B） |
| **PA-3** | U-SOLO 新增 | `solo_scoring.py` + 排版调用 | 单张强调命中率人评提升 |
| **PA-4（可选）** | 路径 B topiq 校准 | curate 阶段开启 | overall 与人评相关性（SRCC）提升 |
| **PA-5（可选）** | 路径 C MLLM 点评 | 接口 + 缓存 + fail-open | 点评可读性人评 ≥ 阈值；成本可控 |

---

## §8 验收与度量

- **离线相关性**：在标注子集上算 overall 与人评的 Spearman SRCC（对齐 NIMA 评测口径）。
- **盲评 A/B**：U-COVER / U-HERO / U-SOLO 的 top-1 选择对比旧逻辑（人工 2 选 1）。
- **稳健性**：缺信号、极端曝光、无 OpenCV、无 torch 时均 fail-open 不崩（对齐 §0.3）。
- **性能**：Layer 1 单图 CPU 增量耗时纳入 `pipeline.timings` telemetry。
- **可解释**：每张照片可输出 top-3 维度因子（供 Studio 展示）。

---

## §9 开放问题

1. **权重从哪来**：先用经验权重，是否后续用小规模人评数据做轻量拟合（避免重训大模型）？
2. **U-SOLO 的 uniqueness**：无 CLIP 时用 ΔE 色调代理是否足够，还是默认要求开启 vision？
3. **MLLM 成本**：是否仅对"已通过 cull 的候选池"调用（而非全量），以控成本？
4. **人像 trip**：人像主导行程下，审美权重是否要把 `subjectClarity/composition` 上调（沿用 `resolve_person_demote` 的人像占比判断）？

---

## §10 变更记录

| 版本 | 日期 | 说明 |
|------|------|------|
| v0.1 | 2026-06-05 | 初版草案：三层架构 + 分项指标 + 集成点 + 分阶段计划 |
