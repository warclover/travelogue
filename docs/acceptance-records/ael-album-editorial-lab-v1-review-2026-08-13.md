# PRD-ALBUM-EDITORIAL-LAB-V1 · 七席评审纪要

| 属性 | 内容 |
|------|------|
| **文档** | [PRD-ALBUM-EDITORIAL-LAB-V1.md](../PRD-ALBUM-EDITORIAL-LAB-V1.md)（**AEL** · 画册编辑试验床） |
| **触发备忘** | [智能模板建议0813.md](../智能模板建议0813.md) · 产品确认：参考 40 页更适合单独升画册，验证 EDC W1+W2 内核 |
| **相邻挡门** | [ECC](../PRD-EXPORT-CARD-COMPOSE-V1.md) · [ABE](../PRD-ALBUM-EXPORT-BOOKENDS-V1.md) · [ADR-021](../adr/021-export-compose-dual-engine.md) · [EDC](../PRD-EDITORIAL-COMPILER-V1.md) · [MSA](../PRD-MOSAIC-SLOT-ADAPTATION-V1.md)（默认 off）· `crop_solver` · `card_grouper` / `card_renderer` / `card_templates` · FRP · NAS |
| **评审版本** | PRD **v0.1.0** → Must-Fix 回写后升 **v0.2.0** |
| **日期** | 2026-08-13 |
| **结论** | **有条件通过（Conditional Go · 主线可冻结；L0 隔离可 Kickoff；L1 合码挡 BLK-AEL-01/02/04/07；L2 挡 BLK-AEL-05/08；通行证挡 BLK-AEL-06）** |
| **编码** | ☑ 策划回写 v0.2　☐ L0 旗+cfg 穿线+xhs 金样　☐ L1 SSC 增量　☐ L2 角色　☐ L3 探针 |
| **参评角色（七席）** | 产品 · 算法 · 架构 · 开发 · 测试/QA · 视觉/排版（ECC·装裱）· 用户体验（狗粮手测） |
| **评审方式** | 分席只读 PRD v0.1 §0～§12 · D/G/AC/OQ + **对照现网**（`CARD_TEMPLATES` / `_ALL_TEMPLATES`、`plan_cards`、`assign_photos_to_slots`、`card_renderer` 一律 cover、`collage_pack` `_ = cfg`、`crop_solver.solve_slot_focal`、`msa_fit.crop_risk_for_pair`、ABE 书衣、AC-ECC-01 单测、import-linter 分层） |
| **记录人** | 七席联合纪要（跨职能模拟联评 · 基于 2026-08-13 PRD v0.1.0 + 代码事实核查） |
| **本纪要状态** | **已结案 · Conditional Go** · **PRD v0.2.0 已回写 BLK-AEL-01～08** · **v0.2.1 产品补记见本文 §11（非二次七席）** |
| **审查基线** | 编辑器不是模板工厂 · 只动画册 · 不打开 MSA · 默认可达零外呼 · 零步不增加 · 画册绿 ≠ EDC 80% 门 · **不把现网已有能力写成新开关** · **探针不得泄漏进 CARD_TEMPLATES** |

---

## 0. 会前宣读（主持人）

1. **切口**：用 `album_spread` 当 EDC 的选图×裁切试验床，不是把 40 页纸书搬进默认库，也不是先动 16:9 全书。  
2. **已拍（勿重开）**：只动画册；28 套成熟库为退路；先测裁切再上 3～5 探针；本轮无字无胶带；不打开 MSA；零步。  
3. **勿重开**：Canva 手填、运行时生模板、纸书第二引擎、打开 MSA、LVP 第三卡、把画册观感当 EDC W3。  
4. **本场必拍**：运行时模板权威是 Python registry 不是 md 目录；同卡换槽在等权宫格上是否空转；`crop_risk` 能否从 export 直接 import `msa_fit`；FRP 是否真在画册路径上；通行证会不会把已 Go 的 EDC W0/W1 绑死；`collage_pack` 现网丢弃 `cfg`。  
5. **OQ-AEL-01～06** 本场关闭。

