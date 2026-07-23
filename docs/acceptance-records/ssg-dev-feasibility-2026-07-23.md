# SSG · 开发负责人实施前可行性调研

| 属性 | 内容 |
|------|------|
| **日期** | 2026-07-23 |
| **角色** | 开发负责人（落地 PR-A→F · 落实 [PRD SSG v0.2.0](../PRD-SMART-SHOT-GROUPING-V1.md)） |
| **材料** | PRD v0.2.0 · [七席评审](./ssg-smart-shot-grouping-v1-review-2026-07-23.md) · 现网代码探查 |
| **结论** | **M0/M1 可 Kickoff**；SUP-01～10 **产品已会签**（2026-07-23）并回写 PRD **v0.2.1** |
| **状态** | active · 已转入实现分支 `feature/smart-shot-grouping-v1` |

---

## 0. 一句话

PRD 方向与管线事实对齐，七席也收口了「分镜≠章 / 双痛点分 M1·M2」；但作为落地负责人，我认为 **v0.2 仍有三处「看起来写清、对照代码会翻车」的合同缺口**——（1）豁免白名单与 LTE `slot.role` **不是同一命名空间**；（2）`near_scene_clone_gate` 默认 **off** 与「硬契约」语义未钉单一真相；（3）M2 误把 `face_crop_embedding` 当成外观向量会直接做错。若不在 PR-A 补丁里钉死，M1 会做出假绿门、M2 会做出假 look。

---

## 1. 总判断

| 维度 | 评分 | 说明 |
|------|------|------|
| 问题真伪 | ✅ | 混导假切条 / 换装粘组与现网「时间 clone + 无造型」一致 |
| 与 Phase3 边界 | ✅ | 投影层独立；不抢章 |
| M0 可开工性 | ✅ | 文档 · schema 草案 · fixture 契约 · SUP 回写 |
| M1 可开工性 | ⚠ | 挂点齐；须先补豁免映射 + gate 配置真相 + Stage Literal |
| M2 合同完备度 | ⚠ | 上半身 crop / CLIP-ROI **无现成 API**；脸框不持久化 |
| Studio 融入风险 | 低 | `run_trip(from=clustering, until=structure)` 会自然扫到新 stage |
| 测试债 | 中 | 需新建 `shot-grouping` fixture；扩 burst / clone / orchestrator 测 |
| 默认用户无感 | 已知 | vision 默认 false → 强分镜仅验收/狗粮路径；产品已知情（D-20） |

---

## 2. 无缝融入：推荐架构（对照代码裁定）

```text
ingest
  → clustering              # 不变：segments + 可选 sceneClusterId
  → shot_grouping           # NEW · 投影 shotGroup（独立 stage）
  → curate                  # 章仍吃 segments；屏序读 shotGroupId
  → layout / mosaic         # 扩展 near_scene_clone_*（不平行方言）
```

### 2.1 为何必须独立 stage（禁止 clustering 尾钩）

| 依据 | 说明 |
|------|------|
| 合同 | D-SSG-16 / BLK-04 已锁显式 stage |
| 编排 | `from_stage` 依赖 `stages_order` 字面量；非法名会 `start_idx=0` **误从 ingest 重跑** |
| 隔离 | clustering 有 vision timeout / 丢线程语义；投影不应绑进 `_work()` |
| 运维 | `reshotgroup` 可单独重跑；telemetry 独立键 |
| Studio | `until=structure→curate` 已覆盖插入区间，**无需改 studio_pipeline 调用序** |

### 2.2 精确挂点清单

