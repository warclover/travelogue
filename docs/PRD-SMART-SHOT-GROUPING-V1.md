# Travelogue · 智能分镜 V1 产品需求文档（PRD）

| 属性 | 内容 |
|------|------|
| **产品代号** | Travelogue Studio |
| **文档版本** | **v0.2.1** |
| **状态** | **Conditional Go · M0/M1 可 Kickoff**（[七席](./acceptance-records/ssg-smart-shot-grouping-v1-review-2026-07-23.md) · [开发可行性](./acceptance-records/ssg-dev-feasibility-2026-07-23.md) · **SUP-01～10 产品会签 2026-07-23** · **M2 合码前关 BLK-SSG-03**） |
| **DOC-STATUS** | **active** |
| **主题代号** | 「智能分镜 V1」— **SSG**（Smart Shot Grouping） |
| **调研来源** | 2026-07-23 用户需求确认（混导拼图乱 / 同景点换装须拆组）· 聚类能力对照 · 业界 CLIP 场景簇 / Photo Stacks / 服装连续性实践 · [RESEARCH-TRAVEL-PHOTO-AUTO-LAYOUT-V1](./RESEARCH-TRAVEL-PHOTO-AUTO-LAYOUT-V1.md) |
| **审查基线** | Phase 3 ClusteringLayer（geo + 可选 CLIP scene）· mosaic `near_scene_clone` 时间启发式 · ADR-012 L2 暂缓 · vision 默认 off · cohort 需 featuredSubjects |
| **关联文档** | [PRD-PHASE3](./PRD-PHASE3.md) · [ADR-007](./adr/007-native-clustering.md) · [ADR-012](./adr/012-semantic-tagging-p8-p12-split.md) · [PRD-PHASE12](./PRD-PHASE12.md) · [P15 MCS](./PRD-PHASE15-photo-mosaic-evolution.md) · [MSA](./PRD-MOSAIC-SLOT-ADAPTATION-V1.md) · [MTSO](./PRD-MOSAIC-TEMPLATE-SELECTION-OPTIMIZATION-V1.md) · [Keep-All](./PRD-KEEP-ALL-PHOTOS-V1.md) · [NAS](./PRD-NO-AI-SURFACE-V1.md) · [DATA-MODEL](./DATA-MODEL.md) · [algorithm-inventory](./algorithm-inventory.md) |
| **评审纪要** | [ssg-smart-shot-grouping-v1-review-2026-07-23.md](./acceptance-records/ssg-smart-shot-grouping-v1-review-2026-07-23.md)（结案）· [模板](./acceptance-records/ssg-smart-shot-grouping-v1-review-TEMPLATE.md) |
| **验收** | [ACCEPTANCE-SMART-SHOT-GROUPING-V1.md](./ACCEPTANCE-SMART-SHOT-GROUPING-V1.md) · [IMPLEMENTATION-SMART-SHOT-GROUPING-V1.md](./IMPLEMENTATION-SMART-SHOT-GROUPING-V1.md)；摘要见本文 §8 |
| **更新日期** | 2026-07-23 |

> **v0.2.1 相对 v0.2.0（开发可行性 SUP 会签 · 2026-07-23）**
>
> 产品认可 [ssg-dev-feasibility](./acceptance-records/ssg-dev-feasibility-2026-07-23.md) **SUP-01～10**，写入 §3.1 / D-SSG-17b～22：  
> 豁免为**屏级映射**（非 LTE `slot.role`）；slice 作用域=`prefers_burst is not True`；`shotGrouping` 生效时硬拒路径跟随 on；timings=`shotGroupingMs`；sceneCluster 缺席≠`-1`；M2 明文 CLIP-on-torso。

