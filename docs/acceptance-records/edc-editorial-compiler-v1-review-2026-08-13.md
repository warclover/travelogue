# PRD-EDITORIAL-COMPILER-V1 · 七席评审纪要

| 属性 | 内容 |
|------|------|
| **文档** | [PRD-EDITORIAL-COMPILER-V1.md](../PRD-EDITORIAL-COMPILER-V1.md)（**EDC** · 编辑编译器） |
| **触发备忘** | [智能模板建议0813.md](../智能模板建议0813.md) |
| **相邻挡门** | LTE · MCS/MTSO · MSA（默认 off）· LVP · SCR · P23 · FRP · [ADR-020](../adr/020-narrative-contract.md) · `crop_solver` · `breath_pauses.py` |
| **评审版本** | PRD **v0.1.0** → Must-Fix 回写后升 **v0.2.0** |
| **日期** | 2026-08-13 |
| **结论** | **有条件通过（Conditional Go · 主线可冻结；W0 文档/schema 可 Kickoff；W1 合码挡 BLK-EDC-01/04；W3 挡 BLK-EDC-02/03/06）** |
| **编码** | ☑ 策划回写 v0.2　☐ W0 schema+纸面页数　☐ W1 SSC 增量　☐ W2 角色　☐ W3 纲领+扉页（80% 门） |
| **参评角色（七席）** | 产品 · 算法 · 架构 · 开发 · 测试/QA · 视觉/排版（LTE·装裱）· 用户体验（狗粮手测） |
| **评审方式** | 分席只读 PRD v0.1 §0～§12 · D/G/AC/OQ + **对照现网**（`crop_solver.apply_slot_crop_focals`、`insert_breath_screens_in_chapters`、ADR-020 `narrativeRole`、LVP `magazine_default`、`chapter-separator`） |
| **记录人** | 七席联合纪要（跨职能模拟联评 · 基于 2026-08-13 PRD v0.1.0 + 代码事实核查） |
| **本纪要状态** | **已结案 · Conditional Go** · **PRD v0.2.0 已回写 BLK-EDC-01～06** |
| **审查基线** | 编辑器不是模板工厂 · 不打开 MSA · 默认可达零外呼 · 零步不增加 · 80% 是语法量尺 · **不把现网已有能力写成新开关** |

---

## 0. 会前宣读（主持人）

1. **切口**：自动化的是「主编」（选页、配角色、保主体裁切），不是运行时发明模板。北极星是人类手工排版约 80% 的**编辑语法**，不是 40 页参考书像素。  
2. **已拍（勿重开）**：总 PRD 管线；W1 裁切先盲评再默认开；W3 每章 +1 扉页、breath 有条件；不绑 MSA；不改舞台 AR。  
3. **勿重开**：Canva 手填、运行时生模板、纸书对页第二画布、打开 MSA、LVP 第三卡、GNR 全书装裱分级（已 superseded）。  
4. **本场必拍**：现网 `crop_solver` 已默认跑，W1 增量是什么；`program` vs `narrativeRole`；密插 breath vs「每章 +1」；失败链换 pattern 与 AC-EDC-05；LVP GA 定义；扉页 vs `chapter-separator`。  
5. **OQ-EDC-01～05** 本场关闭。

---

## 1. 总评（一句话）

> **七席一致 Conditional Go：主线立得住——要的是编辑编译器而不是模板工厂；80% 五维量尺可签核，比空喊「更有艺术感」可验收。但 v0.1 把三件现网事实写成了「待建设能力」，按原文 Kickoff 会假绿或把册做更长：（1）人像保主体裁切已在默认路径写入 `cropFocal`；（2）`screen-breath-pause` 已按约每 4 张内容屏密插，与「每章最多 +1 breath」直接冲突；（3）ADR-020 已有 `narrativeRole`，再写一套 `program` 会双真相。另：失败链「换模板」会改屏构成，打穿 AC-EDC-05；SSC 进 LVP 推荐会改写 AC-LVP-01；扉页巨字可能与现网章分隔标题叠两层。关 BLK 后升 v0.2；W0 可做 schema 与三册页数纸面模拟；W1 只做裁切增量，不得把现网人脸求解再包一层开关。**

---

## 2. 分席表决