| # | 文件 | 改动 |
|---|------|------|
| 1 | `travelogue/domain/pipeline_view.py` | `Stage` Literal 增加 `"shot_grouping"`；`STAGE_MIN_STATUS`=`ingest_ready`（同 clustering） |
| 2 | `travelogue/orchestrator/run.py` | `stages_order` 插入；`elif stage == "shot_grouping"`；fail-open；timings；hint「整理分镜…」 |
| 3 | **新建** `travelogue/curation/shot_grouping.py` | `run_shot_grouping_layer(trip, trip_dir, cfg)` |
| 4 | **新建** `travelogue/config/shot_grouping.py` | `ShotGroupingConfig` + from_dict；挂 `AppConfig` / loader |
| 5 | `travelogue/curation/cluster_run_sort.py` | burst **不动**；插入 `shotGroupId` run（先于 sceneCluster） |
| 6 | `travelogue/curation/clustering_buckets.py` | sort gate：有 shotGroup **或** sceneCluster 即启用 run_aware |
| 7 | `layout_engine/mosaic/clone_detection.py` | 优先读 `shotGroupId`；无则回退时间启发式 |
| 8 | `layout_engine/mosaic/candidates.py` | 切条类硬拒扩展（仍走现 gate 路径） |
| 9 | `schemas/trip.schema.json` | asset 三字段 + `tripCuration.shotGrouping`（**勿**塞进 `clustering`，其 `additionalProperties:false`） |
| 10 | `cli/cluster.py` 邻接 / pipeline help | `reshotgroup`；`--from` 补字面量 |

**明确不改**：章 merge/cap、narrate、MSA/MTSO KPI、Keep-All 丢片逻辑。

### 2.3 Studio / CLI / Refine 行为矩阵

| 路径 | 是否跑 SSG | 备注 |
|------|------------|------|
| Studio `from=clustering, until=structure` | ✅ 会 | 插入 stage 即生效 |
| CLI 默认 `StudioProfile.run_clustering=False` | ⚠ clustering skip | SSG 应 fail-open 空分镜；或跟随 `shotGrouping.enabled` |
| `handle_trip_curate` 只 `run_curate` | ❌ 不重投影 | 与 OQ-03 一致；分镜可能陈旧可接受 |
| `cluster recluster` | 今日只 clustering | M1 后链式 `reshotgroup` 或文档写清 |
| tier / 精选升降 | ❌ | 不触碰 SSG |

---

## 3. 代码对照：PRD 主张 vs 现实

| # | PRD / 七席主张 | 代码现实 | 风险 | 开发建议 |
|---|---------------|----------|------|----------|
| **C-01** | 独立 stage | `stages_order` 无该槽；`Stage` Literal 未含 | 非法 from_stage 重跑 ingest | PR-B 第一步改 Literal+order |
| **C-02** | 复用 sceneCluster | vision 成功才有字段；失败时常**缺席**（≠`-1`） | weak 规则歧义 | IMPL 写死：缺席→不写强分镜；`-1`→weak |
| **C-03** | 扩 near_scene_clone | `NearSceneCloneGateConfig` **仅** `enabled`，**默认 false**；软罚始终在 scorer | 「硬契约」默认不生效 | SUP-03：验收/狗粮 snippet 强制 gate on；或 SSG on 时 gate 跟随 |
| **C-04** | 切条类=`prefers_burst:false` | candidates 已用 `is not True`；与 BLK-01 对齐 | 另造名单会双标准 | **操作定义=现网判定**；4mix 硬编码 False 已覆盖 |
| **C-05** | 豁免 cover/moment/… | LTE slot.role 是 `main/portrait/landscape/tile`——**没有**五白名单名 | AC-04/19 假绿或误杀 | **SUP-01 映射表**（见 §5） |
| **C-06** | 屏序叠加 shotGroup | `cluster_run_sort` 只 burst→sceneCluster | 优先级合同落空 | PR-B 必改；基线测 `test_burst_priority.py` |
| **C-07** | cohort 作 M2 轨 | `apply_cohort_tags` 需 featuredSubjects≥2 | 七席已否；勿回潮 | 默认主脸重检；cohort 可选 |
| **C-08** | 上半身 crop + CLIP | **无** torso API；`face_crop_embedding`=64×64 flatten **非 CLIP** | M2 用错 API | 新建 ROI encode；禁复用 face_embed 当外观 |
| **C-09** | 脸面积比 D-19 | ingest 多只落 `faceCount`；框常不持久 | 每次重检 | M2 接受重检；无 OpenCV→skip look |
| **C-10** | `curation.shotGrouping` | schema 严；塞进 clustering 会 L1 失败 | 合入红 | 父对象挂 `tripCuration.properties` |
| **C-11** | timings `shot_grouping` | 现网习惯 `clusterMs`/`embedMs` camel | 遥测对账乱 | **SUP-04**：统一 `shotGroupingMs` |
| **C-12** | Studio 无需大改 | `studio_pipeline` 已 orchestrator 扫 stage | 低 | 仅 hint 文案；可选 `run_shot_grouping` |