> **v0.2.0 相对 v0.1.0（七席回写 · 2026-07-23）**
>
> 1. **BLK-01**：mosaic 硬拒作用域收窄为「切条/假一条」类 pattern；合法杂志混拼可跨组同窗。  
> 2. **BLK-02**：AC 数值门锁进合同（同组率≥0.85 · 假切条↓≥40% · look F1≥0.70）。  
> 3. **BLK-03**：M2 默认主脸轨，**不**依赖 `intent.featuredSubjects`；cohort 仅可选增强。  
> 4. **BLK-04**：`stages_order` 显式 `"shot_grouping"`。  
> 5. **BLK-06/07/08**：豁免白名单写死；配置键唯一；`curation.shotGrouping` 父对象。  
> 6. OQ-01～05 本场关闭或暂定（见 §10.2）。

> **定位**
>
> 用户一次导入多组旅行照片时，系统应自动形成**可拼图、可排版的分镜单元**——同场景不拆散、不同场景不强拼成「假一条」；同一景点换了多套衣服时，必须拆成不同分镜组。  
> 现有 ClusteringLayer 解决的是「**章与叙事骨架**」，**不是**「拼图该把谁放进同一格组」。
>
> 本 PRD 引入一等公民 **`shotGroup`（分镜组）**：在 ClusteringLayer **之后**投影，供 mosaic / 屏规划消费；不重写章边界，不替代 burst，不做用户可见「分镜工作台」（V1）。

> **一句话目标**：**混导不乱拼；同景不拆条；换装必分镜；本地可降级。**

> **完成定义**

| 门 | 含义 | 不等于 |
|----|------|--------|
| **M0 Go** | 术语/字段/优先级切清；双 golden 契约；ACCEPTANCE/IMPL 拆文；数值门写入 | 改默认 GA；开 vision 默认 on |
| **M1 Go** | scene→shotGroup；显式 stage；切条类硬契约；假切条↓≥40% | 服装/换装；Studio 分镜 UI |
| **M2 Go** | 主脸 look 边界；换装 F1≥0.70；同景点必拆组 | 服装品类识别；云 API；依赖 featuredSubjects |
| **M3 Go** | 狗粮盲评；开关；acceptance 闭环 | 默认强制 vision on（另决策） |

---

## 0. 读者指南与边界

### 0.1 与相邻主题

| 主题 | 关系 | 本主题做什么 |
|------|------|--------------|
| [Phase 3 Clustering](./PRD-PHASE3.md) | **上游生产者** | 继续产 `segments` / `sceneClusterId`；**不**用分镜重写 3–5 章 |
| [ADR-012](./adr/012-semantic-tagging-p8-p12-split.md) / [P12](./PRD-PHASE12.md) | **可选加强** | L1 仍作评分；若复活 L2，**仅**服务 shotGroup 细化 |
| [P15 MCS](./PRD-PHASE15-photo-mosaic-evolution.md) | **主消费者** | 扩展现有 `near_scene_clone_gate`；读 `shotGroupId` |
| [MSA](./PRD-MOSAIC-SLOT-ADAPTATION-V1.md) / [MTSO](./PRD-MOSAIC-TEMPLATE-SELECTION-OPTIMIZATION-V1.md) | **正交** | MSA=槽几何；MTSO=选模板；SSG=**谁该进切条窗** |
| [Keep-All](./PRD-KEEP-ALL-PHOTOS-V1.md) | **正交** | 分镜不丢片 |
| [NAS](./PRD-NO-AI-SURFACE-V1.md) | **继承** | 本地 CLIP；不上云 |
| [Portrait Cull](./PRD-PORTRAIT-CULL.md) / cohort | **M2 可选增强** | 默认主脸轨；cohort/featuredSubjects **非**前置 |

### 0.2 三层概念（禁止混称）

```text
trip
  └── chapters / events          ← 叙事章（geo/time · Phase 3 · cap 3–5）
        └── shotGroups           ← 分镜组（本主题）  kind: scene | look | weak
              └── burst groups   ← 连拍不可拆（最高优先级）
                    └── assets
```

