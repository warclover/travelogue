# PRD-SMART-SHOT-GROUPING-V1 · 跨职能评审纪要（模板）

| 属性 | 内容 |
|------|------|
| **文档** | [PRD-SMART-SHOT-GROUPING-V1.md](../PRD-SMART-SHOT-GROUPING-V1.md)（**SSG** · 智能分镜） |
| **相邻挡门** | [Phase 3](../PRD-PHASE3.md) · [ADR-012](../adr/012-semantic-tagging-p8-p12-split.md) · [P15](../PRD-PHASE15-photo-mosaic-evolution.md) · [MSA](../PRD-MOSAIC-SLOT-ADAPTATION-V1.md) · [MTSO](../PRD-MOSAIC-TEMPLATE-SELECTION-OPTIMIZATION-V1.md) · [Keep-All](../PRD-KEEP-ALL-PHOTOS-V1.md) · [NAS](../PRD-NO-AI-SURFACE-V1.md) |
| **验收 / 实施** | 评审后拆否：□ 是 → `ACCEPTANCE-SMART-SHOT-GROUPING-V1.md` / `IMPLEMENTATION-…`　□ 否 · 暂用 PRD §6–§8 |
| **评审版本** | **v0.1.0 Draft** → Must-Fix 回写后升 **v0.x.x**（填） |
| **日期** | YYYY-MM-DD（填） |
| **结论** | □ Go　□ **Conditional Go**　□ No-Go　（勾选） |
| **编码** | □ 本轮仅文档回写　□ 可 Kickoff **M0**　□ 可 Kickoff **M1 / PR-B**　□ 可开 M2　（勾选） |
| **参评角色（七席）** | 产品 · 算法 · 架构 · 开发 · 测试/QA · 视觉/排版（拼图跳戏）· 用户体验（混导/换装狗粮） |
| **评审方式** | 分席只读（定位块 · §0 · §3 D-SSG · §6 M1/M2 · §8 AC）+ **对照现网代码核查**（见 §3） |
| **记录人** | （填） |
| **本纪要状态** | **模板 · 备查**（正式结案另存 `ssg-smart-shot-grouping-v1-review-YYYY-MM-DD.md`） |

> **使用说明**  
> 1. 会前：只读定位块 + §0.2 三层概念 + §0.3 非目标 + D-SSG-01/03/05/08/09；对照混导拼图乱 / 同景点换装须拆组。  
> 2. 会中：§2 分席表决 → §3 确认代码事实 → §5 收 Must-Fix → §7 拍板 D-SSG / OQ。  
> 3. 会后：另存日期版纪要；Must-Fix 回写 PRD；更新 [DOC-STATUS](../DOC-STATUS.md)、[README](../README.md)。  
> 4. **勿重开**：用分镜重写 3–5 章、云分镜 API、服装品类识别、Studio 分镜工作台（V1）、把 SSG 塞进 MTSO/MSA KPI。

---

## 0. 会前宣读（主持人 · 3 分钟）

1. **切口**：拼图/排版的 **分镜单元**，不是再写一套分章聚类。  
2. **双痛点均在 V1**：P-SSG-01 混导乱拼（M1）· P-SSG-02 换装须拆（M2）。  
3. **已定案精神（勿重开）**：分层不抢章；投影层；本地 fail-open；V1 无分镜工作台。  
4. **本场必拍**：D-05 硬契约作用域 · M2 主体轨是否依赖 cohort · AC 数值门 · 编排插入点。  
5. **本轮默认**：先文档/Must-Fix；**M0** 必过；**M1** 在 BLK 回写后 Kickoff；禁止单 PR 塞满 M1–M3。

---

## 1. 总评（一句话）

> （会后填写）

---

## 2. 分席表决

| 席位 | 表决 | 一句话（必填） |
|------|------|----------------|
| **产品** | □ Go / □ CG / □ No | |
| **算法** | □ Go / □ CG / □ No | |
| **架构** | □ Go / □ CG / □ No | |
| **开发** | □ Go / □ CG / □ No | |
| **测试 / QA** | □ Go / □ CG / □ No | |
| **视觉 / 排版 · 拼图** | □ Go / □ CG / □ No | |
| **用户体验 · 狗粮手测** | □ Go / □ CG / □ No | |

