# PRD-MOSAIC-TEMPLATE-SELECTION-OPTIMIZATION-V1 · 跨职能评审纪要（模板）

| 属性 | 内容 |
|------|------|
| **文档** | [PRD-MOSAIC-TEMPLATE-SELECTION-OPTIMIZATION-V1.md](../PRD-MOSAIC-TEMPLATE-SELECTION-OPTIMIZATION-V1.md)（**MTSO** · 拼图模板选型与使用优化） |
| **相邻挡门** | [P21 密度](../PRD-PHASE21-mosaic-density-budget.md) · [TPC](../PRD-TEMPLATE-CONTRACT-V1.md) · [LTN 峰会](./ltn-template-slot-summit-2026-07-20.md) · [6 张拼图](../PRD-6张拼图优化.md) · [MGQ](../PRD-MCS-GEOMETRIC-QUALITY-V1.md) · [URO](../PRD-USAGE-RULES-LAYOUT-OPTIMIZATION.md) · [MSR](../PRD-MCS-SIGNATURE-ROUTING-V1.md) |
| **验收 / 实施** | 评审后拆否：□ 是 → `ACCEPTANCE-MOSAIC-TEMPLATE-SELECTION-OPTIMIZATION-V1.md` / `IMPLEMENTATION-…`　□ 否 · 暂用 PRD §8–§9 |
| **评审版本** | **v0.1.0 Draft** → Must-Fix 回写后升 **v0.x.x**（填） |
| **日期** | YYYY-MM-DD（填） |
| **结论** | □ Go　□ **Conditional Go**　□ No-Go　（勾选） |
| **编码** | □ 本轮仅文档回写　□ 可 Kickoff **M1 / PR-A**（生命周期+漏斗）　□ 可开 M2　（勾选） |
| **参评角色（七席）** | 产品 · 算法 · 架构 · 开发 · 测试/QA · 视觉/排版（LTE SKU）· 用户体验（狗粮手测） |
| **评审方式** | 分席只读（PRD §0.2 代码事实 · §2 目标/非目标 · §4 D-MTSO · §5 规格 · §9 AC）+ **对照现网代码核查**（见 §3） |
| **记录人** | （填） |
| **本纪要状态** | **模板 · 备查**（正式结案另存 `mtso-mosaic-template-selection-v1-review-YYYY-MM-DD.md`） |

> **使用说明**  
> 1. 会前：参评人只读 PRD 定位块 + §0.2 F-01～F-09 + §2.2 非目标 + §4 D-01/D-05/D-07；对照本机若开过 `template_contract` 的手测体感。  
> 2. 会中：§2 分席表决 → §3 确认/修正代码事实 → §5 收 Must-Fix → §7 拍板 D-MTSO / O-*。  
> 3. 会后：另存日期版纪要，删「模板」字样；Must-Fix 回写 PRD 后再改结论行、[DOC-STATUS](../DOC-STATUS.md)、[README](../README.md)。  
> 4. **勿重开**：P21 dense 硬上限、禁 runtime 改 `slots[].rect`、MCS 权威选窗、QFX 正交。

---

## 0. 会前宣读（主持人 · 3 分钟）

1. **切口**：现网拼图已「及格」；本案修的是 **选型与生命周期**，不是堆模板、不是放宽密度。  
2. **三场手测债（已探查）**：  
   - 混向弱（竖强仍塞横主竖辅）；  
   - 「两竖三横」实为 TPC ON 解锁的 `2p3l-rail`，非 deprecated `equal` 回潮；  
   - 「主图+右二+底三」六图 hero 模板仍 ga，被 **5→4→6 + landscape-4 + 章配额** 饿死（本地曝光 0）。  
3. **已定案精神（勿重开）**：不放宽 `dense_collage_max` / 相邻 dense；不恢复等权 6/8/9 平铺；不以「六图屏数」为 KPI。  
4. **本场必拍**：D-MTSO-01（TPC≠实验解锁）、D-05/07（合格六图机会）、D-03/04（混向主次）、D-13（转化率主指标）；关闭 O-1～O-4 或明确保持开放。  
5. **本轮默认**：先文档/Must-Fix；**M1（生命周期+漏斗）**可优先 Kickoff，**不**单 PR 塞满 M1–M3。

---

## 1. 总评（一句话）