| 名称 | 字段 | 问的问题 | 主消费者 |
|------|------|----------|----------|
| **章 / 行程段** | `eventId` · `chapters` · `segments` | 故事怎么分章？ | curate / narrate |
| **场景簇** | `sceneClusterId` | 视觉上像不像？ | run 输入；**SSG M1 源** |
| **分镜组** | `shotGroupId` · `curation.shotGrouping.groups[]` | **拼图/切条窗该不该在一组？** | mosaic / screen planner |
| **连拍** | `burstGroupId` | 几秒内同一瞬间？ | 不可拆屏 |

对外可称「智能分镜」；对内用 `shotGroup`。禁止对用户暴露 `sceneClusterId` / CLIP / HDBSCAN。

### 0.3 非目标（明确不做）

| ID | 非目标 | 理由 |
|----|--------|------|
| **N-SSG-01** | 用分镜重写 3–5 章 | 破坏 Phase 3 |
| **N-SSG-02** | V1 Studio 分镜工作台 | 零打扰；另立 PRD |
| **N-SSG-03** | 云端分镜 API | 本地优先 / NAS |
| **N-SSG-04** | 服装品类/品牌识别 | ROI 低 |
| **N-SSG-05** | 跨 trip 全局人脸库 | Out of Charter |
| **N-SSG-06** | 视频参与 CLIP/look | 继承 Phase 3 |
| **N-SSG-07** | 把 SSG 塞进 MTSO/MSA KPI | 正交 |
| **N-SSG-08** | 结案强制 vision 默认 on | 另决策 |
| **N-SSG-09** | 禁止一切跨 `shotGroupId` 同屏 | 误杀杂志混拼（见 D-05） |

### 0.4 代码事实（2026-07-23 · 七席确认）

| ID | 事实 |
|----|------|
| **F-01** | `stages_order`: ingest→clustering→curate→layout… |
| **F-02** | `VisionConfig.enabled` 默认 `"false"` |
| **F-03** | `run_aware` 仅屏序；mosaic 无 sceneCluster 硬拒 |
| **F-04** | `near_scene_clone` 纯时间 + `prefers_burst` |
| **F-05** | ADR-012：L2 暂缓 |
| **F-06** | 优先级现网：burst > sceneCluster run > takenAt |
| **F-07** | CLIP 缓存 `.cluster-cache/` |
| **F-08** | `apply_cohort_tags` **需** `intent.featuredSubjects`——**不可**作 M2 默认轨 |
| **F-09** | 现网 **无** `shot_grouping` stage（本主题新增） |
| **F-10** | mosaic 已有 `near_scene_clone_gate` 挂点（应扩展，不平行方言） |
| **F-11** | `cluster_run_sort` 须叠加读 `shotGroupId` |
| **F-12** | 分镜元数据用父对象 `curation.shotGrouping`，非仅数组 |

### 0.5 用户可感知问题 → 落点

| ID | 问题 | 严重度 | 里程碑 |
|----|------|--------|--------|
| **Q1** | 混导后同场景被拆成假切条 | **P0** | **M1** |
| **Q2** | 不同场景硬拼成假一条跳戏 | **P0** | **M1** |
| **Q3** | 同景点换三套衣服未分开 | **P0** | **M2** |
| **Q4** | vision 关时无强分镜 | **P1** | fail-open + 验收路径 on |
| **Q5** | 分镜过碎致候选枯竭 | **P1** | D-SSG-07 |

---

## 1. 背景与根因

### 1.1 两个痛点（均在 V1）

| 痛点 | 描述 | 解法层 |
|------|------|--------|
| **P-SSG-01** | 混导后拼图乱；同场景被拆；不同场景硬拼成假一条 | **M1 场景分镜** |
| **P-SSG-02** | 同一景点换三套衣服必须分开成组 | **M2 造型分镜** |

### 1.2 为什么「已有聚类」不够

