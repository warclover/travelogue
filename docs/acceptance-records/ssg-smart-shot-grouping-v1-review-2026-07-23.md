# PRD-SMART-SHOT-GROUPING-V1 · 跨职能评审纪要

| 属性 | 内容 |
|------|------|
| **文档** | [PRD-SMART-SHOT-GROUPING-V1.md](../PRD-SMART-SHOT-GROUPING-V1.md)（**SSG** · 智能分镜） |
| **模板来源** | [ssg-smart-shot-grouping-v1-review-TEMPLATE.md](./ssg-smart-shot-grouping-v1-review-TEMPLATE.md) |
| **相邻挡门** | [Phase 3](../PRD-PHASE3.md) · [ADR-012](../adr/012-semantic-tagging-p8-p12-split.md) · [P15](../PRD-PHASE15-photo-mosaic-evolution.md) · [MSA](../PRD-MOSAIC-SLOT-ADAPTATION-V1.md) · [MTSO](../PRD-MOSAIC-TEMPLATE-SELECTION-OPTIMIZATION-V1.md) · [Keep-All](../PRD-KEEP-ALL-PHOTOS-V1.md) · [NAS](../PRD-NO-AI-SURFACE-V1.md) |
| **评审版本** | **v0.1.0 Draft** → Must-Fix 回写后升 **v0.2.0** |
| **日期** | 2026-07-23 |
| **结论** | **有条件通过（Conditional Go）** · **可 Kickoff M0**（合同回写 + golden 契约 + 拆 ACCEPTANCE/IMPL）；**M1 合码前须关闭 BLK-SSG-01/02/04/05/06**；**M2 合码前须关闭 BLK-SSG-03** |
| **编码** | □ 本轮仅文档　☑ **可 Kickoff M0**　□ 可 Kickoff M1（待 BLK）　□ 可开 M2 |
| **参评角色（七席）** | 产品 · 算法 · 架构 · 开发 · 测试/QA · 视觉/排版（拼图跳戏）· 用户体验（混导/换装狗粮） |
| **评审方式** | 分席只读 + **对照现网代码核查**（`orchestrator.stages_order` · `VisionConfig` · `cluster_run_sort` · `clone_detection` · `cohort_faces`） |
| **记录人** | 七席联合纪要（跨职能模拟联评 · 基于 PRD v0.1.0 + 2026-07-23 代码探查） |
| **本纪要状态** | **已结案 · Conditional Go** · **PRD v0.2.0 已回写** · 可 Kickoff M0 |
| **审查基线** | Phase 3 clustering · vision 默认 off · near_scene_clone 时间启发式 · cohort 需 featuredSubjects |

---

## 0. 会前宣读（主持人）

1. **切口**：拼图/排版的 **分镜单元（shotGroup）**，不是再写一套分章。  
2. **双痛点均在 V1**：混导乱拼（M1）· 同景点换装须拆（M2）。  
3. **勿重开**：抢章、云 API、服装品类、V1 分镜工作台、搅 MTSO/MSA KPI。  
4. **本场必拍**：硬契约作用域 · M2 主体轨 · AC 数值门 · 编排插入点。  
5. **列车**：M0 先过；M1/M2 合码挡在对应 BLK。

---

## 1. 总评（一句话）

> **七席一致 Conditional Go：「分镜 ≠ 章、投影层、双痛点分 M1/M2」方向成立，且与 Phase3/P15/MSA 边界清楚；但 v0.1 有四处开工前必须钉死——（1）mosaic 硬拒不得误杀合法杂志混拼；（2）AC「spike 锁」空指针；（3）M2 默认依赖 featuredSubjects cohort 与代码事实不符；（4）编排插入点与跨组豁免未枚举。M0 可立即 Kickoff；M1 合码挡在 BLK-01/02/04/05/06；M2 合码挡在 BLK-03。**

---

## 2. 分席表决

