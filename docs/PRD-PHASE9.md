# Travelogue · Phase 9 产品需求文档（PRD · 总览）

| 属性 | 内容 |
|------|------|
| **产品代号** | Travelogue |
| **文档版本** | v0.9.1-PHASE9 |
| **状态** | **W1 Done**（G-P9-W1 已闭合 · 2026-06-02）· W2 可选进行中 |
| **Phase 9 代号** | 「排版前闸口」— Quality Gate · 静默筛选 · 为智能排版准备干净资产池 |
| **前置条件** | Phase 2 Studio 导入管线可用；Phase 7 ingest 性能基线已登记；[PRD-EXPERIENCE-附录A-精选上传.md](./PRD-EXPERIENCE-附录A-精选上传.md) 双文件夹 ingest 已落地或并行 |
| **交付形态** | 用户选文件夹 / 上传后，**后台静默**完成照片评价与筛选；仅一行摘要提示「经挑选 N 张进入排版」；被筛照片 **不可见**、不可恢复（MVP） |
| **关联文档** | 子文档见 §2；下游 [PRD-PHASE10-food-grid.md](./PRD-PHASE10-food-grid.md)、规划 [PRD-PHASE8-photo-semantic-clustering.md](./PRD-PHASE8-photo-semantic-clustering.md)；[AGENT-ARCHITECTURE.md](./AGENT-ARCHITECTURE.md)、[智能排版V2.md](./智能排版V2.md) §14.2 Step 0、[DATA-MODEL.md](./DATA-MODEL.md) |
| **更新日期** | 2026-06-02 |

> **定位说明**
>
> - Phase 9 在 **Agent 0 · 媒体工坊** 内新增 **Quality Gate（0c）**：在 curate / 聚类 / 排版之前，从非职业摄影师的杂乱素材中筛出 **可排版资产池**。
> - 与 Phase 3 聚类 **分工明确**：Phase 9 决定 **谁进池**；Phase 3/8 决定 **池内如何理解与分组**。
> - 本 Phase **不新增** 用户浏览被筛照片的 UI；**不实现** 11 类语义聚类（Phase 8）与 food grid 组屏（Phase 10）。

---

## 1. 背景与问题陈述

### 1.1 现状

当前 ingest 已具备：MD5/pHash 去重、连拍合并（保留更清晰帧）、`mediaClass` 启发式、`quality.sharpness`、低分辨率相对剔除（`layoutEligible=false`）、OpenCV 人脸检测。

**缺口**：缺少 **美学 / 失焦 / 批次相对质量** 的软筛选；非 featured 的 **连拍废片、模糊片、无意义截图** 仍大量进入 curate，拖累组屏质量与用户「这本游记怎么这么多糊图」的主观感受。

### 1.2 Phase 9 要解决的断裂点

| 断裂 | 现状 | Phase 9 目标 |
|------|------|--------------|
| **断裂 A · 准入** | 仅低分辨率 + mediaClass 硬规则 | **减噪 + 轻精选**，保留率 **≥80%**（全库 scanned 口径） |
| **断裂 B · 用户意图** | featured 仍可能被 layout 规则误伤 | **featured 全豁免**（任意精选目录导入） |
| **断裂 C · 管线顺序** | dedupe 与 cap 交织 | **scan → dedupe → cull → low-res → cap** 明确顺序 |
| **断裂 D · 下游信号** | `subject_tagging` 不读 CLIP `subjectClass` | **Wave 3 桥接**，解锁 Phase 10 food grid |
| **断裂 E · 可感知** | ingest 报告偏工程 | **人话摘要**一行 + 可选分项（CLI / Job 完成态） |

### 1.3 已拍板决策（D-P9）

| ID | 决策 | 结论 |
|----|------|------|
| **D-P9-01** | 筛选强度 | **减噪 + 轻精选**；非 featured 保留率地板 **≥80% × N_scan** |
| **D-P9-02** | 80% 分子 | **仅计非 featured** 的 `layoutEligible`；featured **不计入分子**，全豁免 |
| **D-P9-03** | featured 豁免 | 任意 `featured_dir_names` 导入 → **永不** `layoutEligible=false` |
| **D-P9-04** | 被筛可见性 | **不可见**；无 Studio 回收 UI（MVP） |
| **D-P9-05** | ML 部署 | 可选 `[vision]`；无 GPU / 未安装 → **自动降级 P0 规则** |
| **D-P9-06** | max_photos 冲突 | **方案 B**：featured 全留；允许 layout 池 **超过 250** 并 **WARN** |
| **D-P9-07** | 文档拆分 | 算法 / 管线 / 数据 / UX / 桥接 **分册**（§2） |
| **D-P9-08** | 阶段编号 | 本 Phase = **9**；food grid = **Phase 10**；11 类语义 = **Phase 8** |
| **D-P9-09** | W1 发版范围 | **W1 独立发版**（`cull.mode=rules` 默认）；W2 ML **不阻塞** W1 |
| **D-P9-10** | 增量 cull 范围 | **全 trip re-cull**（每次 ingest 结束对 `trip.assets` 全量） |
| **D-P9-11** | `layout_eligible_assets` | **必须**读 `asset.layoutEligible`（W1 前置 · M30-0a） |
| **D-P9-12** | Pass 1 exposure | **W1 不做** R-P9-03；W2+ 再评估 |
| **D-P9-13** | 80% 未达标 | Pass 1–2 保守；池已低于 floor 则 Pass 3 跳过并 **接受**（见 P9-A §3.4） |
| **D-P9-14** | cull 异常 | **Fail-open**：全员 eligible + `cullSummary.error` + Job 仍 success |
| **D-P9-15** | cullUserLine 展示 | 现有成功 toast **下追加第二行**（不替换主文案） |
| **D-P9-16** | golden 回归 | **cull-on 为新基线**；mao/maomi 人工签 off（NR-P9-04） |

