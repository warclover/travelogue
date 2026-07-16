# Output Recipe V1 · 跨职能评审纪要

| 属性 | 内容 |
|------|------|
| **评审对象** | [PRD-OUTPUT-RECIPE-V1.md](../PRD-OUTPUT-RECIPE-V1.md) **v1.0.0-OUTPUT-RECIPE**（Draft） |
| **评审日期** | 2026-07-14 |
| **形式** | 跨职能模拟评审（产品 · UI/UX · 用户流程 · 典型用户 · 社交资深用户 · 架构 · 工程 · 增长/商业） |
| **对照基线** | [PRD-LONGSHOT-2.0.md](../PRD-LONGSHOT-2.0.md) · [PRD-PREVIEW-EXPORT-FACADE-V1.md](../PRD-PREVIEW-EXPORT-FACADE-V1.md) · [SHARING.md](../SHARING.md) · [ADR-016](../adr/016-longshot-platform-export.md) · [CHARTER.md](../CHARTER.md) · [PRD-OVERSEAS-SHARE-PACK-V2.md](../PRD-OVERSEAS-SHARE-PACK-V2.md) · [TRAVELOGUE-PROJECT-BUSINESS-ASSESSMENT.md](../TRAVELOGUE-PROJECT-BUSINESS-ASSESSMENT.md) · `config/platform_profiles.yaml` |
| **结论状态** | **有条件通过（Conditional Go）** · **P0 已回写 PRD v1.1** · ACCEPTANCE / IMPLEMENTATION 已拆 · **未开工代码** |
| **记录人** | 跨职能联合纪要 |
| **回写** | [PRD-OUTPUT-RECIPE-V1.md](../PRD-OUTPUT-RECIPE-V1.md) v1.1.0 · [ACCEPTANCE-OUTPUT-RECIPE-V1.md](../ACCEPTANCE-OUTPUT-RECIPE-V1.md) · [IMPLEMENTATION-OUTPUT-RECIPE-V1.md](../IMPLEMENTATION-OUTPUT-RECIPE-V1.md) · [ADR-016 v0.5](../adr/016-longshot-platform-export.md) |

---

## 1. 与会角色

| 角色 | 关注点 |
|------|--------|
| **产品负责人** | 战略聚焦 vs 多场景；CHARTER；Ambiguous 是否滑向导出品类 |
| **UI / UX** | 主 CTA 语义、命名合同、认知负荷、词表一致性 |
| **用户流程** | 点击预算、书架/预览一致性、pending 叠层、失败回退 |
| **用户 · 摄影爱好者（≥50）** | 按章默认、再导出社交摘录、成书心流 |
| **用户 · 近郊（10–30）** | 真九宫格 vs 长图连读；三选一是否说人话 |
| **用户 · 极简（1–9）** | 不凑九宫格；默认发群是否可理解 |
| **资深微信用户** | 群长图 / 圈配图习惯；横三拼；publishGuide |
| **资深小红书用户** | 封面与笔记心智 vs 现网长卷 letterbox |
| **资深 Instagram 用户** | Overseas 钩子是否冒充原生 Carousel |
| **架构** | Recipe 层厚度、ADR-016 分支、Intent/Platform 分层 |
| **工程负责人** | Phase 切分、回归面、feature flag、工时 |
| **增长 / 商业** | 复用证据、付费锚、虚荣指标 |

---

## 2. 总评（一句话）

> **方向正确：Band × Intent → OutputRecipe 能同时避免「一律长图」与「平台设置中心」；最大阻塞不是愿景，而是 Phase A「九宫格文案 + scroll 后端」的预期债、`moments_grid` 尚未写入 ADR-016、以及 Overseas IG「默认可映射」措辞过激。**

**表决**：十二席综合 **有条件通过（Conditional Go）** · 附 §5 Must-Fix。

| 角色 | 表决 | 备注 |
|------|------|------|
| 产品 | Conditional Go | 战略 OK；须压住「社交导出器」心智、收窄 Phase A |
| UI / UX | Conditional Go | 分名赞；否决名实不符；词表须单一真相源 |
| 用户流程 | Conditional Go | 须冻书架/预览矩阵与 pending 优先级 |
| 摄影用户 | Conditional Go | 按章默认强支持；要再导出入口 |
| 近郊用户 | Conditional Go | 无真九宫格则勿承诺九宫格 |
| 极简用户 | Conditional Go | Sparse 默认发群正确 |
| 微信资深 | Conditional Go | 拆名刚需；横三拼规则升格决策 |
| 小红书资深 | Conditional Go | V1 须诚实标注「长卷适配配图」 |
| Instagram 资深 | Conditional Go | 仅 hook；Discovery 前不切 en 默认 |
| 架构 | Conditional Go | 须补分支 D；否决假九宫格过渡 |
| 工程 | Conditional Go | Phase A 锁范围 + feature flag |
| 增长/商业 | Conditional Go | 补复用指标；九宫格是表、成书是里 |

