# 战略优先级复盘 · 从 Flipin 对照看资源配置风险

| 属性 | 内容 |
|------|------|
| **文档版本** | v1.0 |
| **状态** | Draft |
| **调研日期** | 2026-08-03 |
| **调研方法** | [INSIGHT-FLIPIN-COMPETITIVE-ANALYSIS-2026-08-03.md](./INSIGHT-FLIPIN-COMPETITIVE-ANALYSIS-2026-08-03.md) 竞品对照结论延伸 + `docs/DOC-STATUS.md` 现行状态表 + `docs/README.md` 现行导读 + `git log` 最近 25 条提交焦点交叉核查 |
| **关联文档** | [INSIGHT-FLIPIN-COMPETITIVE-ANALYSIS-2026-08-03.md](./INSIGHT-FLIPIN-COMPETITIVE-ANALYSIS-2026-08-03.md) · [CHARTER.md](./CHARTER.md) · [PRD-COMMERCIALIZATION-MVP-V1.md](./PRD-COMMERCIALIZATION-MVP-V1.md) · [PRD-NO-AI-SURFACE-V1.md](./PRD-NO-AI-SURFACE-V1.md) · [PRD-AI-RETURN-V1.md](./PRD-AI-RETURN-V1.md) · [DOC-STATUS.md](./DOC-STATUS.md) |

> 定位：本文不是新功能 PRD，而是一份**资源配置 / 优先级健康度**复盘。目的是把「Flipin 没有算法投入却仍是完整产品」这个反差，从功能借鉴提升到战略判断层面，并给出一张可直接排期的收口清单。

---

## 一、核心判断：算法精修与商业化验证的优先级已经错位

### 1.1 观察到的事实

最近 25 条提交（`git log`）显示，当前工程精力高度集中在**排版几何与视觉质感的边际优化**：`MTSO`/`MSA`/`MEGC`/`SSG`/`ALG-V3` 五个排版算法专题并行推进，且刚合入十款 V6 封面样式。但按 [`docs/DOC-STATUS.md`](./DOC-STATUS.md) 的现行状态表：

| 专题 | 状态摘要 |
|------|----------|
| **MTSO**（拼图模板选型） | Conditional Go · 可 Kickoff M1 |
| **MSA**（拼图槽位自适应） | Conditional Go · 可 Kickoff M0 · **默认仍 off** · AC-09 待实册盲评 |
| **MEGC**（等权拼图几何合同） | Conditional Go · PR-A 可 Kickoff · **M3 延期** |
| **SSG**（智能分镜） | Conditional Closed · **默认 on Hold** |
| **ALG-V3**（算法优化 V3） | v0.3.2 **Done · 本波关闭** |

**五个算法专题里有四个仍处于"悬而未决"（default off / Hold / 延期 / 待盲评）**，而决定项目商业生死的 [`PRD-COMMERCIALIZATION-MVP-V1.md`](./PRD-COMMERCIALIZATION-MVP-V1.md)（CMZ）至今仍是 **v0.1.0 Draft，零真实付款证据**。

### 1.2 与 Flipin 对照的启示

Flipin **没有任何算法投入**，用户体验是"手动拖拽 + 抠图"这种粗糙工具，却已经是一个完整、可用、有留存钩子（书架）的产品。这提示一个扎心的问题——**用户为"完工的成册"付费的意愿，和排版算法有多精细，相关性可能很低**；持续投入算法边际优化，本质是在"自己最熟练、最有掌控感的地方"（调参）回避"最不确定、最需要走出去验证的问题"（有没有人愿意付钱）。

### 1.3 建议

在启动下一个算法专题之前，先做一件事——挑 `MSA`/`MEGC`/`SSG` 里任意一个"待盲评"的专题，**关闭新 Kickoff 权限，直到它完成一轮真人盲评并给出 default on/off 的最终结论**。同时把 CMZ 商业化验证从 Draft 推进到"至少收到 1 笔真实付款"，用真实市场反馈倒逼后续算法投入的取舍。

---

## 二、许可证系统建议"先验证、再工程化"

`PRD-COMMERCIALIZATION-MVP-V1.md` 设计了 Ed25519 签名验证、设备指纹、吊销列表等相对完整的许可基础设施（§6），但它的成功标准只是"**3 笔真实非关联付款**"（§9 M3）。

对照 Flipin——完全没有付费墙，却能让用户走完整套流程并产生依赖。这说明现在的风险不是"许可证不够严谨会被破解"，而是**根本没验证"游记工具"这个品类有没有人愿意为它掏钱**。在没有第一笔真实付款之前投入设备绑定/吊销列表这类工程，本质上是在给一个未经验证的商业假设建地基。