### 1.4 Kickoff 修订摘要（v0.9.1）

2026-06-02 开发评审结论已写入各分册，要点：

- **M30-0a**：`layout_eligible_assets()` 及所有 curate/cluster 入口统一读 `asset.layoutEligible`
- **增量 ingest**：每次 `_finalize_ingest_assets` 对 **全 trip** re-cull（非单 batch）
- **Pass 分工**：ingest dedupe 保持现状；cull Pass 2 主攻 **featured 混合组** + recalc 安全网
- **W1 范围**：无 exposure_extreme、无 pyiqa；**W1 可独立发版**
- 验收见 [ACCEPTANCE-PHASE9.md](./ACCEPTANCE-PHASE9.md)

---

## 2. 文档体系（分册索引）

| 文档 | 代号 | 内容 |
|------|------|------|
| **本文** | P9-00 | 总览、目标、决策、波次、验收索引 |
| [PRD-PHASE9-A-quality-gate-algorithm.md](./PRD-PHASE9-A-quality-gate-algorithm.md) | P9-A | Pass 1–4 算法、评分、80% 公式、featured、P0/P1 ML |
| [PRD-PHASE9-B-pipeline-integration.md](./PRD-PHASE9-B-pipeline-integration.md) | P9-B | Agent 0 管线顺序、与聚类/curate 衔接、config、降级 |
| [PRD-PHASE9-C-data-model.md](./PRD-PHASE9-C-data-model.md) | P9-C | `trip.json` 字段、`excludeReason`、`cullSummary`、schema |
| [PRD-PHASE9-D-studio-ux.md](./PRD-PHASE9-D-studio-ux.md) | P9-D | Importing stageHint、完成摘要、WARN 文案；**无** 被筛图 UI |
| [PRD-PHASE9-E-subject-bridge.md](./PRD-PHASE9-E-subject-bridge.md) | P9-E | Wave 3：`subject_tagging` 消费 CLIP `subjectClass` |
| [IMPLEMENTATION-PHASE9.md](./IMPLEMENTATION-PHASE9.md) | — | 里程碑 **M30** 任务清单与文件映射 |
| [ACCEPTANCE-PHASE9.md](./ACCEPTANCE-PHASE9.md) | — | W1/W2/W3 验收与 NR-P9 |

**下游（另立 PRD，不在本 Phase 实现范围）**

| 文档 | 说明 |
|------|------|
| [PRD-PHASE8-photo-semantic-clustering.md](./PRD-PHASE8-photo-semantic-clustering.md) | 11 大类 L1 + L2 子簇 · **依赖 Phase 9 完成后** |
| [PRD-PHASE10-food-grid.md](./PRD-PHASE10-food-grid.md) | mundane 食物 grid 组屏 · **依赖 Phase 9 Wave 3** |

---

## 3. 目标与非目标

### 3.1 产品目标

| ID | 目标 | 衡量方式 |
|----|------|----------|
| **G-P9-01** | 非 featured 保留率 **尽量 ≥80% × N_scan** | mao fixture；若 Pass 1–2 后池已低于 floor 则记录 `cullSummary.floorNotMet` 仍通过 W1（见 P9-A §3.4） |
| **G-P9-02** | featured **100%** layoutEligible | 双文件夹 fixture 零误杀 |
| **G-P9-03** | 用户 **无感** 完成筛选 | 无新页面；仅 stageHint + 完成一行摘要 |
| **G-P9-04** | 下游只消费统一入口 | curate/cluster/cover 仅读 `layoutEligible` |
| **G-P9-05** | P0 无 GPU 可交付 | `cull.mode=rules` 全绿 pytest |
| **G-P9-06** | P1 vision 增强不误杀 | 同 fixture 保留率 **不低于** P0 −2% |
| **G-P9-07** | 桥接解锁 food grid | `subject_class_for_asset` 读 CLIP 字段 · 见 P9-E |