| 席位 | 表决 | 一句话 |
|------|------|--------|
| **产品** | **Conditional Go** | 双痛点同时进 V1 正确；须诚实对待「默认 vision off = 多数用户无强分镜」；硬契约勿伤杂志混拼 |
| **算法** | **Conditional Go** | M1 复用 scene+时间软切合理；M2 crop 外观可行；AC-02/05/11 必须锁数值，否则假绿 |
| **架构** | **Conditional Go** | 投影层正确；须显式 stage/`shotGrouping` 父对象；**禁止**把 M2 绑死在 intent.featuredSubjects |
| **开发** | **Conditional Go** | M1 可挂 clustering 后；clone_detection/candidates 有挂载点；配置双名与豁免「等」必须收口 |
| **测试 / QA** | **Conditional Go** | 双 golden 方向对；AC 数值门与 deterministic 双跑可测；须拆 ACCEPTANCE 防假绿 |
| **视觉 / 排版 · 拼图** | **Conditional Go** | 假切条/跳戏是真债；**跨组分镜≠禁止同屏**——杂志页常要氛围混搭；硬拒作用域必须收窄 |
| **用户体验 · 狗粮手测** | **Conditional Go** | 混导与换装痛点真实；V1  invisible工作台可接受，但验收狗粮必须 vision on，否则「做了等于没做」 |

**汇总**：**七席一致 Conditional Go**。  
- **M0**：可 Kickoff（回写 v0.2 + golden 契约 + 拆 ACCEPTANCE/IMPL）。  
- **M1 合码**：BLK-SSG-01/02/04/05/06 关闭前 **不批**。  
- **M2 合码**：BLK-SSG-03 关闭前 **不批**（阈值 spike 另计）。

**对齐评分**

| 维度 | 分（/10） | 说明 |
|------|-----------|------|
| 问题→根因完整度 | **9** | P-SSG-01/02 与聚类差距写清 |
| 与 Phase3/P15/MSA 边界清晰度 | **9** | 正交正确 |
| 工程可开工性 | **6** | M0 可开；M1 卡作用域/插入点/豁免 |
| AC 可测性 / 防假绿 | **5** | 「spike 锁」未进合同 |
| 拼图可签核性 | **5** | 硬拒过宽有误杀风险 |

---

## 3. 事实核查（代码核对）

| # | 假设 | 代码事实 | 会中 |
|---|------|----------|------|
| **F-01** | clustering 在 curate 前 | `stages_order`: ingest→clustering→curate→layout… | ✅ 属实 |
| **F-02** | vision 默认 false | `VisionConfig.enabled: TriState = "false"` | ✅ 属实 |
| **F-03** | run_aware ≠ mosaic 硬契约 | `cluster_run_sort` 只排序；mosaic 候选不按 sceneCluster 硬拒 | ✅ 属实 |
| **F-04** | near_scene_clone 纯时间 | `clone_detection.py` 时间窗 + `prefers_burst` | ✅ 属实 |
| **F-05** | L2 暂缓 | ADR-012 | ✅ 属实 |
| **F-06** | burst > cluster run > time | `sort_bucket_asset_ids_run_aware` | ✅ 属实 |
| **F-07** | CLIP cache | `.cluster-cache/` | ✅ 属实 |
| **F-08** | cohort = M2 默认轨 | `apply_cohort_tags` **要求** `intent.featuredSubjects`；Studio 意图驱动，**非**全量默认主路径 | ✅ **属实且修正 PRD 假设** |

**新增事实（评审发现）**

| # | 事实 | 影响 |
|---|------|------|
| **F-09** | `stages_order` **无** `shot_grouping` 槽位 | 须新增 stage 或明确挂在 clustering 尾；影响 `from_stage` / timings |
| **F-10** | mosaic 已有 `near_scene_clone_gate` 配置挂点（candidates + scorer） | SSG 硬契约应扩展该门，而非平行第二套方言 |
| **F-11** | `cluster_run_sort` 今日只读 `sceneClusterId` | M1 须改为（或叠加）读 `shotGroupId`，否则优先级合同落空 |
| **F-12** | `curation.shotGroups[]` 草案把 `version` 写在数组项语义不清 | 应升为 `curation.shotGrouping` 父对象 |

---

## 4. 全场共识