**汇总**：_/_ 席 · 结论 ______ · 未回写 Must-Fix 前 □ 不批无条件 Go · □ 不批 M1 合码 · □ 不批 M2

**对齐评分（主观 · 会后填）**

| 维度 | 分（/10） | 说明 |
|------|-----------|------|
| 问题→根因完整度 | | P-SSG-01/02 · 与聚类差距 |
| 与 Phase3/P15/MSA 边界清晰度 | | 有无抢章或搅合选型 |
| 工程可开工性 | | 插入点 / cohort 依赖 / cache |
| AC 可测性 / 防假绿 | | 数值门是否空指针 |
| 拼图可签核性 | | 硬拒是否误杀杂志混拼 |

---

## 3. 事实核查（会前代码核对 · 影响结论）

| # | PRD / 假设 | 代码事实（预填） | 会中 |
|---|------------|------------------|------|
| **F-01** | ClusteringLayer 在 curate 前 | `orchestrator.stages_order`: ingest→**clustering**→curate→layout… | □ 属实 □ 修正 |
| **F-02** | vision 默认 false | `VisionConfig.enabled` 默认 `"false"` | □ 属实 □ 修正 |
| **F-03** | run_aware 非 mosaic 硬契约 | `cluster_run_sort` 只管屏序；mosaic 不读 sceneCluster 作硬拒 | □ 属实 □ 修正 |
| **F-04** | near_scene_clone 纯时间 | `clone_detection.py` 时间窗 + prefers_burst；无衣着 | □ 属实 □ 修正 |
| **F-05** | L2 暂缓 | ADR-012 | □ 属实 □ 修正 |
| **F-06** | burst > cluster run > time | `cluster_run_sort.sort_bucket_asset_ids_run_aware` | □ 属实 □ 修正 |
| **F-07** | CLIP cache 可复用 | `.cluster-cache/` | □ 属实 □ 修正 |
| **F-08** | cohort 可作 M2 轨 | `apply_cohort_tags` **需** `intent.featuredSubjects`；非全量默认主路径 | □ 属实 □ 修正 |

**会中新增事实**：

- …

---

## 4. 全场共识（预填 · 会中可改）

1. **分镜 ≠ 章**；投影层正确。  
2. **双痛点都做**：M1 scene + M2 look。  
3. **硬契约必须收窄作用域**，禁止误杀合法杂志混拼。  
4. **M2 不得默认绑 featuredSubjects cohort**。  
5. **AC 数值门必须进 PRD**，禁「spike 锁」空指针。  
6. **默认 vision off 诚实**；验收路径 on。  
7. **列车**：M0 → M1 → M2 → M3；禁单 PR 塞满。

**会中新增共识**：

- …

---

## 5. Must-Fix（阻塞 Kickoff / 合码 · 候选）

| ID | 议题 | 来源席位 | 要求（冻结一字面） | 挡 | 状态 |
|----|------|----------|-------------------|----|------|
| **BLK-SSG-01** | 硬契约作用域 | 视觉 / 算法 | AC-04/D-05 收窄为切条类/假一条；合法跨组杂志混拼白名单 | M1 | □ |
| **BLK-SSG-02** | AC 数值门 | QA / 算法 | M0 锁同组率/假切条↓/look F1 进 PRD | M0 | □ |
| **BLK-SSG-03** | M2 主体轨 | 架构 / 算法 | 默认主脸轨不依赖 featuredSubjects；cohort 可选增强 | M2 | □ |
| **BLK-SSG-04** | 编排插入点 | 架构 / 开发 | `stages_order` 显式 `shot_grouping` 或 clustering 尾钩；from_stage/timings | M1 | □ |
| **BLK-SSG-05** | 拆 ACCEPTANCE/IMPL | 测试 / 产品 | M1 合码前必须拆文 | M1 | □ |
| **BLK-SSG-06** | 跨组豁免枚举 | 产品 / 开发 | solo/封面/hero/moment 白名单写死，禁「等」 | M1 | □ |
| **BLK-SSG-07** | 配置键唯一 | 开发 | 仅 `shotGrouping.look.enabled` | M0 | □ |
| **BLK-SSG-08** | 数据模型父对象 | 架构 | `curation.shotGrouping` 对象含 version + groups[] | M0 | □ |

