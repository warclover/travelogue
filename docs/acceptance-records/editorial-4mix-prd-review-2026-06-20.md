# screen-editorial-4mix PRD 评审会纪要

| 属性 | 内容 |
|------|------|
| **会议** | 四图横竖交错拼图（editorial-4mix）PRD 跨职能评审 |
| **日期** | 2026-06-20 |
| **文档** | [PRD-screen-editorial-4mix.md](../PRD-screen-editorial-4mix.md) v0.1 → **v0.2** |
| **前置参考** | [PRD-portrait-row-editorial.md](../PRD-portrait-row-editorial.md) v0.3（已落地 PR-1～PR-5）、[PRD-screen-editorial-2land.md](../PRD-screen-editorial-2land.md) v0.1 |
| **发起人** | 产品负责人 |
| **结论** | **有条件通过** — 可进入 P0（PR-1）；须合并 §4 决议升版 **v0.2** 后开工 |

---

## 1. 参会与角色

| 角色 | 代号 | 关注点 |
|------|------|--------|
| **产品负责人** | PM | 杂志拼贴差异化、与三竖 editorial / 2land 定位切分、试点节奏 |
| **版式 / BSP 设计** | DES | 行等高脚线、横图 25% 克制、Z 字动线、文案不抢图 |
| **排版工程 / LTE** | ENG | YAML 权重、skip_stage_aspect、双 CSS、注册表完整性 |
| **策展算法** | ALG | 2L+2P 窗口、chess 重排、与 mosaic-4 / 2land 优先级 |
| **渲染工程** | FE | copy overlay、fit 策略、generic contain 覆盖风险 |
| **摄影社区顾问** | PHO | 横竖混排裁切、人物 contain、杂志 mockup 对标 |
| **QA** | QA | AC 可测化、Playwright bbox、golden 零 diff |
| **零编辑用户代言人** | UX80 | 默认关开关、纯照片 collapse、mobile 不断裂 |

---

## 2. 议程与讨论摘要

### 2.1 需求方向（一致通过 · 全票赞成）

**PM**：4mix 填补「双横 stack 太平 / mosaic 太密 / 三竖 editorial 无横图」的中间带——**2 横 + 2 竖棋盘 + 短文案**，对标用户 mockup 的杂志拼贴页。

**DES**：固定 TL/BR 横、TR/BL 竖的 **chess 位置** 比自由混排更可预期；上行权重 3、下行 2 与参考图一致，**赞成**。

**UX80**：默认关闭 + trip 显式开关，与 portrait-row 一致——**赞成**；担心 4 图 + 文案一屏信息过密。

**决议**：

- 4mix **立项通过**；定位与 PRD §1–§2 不变。
- 一屏视为 **「停顿—拼贴」屏**：同章 **≤1** 个 editorial composite（与 2land 共享 rhythm 配额，见 §2.6）。

---

### 2.2 开放问题 O-4M-01～04（产品已拍板 · 评审确认）

| ID | 问题 | 产品决议 | 评审会 |
|----|------|----------|--------|
| **O-4M-01** | Kicker/Body **独立 grid 行** vs **浮层 overlay** | **P0 overlay**（照片块外缘条带）；**P1** 扩 LTE `rows: [1,3,2,1]` + `intentionalGaps` 正式 rect | ✅ 全票。ENG：overlay 与 2land P0 路径一致，不阻塞 CSS 验 AC |
| **O-4M-02** | 横图 25% 指 **槽面积** vs **img 可见面积** | **槽面积**（与 2land 一致）；cover 时 img 可见可略大于槽 | ✅ 同意。AC-4M-03 量测 **`.layout-slot` bbox** |
| **O-4M-03** | 镜像变体（对角互换） | **P2** · 新 pattern `screen-editorial-4mix-mirror`；P0–P1 **不做** | ✅ 同意。避免 P0 双套 CSS |
| **O-4M-04** | 与 `screen-mosaic-4` 共存优先级 | **editorial-4mix 优先**：同 4 槽窗口且 `editorial4Mix` enabled 时，MCS 选 4mix 而非 generic mosaic-4 | ✅ 同意。ALG：须 `denseBudgetExempt` + 显式 `pattern_preference` |

> 以上四项 **闭合**，自 v0.2 起从 §10「开放项」移至 §1 已拍板决策。

---

### 2.3 行等高与脚线（DES + FE · 修订通过）

**DES**：

- 「行等高」指 **Row1 内 TL 横与 TR 竖槽顶/底 bbox 齐**、Row2 内 BL/BR 同理——与三竖 editorial 脚线族一致，**赞成** D-03。
- **争议**：TR 竖槽 LTE 面积 36%，竖图 contain 后可能窄条居中，是否破坏「满宽杂志感」？

**FE**：