1. **分镜 ≠ 章**；投影层是正确架构。  
2. **双痛点都做**：M1 scene + M2 look，不砍范围。  
3. **硬契约作用域 = 假切条 / 切条类拼图**，不是禁止一切跨组分镜同屏。  
4. **M2 默认主脸轨**，不依赖 featuredSubjects；cohort 仅可选增强。  
5. **AC 数值门进 PRD**；禁止空指针「spike 锁」。  
6. **验收/狗粮路径 vision on**；产品默认保持 false/auto，另决策。  
7. **回滚**：`shotGrouping.enabled=false` 即回基线。  
8. **列车**：M0 → M1 → M2 → M3；禁单 PR 塞满。

---

## 5. Must-Fix（结案成立）

| ID | 议题 | 要求（冻结一字面） | 挡 | 状态 |
|----|------|-------------------|----|------|
| **BLK-SSG-01** | 硬契约作用域 | D-05/AC-04：**仅**对「切条/同走假拼」类 pattern（`prefers_burst:false` 或等价名单）执行跨组硬拒；合法杂志混拼允许跨 `shotGroupId` 同窗，但受 `category_coherence`/评分约束。同组 `sameGroupAntiSlice` 仍硬 | M1 | ✅ 本场拍板 · 待回写 |
| **BLK-SSG-02** | AC 数值门 | M0 锁进 PRD：**同组率≥0.85**（AC-02）；假切条窗相对基线 **↓≥40%**（AC-05）；look 边界 F1 **≥0.70**（AC-11）；允许 M0 spike ±0.05 微调一次并改版号 | M0 | ✅ 本场拍板 · 待回写 |
| **BLK-SSG-03** | M2 主体轨 | **默认**：最大脸 / 主脸检测轨（无需 featuredSubjects）。`intent.featuredSubjects`+cohort **可选增强**。多人歧义：最大脸面积比 &lt;0.15 或脸数≥4 → **跳过 look** | M2 | ✅ 本场拍板 · 待回写 |
| **BLK-SSG-04** | 编排插入点 | `stages_order` **显式**插入 `"shot_grouping"`（clustering 后、curate 前）；timings 键 `shot_grouping`；`from_stage=shot_grouping` 合法 | M1 | ✅ 本场拍板 · 待回写 |
| **BLK-SSG-05** | 拆 ACCEPTANCE/IMPL | M1 合码前必须存在 `ACCEPTANCE-SMART-SHOT-GROUPING-V1.md` + `IMPLEMENTATION-…` | M1 | ✅ 成立 · M0 交付 |
| **BLK-SSG-06** | 跨组豁免枚举 | V1 白名单写死：`cover` · `moment` · `chapterHero` · `solo`（单图屏）· `bookend`；**禁止**「等」。白名单外切条类仍硬拒 | M1 | ✅ 本场拍板 · 待回写 |
| **BLK-SSG-07** | 配置键唯一 | 删除 `lookGrouping.*` 双名；唯一 `shotGrouping.look.enabled` | M0 | ✅ 待回写 |
| **BLK-SSG-08** | 数据模型父对象 | `curation.shotGrouping: { version, groups[], stats? }`；asset 仍挂 `shotGroupId` | M0 | ✅ 待回写 |

---

## 6. Should-Fix

| ID | 建议 | 席位 | 状态 |
|----|------|------|------|
| **S-01** | `ssg-local-dogfood-GUIDE`：混导 + 换装 + vision on/off 对照 | UX / 产品 | ☐ M0/M3 |
| **S-02** | Phase 3 §8.1 加 SSG 优先级指针 | 产品 | ☐ |
| **S-03** | near_scene_clone → shotGroup 门对照表进 IMPL | 算法 | ☐ |
| **S-04** | 盲评三问：跳戏 / 假切条 / 换装该不该拆 | QA / 视觉 | ☐ TEMPLATE |
| **S-05** | `cluster_run_sort` 叠加 `shotGroupId` 写进 IMPL PR-B | 开发 | ☐ |

---

## 7. D-SSG / OQ 拍板

### 7.1 决策

