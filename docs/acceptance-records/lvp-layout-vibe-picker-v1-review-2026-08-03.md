# PRD-LAYOUT-VIBE-PICKER-V1 · 跨职能评审纪要

| 属性 | 内容 |
|------|------|
| **文档** | [PRD-LAYOUT-VIBE-PICKER-V1.md](../PRD-LAYOUT-VIBE-PICKER-V1.md)（**LVP** · 一句话选风格） |
| **模板来源** | [lvp-layout-vibe-picker-v1-review-TEMPLATE.md](./lvp-layout-vibe-picker-v1-review-TEMPLATE.md) |
| **相邻挡门** | [MTSO](../PRD-MOSAIC-TEMPLATE-SELECTION-OPTIMIZATION-V1.md) · [MEGC](../PRD-MOSAIC-EQUAL-GRID-CONTRACT-V1.md) · [MSA](../PRD-MOSAIC-SLOT-ADAPTATION-V1.md) · [SSG](../PRD-SMART-SHOT-GROUPING-V1.md) · [CAD](../PRD-COVER-ART-DIRECTION-V1.md) · [FTUE](../PRD-FTUE-OPTIMIZATION-V1.md) · [智能排版开关页](../PRD-智能排版开关页.md) · [战略复盘](../INSIGHT-STRATEGIC-PRIORITY-REVIEW-2026-08-03.md) |
| **验收 / 实施** | Kickoff 后拆 ACCEPTANCE / IMPLEMENTATION（本纪要 BLK-LVP-02） |
| **评审版本** | **v0.1.0 Draft** → Must-Fix 回写后升 **v0.2.0** |
| **日期** | 2026-08-03 |
| **结论** | **有条件通过（Conditional Go）** |
| **编码** | ☑ **可 Kickoff M0（文档冻结）**　☑ **可 Kickoff M1（配置剖面 + 持久化）**　□ M2 UI 待 BLK-LVP-03/04　□ M3 可选延期 |
| **参评角色（七席）** | 产品 · 算法 · 架构 · 开发 · 测试/QA · 视觉/排版 · 用户体验（狗粮手测） |
| **评审方式** | 分席只读 PRD §0～§9 · D/O 表 + **对照现网**（GA 默认栈 · MSA 盲评 · SSG 人脸探针 · Studio 精修 Sheet 触点） |
| **记录人** | 七席联合纪要（跨职能模拟联评 · 基于 2026-08-03 算法收口与代码触点核查） |
| **本纪要状态** | **已结案 · Conditional Go** · **PRD v0.2.0 已回写** |
| **审查基线** | MTSO **GA** · MEGC **默认 on** · MSA **默认 off（AC-09 不通过）** · SSG look **Hold**（live 人脸门） |

---

## 0. 会前宣读（主持人）

1. **切口**：LVP = **用户语言收编已落地算法**，不是新几何、不是风格商店。  
2. **实锤**：仓库默认已是 MTSO on + MEGC on + MSA off，但 Studio **无产品句**说明气质；MSA 有实验价值但盲评否决默认 on，且有 pacing 副作用。  
3. **勿重开**：MTSO/MEGC/MSA 各自默认决策、MEGC M3、SSG look 默认 on、付款/CMZ。  
4. **本场必拍**：D-LVP-01～08 · O-01/02/03 · 两卡是否假选择 · 回滚路径。  
5. **列车**：先 M1 剖面/持久化，再 M2 UI；禁单 PR 夹带新算法或 SSG look。

---

## 1. 总评（一句话）

> **七席一致 Conditional Go：问题真实（算法已转正、用户侧无出口），解法切口正确（两卡映射、不新开几何）；默认卡必须与 GA 栈字节级等价，实验卡才能开 MSA 且必须二次确认分页风险。O-01～03 按 PRD 倾向关闭。M1 可 Kickoff；M2 挡在实验文案签字与三册狗粮。SSG look / 付款明确不进本主题。**

---

## 2. 分席表决

| 席位 | 表决 | 一句话 |
|------|------|--------|
| **产品** | **Conditional Go** | 收编开关是战略复盘 P0 用户侧出口；两卡够用，反对第三卡「全关」制造假对比 |
| **算法** | **Conditional Go** | 映射表正确：MTSO+MEGC 已共同构成推荐栈，拆成「电影 vs 单反」两卡会假选择；MSA 才是需知情同意的差分 |
| **架构** | **Conditional Go** | `trip.studio.layoutVibe` 优先于进程 config 的优先级链要写死；与 `/lse-flags-admin` 正交必须单测锁 |
| **开发** | **Conditional Go** | M1 落点清晰（剖面解析 + 持久化）；UI 挂 `preview-sheet` 封面区同级可复用 apply-layout；勿新造等待面 |
| **测试 / QA** | **Conditional Go** | AC-01/02 可测；AC-06「可感知差异」须允许「无加权屏则差异小」免假绿；回滚路径要进验收 |
| **视觉 / 排版** | **Conditional Go** | 卡片只写人话与后果，禁止 MTSO/MEGC/MSA 缩写上卡面；实验标必须可见 |
| **用户体验 · 狗粮** | **Conditional Go** | 入口勿阻塞首访；导入后弱提示一次可接受；实验卡无「分页可能变」确认会重演 MSA 盲评挫败 |