| 席位 | 表决 | 一句话 |
|------|------|--------|
| **产品** | **Conditional Go** | 80% 操作化通过，N-EDC-08/09 把文笔和像素克隆剔出去是对的。但对外不能说「我们还没有智能裁切」——用户册里已经在做人像 object-position。W3 若在密插 ··· 之上再加扉页，长图会更劝退，画册感不会更好。OQ-01 极小章跳过扉页、OQ-02 章名优先：同意。 |
| **算法** | **Conditional Go** | 角色→纲领→模板顺序对。W1 真正增量是：无人脸时的 crop_risk contain，以及**同屏换槽**。换 pattern 会改 MCS 胜出，等于把裁切分反馈进选型——MSA 盲评就是这样把页数打飞的。风景地平线模型不进 W1（OQ-03 关）。`editorialRole` 规则表保守：不确定不降级。 |
| **架构** | **Conditional Go** | `program` 必须是 `narrativeRole` 的上层或映射，禁止 layoutScreen 两个互不翻译的枚举。`editorialHints` 默认 false 且不改 screens；W3 消费的真实挂钩是 `insert_breath_screens_in_chapters` 与节奏 post-check，不是 CAP-14 hint。schema `additionalProperties: false`，W0 必须扩字段否则 trip 无法落盘。 |
| **开发** | **Conditional Go** | W1 可开工面：扩展 `solve_slot_focal` / contain 条件 + 同屏匈牙利换槽；挂点已在 `screen_planner_stages` persist cropFocal。不要再做「父开关 false 时卸载现网 crop」。W3 必须先改 `DEFAULT_INTERVAL=4` 的插入政策，再谈 opener YAML。长图 flatten 学 SCR，opener 不能丢。 |
| **测试 / QA** | **Conditional Go** | AC-EDC-01「父关 ≡ GA」若把现网 crop 也关掉，金样会大面积红。须改成：父关 ≡ 关闭前 GA（含已有人像求解）。AC-EDC-05 要测「W1 增量不改章内内容屏张数」；breath 屏张数是 W3 的尺。80% 门禁止用开发者未打乱标签的自评当绿。OQ-05：1 产品 + 1 非作者，通过。 |
| **视觉 / 排版** | **Conditional Go** | 扉页把字当建筑——要，但现网已有 `chapter-separator` 章名。两层巨字是廉价不是杂志。有 opener 则该章分隔降为细线或不上标题。contain 留白须杂志纸色（MSA BLK-06 可借），否则「得体」会被看成「没铺满」。工艺 W4 微倾可做；默认满胶带否决。 |
| **用户体验 · 狗粮** | **Conditional Go** | 零步同意。不要新向导。LVP 仍两卡；推荐气质变了要改那句「后果」，不能 silently 多留白。现网有的册已经 ··· 太多（仙本那类），先少插呼吸、再加「出发」，不要又加又留。无 Key 必须仍能出册。 |

**汇总**：**7/7 Conditional Go**。未回写 Must-Fix 前 **不批无条件 Go** · **不批 W1 合码** · **不批 W3 编码**。

**对齐评分**

| 维度 | 分（/10） | 说明 |
|------|-----------|------|
| 问题→方案因果完整度 | **8** | P-EDC-01～06 真；「主编层」切口对 |
| 与现网能力对齐 / 防假绿 | **5** | v0.1 把 crop/breath/narrativeRole 写成待建 |
| 与 MSA/LVP/ADR-020 边界 | **6** | 不绑 MSA 对；LVP GA 与 program 双枚举未钉 |
| 工程可开工性 | **7** | W1 增量面清晰；W3 依赖 breath 政策改写 |
| AC 可测性 | **7** | 80% 量尺好；AC-01/05 须按 As-Is 改写 |
| 80% 可签核性 | **8** | 五维 + 红线 + 相对 GA；N 条挡住加码 |

---

## 3. 事实核查（对照现网 · 影响结论）

| # | PRD v0.1 假设 | 代码事实（2026-08-13） | 会中 |
|---|----------------|------------------------|------|
| **F-01** | 保主体裁切是待建主战场 | `apply_slot_crop_focals` 已对 **cover 槽**求解并写 `cropFocal`；人脸 clipped 才 contain flip；无人脸则中心/focal cover，**不**因 crop_risk contain | **修正**：W1 增量 = 风景高风险 + 同屏换槽，不是从零接入求解器 |
| **F-02** | `cropFocal` 可扩展、不必新键 | schema 已有 `cropFocal` / `cropContain` / `cropSafety`；`additionalProperties: false` | **属实**（扩展，不改名） |
| **F-03** | breath 只写 hint、W3 才消费 | `insert_breath_screens_in_chapters` **默认 interval=4** 密插；`editorial_hints` 默认 **false** 且 **不 mutate screens** | **修正**：W3 是治理密插，不是从零插入 |
| **F-04** | 可新写 `screens[].program` | ADR-020 已冻结 `narrativeRole`：`plate/hero_single/stack/pair/mosaic_hero/mosaic_flat/breath` | **修正**：必须映射，禁止平行真相 |
| **F-05** | 每章 +1 breath 可控 pacing | 实证册可出现数十个 `breath-pause`（BSP）；再 + opener 会叠加 | **属实风险** |
| **F-06** | 换模板失败链不影响页数 | MCS 换 pattern / 换窗宽会改屏数（MSA 盲评：24→17 blocks） | **AC-EDC-05 与 D-EDC-12 原文冲突** |
| **F-07** | LVP 推荐可吸收 SSC | AC-LVP-01：`magazine_default` ≡ MTSO on · MEGC on · MSA **off**；剖面无 crop 键 | **须改写 GA 定义，不能静默** |
| **F-08** | 扉页是新的字建筑 | `chapter-separator` 已渲染章名；长图也读分隔标题 | **叠字风险** |
| **F-09** | schema 可先写 trip 再补 | `layoutScreen` / asset **additionalProperties: false** | **W0 必修 schema** |
| **F-10** | `screen-breath-pause` 在 LTE YAML 库 | **无**对应 YAML；特殊 pattern + 专用 hbs | **属实**；opener 才走 YAML 准入 |
| **F-11** | 不打开 MSA | `slot_adaptation` 默认 off；LVP 实验才开 | **属实 · 保持** |
| **F-12** | layout_critic 不改 chapters | `run_layout_critic` 只写 `layoutSuggestions[]` | **属实 · 保持** |