| 已有能力 | P-SSG-01 | P-SSG-02 |
|----------|----------|----------|
| geo → 章 | 间接（过粗） | 否 |
| `sceneClusterId` + run_aware | 部分（非硬契约） | 否 |
| `near_scene_clone` | 弱近似 | 否 |
| cohort（featuredSubjects） | 间接 | **不可作默认**（F-08） |

---

## 2. 目标与成功标准

| ID | 目标 |
|----|------|
| **G-SSG-01** | `shotGroup` 合同与优先级切清 |
| **G-SSG-02** | **M1**：假切条↓≥40%；切条类跨组硬拒；合法混拼不误杀 |
| **G-SSG-03** | **M2**：同景点换装拆组；look F1≥0.70 |
| **G-SSG-04** | fail-open；不阻断 pipeline |
| **G-SSG-05** | Keep-All / NAS 兼容 |
| **G-SSG-06** | deterministic 双跑一致 |
| **G-SSG-07** | 验收/狗粮路径 **vision on**（产品默认另决策） |

---

## 3. 决策表（D-SSG-* · 七席锁定）

| ID | 决策 | 说明 |
|----|------|------|
| **D-SSG-01** | **分层不抢章** | 章仍 Phase 3 + curate |
| **D-SSG-02** | **投影层** | 新模块 `shot_grouping`；不重写 ClusteringLayer |
| **D-SSG-03** | **优先级** | `burst` **>** `look` **>** `scene` shotGroup **>** `sceneCluster` run **>** `takenAt` |
| **D-SSG-04** | **M1 源** | `kind=scene` ← `sceneClusterId` + **时间软切** |
| **D-SSG-05** | **硬契约作用域（修订）** | **仅**切条/假一条类 pattern（`prefers_burst:false` 或等价名单）对跨 `shotGroupId` **硬拒**；合法杂志混拼允许跨组同窗（评分约束）。**同组** `sameGroupAntiSlice` 始终硬 |
| **D-SSG-06** | **升级 clone 门** | 扩展现有 `near_scene_clone_gate`：优先读 `shotGroupId`；无分镜时回退今日时间启发式 |
| **D-SSG-07** | **防过碎** | `minShotGroupSize`（默认 2）合并弱 scene/weak；**look 边界不合并** |
| **D-SSG-08** | **M2 默认主脸轨（修订）** | 最大脸/主脸检测 → 上半身 crop → embedding；**不**要求 featuredSubjects。cohort 可选增强 |
| **D-SSG-09** | **M2 边界** | 轨内 Δ 持续越过阈值 → 新 look；**禁止**用 GPS 粘合换装 |
| **D-SSG-10** | **单次 forward 纪律** | 继承 G-P3-C05；批处理 + cache |
| **D-SSG-11** | **开关（修订）** | 仅 `shotGrouping.*`；`enabled: auto` = vision 可用且 scene 簇非空才写强 scene 分镜；`look.enabled: auto` |
| **D-SSG-12** | **用户不可见** | V1 无分镜列表 UI；hint 可用「整理分镜…」 |
| **D-SSG-13** | **L2 可选** | 仅服务 shotGroup 细化 |
| **D-SSG-14** | **Keep-All** | 不改变进册集合 |
| **D-SSG-15** | **噪声** | `sceneClusterId=-1` → weak；禁止噪声大熔炉 |
| **D-SSG-16** | **显式 stage** | `stages_order` 含 `"shot_grouping"`（clustering 后、curate 前） |
| **D-SSG-17** | **跨组豁免白名单（V1 写死）** | 逻辑名：`cover` · `moment` · `chapterHero` · `solo` · `bookend`；禁止「等」 |
| **D-SSG-17b** | **豁免=屏级映射（SUP-01）** | **禁止** `slot.role in whitelist`。判定 `screen_exempt_from_shot_group_hard_reject(ctx)`，映射见 §3.1 |
| **D-SSG-18** | **父对象** | `curation.shotGrouping: { version, groups[], stats? }` |
| **D-SSG-19** | **多人跳过 look** | 最大脸面积比 &lt;0.15 **或** 脸数≥4 → skip look，保留 scene |
| **D-SSG-20** | **验收 vision** | 验收/狗粮强制 vision on；产品默认保持 false/auto |
| **D-SSG-21** | **slice 作用域（SUP-02）** | 操作定义：`template_prefers_burst(pattern_id) is not True`（与 candidates 现逻辑一致） |
| **D-SSG-22** | **硬拒跟随（SUP-03）** | `shotGrouping` 解析为生效且 `mosaic.sliceCrossGroupHardReject=true` 时，candidates 硬拒路径**视为 on**（不依赖用户手动开 `near_scene_clone_gate`）；gate 仍可显式 false 作总开关回滚 |
| **D-SSG-23** | **timings（SUP-04）** | 落盘键 **`shotGroupingMs`** |
| **D-SSG-24** | **缺席 vs 噪声（SUP-05）** | `sceneClusterId` **缺席** → 不写强分镜；**`-1`** → `kind=weak`；禁止缺席熔炉 |
| **D-SSG-25** | **配置单一真相（SUP-06）** | 行为扩展挂 `near_scene_clone_*` helper；`shotGrouping.mosaic.*` 为意图开关 |
| **D-SSG-26** | **StudioProfile（SUP-07）** | `run_shot_grouping`：Studio 默认 True；CLI 默认跟随 `run_clustering` |
| **D-SSG-27** | **M2 embed（SUP-09）** | **CLIP on upper-body ROI**；禁止 `face_crop_embedding` 充当外观向量 |