**汇总**：**七席 7/7 Conditional Go**。  
- **M0**：文档冻结 ✅（本纪要 + PRD v0.2）。  
- **M1**：可 Kickoff（关闭 BLK-LVP-02 拆文后合码）。  
- **M2**：BLK-LVP-03/04 关闭前 **不批** UI 合入。  
- **M3**：默认延期（与 CAD 同屏编组可选）。

**对齐评分**

| 维度 | 分（/10） | 说明 |
|------|-----------|------|
| 问题→解法完整度 | **9** | 与 Flipin/战略复盘对齐；不发明算法 |
| 与 MTSO/MEGC/MSA/SSG 边界 | **9** | 不重开默认；look 明确排除 |
| 工程可开工性 | **8** | M1 清晰；优先级链与 Studio 触点已锚 |
| AC 可测性 / 防假绿 | **7** | AC-06 已留「无加权则差异小」；须写进 ACCEPTANCE |
| 视觉/文案可签核性 | **6** | 实验确认句仍属草案，挡 M2 |

---

## 3. 事实核查（对照现网）

| # | 假设 | 会中 |
|---|------|------|
| **F-01** | 仓库 `selection_optimization.enabled` 默认 true（MTSO GA） | ✅ 属实（`config.yaml.example`） |
| **F-02** | 仓库 `equal_grid_contract.enabled` 默认 true（MEGC） | ✅ 属实 |
| **F-03** | 仓库 `slot_adaptation.enabled` 默认 false（MSA） | ✅ 属实 |
| **F-04** | MSA AC-09 盲评不通过；存在 pacing 副作用 | ✅ 属实（[msa-blind-review-2026-08-03](./msa-blind-review-2026-08-03.md)） |
| **F-05** | SSG look 在 demo-2025 实拍 `lookEncoded=0`（人脸门） | ✅ 属实（[ssg-face-metadata-gap](./ssg-face-metadata-gap-2026-08-03.md)） |
| **F-06** | Studio 精修 Sheet 已有封面版式区与 apply-layout | ✅ 属实（`features.js` / `core.js`） |
| **F-07** | `/lse-flags-admin` 为研发 LSE 能力页，非 C 端 | ✅ 属实 |

**新增事实（评审发现）**

| # | 事实 | 影响 |
|---|------|------|
| **F-08** | PRD D-LVP-01 文案「两个正式 + 一个实验」易与 §4「一荐一实验」混淆 | → **D-LVP-01 改写**：V1 = **1 推荐 + 1 实验**；`film_wide` 不交付 |
| **F-09** | 本机用户 `config.yaml` 常驻与仓库默认可能不一致 | → 优先级链：`trip.layoutVibe` > 进程 overlay > 仓库默认；LVP 应用时写 trip 并驱动 layout，避免「选了推荐仍跟本机 YAML」 |
| **F-10** | LVP 可整卡下线回滚，算法栈独立 | → AC 增 **AC-LVP-08** 回滚：无 vibe / 清字段 ≡ GA 默认 |

---

## 4. 全场共识

1. **LVP 是收编层，不是算法层**；禁止借 LVP 改公式或加模板。  
2. **推荐卡 ≡ GA 字节等价**（MTSO on · MEGC on · MSA off）。  
3. **唯一差分是 MSA on**；必须「实验」标签 + 分页风险二次确认。  
4. **禁止**用户单独拆 MTSO/MEGC；禁止第三卡「全关优化」。  
5. **SSG look 不进 V1**；scene 不因 vibe 关闭。  
6. **不阻塞首访**：无全屏 Wizard；精修一等 + 导入后弱提示一次。  
7. **可回滚**：下线 UI / 清 `layoutVibe` 即回 GA；须进验收。  
8. **列车**：M1 剖面 → M2 UI；M3 与 CAD 同屏默认延期。

---

## 5. Must-Fix（阻塞）