> （会后填写：选型合同是否立得住？六图「机会保护」是否比全局改 `window_order` 更安全？2P3L 主从几何是否够格占第 12 席？最大阻塞是生命周期耦合、资格预检可测性，还是新 SKU 视觉？）

---

## 2. 分席表决

| 席位 | 表决 | 一句话（必填） |
|------|------|----------------|
| **产品** | □ Go / □ CG / □ No | |
| **算法** | □ Go / □ CG / □ No | |
| **架构** | □ Go / □ CG / □ No | |
| **开发** | □ Go / □ CG / □ No | |
| **测试 / QA** | □ Go / □ CG / □ No | |
| **视觉 / 排版 · LTE SKU** | □ Go / □ CG / □ No | |
| **用户体验 · 狗粮手测** | □ Go / □ CG / □ No | |

**汇总**：_/_ 席 · 结论 ______ · 未回写 Must-Fix 前 □ 不批无条件 Go · □ 不批 M2 合码

**对齐评分（主观 · 会后填）**

| 维度 | 分（/10） | 说明 |
|------|-----------|------|
| 问题→根因完整度 | | 是否覆盖 Q1–Q6 / F-01～F-09 |
| 与 P21/TPC/LTN 边界清晰度 | | 有无二次放宽密度或双轨准入 |
| 工程可开工性 | | M1 是否可独立 Kickoff |
| AC 可测性 / 防假绿 | | 转化率 vs 屏数；漏斗字段是否硬 |
| 视觉/SKU 可签核性 | | 2P3L / 竖主 1P4L 几何是否可审 |

---

## 3. 事实核查（会前代码核对 · 影响结论）

> 下列为 **2026-07-23 探查预填**；会中勾选「属实 / 修正」。修正项必须升为 BLK 或回写 PRD §0.2。

| # | PRD / 手测假设 | 代码事实（预填） | 会中 |
|---|----------------|------------------|------|
| **F-01** | MCS 活跃约 11 | `lte_policy.yaml` · `MOSAIC_*_PATTERN_IDS` = 11；8/9 空 | □ 属实 □ 修正：___ |
| **F-02** | 两竖三横退役仍见 | deprecated=`2p3l-equal`；现网狗粮见的是 experimental `2p3l-rail`（同拓扑） | □ 属实 □ 修正：___ |
| **F-03** | TPC ON 解锁实验族 | `_contract_unlocks_experimental()`：contract ON ⇒ experimental+percent=0 进 registry | □ 属实 □ 修正：___ |
| **F-04** | 六图 hero 模板没了 | `main-hero-plus-4/5` 仍 **ga** 且 in registry；本地 trips HTML 曝光 **0** | □ 属实 □ 修正：___ |
| **F-05** | 全横被四宫抢走 | `window_order=(5,4,6)`；全横 size5→`hero-3-2` 几何失败→**landscape-4** 先胜；仿真 rem=7/8/10/12 均饿死 6 | □ 属实 □ 修正：___ |
| **F-06** | 5 槽吃掉六图章配额 | `large_mosaic_min_slots=5` + `max_large_mosaic_per_chapter=1` | □ 属实 □ 修正：___ |
| **F-07** | 小册 dense≈1 | `dense_collage_limits_for_trip`；`landscape-4` 计 dense | □ 属实 □ 修正：___ |
| **F-08** | 横主竖辅委屈强竖 | `main-portrait-3land` usage 已写 whenNotToUse；缺硬拒选 | □ 属实 □ 修正：___ |
| **F-09** | 跨段凑六图 | 粗分段 `seg_cap` 禁止跨段（正确） | □ 属实 □ 修正：___ |

**会中新增事实**：

- …

---

## 4. 全场共识（预填 · 会中可改）

1. **及格≠优秀**：门禁压翻车有功；混向主次与六图机会是下一档。  
2. **P21 硬上限不放宽**：本案只保护「合格六图」不被 4/5 系统性饿死。  
3. **TPC ≠ 上线开关**：合同求值与 experimental 狗粮必须解耦。  
4. **不恢复等权 2P3L**：`2p3l-equal` / 默认 `2p3l-rail` 不得转 GA；空位只给主从继任。  
5. **成功看转化率**：`won/qualified`，不设全局最低六图屏数。  
6. **列车拆分**：PR-A 生命周期+漏斗 → PR-B 六图机会 → PR-C 混向 SKU → PR-D 转正。  
7. **本轮默认先回写文档**；M1 可单独 Kickoff。