---

## 3. 分角色意见摘要

### 3.1 产品负责人

| 态度 | 要点 |
|------|------|
| ✅ 赞成 | §4.2 聚焦 Narrative 付费锚 / Ambiguous 复用 / 不做拼图品类，与商业评估一致 |
| ⚠️ 风险 | Ambiguous 把小红书抬到与发群等权，易把心智拉向「社交导出器」 |
| 📌 Must | 对外禁语：禁止「支持一切社交 / 全能导出」；三卡不等权（发群 > 九宫格 > 小红书） |
| 🔧 Should | Band 阈值标为可实验常量；默认成功态 Sparse/Narrative 仍是微信群长图 |

### 3.2 UI / UX

| 态度 | 要点 |
|------|------|
| ✅ 赞成 | 选意图不堆面板；朋友圈强制分名是本 PRD 最大 UX 贡献 |
| ⚠️ 风险 | 「选择分享方式」打断金色导出语义；OQ-OR-06 名实破产；附录 A 与 §7.2 文案不一致 |
| 📌 Must | 禁止「九宫格」指向 scroll；未交付 Writer 则入口不可用或「即将推出」；统一词表 |
| 📌 Must | Ambiguous 标题用「这趟精选了 N 张」；勿说 10–30「照片不多」 |
| 🔧 Should | OQ-OR-02 采纳「选择并导出」；记住偏好默认关 |

### 3.3 用户流程专家

| 态度 | 要点 |
|------|------|
| ✅ 赞成 | Sparse/Narrative 守 C1；Ambiguous 允许 +1 且可合并——与导出门面可共存 |
| ⚠️ 风险 | 书架 silent 发群 vs 预览强制意图；`layoutPending` vs `needs_intent` 未定义；intent 跨 Phase 迁移未写 |
| 📌 Must | 冻结入口一致性矩阵；注意力优先级 `layoutPending` > `needs_intent` > `longshotStale`；失败 CTA「换种分享方式」 |

### 3.4 摄影爱好者（≥50）

| 态度 | 要点 |
|------|------|
| ✅ 赞成 | Narrative 默认按章 + ≥50 强化，打中大图失败现实 |
| ⚠️ 风险 | 还要「再出一套发圈」；`kept_n` 28–35 可能误伤成书心流 |
| 📌 Must | ≥50 整卷须二次确认 + 风险文案 |
| 🔧 Should | Narrative 次入口「再导出九宫格/小红书」；不改默认 |

### 3.5 近郊用户（10–30）

| 态度 | 要点 |
|------|------|
| ✅ 赞成 | 强制显式意图正确；静默猜默认会双杀 |
| ⚠️ 风险 | 要的是相册九宫格，不是可变高长图切片；假九宫格真发出会翻车 |
| 📌 Must | 选项 B 仅在真 `moments_grid` 可用时上线 |
| 🔧 Should | 文案写清产物形态；小红书副文说明非笔记重排版 |

### 3.6 极简用户（1–9）

| 态度 | 要点 |
|------|------|
| ✅ 赞成 | 默认发群、不凑九宫格、禁止灌水 |
| ⚠️ 风险 | ▾ 仍露九宫格易误点；`kept_n=9` 常想发圈 |
| 📌 Must | Sparse 选 grid 时 UI 可见「有几张发几张」hint |
| 🔧 Should | `kept_n=9` 弱提示一次可切朋友圈（不阻断） |

### 3.7 资深微信用户

| 态度 | 要点 |
|------|------|
| ✅ 赞成 | 拆名刚需；现网 moments 本质是长图连载 |
| ⚠️ 风险 | 可变高切片发圈体验差；横竖混拼会丑；废片进九宫格 |
| 📌 Must | UI/YAML/platform 标识一致；OQ-OR-05 升格 D-OR；两套 publishGuide |
| 🔧 Should | grid 选图 Top-N / 可剔除 |

### 3.8 资深小红书用户

| 态度 | 要点 |
|------|------|
| ✅ 赞成 | Intent 绑定 3:4 / 1080×1440 与现网 profile 对齐 |
| ⚠️ 风险 | 笔记心智要封面；现网是长卷 letterbox——承诺与能力不匹配 |
| 📌 Must | 诚实标注 V1 =「杂志页适配为配图」，非笔记构图引擎 |
| 🔧 Should | Ambiguous 中 xhs 降权或进 ▾；评估关页脚 |

### 3.9 资深 Instagram 用户