---

## 1. 总评（一句话）

> **七席一致 Conditional Go：主线立得住——画册当试验床、联立环、成熟库为退路、通行证写死「绿了也不能跳 EDC W3」，比空喊「把 40 页自动化」可验收。但 v0.1 有六处按原文 Kickoff 会假绿或打穿小红书：（1）探针若只放进 `docs/templates/card-aspect-3x4/`，运行时 `CARD_TEMPLATES` / `AVAILABLE_SLOT_COUNTS` 会让 xhs 看见；（2）`crop_risk_for_pair` 住在 `msa_fit.py`，export 直接 import 等于把 MSA 模块拖进画册；（3）等权宫格槽 AR 全同，「同卡换槽」在 L1 是空操作，只能 contain；（4）G-AEL-08「像素级」与 PNG 压缩/AC-AEL-03 模板序列打架；（5）现网画册根本不跑 FRP，AC-AEL-12「不回退」是假回归；（6）通行证把 EDC W1 绑在 L1+L2 之后，过粗，且 `collage_pack` 现网 `_ = cfg`，旗不穿进去等于没旗。关 BLK 后升 v0.2；L0 可合隔离与穿线；L1 只做 28 套上的裁切增量。**

---

## 2. 分席表决

| 席位 | 表决 | 一句话 |
|------|------|--------|
| **产品** | **Conditional Go** | 切口对：先画册、不抄 40 套、不做字胶带。对外不能说「画册还不会裁」——focal cover 每天都在跑；也不能说「试验绿了全书就像那本册」。通行证必须拆开，别把 EDC W0 文档工作停掉。 |
| **算法** | **Conditional Go** | 联立环对。L1 真正增量是：人脸 clipped→contain/换槽，以及无人脸时的 crop_risk contain。等权宫格换槽不改 AR，必须写明「仅槽 AR 不同才换」。合影用 `faces[]` 并集，不能只信可能缺失的 `quality.faceCount`。judge 不准进默认环。 |
| **架构** | **Conditional Go** | export→`crop_solver` 分层合法（export 在 layout_engine 之上）。**禁止** import `layout_engine.mosaic.msa_fit`（拖 `SlotAdaptationConfig`）。探针独立 `PROBE_TEMPLATES`，不得写入 `_ALL_TEMPLATES`。角色枚举与 EDC 一张表，默认不改 schema 同意。 |
| **开发** | **Conditional Go** | L0 开工面：把 `cfg` 穿进 `export_collage_pack`（现网丢弃）、album 分支读旗、xhs 仍走 `plan_cards_for_feed`。L1：Renderer 增 contain 绘槽；`solve_slot_focal` 包一层风景风险；同卡匈牙利仅异 AR 槽。探针目录只是文档，运行时要第二份 registry。 |
| **测试 / QA** | **Conditional Go** | AC-AEL-03 / NFR-05 测模板 id 序列 + 槽朝向，**禁止**像素哈希。现网 `test_render_card_covers_every_pixel_no_background_bleed` 是 AC-ECC-01，album contain 不得改红这条。L1 出门要有「卡数/模板序列不漂」的金样。盲评 1 产品 + 1 非作者，打乱 A/B。 |
| **视觉 / 排版** | **Conditional Go** | 槽内 contain 必须杂志纸色，否则「得体」=「没铺满」。等权宫格一旦大量 contain，画册会从「密铺磁砖」变成「格子里的明信片」——这是气质变化，L1 盲评要能解释留白，不能默默上。探针默认关、每 spread 最多一张，同意。 |
| **用户体验 · 狗粮** | **Conditional Go** | 导出仍一键。不要把 AEL 写到面板上。contain 多了用户会问「为什么有白边」——提示说「为了不切到人/天」，不说失败。无 Key 必须仍能导出。封面封底别在本轮被裁切实验伤到。 |