**会中新增事实**

- `solve_slot_focal`：无 face/protect 时直接用 prefer focal + cover，**feasible=True**，风景切边不会触发 contain。  
- 长图另有 `interleave_breath_items`（interval=4）；紧凑档可跳过 breath（SFI）。W3 须同时改 web 屏与长图 interleave，否则三模式叙事合同再次分叉（ADR-020 D1）。

---

## 4. 全场共识

1. **主线冻结**：编辑编译器，不是模板工厂；80% = §7 五维量尺；运行时不生模板；不打开 MSA。  
2. **W1 只做增量**：现网人像求解保持默认开；新增风景高风险 contain + **同屏换槽**；换 pattern **不准进 W1**。  
3. **W3 先治 breath、再加扉页**：EDC `program.enabled` 时接管插入政策（每章有条件 ≤1 次有高度的 breath），关闭 interval=4 密插；父关则回现网密插（GA）。  
4. **`program` 映射 `narrativeRole`**：一张表，可推导；缺 `program` 的旧 trip fail-open。  
5. **有 opener 的章，章分隔标题让路**（细线或无标题），禁止双巨字。  
6. **SSC 进推荐气质必须改 LVP 剖面与「后果」文案**，并修订 AC-LVP-01 的 GA 含义（另条记录，不在本主题偷偷改）。  
7. **OQ-01～05 按产品倾向关闭**（见 §7）。  
8. **L0 / NAS / 零步 / 人脸硬闸** 不回退。

---

## 5. Must-Fix（阻塞 · 升 v0.2 前关闭）

| ID | 议题 | 要求（冻结一字面） | 挡 | 状态 |
|----|------|-------------------|----|------|
| **BLK-EDC-01** | 把现网 crop 写成待建且默认 off | **D-EDC-21**：As-Is 人像 `crop_solver` 保持默认可达。W1 开关只控**增量**（风景 crop_risk contain、同屏换槽）。AC-EDC-01 父关 ≡ 关闭增量，**不得**卸载现网人脸求解。 | 策划→v0.2 · W1 合码 | ✅ **已回写 v0.2.0** |
| **BLK-EDC-02** | `program` 与 `narrativeRole` 双真相 | **D-EDC-22**：W0 出映射表；`program` 可空并由 `narrativeRole`+pattern 推导。禁止第二套互不翻译枚举。AC-EDC-21。 | W3 编码 · schema | ✅ **已回写** |
| **BLK-EDC-03** | 密插 breath vs 每章 +1 | **D-EDC-23**：`program.enabled` 时 **禁用** `DEFAULT_INTERVAL=4` 密插；改为每章有条件 ≤1 次 breath（有可读高度）。长图 `interleave_breath_items` 同步。父关回 GA 密插。 | W3 编码 | ✅ **已回写** |
| **BLK-EDC-04** | 换 pattern 打穿 AC-EDC-05 | **D-EDC-12 收窄**：W1 失败链 = 同屏换槽 → contain。换同 `photoCount` 的 pattern 最早 W2，且须单测「内容屏张数不变」。 | W1 合码 | ✅ **已回写** |
| **BLK-EDC-05** | LVP GA 被静默改写 | **D-EDC-24**：W1 增量默认 on 出门时，同步修订 LVP：`magazine_default` 剖面 + SSC 增量；更新推荐卡「后果」一句；AC-LVP-01 增补记录。W1 实验期 LVP 文案不承诺。 | W1 默认 on | ✅ **已回写** |
| **BLK-EDC-06** | 扉页与章分隔叠字 | **D-EDC-25**：该章存在 `program=opener` 且标题非空 → `chapter-separator` 不上章名（可保留分隔线）。长图同样。 | W3 编码 | ✅ **已回写** |