**建议**：先用"人工发码 + 本地简单校验（不做设备指纹/吊销列表）"跑通前 3 笔付款，把 §9 M0→M3 的门禁压缩成"两周内能不能收到第一笔钱"，工程精细度留到验证通过之后再补。

---

## 三、AI 叙事能力是"被藏起来的资产"，需要一个明确的解冻时间表

代码库里有完整的 LLM 叙事管线（Agent 2），但 [`PRD-NO-AI-SURFACE-V1.md`](./PRD-NO-AI-SURFACE-V1.md)（NAS，**v0.2.3 Conditional Go**）是现行的**默认对用户隐藏 AI 面**合同，[`PRD-AI-RETURN-V1.md`](./PRD-AI-RETURN-V1.md)（AIR，"解冻计划"）还停留在 **v0.1.0 Draft**，没有具体解冻日期。

这是一个悬而未决很久的资产闲置问题：如果隐藏的原因是 `CHARTER.md` §10 风险表第一条"LLM 虚构地点/事实"没解决，那应该把 AIR 的验收标准聚焦到"事实校验闭环"上，给出明确解冻日期；如果隐藏只是因为"还没想好怎么讲这个故事"，那这笔投入（整条 Agent 2 管线）就在持续贬值。

**建议**：给 NAS→AIR 的转换设一个**具体日期而不是"待评审"**，哪怕是灰度给 5% 种子用户先看到 AI 文案效果，收集"愿不愿意为更好的文案多付钱"的信号——这可能是比排版算法更直接的付费锚点。

---

## 四、体验层文档已经"加法太多"，Flipin 的真正启示是减法

数一下现有体验类 V1 文档及其状态（按 `docs/README.md` 现行导读原文摘要）：

| 文档 | 版本/状态摘要 |
|------|----------------|
| `PRD-FTUE-OPTIMIZATION-V1.md` | v1.1.0 · W0 编码中 |
| `PRD-WAIT-TIPS-V1.md` | v0.2.0 · Conditional Go · W0–W2 编码已合入 · **手测待填** |
| `PRD-HELP-ONBOARDING-V1.md` | v1.1.1 · Conditional Go · 可开 W0 |
| `PRD-SHARE-READY-OPTIMIZATION-V1.md` | v1.0.2 · Conditional Go · W0–W2 工程已合入 · **产品手测待签** |
| `PRD-FIRST-SESSION-TRUST-V1.md` | v1.0.2 · Conditional Go · W0–W2 工程已合入 · **完成宣布待 AC-FST-15** |
| `PRD-SHARE-FACE-CLOSEOUT-V1.md` | v1.0.2 · Conditional Go · W0–W2 工程已合入 · §12 质量收口全部必修 |
| `PRD-SHARE-FACE-INTEGRITY-V1.md` | v0.2.1 · Conditional Go · Doc 包齐 · **编码另排期** |
| `PRD-POST-MERGE-UX-FIXPACK-V1.md` | v0.2 · Conditional Go · M1–M3 同包 |
| `PRD-REFINE-FEEDBACK-LOOP-V1.md` | v0.1.3 · Conditional Go · M1+M2+P0+M3 |

**九个平行的"引导/提示/信任"体验 PRD**，大多是 Conditional Go、手测待签状态，且多数**不在** `docs/DOC-STATUS.md` 的现行治理表内（只有 `POST-MERGE-UX-FIXPACK` 被正式盖章追踪），说明它们游离在正式治理之外持续累积。

这恰恰是 Flipin 案例最该刺痛我们的地方：它全流程只有"选一种感觉"这一次决策，剩下全自动；而本项目却在不断地给用户"加提示层"来弥补体验缺口。`CHARTER.md` §7.2 第 9 条原则写得很清楚——"防搁置优先于功能堆叠"，**引导本身也是一种隐性的配置负担**，九个引导 PRD 叠起来，未必比"少一步决策"更接近北极星。

**建议**：在开下一个体验类 V1 文档之前，先做一次**"删除测试"**——找几个没看过任何文档的真人，把 Wait Tips / Help Onboarding 里能关的提示先关掉，看看完工率掉多少：

- 掉得不多 → 说明这些引导层的边际价值被高估了，应该合并/砍掉，而不是继续叠新文档；
- 掉得多 → 针对性保留那几个真正生效的触点，其余进入归档候选。

这是把 Flipin"一步到位"的启示，从"抄一个 vibe picker 功能"提升到"给整条体验层做减法"的方法论层面。

---

## 五、承接竞品分析的具体产品建议（按大局重新排序）