**汇总**：**7/7 Conditional Go**。未回写 Must-Fix 前 **不批无条件 Go** · **不批 L1 合码** · **不批 L3 编码**。

**对齐评分**

| 维度 | 分（/10） | 说明 |
|------|-----------|------|
| 问题→方案因果完整度 | **8** | P-AEL-01～05 真；试验床切口对 |
| 与现网能力对齐 / 防假绿 | **6** | 人像 focal 已写明 As-Is；FRP/换槽/md 目录三处仍假绿 |
| 与 ECC/MSA/EDC 边界 | **7** | 不绑 MSA、不代替 EDC W3 对；探针泄漏与 msa_fit import 未钉 |
| 工程可开工性 | **7** | L0 穿线面清晰；L1 contain 绘槽是新路径 |
| AC 可测性 | **7** | 夹具好；像素级合同必须改掉 |
| 通行证可签核性 | **8** | 「画册绿 ≠ EDC 80%」写死了；W1/W2 应拆开 |

---

## 3. 事实核查（对照现网 · 影响结论）

| # | PRD v0.1 假设 | 代码事实（2026-08-13） | 会中 |
|---|----------------|------------------------|------|
| **F-01** | 三出口共用 CardGrouper / Renderer | `collage_pack`：xhs/mp 走 `plan_cards_for_feed`；album 走 `plan_cards(..., avoid_immediate_repeat=True)` + ABE；Renderer 同源 | **属实**；隔离必须在 album 分支与独立 registry，不能只靠 md 子目录 |
| **F-02** | 聚类只是平局打破 | `card_grouper` 模块文档写死：不要求分镜；`assign_photos_to_slots` 只按朝向队列 | **属实**；L2 软聚类须另传 asset 元数据（现 `plan_cards` 只收 `Path`） |
| **F-03** | 槽内一律 cover；AC-ECC-01 铺满 | `card_renderer._paint_template` 只 `crop_aspect_focal`；`test_render_card_covers_every_pixel_no_background_bleed` 断言无底色 | **属实**；album contain 是**新绘槽路径**；该单测属 xhs/ECC，不得改红 |
| **F-04** | 28 套；仅 card-4 顶部 1.125 需裁 | `_ALL_TEMPLATES` **28** 条；`AVAILABLE_SLOT_COUNTS` 由其派生 | **属实** |
| **F-05** | 画册未接 `crop_solver` | export **零** `layout_engine` import；人脸走 `focalPoint` + 人像偏置 | **属实**；L1 才接入。分层上 export→layout_engine **合法** |
| **F-06** | 探针放 `docs/.../probes/` 即可隔离 | 运行时权威是 `card_templates.py` 的 `_ALL_TEMPLATES` → `CARD_TEMPLATES`；`plan_cards` 遍历 `CARD_TEMPLATES.values()` | **修正**：md 子目录**不会**自动隔离；写入 `_ALL_TEMPLATES` 会立刻改变 xhs 供给算法 |
| **F-07** | 可调用 `crop_risk_for_pair` | 函数在 `layout_engine.mosaic.msa_fit`，模块顶层 import `SlotAdaptationConfig`；函数本身不算 MSA 开关 | **修正**：公式可抽到 `crop_solver`；**禁止** export import `msa_fit` |
| **F-08** | L1 同卡换槽有用 | `assign_photos_to_slots` 按横/竖两池填；`card-9/16-grid-equal` 等槽 AR 全同，换槽不改 `display_aspect` | **修正**：异 AR 才换；等权宫格 L1 只能 contain |
| **F-09** | `collage_pack` 可读实验旗 | `export_collage_pack(..., cfg=...)` 现网 **`_ = cfg` 丢弃** | **修正**：L0 必修穿线，否则旗是死合同 |
| **F-10** | AC-AEL-12「FRP 不回退」 | 画册路径无 FRP / `subjectClass=food` 处理；只消耗 kept 池 | **修正**：现网没有可回归的 FRP 行为；L2 写成「美食不得升主槽」 |
| **F-11** | G-AEL-08 像素级不变 | PNG 压缩头、字体、时间戳都会漂；AC-AEL-03 已写模板序列 | **修正**：以序列+朝向为准 |
| **F-12** | `quality.faceCount ≥ 3` 即合影 | `crop_solver.faces_from_asset` 读 `faces[]` / `salientBox`；旧 trip 常缺 `faceCount`（见 SSG 人脸元数据缺口） | **修正**：`max(faceCount, len(faces))`；皆缺则不当 group |
| **F-13** | 通行证 L1+L2 才开 EDC W1/W2 | EDC v0.2 已 Conditional Go：W0 文档可 Kickoff；W1 是 layout 侧 SSC 增量 | **修正**：AEL L1 绿 → EDC W1；AEL L2 绿 → EDC W2；**不挡 EDC W0** |
| **F-14** | 不打开 MSA | `slot_adaptation` 默认 off | **属实 · 保持** |
| **F-15** | ABE 封面封底已落地 | `collage_pack` album 分支先 `_try_album_bookends` 再剔正文池 | **属实**；本主题不 SSC 书衣 |