**Should-Fix（不阻塞 v0.2）**

| ID | 建议 | 状态 |
|----|------|------|
| **SHD-EDC-01** | W0 三册纸面模拟：现网密插 breath 数 vs EDC 配额后的屏数/长图高度 | W0 |
| **SHD-EDC-02** | contain 底色对齐 MSA 杂志纸色 | W1 |
| **SHD-EDC-03** | `journal` 枚举保留，V1 只映射现有 editorial/SCR 屏，不新引擎（OQ-04） | 已锁 |
| **SHD-EDC-04** | 拆 ACCEPTANCE / IMPLEMENTATION | W0 Kickoff |
| **SHD-EDC-05** | 与 GNR/HGM：不复活全书装裱分级；opener 不是 mountLevel | 共识 |
| **SHD-EDC-06** | 开发可行性备忘：挂点 `screen_planner_stages` persist、curate 末尾 breath 插入 | W0 可写短 SUP |

---

## 6. 典型用户提问 Q&A

| 提问 | 会中回应 |
|------|----------|
| 以后出册还要我选模板、裁图吗？ | 不要。默认仍是选相册 → 出游记。精修可改，不是主路径。 |
| 为什么有的图旁边有白边？ | 为了不切到脸或地平线。W1 过盲评才会变成推荐默认；不喜欢可关实验。 |
| 每章开头会不会又多一页大字？ | 合格章最多一页扉页；照片很少的章会跳过。有扉页时原来的章名条会让路，避免写两遍。 |
| 中间那些「···」会不会更多？ | 目标是更少、更像换气。打开页纲领后不再每四屏插一个。 |
| 没有配 AI 还能出册吗？ | 能。这三波都不靠外呼。 |
| 会不会变成那种歪贴胶带的手帐？ | 默认不会。那是以后可选气质，且默认关。 |

---

## 7. 开放问题结案

| ID | 结案 |
|----|------|
| **OQ-EDC-01** | ✅ **跳过**。layoutEligible &lt; 4 的章不强制 opener。 |
| **OQ-EDC-02** | ✅ 标题优先级：**章名 → 地名 → 皆空则跳过 opener**。 |
| **OQ-EDC-03** | ✅ W1 **不上**地平线/显著物模型；用 AR 错配 + crop_risk。系统性切地平线再拆 SSC 子 PRD。 |
| **OQ-EDC-04** | ✅ 枚举保留 `journal`；V1 映射现有屏，不新增长文引擎。 |
| **OQ-EDC-05** | ✅ 盲评至少 **1 产品 + 1 非作者**；开发者可评但必须打乱 A/B。 |

---

## 8. 决策表（相对 v0.1 增改）

| ID | 会中 |
|----|------|
| D-EDC-01～11、13、15～20 | **维持** |
| **D-EDC-03** | **改写**：现网人像求解保持默认开；「先盲评再默认开」只适用于 W1 **增量** |
| **D-EDC-04** | **维持配额**；实现改为接管密插（D-EDC-23） |
| **D-EDC-12** | **收窄**见 BLK-04 |
| **D-EDC-14** | **补映射**见 D-EDC-22 |
| **D-EDC-21～25** | **新增**（BLK-01～06） |

---

## 9. 里程碑（评审后）

| 波次 | 评审后口径 |
|------|------------|
| **W0** | **可 Kickoff（文档）**：schema 扩字段、映射表、三册页数纸面模拟、拆 AC/IMPL |
| **W1** | 关 BLK-01/04 后可合码；增量默认 off；盲评只评 A 维 + **内容屏张数不漂移** |
| **W2** | 角色规则；换同 photoCount pattern 最早本波 |
| **W3** | 关 BLK-02/03/06；80% 全量门；插入单独可回滚 |
| **W4/W5** | 维持；不挡 80% |

---

## 10. 签字

| 席位 | 签字（模拟） | 日期 |
|------|--------------|------|
| 产品 | Conditional Go | 2026-08-13 |
| 算法 | Conditional Go | 2026-08-13 |
| 架构 | Conditional Go | 2026-08-13 |
| 开发 | Conditional Go | 2026-08-13 |
| 测试 / QA | Conditional Go | 2026-08-13 |
| 视觉 / 排版 | Conditional Go | 2026-08-13 |
| 用户体验 · 狗粮 | Conditional Go | 2026-08-13 |

---

## 11. 变更记录

| 版本 | 日期 | 说明 |
|------|------|------|
| v1.0 | 2026-08-13 | 七席结案 · Conditional Go · BLK-EDC-01～06 回写 PRD v0.2.0 |