---

## 6. Should-Fix / 建议（不阻塞 M0/M1）

| ID | 建议 | 席位 | 状态 |
|----|------|------|------|
| **S-01** | 混导/换装狗粮 GUIDE + on/off 对照截图 | UX / 产品 | □ |
| **S-02** | Phase 3 文档加 SSG 优先级指针 | 产品 | □ |
| **S-03** | near_scene_clone 升级前后对照表进 IMPL | 算法 | □ |
| **S-04** | 盲评三问：跳戏 / 假切条 / 换装是否该拆 | QA / 视觉 | □ |

---

## 7. D-SSG / OQ 拍板表

### 7.1 决策（对照 PRD §3）

| ID | PRD 建议摘要 | 结论 | 备注 |
|----|--------------|------|------|
| **D-SSG-01～04** | 分层/投影/优先级/M1 源 | □ 按建议　□ 修改：___ | |
| **D-SSG-05～06** | mosaic 硬契约 / clone 升级 | □ 按建议　□ **收窄作用域** | |
| **D-SSG-07～15** | 防碎/look/开关等 | □ 按建议　□ 修改：___ | |

### 7.2 开放项（PRD §10.2）

| ID | 问题 | 结论 |
|----|------|------|
| **OQ-01** | 验收是否强制 vision on | □ 验收 on · 产品默认另定　□ 其他 |
| **OQ-02** | look 向量模型 | □ 默认 CLIP crop　□ spike 后再定 |
| **OQ-03** | refine 重投影 | □ V1 不重算　□ 其他 |
| **OQ-04** | 用户一句摘要 | □ M3 可选　□ V1 不做 |
| **OQ-05** | softSplit 与 geo 联动 | □ 独立　□ 联动 |

---

## 8. 风险与回滚确认

| 风险 | 可接受？ | 备注 |
|------|----------|------|
| vision off 用户无感 | □ 是 □ 否 | 诚实文案 |
| 硬拒误杀混拼 | □ 是 □ 否 | BLK-01 |
| look 光照误切 | □ 是 □ 否 | 可关 look |
| 二次 embed 性能 | □ 是 □ 否 | cache |

**回滚顺序确认**：`shotGrouping.enabled=false` → mosaic/章不变　□ 同意

---

## 9. 结论与下一步

| 项 | 内容 |
|----|------|
| **结论** | □ Go　□ Conditional Go　□ No-Go |
| **可 Kickoff M0** | □ 是　□ 否 |
| **可 Kickoff M1** | □ 是　□ 否（须先关 BLK：___） |
| **可开 M2 合码** | □ 是　□ 否（须先关 BLK：___） |
| **回写 PRD 目标版本** | v0.2.0 |
| **是否拆 ACCEPTANCE / IMPLEMENTATION** | □ 是　□ 豁免至：___ |

---

## 10. 签名栏

| 角色 | 姓名 | 日期 | 表决 |
|------|------|------|------|
| 产品 | | | |
| 算法 | | | |
| 架构 | | | |
| 开发 | | | |
| 测试 / QA | | | |
| 视觉 / 排版 | | | |
| 用户体验 · 狗粮 | | | |

---

## 附录 · 表决口径

| 符号 | 含义 |
|------|------|
| **Go** | 合同可开工；无阻塞 Must-Fix |
| **Conditional Go (CG)** | 方向成立；列出的 BLK 回写前不批对应里程碑合码 |
| **No-Go** | 根因/边界不成立；须改切口或缩范围后再评 |