### 3.1 豁免屏级映射（SUP-01 · 会签锁定）

| 逻辑名 | 现网判定（写死） |
|--------|------------------|
| `cover` | cover / opening 封面屏（`coverAssetId` 主屏、opening cover） |
| `moment` | moment pattern / `momentAssetId` 签名时刻屏 |
| `chapterHero` | 章英雄单图屏（`featuredHeroByChapter` / chapter hero） |
| `solo` | 单图全幅屏（`len(slots)==1` 或 `screen-full-frame*`） |
| `bookend` | opening/closing bookend 屏 |

候选窗路径若尚无完整 screen ctx：允许用 **pattern 前缀 / 单槽** 作等价判定；**禁止**读 LTE `slot.role`。

---

## 4. 流水线位置

```text
ingest
  → clustering（Phase 3）
  → shot_grouping（NEW · D-SSG-16）
       M1: sceneCluster + time soft-split → kind=scene|weak
       M2: 主脸轨 + appearance Δ → kind=look
  → curate（章吃 segments；屏序 D-SSG-03）
  → layout / mosaic（D-SSG-05/06/17）
  → narrate（只读分镜）
  → render
```

| 约束 | 要求 |
|------|------|
| narrate / render | 不得改 `shotGroupId` |
| refine 删图 | V1 不自动全库重投影 |
| CLI | `reshotgroup` 或 recluster 邻接，复用 cache |
| timings | 键名 **`shotGroupingMs`**（D-SSG-23） |
| from_stage | `shot_grouping` 合法 |

---

## 5. 数据模型

### 5.1 Asset 字段（新）

| 字段 | 类型 | 说明 |
|------|------|------|
| `shotGroupId` | string \| null | 如 `sg-scene-12a` / `sg-look-03` |
| `shotGroupKind` | enum? | `scene` \| `look` \| `weak` |
| `shotGroupConfidence` | number? | \[0,1\] |

### 5.2 `curation.shotGrouping`（新 · 父对象）