- 竖槽 **stretch 行高** + `object-position: bottom center` 已验证于 portrait-row；4mix 需 **独立 grid 类**，避免 `:has(.layout-slot__img--contain)` 通用规则覆盖（三竖 editorial 教训）。

**PHO**：

- 人物竖槽 **contain + 脚线** 非 negotiable；风景竖槽 P2 才考虑 cover 随机。

**决议**：

- AC-4M-04/05 量测 **槽 bbox**（非 img 可见像素）；Portrait 槽面积 **不设** 25% 上限 AC。
- CSS 选择器 **必须** `:not([data-pattern="screen-editorial-4mix"])` 排除通用 contain 覆盖（**A4**）。
- §12.8 视觉 note：**竖槽宽于 img 时两侧留白为预期**，非 bug。

---

### 2.4 文案区与 2land parity（PM + DES · 通过附条件）

**PM**：4 照片槽 + Kicker/Body 是明确产品要求；`copy-display=photos` collapse 后应呈现 **纯四图棋盘**（与 mockup 一致）。

**DES**：Kicker 顶、Body 底，Z 字动线 **Kicker → TL → TR → BL → BR → Body**；文案 maxChars 与 2land 对齐（30/80）。

**UX80**：纯照片模式 **不得** 留空框 DOM（与 2land G-E2L-06 同口径）。

**决议**：

- P0 overlay 文案 **占位但不挡照片槽 rect**；collapse 时 `display: none` + **0 高度**，非透明占位。
- 新增 **AC-4M-10**：`copy-display=photos` 时 DOM 无 `.layout-copy--kicker` / `--body` 可见节点。
- P1 再对齐 2land 的 `copySlots` schema 与 inline-edit E2E。

---

### 2.5 横图面积 25% ±3%（DES + QA · 通过）

**QA**：AC-4M-03 在 **1440×viewport** 量测；需 fixture 固定 16:9 舞台占位与 skip_stage_aspect 后 intrinsic 高度。

**ENG**：`cols [2,3] · rows [3,2]` 下单格 ≈24% 符合 ±3%；**行 gutter** 从舞台扣除后再验，避免假红。

**决议**：

- AC-4M-03 验收环境：**1440px 宽 · 默认 journal CSS · 含 overlay 文案条**（文案 collapse 模式下单测另列）。
- Playwright bbox 测试 **仅 P0 fixture**（人工选 2L+2P 金样）；Safari flaky 时 skip 同 portrait-row 策略。

---

### 2.6 Planner / MCS 与 rhythm（ALG · 有条件赞成）

**ALG**：

- 窗口：**连续或同 burst 2 landscape + 2 portrait**（顺序任意）→ planner 重排 `[L,P,P,L]`。
- **争议**：与 2land 同章 `max_per_chapter: 1` — 指 **任一** editorial composite（2land **或** 4mix），非各 1。

**ENG**：`denseBudgetExempt: true` 须写入 template meta，否则 Phase 21 误判 4 槽 dense。

**决议**：

- rhythm 键 **`editorial_composite_per_chapter: 1`**（2land 与 4mix **互斥**）（**A6**）。
- MCS：`enabled` 且窗口匹配时，4mix base_weight **0.88** > mosaic-4 generic；无 copy 信号时不降级。
- 横图 hero 分最高者默认 **TL**（slot 0）；次高 **BR**（slot 3）（**A7**）。

---

### 2.7 工程范围与 PR 切分（ENG · 赞成 · 沿用 portrait-row 经验）

**ENG**：建议 **5 PR** 切分，P0 **不上** planner 自动替换：

| PR | 阶段 | 内容 |
|----|------|------|
| **PR-1** | P0 | LTE YAML + CSS 棋盘 + skip_stage_aspect + blur 登记 + 手工 `patternId` 验 AC-4M-03/04/05/07 |
| **PR-2** | P1a | 注册表 + config + `_maybe_editorial_4mix` + rhythm + scope 单测 |
| **PR-3** | P1b | copy overlay + inline-edit + AC-4M-06/10 |
| **PR-4** | P1c | mobile 拆 **4×** 单槽（TL→TR→BL→BR）+ §12.4 连带 |
| **PR-5** | P2–P3 | 风景竖 cover 随机 + probe + dogfood 对比页 |

**FE**：PR-4 **独立 revert**；与 PR-2 不捆绑。

**决议**：

- Kickoff 顺序：**PR-1 先行**；PR-2/PR-3 可部分并行；**PR-4 阻塞 mobile 试点**。
- 配置优先级冻结：`trip.export.editorial4Mix` > allowlist > global `enabled`（**A3**）。

---

### 2.8 Mobile 拆屏（UX80 + ENG · 通过）

**UX80**：4 图一屏在手机上必须拆；顺序 **TL→TR→BL→BR** 保持 Z 字叙事。