| ID | 结论 |
|----|------|
| **D-SSG-01～04** | ✅ **按建议** |
| **D-SSG-05～06** | ✅ **修订**：作用域收窄见 BLK-01；clone 升级挂现有 `near_scene_clone_gate`，优先读 `shotGroupId` |
| **D-SSG-07** | ✅ **按建议**（look 边界不受 minSize 合并） |
| **D-SSG-08～09** | ✅ **修订**：默认主脸轨（BLK-03）；其余按建议 |
| **D-SSG-10** | ✅ **按建议** |
| **D-SSG-11** | ✅ **修订**：仅 `shotGrouping.*`（BLK-07）；`auto` = vision 可用且 scene 簇非空才写强 scene 分镜 |
| **D-SSG-12～15** | ✅ **按建议** |
| **D-SSG-16**（新） | ✅ **编排显式 stage**（BLK-04） |
| **D-SSG-17**（新） | ✅ **豁免白名单**（BLK-06） |
| **D-SSG-18**（新） | ✅ **父对象 `curation.shotGrouping`**（BLK-08） |

### 7.2 开放项

| ID | 结论 |
|----|------|
| **OQ-01** | ✅ **关闭**：验收/狗粮路径 **强制 vision on**；产品默认保持 false/auto，M3 另决策 |
| **OQ-02** | ✅ **暂定 CLIP crop**；M2 spike 若 F1&lt;0.70 再议轻量模型 |
| **OQ-03** | ✅ **V1 不重算**；列 M3+ |
| **OQ-04** | ✅ **V1 不做**用户摘要句；M3 可选 |
| **OQ-05** | ✅ **独立**于 geo stay，避免双源抖动 |

---

## 8. 风险与回滚

| 风险 | 可接受？ | 备注 |
|------|----------|------|
| vision off 用户无感 | ✅ | 验收 on；产品默认另决策 |
| 硬拒误杀混拼 | ✅ | BLK-01 收窄 |
| look 光照误切 | ✅ | sustainFrames + 可关 |
| 二次 embed 性能 | ✅ | cache + 批处理 |
| 过碎致候选枯竭 | ✅ | D-07 + fallback 率监控 |

**回滚顺序**：`shotGrouping.enabled=false` → 章/mosaic 基线保持　✅ 同意

---

## 9. 结论与下一步

| 项 | 内容 |
|----|------|
| **结论** | **Conditional Go** |
| **可 Kickoff M0** | ✅ 是 |
| **可 Kickoff M1** | ❌ 否（先关 BLK-01/02/04/05/06 合同/拆文；再开码） |
| **可开 M2** | ❌ 否（BLK-03 + look 阈值 spike） |
| **Must-Fix 责任人** | 产品+架构主笔合同回写；算法锁 AC 数值；开发落 stage/挂点 |
| **回写 PRD** | **v0.2.0** |
| **拆 ACCEPTANCE / IMPLEMENTATION** | ✅ 是（BLK-05 · M0 交付 / M1 合码前必备） |

**建议列车**

| PR | 内容 | 依赖 |
|----|------|------|
| **M0** | PRD v0.2 回写 · 双 golden 契约 · 拆 ACCEPTANCE/IMPL · DOC-STATUS | 本纪要 |
| **PR-B / M1** | `shot_grouping` stage · scene 投影 · run_sort · mosaic 门（收窄作用域） | BLK-01/02/04/05/06 |
| **PR-C / M1** | telemetry · deterministic · NR off 路径 | PR-B |
| **PR-D / M2** | 主脸 look 轨 · crop embed · AC-11 | BLK-03 · PR-B |
| **PR-E / M2** | 阈值标定锁参 | PR-D · outfit golden |
| **PR-F / M3** | 狗粮盲评 · 开关文案 · 默认 on 决策 | AC-17 |

---

## 10. 签名栏（模拟联评）

| 角色 | 表决 |
|------|------|
| 产品 | Conditional Go |
| 算法 | Conditional Go |
| 架构 | Conditional Go |
| 开发 | Conditional Go |
| 测试 / QA | Conditional Go |
| 视觉 / 排版 | Conditional Go |
| 用户体验 · 狗粮 | Conditional Go |

---

## 附录 · 结案清单

| 项 | 状态 |
|----|------|
| 七席表决完成 | ✅ |
| 代码事实 F-01～F-12 | ✅ |
| BLK-SSG-01～08 成立 | ✅ |
| PRD 回写 v0.2.0 | ✅（本轮） |
| 拆 ACCEPTANCE/IMPL | ☐ M0 立即跟进 |
| DOC-STATUS / README 索引 | ✅（本轮） |