**会中新增事实**

- `solve_slot_focal`：无 face/protect 时 `feasible=True` 的 cover，风景切边不会触发 contain——与 EDC F-01 同一增量定义。  
- 小红书走 `plan_cards_for_feed`（质量切块 + 开篇宫格），画册走 `plan_cards` + `avoid_immediate_repeat`。共享的是 `CARD_TEMPLATES` 与 Renderer，不是同一条 `plan_*` 入口。  
- ABE 横图封面已 contain/letterbox（`card_bookends`），与正文 cover 合同本来就不同。

---

## 4. 全场共识

1. **主线冻结**：画册试验床，不是模板工厂，不是 EDC 替代验收。  
2. **L1 只做增量**：28 套上接 `crop_solver` + 风景 crop_risk contain + **异 AR** 同卡换槽；换模板不准进 L1。  
3. **探针独立 registry**：`PROBE_TEMPLATES`，禁止进入 `_ALL_TEMPLATES` / `AVAILABLE_SLOT_COUNTS`。  
4. **crop_risk 公式下沉 `crop_solver`（或等价无 MSA 依赖模块）**；不 import `msa_fit`。  
5. **通行证拆开**：AEL L1 绿 → 可 Kickoff EDC W1；AEL L2 绿 → 可 Kickoff EDC W2；不挡 EDC W0；画册绿仍 ≠ EDC W3。  
6. **回归尺是模板序列**，不是像素。  
7. **L1–L3 默认可达零外呼**；mosaic_judge 不进默认环。  
8. **OQ-01～06** 按产品倾向关闭（见 §7）。  
9. **人脸硬闸 / NAS / 零步 / 不打开 MSA** 不回退。

---

## 5. Must-Fix（阻塞 · 升 v0.2 前关闭）