---

## 4. M1 算法落地草图（最小 diff）

### 4.1 投影（`shot_grouping.py`）

```text
if shotGrouping.enabled 解析为 off → return
if 无任何有效 sceneClusterId（非缺席且非全噪声可聚类失败）→ fail-open 不写强组
按 sceneClusterId 分组（跳过缺席）
  组内按 takenAt
  间隙 > timeSoftSplitHours → 拆子段
  每段赋 shotGroupId / kind=scene
sceneClusterId==-1 → kind=weak（可时间近邻合并）
minShotGroupSize：仅合并 scene/weak；look 不适用（M1 无 look）
写 curation.shotGrouping + asset 字段
```

### 4.2 屏序

```text
burst 整组（sharpness） > shotGroupId 邻接 run > sceneClusterId run > takenAt
```

### 4.3 Mosaic 门（扩现有，不平行）

```text
candidates 硬拒（gate 有效时）:
  template_prefers_burst is not True
  AND 窗内存在 ≥2 个不同非空 shotGroupId
  AND 窗目的不在豁免映射（SUP-01）
  → reject reason: shot_group_cross / 或复用 near_scene_clone + detail

同组 sameGroupAntiSlice:
  同 shotGroupId + 原时间窗假切条特征 → 硬拒或高罚（切条类）

无 shotGroupId:
  回退今日 near_scene_clone_penalty
```

合法混拼（`prefers_burst is True` / 非切条）→ **不硬拒**（AC-19）。

---

## 5. 必须补进 PRD/IMPL 的合同（SUP · 开发挡门）

| ID | 缺口 | 冻结建议（开发案） | 挡 |
|----|------|-------------------|----|
| **SUP-01** | 豁免五名 ≠ LTE role | 映射写死：`cover`→cover/opening 屏；`moment`→moment pattern / momentAssetId 屏；`chapterHero`→章英雄单图；`solo`→单图全幅屏；`bookend`→opening/closing bookend。判定函数：`screen_exempt_from_shot_group_hard_reject(screen_ctx) -> bool`，**禁止** `slot.role in whitelist` | M1 |
| **SUP-02** | slice 作用域 | 操作定义：`template_prefers_burst(pid) is not True`（与 candidates 现逻辑一致） | M1 |
| **SUP-03** | gate 默认 off | SSG 验收/狗粮：`near_scene_clone_gate.enabled=true` **且** vision on；或 `shotGrouping.enabled=true` 时 candidates 硬拒路径自动视为 on（二选一，推荐后者减少双开关） | M1 |
| **SUP-04** | timings 键 | 落盘 `pipeline.timings.shotGroupingMs`；日志可读 `shot_grouping` | M0 |
| **SUP-05** | sceneCluster 缺席 vs -1 | 缺席=无强分镜；`-1`=weak；禁止把缺席当噪声熔炉 | M1 |
| **SUP-06** | 配置单一真相 | 行为扩展挂 `near_scene_clone_*`；`shotGrouping.mosaic.*` 为意图开关，由同一 helper 读取 | M1 |
| **SUP-07** | StudioProfile | 新增 `run_shot_grouping: bool`（Studio True / CLI 跟随 clustering 或 enabled）；避免 CLI 静默跳过难测 | M1 |
| **SUP-08** | sort gate | 仅有 shotGroup、无 sceneCluster 时仍启用 run_aware | M1 |
| **SUP-09** | M2 embed | 明文：**CLIP on upper-body ROI**；禁止 `face_crop_embedding` 充当外观 | M2 |
| **SUP-10** | 验收配置样例 | `config-ssg-dogfood.example.yaml`：vision on + shotGrouping + gate | M0 |

**产品请在 Kickoff M1 前对 SUP-01/03 二选一拍板。**

---

## 6. 分 PR 落地建议

### 6.1 PR-A / M0（建议立即开工）

1. IMPLEMENTATION + ACCEPTANCE 骨架  
2. schema 草案（父对象 + asset 字段）  
3. `tests/fixtures/shot-grouping/mixed-scenes-*` · `outfit-change-*` 契约（可先 manifest+期望 JSON）  
4. 本文 SUP-01～10 回写 PRD 小版本或 IMPL「合同补丁」章  
5. `config-ssg-dogfood.example.yaml`  
6. DOC-STATUS  