| 优先级 | 建议 | 为什么排在这个位置 |
|------|------|------|
| 1 | **"一句话选风格" vibe picker** | 不只是抄 Flipin 的开场问题，更重要的是它能**收编** MTSO/MSA/MEGC 这些"默认 off、悬而未决"的算法开关——把工程内部一堆布尔开关，收敛成用户能理解的"风格强度"选择，顺便解决第一节算法专题堆积问题的**用户侧出口** |
| 2 | **导出逐页勾选 + 清晰度像素提示** | 成本低，直接复用现有 `--scale`/platform 预设，是"完工体验"最后一米的真实缺口 |
| 3 | **封面/背景一键重掷** | 复用已经很强的 V6/Bookends 引擎，修正"能力强但触达路径重"的现状 |
| 4（P1，不急） | 抠图贴纸、多导出格式 | 挂靠 [PRD-COVER-ART-DIRECTION-V1.md](./PRD-COVER-ART-DIRECTION-V1.md)/[PRD-OUTPUT-RECIPE-V1.md](./PRD-OUTPUT-RECIPE-V1.md) 的增量，不新开文档 |

---

## 六、收口清单（可直接排期打勾）

> 本清单的目的：把"再开新 PRD"的默认动作，换成"先关掉/验证一个悬而未决项"。建议设置 WIP 上限——**同一时间悬而未决项 ≤ 3 条才允许开新专题**。

### 6.1 算法专题收口

- [x] `MSA` — AC-09 实册盲评完成 → **默认继续 off**（[msa-blind-review-2026-08-03](./acceptance-records/msa-blind-review-2026-08-03.md)）；pacing 副作用已记；**冻结重启**除非单独立项修 pacing
- [x] `MEGC` — PR-A/B/B2 + 狗粮 → **默认 on**；M3（P-释/P-函）**正式延期**，不排期
- [ ] `SSG` — 仍 Hold；阻塞为 **live 人脸门全跳过**（[ssg-face-metadata-gap-2026-08-03](./acceptance-records/ssg-face-metadata-gap-2026-08-03.md)）；先标定检测再谈 default on
- [x] `MTSO` — AC-11/12 收口 → **已转正 GA**（[mtso-ac11-ac12-closeout-2026-08-03](./acceptance-records/mtso-ac11-ac12-closeout-2026-08-03.md)）
- [x] **新增几何算法专题前闸**：已满足「至少 2 项收口」；下一产品切片改为 [LVP 一句话选风格](./PRD-LAYOUT-VIBE-PICKER-V1.md)，**不**新开几何 PRD

### 6.2 商业化验证收口

- [ ] （本阶段排除付款验证）CMZ 真实付款 — **暂不排期**
- [ ] 用人工发码 + 简单校验跑通最小闭环，把工程精细化推迟到验证通过后

### 6.3 AI 叙事解冻收口

- [ ] 给 NAS→AIR 的解冻设定具体日期（而非"待评审"）
- [ ] 或明确 AIR 的验收标准聚焦"事实校验闭环"，作为解冻前置条件写死在文档里

### 6.4 体验层 PRD 收口

- [ ] 做一次"真人删除测试"：关掉 Wait Tips / Help Onboarding 部分提示层，测完工率变化
- [ ] 基于测试结果，将 9 个体验类 V1 文档中确认边际价值低的部分标记为归档候选（`docs/archive/DOC-ARCHIVE-CANDIDATES.md`）
- [ ] 把仍保留的体验层文档补齐进 `docs/DOC-STATUS.md` 正式治理表，结束"游离于治理外持续累积"状态

### 6.5 竞品借鉴收口（低成本先行项）

- [x] "一句话选风格" vibe picker — 七席 Conditional Go · PRD v0.2 · 可 Kickoff M1（[评审](./acceptance-records/lvp-layout-vibe-picker-v1-review-2026-08-03.md)）
- [ ] 导出逐页勾选 + 清晰度像素提示（挂靠 Preview Export Facade / Output Recipe 增量）
- [ ] 封面/背景一键重掷按钮（复用 V6/Bookends）

---

## 七、一句话总结

Flipin 对比最大的价值，不是给了几个可以抄的 UI 交互，而是像一面镜子照出**本项目当前"往复杂处使劲"的惯性**——算法专题越开越多但都卡在盲评前，体验引导越叠越厚但北极星（首趟完工/敢发）尚未被"真人删除测试"验证过，商业化设计得很完整但一笔真实付款都还没收到。建议接下来一个阶段的主题不是"再开一个新 PRD"，而是**收口**：关掉/合并悬而未决的算法与体验分支，换成一次"收到第一笔真实付款"和一次"真人删除式可用性测试"。

---

## 变更记录

| 版本 | 日期 | 说明 |
|------|------|------|
| v1.1 | 2026-08-03 | 回写算法收口勾选；挂 LVP Draft；付款验证标为暂不排期；SSG 阻塞更正为 live 人脸门 |
| v1.0 | 2026-08-03 | 初稿：算法/商业化/AI 解冻/体验层四条优先级判断 + 可排期收口清单 |