| ID | 议题 | 要求（冻结一字面） | 挡 | 状态 |
|----|------|-------------------|----|------|
| **BLK-AEL-01** | 探针 md 子目录 ≠ 运行时隔离 | **D-AEL-22**：探针进独立 `PROBE_TEMPLATES`；禁止写入 `_ALL_TEMPLATES` / `CARD_TEMPLATES` / `AVAILABLE_SLOT_COUNTS`。`plan_cards` 默认仍只见成熟库。 | L1 合码（registry 形状 L0 可先做） | ✅ **已回写 v0.2.0** |
| **BLK-AEL-02** | export import `msa_fit` | **D-AEL-23**：`crop_risk_for_pair` / `aspect_mismatch` 抽到 `crop_solver`（或 `layout_contract`）。export **禁止** import `travelogue.layout_engine.mosaic`。不打开 `slot_adaptation`。 | L1 合码 | ✅ **已回写** |
| **BLK-AEL-03** | G-AEL-08 像素级 | **D-AEL-24**：xhs/海报回归 = 模板 id 序列 + 槽朝向分配（允许压缩头差异）。禁止像素哈希当 AC。 | L0 验收 | ✅ **已回写** |
| **BLK-AEL-04** | 同卡换槽在等权宫格空转 | **D-AEL-21**：仅当卡内存在 **不同** `displayAspect` 时换槽；等权宫格 L1 失败链 = contain。禁止为换槽而打破朝向硬门。 | L1 合码 | ✅ **已回写** |
| **BLK-AEL-05** | FRP「不回退」假回归 | **D-AEL-29**：现网画册不执行 FRP。L2 合同改为：美食不得升为 `vista` / 主槽。AC-AEL-12 同步改写。 | L2 编码 | ✅ **已回写** |
| **BLK-AEL-06** | 通行证过粗、绑死 EDC | **D-AEL-25**：AEL L1 绿 → EDC W1；AEL L2 绿 → EDC W2；**不挡 EDC W0**。L3 仍不等于 EDC W3。 | 通行证 / EDC 排期 | ✅ **已回写** |
| **BLK-AEL-07** | `cfg` 被丢弃 | **D-AEL-27**：L0 必须把实验旗从 config 穿进 `export_collage_pack` 的 album 分支。父关且子键全 false ≡ GA。 | L0 合码 | ✅ **已回写** |
| **BLK-AEL-08** | 合影只信 `faceCount`；judge 可能外呼 | **D-AEL-26 / D-AEL-28**：合影人数 `max(quality.faceCount, len(faces))`，皆缺则不当 group。L1–L3 默认环 **零** mosaic_judge / LLM。 | L1 合码 · L2 角色 | ✅ **已回写** |

**Should-Fix（不阻塞 v0.2）**

| ID | 建议 | 状态 |
|----|------|------|
| **SHD-AEL-01** | L2 `plan_cards` 增可选 asset 元数据参数（默认 None），xhs 调用点不传 | L2 |
| **SHD-AEL-02** | contain 纸色对齐 `DEFAULT_BG=(245,245,243)`（OQ-03 结案） | L1 |
| **SHD-AEL-03** | 现网 AC-ECC-01 单测保持；album contain 另测「槽内可见纸色且主体完整」 | L1 |
| **SHD-AEL-04** | 拆 ACCEPTANCE / IMPLEMENTATION | L0 Kickoff |
| **SHD-AEL-05** | 本主题不对 ABE 封面/封底跑 SSC（横图书衣已 contain） | 共识 |
| **SHD-AEL-06** | EDC 实施侧：W1 与 AEL L1 共用求解器适配，避免两套 crop 增量 | 排期 |
| **SHD-AEL-07** | 狗粮三册钉名：`demo-d6697c8dca` · `demo-2025` · `demo-49cbe46479`（MSA 盲评同口径） | OQ-01 |
| **SHD-AEL-08** | L1 盲评须能解释「密铺→偶发明信片留白」的气质变化，避免用户当成回归 | 出门文案 |

---

## 6. 典型用户提问 Q&A

| 提问 | 会中回应 |
|------|----------|
| 导出会不会让我选手填模板、自己裁？ | 不会。仍是一键导出画册。 |
| 为什么有的格子旁边有浅色边？ | 为了不切到脸、合影里的人或天际线。这是试验；过盲评前默认关。 |
| 小红书会不会一起变？ | 不会。试验只作用在画册。 |
| 导出后会不会变成那 40 页带大标题的册？ | 本轮不会。先保证选对图、裁得体；标题和胶带是以后的事。 |
| 没有配 AI 还能导出吗？ | 能。这三波都不靠外呼。 |
| 试验好了是不是游记预览也会一起升级？ | 裁切和角色规则可以迁过去；章节扉页和长图节奏要另验，不会因为画册好看就直接开。 |

---

## 7. 开放问题结案