```json
{
  "version": "1",
  "groups": [
    {
      "id": "sg-look-03",
      "kind": "look",
      "assetIds": ["a1", "a2"],
      "medoidAssetId": "a1",
      "sourceSceneClusterId": 12,
      "sourceEventId": "evt-02",
      "lookTrackId": "face-main",
      "signals": ["face_crop", "delta"],
      "confidence": 0.82
    }
  ],
  "stats": {
    "sceneGroupCount": 6,
    "lookGroupCount": 3,
    "softSplitCount": 2,
    "lookSkippedNoFace": 4
  }
}
```

`validate_trip` L1：optional 子树。

### 5.3 配置（唯一键）

```yaml
shotGrouping:
  enabled: auto              # false | auto | true
  minShotGroupSize: 2
  scene:
    timeSoftSplitHours: 6
    mergeNoise: true
  look:
    enabled: auto
    deltaThreshold: 0.28     # M2 spike 可 ±0.05 锁死
    sustainFrames: 2
    requireFaceOrSubject: true
    minMaxFaceAreaRatio: 0.15
    maxFacesBeforeSkip: 4
  mosaic:
    sliceCrossGroupHardReject: true   # 仅切条类 pattern
    sameGroupAntiSlice: true
    crossGroupExemptRoles:
      - cover
      - moment
      - chapterHero
      - solo
      - bookend
```

---

## 6. 功能需求

### 6.1 M0 · 合同与 Golden

| ID | 需求 | 验收 |
|----|------|------|
| **F-SSG-M0-01** | 七席 Conditional Go + 本 v0.2 回写 | 纪要 |
| **F-SSG-M0-02** | 混导 fixture ≥2 场景 | `tests/fixtures/shot-grouping/mixed-scenes-*` |
| **F-SSG-M0-03** | 换装 fixture 同地 ≥3 look | `tests/fixtures/shot-grouping/outfit-change-*` |
| **F-SSG-M0-04** | DATA-MODEL / schema 草案（父对象） | §5 |
| **F-SSG-M0-05** | 拆 ACCEPTANCE + IMPLEMENTATION | BLK-05 |
| **F-SSG-M0-06** | 数值门写入 AC（§8） | BLK-02 |

### 6.2 M1 · 场景分镜（P-SSG-01）

| ID | 需求 | 验收 |
|----|------|------|
| **F-SSG-M1-01** | vision+scene → 投影 shotGroup | AC-01 |
| **F-SSG-M1-02** | 同簇且时间近 → 同 scene 组 | AC-02（≥0.85） |
| **F-SSG-M1-03** | 跨 softSplit → 拆组 | AC-03 |
| **F-SSG-M1-04** | **切条类** pattern：跨组硬拒（豁免角色除外） | AC-04 |
| **F-SSG-M1-05** | 同组禁止假切条；扩展 `near_scene_clone_gate` | AC-05（↓≥40%） |
| **F-SSG-M1-06** | `cluster_run_sort` 叠加 shotGroup | AC-06 |
| **F-SSG-M1-07** | off / 无簇 = 基线 | AC-07 |
| **F-SSG-M1-08** | telemetry / decision_log | AC-08 |
| **F-SSG-M1-09** | deterministic | AC-09 |
| **F-SSG-M1-10** | 显式 stage `shot_grouping` | AC-18 |

### 6.3 M2 · 造型分镜（P-SSG-02）

| ID | 需求 | 验收 |
|----|------|------|
| **F-SSG-M2-01** | 主脸轨 look（无 featuredSubjects） | AC-10 |
| **F-SSG-M2-02** | 同 event 换装 → 不同 shotGroupId | AC-11（F1≥0.70） |
| **F-SSG-M2-03** | sustainFrames 防闪烁 | AC-12 |
| **F-SSG-M2-04** | 无脸 / D-19 跳过 → 保留 scene | AC-13 |
| **F-SSG-M2-05** | look 优先于 scene 粘合 | AC-14 |
| **F-SSG-M2-06** | look 享受同 mosaic 契约 | AC-15 |
| **F-SSG-M2-07** | 外观 cache | AC-16 |
| **F-SSG-M2-08** | 禁服装品类依赖 | 评审/检索 |