**不做**：业务投影码。  
**工期**：2–3 人日。

### 6.2 PR-B / M1 核心（SUP 拍板后）

1. Stage Literal + orchestrator 分支（fail-open）  
2. `shot_grouping.py` scene 投影  
3. `ShotGroupingConfig`  
4. `cluster_run_sort` + buckets gate  
5. mosaic 门 + SUP-01 豁免函数  
6. 单测：burst 优先 · 跨组硬拒 · 混拼不误杀 · deterministic  

**工期**：5–7 人日。

### 6.3 PR-C / M1 收尾

telemetry · NR off · Studio hint · CLI `reshotgroup` / `--from` help · AC-07/08/09/18  

**工期**：2–3 人日。

### 6.4 PR-D～E / M2

主脸轨 · torso crop · CLIP ROI · cache · 阈值 spike（F1≥0.70）  

**工期**：6–9 人日（含标定）；前置 SUP-09。

### 6.5 PR-F / M3

狗粮盲评 · 开关文案 · 默认 on 决策  

---

## 7. 工期总表（现实）

| 阶段 | 人日 | 备注 |
|------|------|------|
| M0 / PR-A | 2–3 | 含 SUP 回写 |
| M1 / PR-B+C | 7–10 | 视豁免映射复杂度 |
| M2 / PR-D+E | 6–9 | ROI CLIP 为最大未知 |
| M3 / PR-F | 2–4 | 盲评日历另计 |
| **合计** | **17–26** | 不含默认 vision on 产品决策 |

---

## 8. 风险与回滚

| 风险 | 等级 | 缓解 |
|------|------|------|
| 豁免映射做错 → 误杀杂志混拼 | **高** | SUP-01 + AC-19 负例 |
| gate 默认 off → 硬契约假绿 | **高** | SUP-03 |
| M2 用错 face_embed | **高** | SUP-09 代码评审门 |
| vision 默认 off → 用户无感 | 中 | 产品已知；狗粮路径强制 on |
| 过碎致候选枯竭 | 中 | minShotGroupSize + fallback 率 |
| refine 后分镜陈旧 | 低 | V1 接受；文档诚实 |
| from_stage 拼错重跑 ingest | 中 | Literal + CLI help + 单测 |

**回滚**：`shotGrouping.enabled=false` → 不写字段；mosaic 回退时间启发式；章不变。

---

## 9. 开发负责人决议（请产品会签 SUP）

| # | 决议 |
|---|------|
| **R1** | 独立 stage，禁止 clustering 尾钩 |
| **R2** | 扩 `near_scene_clone_*`，禁止第二套 clone 方言 |
| **R3** | M1 合码前必须关闭 SUP-01/03/05/06 |
| **R4** | M2 不得以 cohort/featuredSubjects 为默认轨 |
| **R5** | 默认 GA 不强制 vision on；验收用 dogfood yaml |
| **R6** | 列车：PR-A → B → C → D → E → F；禁单 PR 塞满 |

---

## 10. 签名 / 会签

| 角色 | 意见 | 日期 |
|------|------|------|
| 开发负责人 | **M0/M1 Go · 按 SUP 落地** | 2026-07-23 |
| 产品 | ✅ **认可 SUP-01～10**（会签） | 2026-07-23 |
| 架构 | ✅ 同意 R1/R2 | 2026-07-23 |

---

## 附录 · 关键现网锚点（速查）

| 主题 | 路径 |
|------|------|
| stages | `orchestrator/run.py` · `domain/pipeline_view.py` |
| clustering | `curation/clustering.py` · `scene_clusters.py` |
| 屏序 | `curation/cluster_run_sort.py` · `clustering_buckets.py` |
| clone 门 | `mosaic/clone_detection.py` · `candidates.py` · `config/mosaic.py` |
| Studio | `web/studio_pipeline.py`（~L1087–1122） |
| 脸 | `media/face_embed.py` · `curation/cohort_faces.py` |
| 测 | `tests/unit/curation/test_burst_priority.py` · `tests/unit/layout_engine/test_near_scene_clone_penalty.py` |