| 态度 | 要点 |
|------|------|
| ✅ 赞成 | 只挂钩子、不重写 Overseas 页角色——边界正确 |
| ⚠️ 风险 | G-OR-10「Narrative 默认可映射 IG」对抗 Overseas「切片仅 Discovery A/fallback」 |
| 📌 Must | zh 默认永不被海外改写；preset 状态 `hook_only`；Discovery Go 前不切 en Narrative 默认 |
| 📌 Must | 改写 G-OR-10 措辞 |

### 3.10 软件架构师

| 态度 | 要点 |
|------|------|
| ✅ 赞成 | 纯函数 resolve + YAML；禁止 fork 策展；修订 D-LNG2-01 方式正确 |
| ⚠️ 风险 | ADR-016 无分支 D；Intent 与 Platform 压扁；字段面偏大；假九宫格污染 telemetry |
| 📌 Must | 增补 ADR-016 分支 D `photo_grid_pack`；`intent → preset → engine` 分层；否决 OQ-OR-06 |
| 🔧 Should | V1 schema 瘦身；`custom` 挪 Phase D |

### 3.11 工程负责人

| 态度 | 要点 |
|------|------|
| ✅ 赞成 | A→B→C 切分合理；Go 要求导出门面回归 |
| ⚠️ 风险 | xhs 未稳就进三选一回归爆炸；横三拼 2–4 周偏乐观；trip.`output` 是 schema 变更 |
| 📌 Must | Phase A 仅 Band+resolve+CTA+发群/连读；grid/xhs 进 B；`studio.output_recipe.enabled` flag |
| 🔧 Should | B 再拆 B0 contain / B1 三拼；首周分配 `E_OR_*` |

### 3.12 增长 / 商业

| 态度 | 要点 |
|------|------|
| ✅ 赞成 | Sparse 建信 / Ambiguous 复用 / Narrative 付费与三证据链同构 |
| ⚠️ 风险 | 缺的是复用与支付证据，不是第三平台；九宫格是表、成书是里 |
| 📌 Must | 补 Ambiguous 30 日二次导出率；Narrative≥50 发群手测率 |
| 🔧 Should | 付费实验不绑 Recipe；对外仍讲杂志游记 |

---

## 4. 对照冲突速查

| 基线 | 冲突点 | 严重度 |
|------|--------|--------|
| 导出门面 C1 | Ambiguous 强制意图；书架/预览不一致 | P0 |
| LNG2 D-LNG2-01 | 默认改由 resolve；须交叉引用 | P0 |
| LNG2 / `wechat_moments` | 切片 ≠ 九宫格 | P0 |
| ADR-016 三分支 | grid 无归属 | P0 |
| OQ-OR-06 | 名实不符预期债 | **P0 否决项** |
| Overseas D-OV2-04/14 | G-OR-10 过激 | P0 |
| SHARING 路径 A | 「九宫格替代」vs 真九宫格并存 | P1 |
| CHARTER | 勿滑向内容工厂 / 设置 OS | P1 |
| 商业评估 | 优先复用证据 | P1 |

---

## 5. P0 Must-Fix（关闭后方可进 Phase B / 拆 IMPLEMENTATION）

| # | 项 | 责任 |
|---|----|------|
| **P0-1** | **否决 OQ-OR-06**：禁止「九宫格」文案映射 scroll；未交付 Writer 则不可用或「即将推出」 | 产品 + UX + 工程 |
| **P0-2** | 增补 **ADR-016 分支 D**（`photo_grid_pack` / `moments_grid` Writer 合同） | 架构 |
| **P0-3** | 冻结 Ambiguous **入口矩阵**（预览强制 / 书架 fallback / CLI 必参）；关闭 OQ-OR-01 | 产品 |
| **P0-4** | 冻结 `layoutPending` > `needs_intent` > `longshotStale`；失败回退 CTA | UX + 产品 |
| **P0-5** | G-OR-10 降级为 hook-only；zh 不被海外改写；Discovery 前不切 en 默认 | 产品 + Overseas |
| **P0-6** | Phase A **范围锁**：resolve + CTA + 发群/连读；真九宫格与 xhs 主卡进 Phase B；feature flag | 工程 + 产品 |
| **P0-7** | 用户可见词表单一真相源（主 CTA / 成功态 / 双朋友圈命名） | UX |
| **P0-8** | AC 增补名实一致性；导出门面 C1 在 Sparse/Narrative 回归签字 | 工程 + QA |

---

## 6. P1 Should-Fix