**ENG**：继承 portrait-row §12.4：**longshot 不拆**；folio plate **仅 slot 0（TL）** inherit；breath 锚点不变。

**决议**：

- 新增 **AC-4M-11**：mobile HTML 无 `layout-screen__grid--editorial-4mix` 整块；展开 4× `screen-portrait-1` 或等价单槽。
- 新增 **AC-4M-12**：longshot 面不出现四连展开。

---

### 2.9 明确不在 P0–P1（再次确认）

| 项 | 处理 |
|----|------|
| `screen-editorial-4mix-mirror` | P2 |
| planner 自动替换（无 config） | P0 禁止；手工 trip 验视觉 |
| legacy mosaic-4 / landscape-2 契约改动 | 不做 |
| 用户主路径手选 pattern UI | 不做 |
| 2land PRD 范围（双横无竖） | 并行产品线，不合并 |
| probe baseline PNG | P3（P0–P2 skip 或 xfail） |

---

## 3. 评审会决议清单（Action Items）

| ID | 事项 | 负责人 | 阶段 |
|----|------|--------|------|
| **A1** | PRD 升版 **v0.2**（闭合 O-4M、§12 实施附录、新 AC） | PM | 会后 ✅ |
| **A2** | PR-1：LTE YAML + 双 CSS + skip_stage_aspect | ENG | P0 |
| **A3** | `is_editorial_4mix_enabled()` 单一入口 + 配置优先级文档化 | ENG | P1 |
| **A4** | generic contain 规则加 `:not([data-pattern="screen-editorial-4mix"])` | FE | P0 |
| **A5** | 金样 fixture：2L+2P 人物/风景各 1 套 | QA | P0 前 |
| **A6** | `editorial_composite_per_chapter` rhythm（2land∥4mix 互斥） | ALG | P1 |
| **A7** | chess 重排 + TL hero 优先规则 + 单测 | ALG | P1 |
| **A8** | AC-4M-10/11/12 写入 PRD §8 | QA | 会后 ✅ |
| **A9** | dogfood ≥5 屏 blind review 门槛（G-4M-01） | PM | P3 前 |
| **A10** | `tests/test_editorial_4mix.py` 面积 + bbox golden 骨架 | QA + ENG | P0 |

---

## 4. 各专家书面意见汇总

| 专家 | 总评 | 主要意见 | 处理 |
|------|------|----------|------|
| **PM** | ✅ 通过 | 与三竖/2land 差异化清晰；坚持默认关 | 维持 |
| **DES** | ✅ 通过 | 行等高脚线；竖槽留白预期；Z 字动线 | §12.8 |
| **ENG** | ✅ 有条件 | 5 PR 切分；注册表 checklist；probe P3 前 skip | §12 PR 表 |
| **ALG** | ✅ 有条件 | 4mix > mosaic-4；editorial composite 互斥 | A6、A7 |
| **FE** | ✅ 有条件 | contain 覆盖排除；copy collapse DOM | A4、AC-4M-10 |
| **PHO** | ✅ 通过 | 人物 contain；风景 cover 延 P2 | §6 维持 |
| **QA** | ✅ 有条件 | bbox AC 1440 fixture；mobile/longshot AC | A5、A8 |
| **UX80** | ✅ 通过 | 默认关；纯照片无空框；mobile 顺序 | AC-4M-10/11 |

---

## 5. 风险登记

| 风险 | 级别 | 缓解 |
|------|------|------|
| 竖槽 36% 面积但 img 窄条 — 「不满宽」观感 | 中 | §12.8 产品 note；非 AC 失败 |
| generic contain CSS 覆盖 4mix 脚线 | 中 | A4 + `test_lte_css_sync` |
| 2land 与 4mix 同章争抢 rhythm | 低 | `editorial_composite_per_chapter: 1` |
| mobile 四连拆屏破坏 folio/plate | 中 | plate 仅 TL；AC-4M-12 |
| §11 注册表漏改 | 中 | PR-2 checklist 逐项 tick |
| probe ≠ web intrinsic 态 | 中 | P3 前 skip；同 portrait-row §12.5 |

---

## 6. 下一步

1. 合并决议发布 [PRD-screen-editorial-4mix.md](../PRD-screen-editorial-4mix.md) **v0.2**，状态 → **Approved · 待 P0 Kickoff**。  
2. **R0**（只测不改）：手工改 1 份 trip `patternId=screen-editorial-4mix`，浏览器验行等高 + 25% 横槽 + collapse。  
3. **PR-1 Kickoff**：LTE YAML + CSS；**不**改 planner。  
4. P3 前完成 **G-4M-01** dogfood blind review（≥4/5 屏不劣于 mosaic-4 / 双竖组合）。

---

## 7. 版本

| 版本 | 日期 | 说明 |
|------|------|------|
| v1.0 | 2026-06-20 | editorial-4mix PRD 跨职能评审会纪要 |