**会中新增共识**：

- …

---

## 5. Must-Fix（阻塞 Kickoff / M2 合码 · 候选 · 会中增删）

| ID | 议题 | 来源席位 | 要求（冻结一字面） | 挡 | 状态 |
|----|------|----------|-------------------|----|------|
| **BLK-MTSO-01** | TPC↔experimental 解耦 | 架构 / 算法 | D-01 写死：`template_contract` 永不暗示实验可见；单独 `template_experiments` | M1 | □ |
| **BLK-MTSO-02** | deprecated 全路径负例 | 测试 / 开发 | candidate + self-heal + legacy append 均不可 emit；LTE OFF 硬禁补齐 `2p3l-equal` | M1 | □ |
| **BLK-MTSO-03** | 六图资格可测 oracle | 算法 / QA | `qualified_six_hero` 布尔与预检步骤进 AC；禁只靠曝光数假绿 | M1→M2 | □ |
| **BLK-MTSO-04** | 机会状态机不增 dense | 架构 / 产品 | `hero_six_opportunity` 武装/释放条件钉死；明确 **不** 增加 `dense_collage_max` | M2 | □ |
| **BLK-MTSO-05** | 1P4L 竖强硬拒 | 算法 / URO | `mixed_portrait_is_hero` 与 YAML whenNotToUse 同测；阈值与 URO 对齐或显式覆盖 | M2 | □ |
| **BLK-MTSO-06** | 2P3L 主从几何签核 | 视觉 / 产品 | 主槽≥0.55、主从≥3:1、声明 AR vs 实渲对账；等权拓扑一票否决 | M2 | □ |
| **BLK-MTSO-07** | 漏斗原始日志字段 | 测试 / 开发 | §5.5 最低字段集进 AC-03；展示日志不得作 AC 唯一源 | M1 | □ |
| **BLK-MTSO-08** | 拆 ACCEPTANCE / IMPLEMENTATION | 测试 / 产品 | Conditional Go 后、M2 合码前必须拆文（或书面豁免并写期限） | M2 | □ |

---

## 6. Should-Fix / 建议（不阻塞 M1）

| ID | 建议 | 席位 | 状态 |
|----|------|------|------|
| **S-01** | 本机 `config.yaml` 狗粮说明写入 GUIDE：TPC ON 的预期实验曝光，避免再误判「退役回潮」 | 产品 / UX | □ |
| **S-02** | `main-hero-plus-4` 显示名/usage 强调 photoCount=6，减少「5 图模板」误读 | 视觉 / 开发 | □ |
| **S-03** | 六图漏斗进 weekly dashboard（LTN）只读面板 | 算法 | □ |
| **S-04** | 盲评切片固定含：全横 12、强竖 1P4L、2P3L、段长&lt;6 | QA | □ |
| **S-05** | `2p3l-rail` YAML 文首加「非 MTSO 继任 · 勿转 GA」 | 开发 | □ |

---

## 7. D-MTSO / O-* 拍板表

### 7.1 决策（对照 PRD §4）

| ID | PRD 建议摘要 | 结论 | 备注 |
|----|--------------|------|------|
| **D-MTSO-01** | TPC≠实验解锁；deprecated 永禁 | □ 按建议　□ 修改：___ | |
| **D-MTSO-02** | 活跃集 11+1；空位只给主从 2P3L | □ 按建议　□ 修改：___ | |
| **D-MTSO-03** | 1P4L 竖强禁横主竖辅 | □ 按建议　□ 修改：___ | |
| **D-MTSO-04** | 2P3L 方案 A：单竖 main + 次竖辅 | □ 按建议　□ 改方案 B　□ 其他：___ | |
| **D-MTSO-05** | 默认 5→4→6；仅合格六图局部 6→5→4 | □ 按建议　□ 修改：___ | |
| **D-MTSO-06** | 重排原因码可观测 | □ 按建议　□ 修改：___ | |
| **D-MTSO-07** | hero_six_opportunity；不增 dense | □ 按建议　□ 修改：___ | |
| **D-MTSO-08** | 禁跨段凑六图 | □ 按建议　□ 修改：___ | |
| **D-MTSO-09** | 签名只缩窄；miss 回落全集 | □ 按建议　□ 修改：___ | |
| **D-MTSO-10** | 六图构建红线不放松 | □ 按建议　□ 修改：___ | |
| **D-MTSO-11** | 原始漏斗日志为挡门 | □ 按建议　□ 修改：___ | |
| **D-MTSO-12** | 新 SKU 先实验后转正 | □ 按建议　□ 修改：___ | |
| **D-MTSO-13** | 主指标=合格机会转化率 | □ 按建议　□ 改最低屏数　□ 其他：___ | |