| ID | 议题 | 要求（冻结一字面） | 挡 | 状态 |
|----|------|-------------------|----|------|
| **BLK-LVP-01** | D/O 回写 | D-01 改写为一荐一实验；O-01～03 关闭结论写入 PRD v0.2 | M0 | ✅ 本纪要回写 |
| **BLK-LVP-02** | 拆 ACCEPTANCE / IMPLEMENTATION | M1 合码前拆文；AC-01～08 入 ACCEPTANCE；M1 触点入 IMPL | M1 | ✅ 已拆文 |
| **BLK-LVP-03** | 实验卡二次确认文案 | 产品+体验签字：须含「分页/章节长度可能变」「可改回推荐」 | M2 | 🔶 **草案已上线 · 可合码 · 事后补签**（见下方备注） |
| **BLK-LVP-04** | 三册狗粮 | 王丹昙华林 / 东澳岛 / 斯里兰卡（或等价）推荐 vs 实验；无加权屏允许记录「差异小」 | M2 | ☐ GUIDE+草稿已备；待人工填 [DRAFT](./lvp-dogfood-2026-08-03-DRAFT.md) |
| **BLK-LVP-05** | 优先级链单测 | `layoutVibe` > overlay > 仓库默认；LSE flags 不被改写（AC-07） | M1 | ✅ |
| **BLK-LVP-06** | 回滚 AC | AC-LVP-08：清除 vibe 后行为 ≡ `magazine_default` / GA | M1 | ✅ |

**Should-Fix（不阻塞 M1）**

| ID | 建议 | 状态 |
|----|------|------|
| **SHD-01** | 线框 F1（两卡 + 确认模态）进 `docs/wireframes/`，M2 前 | ✅ `wireframes/layout-vibe-picker-f1-wireframe.html` |
| **SHD-02** | 帮助链「高级配置」指向文档，不链 LSE admin | ✅ Help **H8** · Sheet「了解更多」→ H8（文案指向产品文档，无 `/lse-flags-admin`；H7 仍为 NAS 写作引擎保留号） |
| **SHD-03** | 狗粮 GUIDE 一页：如何辨认「本册有无加权屏」 | ✅ `lvp-dogfood-GUIDE.md` |

### BLK-LVP-03 合码备注（2026-08-03）

确认文案草案已同时落在 UI 与 `layout_vibe_handlers.EXPERIMENTAL_CONFIRM_*`，字面满足「篇幅/页数可能变」+「可改回推荐」。  
**决议**：不阻塞功能分支合入；产品/体验补签后将本行改为 ✅ 并去掉「草案」标注。

---

## 6. 拍板 D / O（锁定）

| ID | 结论 |
|----|------|
| **D-LVP-01** | ✅ **改写锁定**：V1 = **1 推荐**（`magazine_default`）+ **1 实验**（`fit_photo_experimental`）；预留 `film_wide` **不交付** |
| **D-LVP-02** | ✅ 按草案（推荐 ≡ GA） |
| **D-LVP-03** | ✅ 按草案（实验开 MSA + 标实验 + 分页说明） |
| **D-LVP-04** | ✅ 按草案（禁止单独拆 MTSO/MEGC） |
| **D-LVP-05** | ✅ 按草案（SSG look 不进） |
| **D-LVP-06** | ✅ **O-01 关闭**：精修一等 + 导入后弱提示一次（可关）；无全屏阻塞 Wizard |
| **D-LVP-07** | ✅ 按草案（`trip.studio.layoutVibe`） |
| **D-LVP-08** | ✅ 按草案（⊥ LSE admin） |
| **D-LVP-09**（新增） | ✅ **回滚合同**：下线入口或清字段 → GA；不卸载 MTSO/MEGC |
| **O-01** | ✅ **关闭** · 见 D-06 |
| **O-02** | ✅ **关闭** · V1 不影响 CAD |
| **O-03** | ✅ **关闭** · 不要第三卡 |

---

## 7. 结论栏

| 项 | 结果 |
|----|------|
| **Conditional Go** | ✅ |
| **可 Kickoff M0** | ✅ 立即（本纪要 + PRD v0.2） |
| **可 Kickoff M1** | ✅（合码前关闭 BLK-02/05/06） |
| **可 Kickoff M2** | ❌ 待 BLK-03/04 |
| **可 Kickoff M3** | ❌ 默认延期 |
| **No-Go** | 无 |

---

## 8. 会后动作

1. 回写 PRD → **v0.2.0**（本纪要链接 · D/O 锁定 · D-09 · AC-08）。  
2. 更新 DOC-STATUS / README；草稿 `lvp-m0-review-*-DRAFT` 改为指向本结案。  
3. 工程：拆 ACCEPTANCE/IMPL 后开 M1（配置剖面 + 持久化）；**本轮不写 UI**。  
4. 不在本轮改 MSA/SSG 仓库默认。

---

## 9. Studio 触点（供 IMPL）

| 触点 | 路径 | 说明 |
|------|------|------|
| 精修 Sheet「这本」 | `templates/studio/preview-toolbar/features.js` | 封面版式 section 同级挂两卡 |
| 应用版面 | `.preview-sheet__apply-layout` 等（`core.js`） | 复用，不新造进度面 |
| Bookends / CAD | `bookends.js` | 不并入（O-02） |
| LSE admin | `/lse-flags-admin` | 正交 |