| ID | 结案 |
|----|------|
| **OQ-AEL-01** | ✅ 狗粮三册：**`demo-d6697c8dca`（混排）· `demo-2025`（东澳岛）· `demo-49cbe46479`（近全单反/长途）**。与 MSA 盲评同口径。 |
| **OQ-AEL-02** | ✅ 夹具 **100%**；狗粮探针卡不得新增砍头红线，A 维 ≥ 同册成熟卡。 |
| **OQ-AEL-03** | ✅ contain 纸色 = CardRenderer `DEFAULT_BG` **`(245, 245, 243)`**。 |
| **OQ-AEL-04** | ✅ `group_face_min = 3`，人数口径见 D-AEL-28。 |
| **OQ-AEL-05** | ✅ L2 **允许**因换同槽数模板导致卡数变化，须记账；禁止无故碎成大量 1 槽卡（硬顶：1 槽卡占比不得高于 GA +10 个百分点，实施钉进单测）。 |
| **OQ-AEL-06** | ✅ 探针 **4** 套（square / tall / wide / hero-mix）+ 现成 `card-4` 作对照。第 5 套有设计稿再立项，不进 V1。 |

> 产品补记 2026-08-13：第 5 套设计稿已到（p18 三连瘦条）。**混出 4 套的七席结案不变**；第 5 套以评测-only 立项，见 §11。

---

## 8. 决策表（相对 v0.1 增改）

| ID | 相对 v0.1 |
|----|-----------|
| D-AEL-07 | 补异 AR 条件（D-AEL-21） |
| D-AEL-11 | 改为调用下沉后的 crop_risk，禁止 import mosaic |
| D-AEL-14 | 运行时权威改为 `PROBE_TEMPLATES`，md 目录只是文档 |
| G-AEL-08 | 像素级 → 序列+朝向 |
| §8 通行证 | 拆 L1/L2 |
| **D-AEL-21～29** | 新增（本场 BLK 关闭项） |

---

## 9. Kickoff 门（回写后）

| 波次 | 条件 |
|------|------|
| **L0** | v0.2 已回写；可合实验旗、`cfg` 穿线、xhs 序列金样、诊断骨架 |
| **L1** | L0 绿；BLK-01/02/04/07/08 合同在代码里可测；禁止换模板 |
| **L2** | L1 出门门；BLK-05；`plan_cards` 可选资产元数据 |
| **L3** | L1+L2 出门；混出 4 套在独立 registry；`probe-triptych` 评测-only；配额单测 |
| **EDC W0** | **不挡**（已 Go） |
| **EDC W1** | 建议 AEL L1 出门后（共享 SSC） |
| **EDC W2** | 建议 AEL L2 出门后（共享角色表） |
| **EDC W3** | AEL **不能**批准 |

---

## 10. 签字（模拟联评）

| 角色 | 结论 | 日期 |
|------|------|------|
| 产品 | Conditional Go | 2026-08-13 |
| 算法 | Conditional Go | 2026-08-13 |
| 架构 | Conditional Go | 2026-08-13 |
| 开发 | Conditional Go | 2026-08-13 |
| 测试 / QA | Conditional Go | 2026-08-13 |
| 视觉 / 排版 | Conditional Go | 2026-08-13 |
| 用户体验 · 狗粮 | Conditional Go | 2026-08-13 |

---

## 11. 产品补记（2026-08-13 · 非二次七席）

对照约 40 页参考图后，产品确认：

1. **混出 4 套**钉参考页：P-square←p22、P-tall←p21、P-wide←p08 上条、P-hero-mix←p12。只复刻槽几何。  
2. **P-triptych**（p18「一座城的普通一天」）作为第 5 套进入 `PROBE_TEMPLATES`，**评测-only**，不进默认 mix allowlist，不替代 P-tall。兑现 OQ-AEL-06「有设计稿再立项」。  
3. **p33「细节留在记忆里」**常用页任务的是五个角色标签，不是又一种异常 AR。标签映射进 L2 现有枚举（D-AEL-31）；五槽几何 **不进**探针（N-AEL-17）。

合同已回写 PRD **v0.2.1**（D-AEL-30/31 · AC-AEL-26/27）。不重开七席。