### 3.2 非目标

- 被筛照片 Gallery / 恢复 / 用户手动 override（MVP）。
- 11 类 CLIP prompt 扩展（Phase 8）。
- `try_food_grid` 组屏（Phase 10）。
- 改写 curate 章序、叙事、模板渲染。
- 云端推理或第三方 Facet 整包集成。
- featured 因 **截图/损坏** 硬删（默认 **全豁免**，见 P9-A §4.3）。

---

## 4. 用户故事

| ID | 故事 | 验收 |
|----|------|------|
| **US-P9-01** | 作为旅行者，我丢进一个含 200 张手机照的文件夹，系统自动去掉连拍废片和明显糊片，我不需要额外操作 | Job 成功；摘要含「经挑选 **N** 张进入排版」 |
| **US-P9-02** | 作为用户，我在「精选」里放了 12 张搞怪照，它们必须全部进排版 | 12/12 featured layoutEligible |
| **US-P9-03** | 作为用户，我不想知道哪些被删了 | Studio **无** 被筛列表 |
| **US-P9-04** | 作为维护者，我需要在 CLI 看到分项统计 | `format_ingest_report` 含 cull 分项 |

---

## 5. 系统位置（Agent 架构）

```text
Agent 0 · 媒体工坊
  0a  scan / decode / WebP / metadata
  0b  dedupe（md5 · phash · burst）
  0c  ★ Quality Gate（Phase 9）
  0d  low-res layoutEligible（现有 asset_quality）
  0e  max_photos advisory cap（方案 B · featured 优先）

Clustering（Phase 3）— 仅 layoutEligible 资产
Curate / Layout（Phase 1 / 1.5 / 10）
```

权威交互：**[PRD-PHASE9-D-studio-ux.md](./PRD-PHASE9-D-studio-ux.md)**。  
权威算法：**[PRD-PHASE9-A-quality-gate-algorithm.md](./PRD-PHASE9-A-quality-gate-algorithm.md)**。

---

## 6. 交付波次（Waves）

| 波次 | 内容 | 文档 | 出口 |
|------|------|------|------|
| **W1 · P0** | Pass 1–4 规则闸口 + **M30-0a layoutEligible 统一** + UX 摘要 | P9-A/B/C/D | pytest + demo + NR-P9-04 签 off |
| **W2 · P1** | pyiqa 美学 + InsightFace（**可选发版**） | P9-A/B | `[vision]` extra |
| **W3 · 桥接** | `subject_tagging` 读 `subjectClass` | P9-E | 解锁 Phase 10 |

**建议工期**：W1 1–2 周 · W2 1–2 周 · W3 2–3 天（可与 W2 并行收尾）。

---

## 7. 配置入口（摘要）

完整键见 [PRD-PHASE9-B-pipeline-integration.md](./PRD-PHASE9-B-pipeline-integration.md) §4。

```yaml
cull:
  enabled: true
  mode: auto              # rules | ml | auto
  keep_ratio_floor: 0.90  # 相对 N_scan
  min_keep: 15
  featured_exempt: true
  max_photos_warn_only: true   # 方案 B
  hard_exclude_media_classes: [screenshot, thumbnail, reupload]
  featured_hard_exclude: false # 默认 featured 连 screenshot 也保留
```

---

## 8. 验收索引

| 类别 | 文档章节 |
|------|----------|
| 算法正确性 | P9-A §8 · `tests/test_photo_cull.py` |
| 80% 地板 | P9-A §3.3 |
| featured 豁免 | P9-A §4 |
| 管线顺序 | P9-B §2 |
| schema | P9-C §6 |
| Studio 文案 | P9-D §5 · AC-P9-UX-* |
| 桥接 | P9-E §4 |
| 回归 | NR-P9-01～04 · [ACCEPTANCE-PHASE9.md](./ACCEPTANCE-PHASE9.md) |

---

## 9. 风险与降级

| 风险 | 缓解 |
|------|------|
| 误杀好片 | 80% 地板 + min_keep；P1 仅加权不硬删 featured |
| featured 200 张撑爆排版 | WARN + 方案 B 超 cap；curate 采样后续 Phase |
| pyiqa 慢 | W1 默认 `mode=rules`；W2 再开 auto/ml |
| cull 异常 | fail-open（D-P9-14） |
| 与附录 A 冲突 | D-P9-03 优先；附录 A §3.2 已修订 |

---

## 10. 修订记录

| 版本 | 日期 | 说明 |
|------|------|------|
| v0.9.2 | 2026-06-02 | W1 Done · G-P9-W1 闭合；Phase 10 仍不在实现范围 |
| v0.9.1 | 2026-06-02 | Kickoff 修订：D-P9-09～16 · ACCEPTANCE-PHASE9 |
| v0.9.0 | 2026-06-02 | 初稿：分册 PRD + 已拍板 D-P9-01～08 |