**M2 算法合同（方案 A）**

```text
1. 主脸轨：检测脸 → 取最大脸（面积比≥0.15）；脸数≥4 则 skip look
2. （可选）若 intent.featuredSubjects+cohort 可用 → 增强轨，不替代默认
3. 上半身 crop → CLIP（或等价）外观向量
4. 轨内按 takenAt；Δ≥deltaThreshold 连续 sustainFrames → 切开 look
5. look 边界强制生效，即使 sceneClusterId / eventId 相同
```

### 6.4 M3 · 结案

| ID | 需求 | 验收 |
|----|------|------|
| **F-SSG-M3-01** | 混导+换装狗粮盲评 | acceptance-records |
| **F-SSG-M3-02** | 配置可关 shotGrouping / look | AC-17 |
| **F-SSG-M3-03** | ACCEPTANCE/IMPL Closed | 文档 |
| **F-SSG-M3-04** | 默认 on 另决策 | 决策记录 |

---

## 7. 系统解法映射

| 解法 | 覆盖 | 门 |
|------|------|-----|
| **S-01** shotGroup 合同 | 概念 | M0 |
| **S-02** scene 投影 + 软切 | Q1/Q2 | M1 |
| **S-03** 切条类硬契约 + 同组不切条 | Q1/Q2 | M1 |
| **S-04** 主脸 look | Q3 | M2 |
| **S-05** fail-open + 狗粮 | Q4/Q5 | M1–M3 |

---

## 8. 验收标准（AC-SSG-* · 数值门已锁）

| ID | 断言 | 门 |
|----|------|-----|
| **AC-SSG-01** | vision+scene 路径 ≥95% 资产非空 `shotGroupId` | M1 |
| **AC-SSG-02** | 同簇近邻标注对：分镜同组率 **≥0.85** | M1 |
| **AC-SSG-03** | 跨 `timeSoftSplitHours` 同簇应拆组 | M1 |
| **AC-SSG-04** | 切条类 pattern：跨组（非豁免角色）硬拒或 −∞ | M1 |
| **AC-SSG-05** | 假切条窗相对基线 **↓≥40%** | M1 |
| **AC-SSG-06** | burst 不拆；同 shotGroup 成 run | M1 |
| **AC-SSG-07** | enabled=false 或 vision off ≡ 无强分镜；NR 通过 | M1 |
| **AC-SSG-08** | telemetry 含分镜摘要 | M1 |
| **AC-SSG-09** | 双跑 shotGroup 划分一致 | M1 |
| **AC-SSG-10** | 有脸 fixture 产出 `kind=look`（无 featuredSubjects） | M2 |
| **AC-SSG-11** | outfit-change：look 边界 **F1≥0.70** | M2 |
| **AC-SSG-12** | 微小 Δ 不切组 | M2 |
| **AC-SSG-13** | 无人脸：skip look，M1 仍可用 | M2 |
| **AC-SSG-14** | 同 sceneCluster+换装 → 不同 shotGroupId | M2 |
| **AC-SSG-15** | look 与 scene 同等 mosaic 契约 | M2 |
| **AC-SSG-16** | cache 命中不强制全库 CLIP | M2 |
| **AC-SSG-17** | 可关 look / 全部分镜 | M3 |
| **AC-SSG-18** | `stages_order` 含 `shot_grouping`；timings 有键 | M1 |
| **AC-SSG-19** | 合法混拼（非切条类）跨组同窗不因 SSG 被硬拒 | M1 |

> M0 spike 允许对 AC-02/05/11 阈值 **±0.05** 微调一次并升文档小版本；不得删除数值门改回「待定」。

---

## 9. 里程碑与列车