| # | 项 |
|---|----|
| **P1-1** | Ambiguous 三卡不等权；xhs 诚实标注「长卷适配配图」 |
| **P1-2** | OQ-OR-02 采纳；OQ-OR-04/05 升格 D-OR |
| **P1-3** | Narrative≥50 整卷二次确认；grid Top-N / 可剔除 |
| **P1-4** | SHARING / LNG2 头部交叉引用（实施阶段） |
| **P1-5** | 字段瘦身；Intent/engine/platform 分层；custom → Phase D |
| **P1-6** | 埋点补漏斗与复用指标；Band 阈值回看计划 |
| **P1-7** | Phase B 拆 B0/B1；xhs footer 策略 |
| **P1-8** | 对外禁语表；避免「平台覆盖数」虚荣指标 |

---

## 7. 评审决议

1. **裁决**：有条件通过。接受 Band × Intent → OutputRecipe；聚焦 Narrative 成书，Recipe 服务多发行，不转为拼图/社交导出品类。
2. **强制修订后再开 Phase B**：否决假九宫格过渡；补 ADR-016 分支 D；关闭 OQ-OR-01；Overseas IG 仅 hook。
3. **Phase A 批准范围**：`kept_n` Band + `resolve_output_recipe` + Sparse/Narrative 主 CTA + Ambiguous 意图（发群 / 长图连读）+ 导出门面 C1 回归；真 `moments_grid` 与小红书主意图卡放入 Phase B。
4. **保留 LNG2**：`wechat_moments` 不废除；UI 一律称「朋友圈 · 长图连读」，与「朋友圈 · 九宫格」分名。
5. **修订关系**：D-LNG2-01 改为由 resolve 决定（Sparse/Narrative 仍常为 `wechat_chat`）；交叉引用在 IMPLEMENTATION 回写。
6. **通过条件**：P0-1～P0-8 关闭并升 PRD 版本号后，方可拆 ACCEPTANCE / IMPLEMENTATION。

---

## 8. 会前 / 会后必须拍板的 OQ

| ID | 拍板内容 | 决议建议 | 拍板人 |
|----|----------|----------|--------|
| **OQ-OR-01** | 书架 Ambiguous 无 intent | **否强制**；fallback 发群 + 弱提示 | 产品 ✅ 建议关闭 |
| **OQ-OR-02** | 意图卡「选并导出」 | **是** | 产品 + UX |
| **OQ-OR-06** | Phase A grid→scroll | **否** | 全员否决 |
| **OQ-OR-03** | en Sparse 默认 | **先 archive longshot** | Overseas 联席 |
| **G-OR-10** | en Narrative 默认 IG | **否（仅 hook）** | 产品 + Overseas |
| **OQ-OR-04** | grid 画布 | **1:1 contain** | 产品 |
| **OQ-OR-05** | 横三拼 | **横仅与横拼；竖独立** | 产品 + 工程 |
| **Phase A 意图集** | 是否含 xhs/grid | **A 仅发群+连读** | 工程 + 产品 |
| **ADR 增补** | grid 新分支 | **是 · 分支 D** | 架构 |

非阻塞：OQ-OR-07 schema 版本策略 → IMPLEMENTATION。

---

## 9. 主持结语

本 PRD 的价值不在「又多几个平台」，而在 **承认 10–30 张不可猜，并强迫产品说人话**。最大危险已写在风险表：做成设置中心、朋友圈两套认知混乱、用假九宫格透支信任。

**有条件通过 = 收窄 Phase A、否决名实欺诈、补 ADR、锁海外钩子。** 满足后再拆验收与实施；否则应驳回重写范围。

---

## 10. P0 关闭核对（文档回写）

| # | 项 | 状态 |
|---|----|------|
| P0-1 | 否决 OQ-OR-06 / D-OR-17 | ✅ PRD v1.1 |
| P0-2 | ADR-016 分支 D | ✅ ADR v0.5 |
| P0-3 | 入口矩阵 / OQ-OR-01 | ✅ D-OR-16 · §8.3 |
| P0-4 | pending 优先级 | ✅ D-OR-21 |
| P0-5 | G-OR-10 hook_only | ✅ PRD §2.1 / §7.4 |
| P0-6 | Phase A 范围锁 | ✅ §7.3 / §14 · IMPLEMENTATION |
| P0-7 | 词表单一真相源 | ✅ 附录 C |
| P0-8 | AC 名实 + C1 | ✅ ACCEPTANCE |

**代码开发**：未启动；见 IMPLEMENTATION「开工检查单」。

---

## 11. 文档修订历史

| 版本 | 日期 | 说明 |
|------|------|------|
| v1.0 | 2026-07-14 | 首版跨职能评审纪要 · Conditional Go · P0-1～P0-8 |
| v1.1 | 2026-07-14 | 记录 P0 文档回写完成 · 链到 PRD v1.1 / ACCEPTANCE / IMPLEMENTATION / ADR-016 v0.5 |