### 7.2 开放项（PRD §12）

| ID | 问题 | 结论 |
|----|------|------|
| **O-1** | 竖主 1P4L 几何轨道路线 | □ 会后视觉出 2 稿　□ 本场冻结：___　□ 保持开放 |
| **O-2** | `selection_optimization` 何时默认 true | □ M3 后再定　□ M2 狗粮后即 true　□ 其他：___ |
| **O-3** | hero gap 与 URO 阈值 | □ 共用 usage_rules　□ MTSO 独立覆盖　□ 其他：___ |
| **O-4** | `2p3l-rail` 归档策略 | □ 留 YAML+永不默认 allowlist　□ 删除　□ 其他：___ |

---

## 8. 风险与回滚确认（会中勾选）

| 风险 | 可接受？ | 备注 |
|------|----------|------|
| 六图保护导致部分 4/5 变稀 | □ 是 □ 否 | 仅合格窗；可关机会开关 |
| 新 2P3L 仍显假拼图 | □ 是 □ 否 | 不过则归档，空位不强填 |
| 实验隔离过严导致狗粮无样本 | □ 是 □ 否 | 用 cohort，不借 TPC |
| 开关组合导致难回滚 | □ 是 □ 否 | 确认三开关独立默认 off |

**回滚顺序确认**：experiments OFF → hero_six_opportunity OFF → selection_optimization OFF → **P21 保持 ON**　□ 同意

---

## 9. 结论与下一步

| 项 | 内容 |
|----|------|
| **结论** | □ Go　□ Conditional Go　□ No-Go |
| **可 Kickoff M1 / PR-A** | □ 是　□ 否（须先关 BLK：___） |
| **可开 M2 合码** | □ 是　□ 否（须先关 BLK：___） |
| **Must-Fix 责任人** | |
| **回写 PRD 目标版本** | v0.2.0（Conditional Go 后） |
| **是否拆 ACCEPTANCE / IMPLEMENTATION** | □ 是　□ 豁免至：___ |
| **README / DOC-STATUS** | 评审后更新状态行 |

**建议列车（可改）**

| PR | 内容 | 依赖 |
|----|------|------|
| **PR-A** | lifecycle_admit + 实验开关 + 漏斗日志 + 负例 | BLK-01/02/07 |
| **PR-B** | hero_six_opportunity + 窗序局部重排 | BLK-03/04 · PR-A |
| **PR-C** | 1P4L 双分支 + 2P3L 主从 SKU（experimental） | BLK-05/06 · 视觉签核 |
| **PR-D** | 狗粮/盲评 → 转正或归档 | AC-11/12 |

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

## 附录 A · 会前阅读清单（15 分钟）

| # | 材料 | 必读段落 |
|---|------|----------|
| 1 | [MTSO PRD](../PRD-MOSAIC-TEMPLATE-SELECTION-OPTIMIZATION-V1.md) | 定位块 · §0.2 · §2 · §4 · §9 |
| 2 | [P21](../PRD-PHASE21-mosaic-density-budget.md) | §3 已拍板 · 5→4→6 |
| 3 | [TPC](../PRD-TEMPLATE-CONTRACT-V1.md) | AC-TPC-01 默认 off；实验可见性 |
| 4 | [LTN 峰会](./ltn-template-slot-summit-2026-07-20.md) | 活跃集 11+1 |
| 5 | 代码锚点（可选） | `lte_adapter._contract_unlocks_experimental` · `hook.try_mosaic_window` · `builders._order_hero_six` |

## 附录 B · 表决口径

| 符号 | 含义 |
|------|------|
| **Go** | 合同可开工；无阻塞 Must-Fix |
| **Conditional Go (CG)** | 方向成立；列出的 BLK 回写前不批对应里程碑合码 |
| **No-Go** | 根因/边界不成立；须改切口或缩范围后再评 |