| 里程碑 | 交付 | 依赖 BLK |
|--------|------|----------|
| **M0** | v0.2 合同 · 双 golden · 拆 ACCEPTANCE/IMPL | —（可 Kickoff） |
| **M1** | stage + scene 投影 + 切条门 + run_sort | 01/02/04/05/06 |
| **M2** | 主脸 look + 锁参 | 03 |
| **M3** | 狗粮 · 开关 · 默认 on 决策 | — |

| PR | 内容 |
|----|------|
| **PR-A / M0** | 文档 · fixture 契约 · ACCEPTANCE/IMPL 骨架 |
| **PR-B / M1** | stage · 投影 · run_sort · mosaic 门 |
| **PR-C / M1** | telemetry · deterministic · NR |
| **PR-D / M2** | 主脸 look |
| **PR-E / M2** | 阈值标定 |
| **PR-F / M3** | 狗粮盲评 · 结案 |

**禁止**单 PR 塞满 M1+M2+默认 on。

---

## 10. 风险与开放问题

### 10.1 风险

| ID | 风险 | 缓解 |
|----|------|------|
| **R-01** | vision off 无感 | D-20；诚实文档 |
| **R-02** | 过碎 | D-07；fallback 监控 |
| **R-03** | look 光照误切 | sustainFrames；可关 |
| **R-04** | 多人歧义 | D-19 |
| **R-05** | 硬拒误杀混拼 | D-05 · AC-19 |
| **R-06** | 二次 embed | cache |

### 10.2 开放问题（七席处置）

| ID | 结论 |
|----|------|
| **OQ-01** | ✅ 验收/狗粮 **vision on**；产品默认另决策 |
| **OQ-02** | ✅ 暂定 **CLIP crop**；F1&lt;0.70 再议 |
| **OQ-03** | ✅ V1 **不**重投影 |
| **OQ-04** | ✅ V1 **无**用户摘要句 |
| **OQ-05** | ✅ softSplit **独立**于 geo |

---

## 11. 文档与回写

| 文档 | 回写 |
|------|------|
| DATA-MODEL / schema | `shotGroupId` · `curation.shotGrouping` |
| algorithm-inventory | shot_grouping · look |
| PRD-PHASE3 | 优先级指针（S-02） |
| ACCEPTANCE / IMPLEMENTATION | M0 拆文 · 结案 Closed |
| DOC-STATUS / README | 本主题索引 |

---

## 12. 附录

### 12.1 代码锚点

| 区域 | 路径 |
|------|------|
| 上游 | `curation/clustering.py` · `scene_clusters.py` |
| **新建** | `curation/shot_grouping.py` |
| 编排 | `orchestrator/run.py`（插入 stage） |
| 屏序 | `curation/cluster_run_sort.py` |
| mosaic | `mosaic/clone_detection.py` · `candidates.py` · `near_scene_clone_gate` |
| 脸 | `media/face_embed.py`（主脸轨）；cohort **可选** |
| 配置 | `config/` + `config.yaml.example` |

### 12.2 术语

| 中文 | 字段/英文 |
|------|-----------|
| 智能分镜 | SSG / Smart Shot Grouping |
| 分镜组 | `shotGroup` |
| 场景分镜 | `kind=scene` |
| 造型分镜 | `kind=look` |
| 假切条 | 同组被拆成多块切条拼 |
| 硬拼假一条 | 不同组分进切条类窗 |

---

## 13. 修订记录

| 版本 | 日期 | 说明 |
|------|------|------|
| **v0.1.0** | 2026-07-23 | 初稿 · 双痛点入 V1 |
| **v0.2.0** | 2026-07-23 | 七席 Conditional Go 回写：硬契约作用域 · AC 数值门 · 主脸轨 · 显式 stage · 豁免白名单 · 父对象 · OQ 关闭 |
| **v0.2.1** | 2026-07-23 | 开发可行性 SUP-01～10 产品会签写回；豁免屏级映射 · 硬拒跟随 · timings · M2 CLIP-torso |
