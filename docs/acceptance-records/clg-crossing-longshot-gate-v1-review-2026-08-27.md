# PRD-CROSSING-LONGSHOT-GATE-V1 · 七席 + 典型用户评审纪要

| 属性 | 内容 |
|------|------|
| **文档** | [PRD-CROSSING-LONGSHOT-GATE-V1.md](../PRD-CROSSING-LONGSHOT-GATE-V1.md)（**CLG** · 过河长图闸）审的是 **v0.1.1 Draft** + [线框](../wireframes/crossing-longshot-gate-v1-wireframe.html) 帧 A–D |
| **上游合同** | [FXI](../PRD-FRONTEND-IDENTITY-ISOLATION-V1.md)（F1–F3 **已签** · **不重开**默认面 / 精修 / 游记面板）· [PIS](../PRD-PORTFOLIO-IDENTITY-STARS-V1.md)（同夹双本 · 覆盖只盖自身份）· [PFM](../PRD-PORTFOLIO-FOLIO-MODE-V1.md) ISO-04 / D-PFM-10 · [DPI](../PRD-DUAL-PIPELINE-ISOLATION-V1.md) · [ECC](../PRD-EXPORT-CARD-COMPOSE-V1.md) |
| **前序纪要** | [FXI 签核 2026-08-26](./fxi-f1-f3-signoff-2026-08-26.md) · [FXI W3 狗粮 2026-08-27](./fxi-w3-dogfood-2026-08-27.md) · [PIS 八席 2026-08-26](./pis-portfolio-identity-stars-v1-review-2026-08-26.md) · [备忘录](../作品集管线简化讨论备忘录.md) |
| **日期** | 2026-08-27 |
| **结论** | **有条件通过（Conditional Go）**。切口成立：六种不是一类；过河只开导 ECC 四平台；长图两卡留下但灰；有游记打开那本、没有就去做一本；过河不改身份。**按 v0.1.1 原文 Kickoff 会有五处假绿、自相矛盾或越界。** 不批无条件 Go · **不批 DOC-CLG-01 线框签**（须先改字）· **不批 W1**。回写 v0.1.2 + 线框改字后，产品再勾四帧，才开编码门。 |
| **编码** | ☑ 分席只读 v0.1.1 + 线框　☑ 对照现网　☑ v0.1.2 回写　☑ 线框改字　☐ W0 签　☐ W1 |
| **参评角色** | **七席**：产品 · 算法 · 架构 · 开发 · 测试/QA · 视觉/排版 · 用户体验（狗粮手测）· **加席**：典型用户（非从业者 · 昨走过华农作品集 F1 页图 + F2 小红书，并点过「按章」导微信得到一整张竖条 · **本场否决权与产品同等**） |
| **评审方式** | 分席只读 CLG v0.1.1 §0～§16 + 线框帧 A–D，对照 `dispatch.py:188-199`、`export_handlers.py:838-841`、`test_handle_longshot_portfolio_explicit_wechat_allowed`、`peek_existing_album_trip`、`openImportWizard` / `restoreSessionIfAny`、`buildPanelHtml` 社交包装、`journalExportPanelSnapshot`、FXI §7.2 已签主钮/禁「拼贴」、PIS `folderCollisionCopy` |
| **记录人** | 八席联合纪要（跨职能模拟联评 · 2026-08-27） |
| **本纪要状态** | **已结案 · Conditional Go** · Must-Fix **已回写** [CLG v0.1.2](../PRD-CROSSING-LONGSHOT-GATE-V1.md) · 线框已改字 · **待产品重勾** DOC-CLG-01 |
| **审查基线** | FXI F1 / F3 / 游记导出 **零改** · 过河 ≠ `POST /edition` · 加席「看不懂 / 你请我发微信又说不行 / 金子按钮写长图」= Must-Fix · C 端不出现 sidecar / 卷轴 / 拼贴 / edition · 不发明第二套向导 |

---

## 0. 会前宣读（主持人）

1. **切口**：FXI 已把作品集默认面藏干净。本场只评 **过河六种里哪些能导、灰卡点了去哪、缺卷轴时怎么去做一本**。F1 / F3 / 游记六平台 / 装配 / sidecar / 导入双开 **不重开**。
2. **已拍（勿重开）**：过河不改身份（D-FXI-07）；游记快照红则打回（BLK-FXI-01）；同夹两本可同时留、覆盖只盖自身份（PIS）；小红书四平台吃 ECC 不吃预览 HTML（W3 华农已出门）。
3. **本场必拍**：灰卡留下还是删掉；有游记是打开还是 sidecar；F2 主钮还叫不叫「导出长图」；C 端能不能说「拼贴 / 卷轴」；`aria-disabled` 还能不能点。
4. **加席说明**：他昨天在华农过河勾了「按章」，得到一整张。他不知道 kept_stack / ISO-04 / peek。他只会问——微信为什么灰了、那我怎么发群、去做一本会不会把作品集盖掉、按钮写「导出长图」是不是还在骗我。他说「看不懂」，就是 Must-Fix。

---

## 1. 总评（一句话）

> **八席一致 Conditional Go：方向对——过河不是改身份，长图也不该在作品集 trip 上假装按章；两张灰卡留下、打开那本 / 去做一本，比 sidecar 和 kept 竖条都诚实。** 但 v0.1.1 有五处按原文会假绿或把昨天刚签的 FXI 咬穿：（1）副句写「拼贴」、说明层写「卷轴」，前者顶 FXI 已签「C 端不用拼贴」，后者顶本文自己的术语表；（2）主选小红书时金子按钮仍写「导出长图」，加席当场否决——你刚说长图要去游记；（3）闸卡同时 `aria-disabled` 又要求可点，读屏会当死钮，AC-CLG-01 会假绿；（4）`openImportWizard` 现网先 `restoreSessionIfAny`，按原文 `albumPath` 会被旧草稿盖掉；（5）Studio 现网单测 `test_handle_longshot_portfolio_explicit_wechat_allowed` 断言作品集微信可出，BE-CLG-02 若不点名改，CI 必红。关 BLK-CLG-06～10 后升 v0.1.2；**线框四帧结构可留，文案未签；W1 须等回写 + 产品重勾。**

---

## 2. 分席表决

| 席位 | 表决 | 一句话 |
|------|------|--------|
| **产品** | **Conditional Go** | 闸卡方案我签：能导的导，不能导的指到游记，不改这本书。灰卡不准删。sidecar / 双开本波不准混进来。**我改判 FXI F2 确定钮**：点法对齐的是「选平台 → 确定 → Dock」，不是在已经声明「长图不在这里」之后还挂「导出长图」。C 端禁「拼贴 / 卷轴」，副句改用人话平台名。标题「发到微信、小红书…」和底链维持——入口可以问，点进去再说清。 |
| **算法** | **Conditional Go** | 本场无装配 / 选脸。peek 复用、不新造 slug，我签。两次 title/place（夹名 → trip 书名）够华农。同夹多本仍只回一本，不挡。禁止扫书架当第二套算法。 |
| **架构** | **Conditional Go** | 闸写在 `isPortfolioSocialExportFace` / `portfolio-*-logic`，不进 `dock.js` / `chapters.py`，和 DPI / FXI 和解，我签。三处钉死：① `buildPanelHtml(..., {edition:"journal"})` 零改，灰态只许 `syncPanelUI` 在 social face；② Studio **和** `dispatch.py` 双拒，单改 dispatch 会被 handler 现网测试打脸；③ ISO-04 几何门（不拍 `page-*` flatten）**保持**，退役的是 Studio 开导，不是「又可以把页图压进竖条」。 |
| **开发** | **Conditional Go** | W1 文件清单够开。两处按时要诚实：`openImportWizard` 必须加「有 albumPath 则跳过草稿恢复」，否则握手是假的；F2 包装层是 `wrapJournalPanelAsPortfolioSocialFace(buildPanelHtml(journal))`，在 journal HTML 上打闸会红快照。`export_handlers.py:838` 的 `skip_client_fallback` 作品集微信枝要改成先 409。 |
| **测试 / QA** | **Conditional Go** | AC-CLG-02/03/07/09/11 可测。三处假绿：① AC-CLG-01 把 `aria-disabled` 当可点；② AC-CLG-12「无按章」若只测 journal 快照会漏，必须断言 **F2 social face** 的 hidden；③ `test_handle_longshot_portfolio_explicit_wechat_allowed` 不改则 W1 红。华农打开那本、珠海类无游记去做一本，仍是 W2 狗粮，不要塞进 W1 当绿。 |
| **视觉 / 排版** | **Conditional Go** | 令牌对齐 FXI，闸卡 0.48 对比度可接受。帧 B/C/D 把六卡拆掉只留说明层，人会以为过河面被换走了——**说明层叠在网格上**，不要替换。帧 D 缺顶条，补上「这不是在导出作品集」。不新开第二套社交卡样式。 |
| **用户体验 · 狗粮** | **Conditional Go** | 08-27 华农：小红书能出、微信按章是假的，闸卡是对的药。按原文两处会把下一轮狗粮走砸：金子按钮还写长图；说明层「游记卷轴」他读成工程说明书。打开那本用 `?exportPanel=1` 我对，回来靠书架现网「返回」，不本波做跳回。 |
| **典型用户（加席）** | **Conditional Go · 两条否决** | 见 §2.1。总的说：我支持「微信灰了要告诉我去游记」「去做一本不会盖掉作品集」。**我否决两件事**：选着小红书，大金按钮还写「导出长图」；句子里出现「拼贴」「卷轴」——昨天刚说不要这些词。 |

**汇总**：**8/8 Conditional Go**。未回写 Must-Fix 前 **不批无条件 Go** · **不批线框签** · **不批 W1**。

**对齐评分**

| 维度 | 分（/10） | 说明 |
|------|-----------|------|
| 问题→方案因果完整度 | **8** | 六种分类、打开那本 / 去做一本、不改身份，切口准 |
| 与现网代码对齐 / 防假绿 | **5** | 向导会吃旧草稿；handler 单测必红；aria-disabled 自相矛盾 |
| 与 FXI / PIS / PFM / DPI 边界 | **6** | 缝选对了；拼贴 / 导出长图顶已签 F2；ISO-04 Studio 测试未点名 |
| 普通用户可走完一次 | **6** | 路径对；第一眼按钮和黑话会停住 |
| 工程可开工性 | **7** | 任务拆得清；握手与拒闸文件少写了一层 |
| AC 可测性 | **6** | 07/09 硬；01/12 会假绿 |
| 对前序加席 / 铁律的诚实 | **6** | 不改身份守住了；FXI 禁拼贴、F2 主钮没守住 |

### 2.1 加席原话（本场权重最高）

典型用户（华农 31 张：作品集 F1 已出门、F2 小红书已出、微信「按章」得到一整张；同夹有游记）：

1. **「微信灰了可以，但要告诉我去哪。」**  
   「你把微信藏起来我会以为坏了。灰着、写『要先有一本游记』、点开能打开那本，这样行。不要删掉这两张卡。」  
   → 签铁律 3、帧 A/B。**不否决**灰卡。

2. **「选着小红书，不要写导出长图。」**  
   「上面刚写『长图要在游记里做』，下面大金按钮还是『导出长图』。我不知道点下去出的是小红书还是又一张假长图。小红书就说导出小红书，或者就写『导出』。」  
   → **否决** F2 在可用卡上继续挂「导出长图」。BLK-CLG-07。游记那个按钮不要动。

3. **「不要拼贴、不要卷轴。」**  
   「『拼贴和印刷可以在这里做』『没有游记卷轴』——我不知道你在说什么。就说小红书和印刷可以在这里做；去做一本游记之后就能按章发群。」  
   → **否决** C 端「拼贴 / 卷轴」。BLK-CLG-06。

4. **「去做一本，别盖我这本。」**  
   「确认页要有『不会覆盖这本作品集、两本可以同时留』。没有这句话我不敢点。」  
   → 签 D-CLG-06 / AC-CLG-13。不新开 BLK。

5. **「打开那本之后，我怎么回来？」**  
   「书架能找回来就行。不必再做一个『跳回作品集』。」  
   → 签 R-CLG-02。不挡。

---

## 3. 事实核查（对照现网 · 影响结论）

| # | CLG v0.1.1 假设 | 代码 / 合同事实（2026-08-27） | 会中 |
|---|-----------------|-------------------------------|------|
| **F-01** | 作品集 × 微信群走 kept 竖条 | `dispatch.py:188-199` `trip_is_portfolio` → `export_portfolio_wechat_from_kept`；handler `skip_client_fallback` 作品集微信 | **属实 · 闸对症** |
| **F-02** | 小红书不吃预览 HTML | ECC / W3 华农 5 张已出门 | **属实 · 四平台可留** |
| **F-03** | F2 复用 journal `buildPanelHtml` | `wrapJournalPanelAsPortfolioSocialFace(buildPanelHtml(..., {edition:"journal"}))` | **属实 · 闸只能打在 social face 包装 / syncPanelUI** |
| **F-04** | `journalExportPanelSnapshot` 存在 | `longshot-export-panel.js:602` 只拍 `edition:"journal"` | **属实 · BLK-CLG-01 可当门** |
| **F-05** | FXI 允许过河副句写拼贴 | FXI v0.1.1：「C 端不用拼贴」；F2 签核主钮「导出长图」 | **原文越界 · BLK-06 / 07** |
| **F-06** | 本文 C 端不出现「卷轴」 | §0.1 术语表写（不出现）；`sheetHasBody` / `sheetNoneBody` 用了「卷轴」 | **自打脸 · BLK-06** |
| **F-07** | `aria-disabled` 仍可点 | 读屏把 aria-disabled 当不可用；现网闸卡无此模式 | **AC-01 假绿 · BLK-08** |
| **F-08** | `openImportWizard({albumPath})` 能预填 | 现网无 `albumPath` opts；先 `restoreSessionIfAny` 吃草稿 | **握手按原文会偏 · BLK-09** |
| **F-09** | 改 dispatch 即可拒闸 | `test_handle_longshot_portfolio_explicit_wechat_allowed` 断言作品集微信可出 | **必红 · BLK-10** |
| **F-10** | ISO-04 整包可标 deprecated | ISO-04 原文是「不得出现 page-* 几何」，不是「Studio 必须能导微信」 | **几何门保持 · 开导改判** |
| **F-11** | peek 用夹名对齐 album-preview | `import_handlers.py:751-764` `title_hint=folderName` `place=旅途` | **属实 · 保持** |
| **F-12** | 线框四帧覆盖合同 | A 有确定钮；B/C 拆掉网格；D 无顶条 | **结构可留 · 文案/叠层未签** |

---

## 4. Must-Fix（回写 v0.1.2 前不批线框签 · 不批 W1）

预占的 BLK-CLG-01～05 **本场维持**（游记快照、F2 拒两平台、不 POST /edition、有游记不说新建、向导漏认不覆盖）。下列为评审新增，挡 W0 签与 W1。

| ID | 挡哪一波 | 要求 |
|----|----------|------|
| **BLK-CLG-06** | W0 文案 / W1 | **C 端禁「拼贴」「卷轴」。** `leadSecondary` 改为「小红书、海报和印刷可以在这里做。长图要在游记里做。」`sheetHasBody` 去掉「卷轴」，改为「微信群和朋友圈的按章长图，用的是游记那一本。同夹已经有一本《{title}》。」`sheetNoneBody` 改为「这本作品集还没有对应的游记。去做一本之后，就可以按章导出长图。书架上两本可以同时留。」线框同步。正式注明：改判 FXI「F2 副句禁拼贴」仅此一句。 |
| **BLK-CLG-07** | W0 文案 / W1 | **F2 确定钮在主选为可用卡时不得写「导出长图」。** 跟该平台现网确定句（小红书即「导出小红书」或现网同等短句），或中性「导出」。游记面板主钮 / `journalDockChrome` **零改**。改判 FXI §7.2「过河主钮必须叫导出长图」——点法对齐保留，标签对齐取消。OQ-CLG-03 改判。线框帧 A 金子按钮改字。 |
| **BLK-CLG-08** | W1 | **闸卡可点，不用 `aria-disabled`。** 用 `data-clg-locked="1"` + `aria-describedby` 指向「要先有一本游记」；可聚焦、可点、不进入 `aria-pressed`。AC-CLG-01 删除 aria-disabled 断言。 |
| **BLK-CLG-09** | W1 | **握手不得被草稿盖掉。** `openImportWizard({ edition:"journal", albumPath })` 时跳过 `restoreSessionIfAny`，走现网 `afterFolderPicked(albumPath)`。禁止新 URL 合同。§8.4 写明。 |
| **BLK-CLG-10** | W1 | **拒闸双落点 + 点名改测。** `dispatch.py` **和** `export_handlers.py` 作品集 × 两平台都回 `E_CLG_NEEDS_JOURNAL`。同 PR 改 `test_handle_longshot_portfolio_explicit_wechat_allowed` 为 409。`test_iso04_portfolio_wechat_does_not_flatten_page_geometry` **保持**（不拍 page-*）。PFM 验收页挂一句「Studio 开导改判见 CLG」。 |

---

## 5. Should-Fix（不挡 W0 签 · 建议进 v0.1.2）

| ID | 说明 |
|----|------|
| **SHD-CLG-01** | 线框 B/C/D：说明层 **叠在** 六卡网格上，不要拆掉网格。帧 D 补顶条主句 + 副句。 |
| **SHD-CLG-02** | 徽章「按游记来做」与灰微信打架。可改为「用这些照片」。不改则须在副句里压过徽章。不挡签。 |
| **SHD-CLG-03** | §12「W1 须 BLK-01～03」改为 **01～10**（含本场新增）。 |
| **SHD-CLG-04** | 作品集预览打开帮助 H0 仍是「导出适合发群的竖版长图」。W1 扫到则改作品集可见句；游记 H0 **零改**。不新开 H 编号。 |
| **SHD-CLG-05** | AC-CLG-12 写明：断言对象是 F2 `data-export-face=portfolio:social` 的按章区 `hidden`，不是 journal 快照缺字。 |
| **SHD-CLG-06** | 帧 B 书名若与作品集同名（华农两本都叫《华农油菜花》），说明层用「同夹已经有一本游记」，不复读两个《同一书名》（沿 PIS BLK-02）。 |

---

## 6. 开放问题 · 本场裁决

| ID | 草案预裁 | **本场裁决** | 理由 |
|----|----------|--------------|------|
| **OQ-CLG-01** 同夹多本怎么选 | peek 那一本 | **维持** | 不新开列表；不挡 |
| **OQ-CLG-02** 去做一本回首页还是内嵌 | 回首页 | **维持** | 少造面；加席接受书架回来 |
| **OQ-CLG-03** F2 主钮是否改叫导出拼贴 | 不改，仍导出长图 | **改判：可用卡上不得写导出长图**（绑 BLK-07）。禁止改叫「导出拼贴」 | 加席否决；拼贴亦禁 |
| **OQ-CLG-04** CLI 是否删 `portfolio_wechat.py` | 只拒，文件可留 | **维持** | ISO-04 几何单测还吃得到函数 |

**本场新增**

| ID | 问题 | 裁决 |
|----|------|------|
| **OQ-CLG-05** | F2 标题还叫不叫「发到微信、小红书…」 | **维持。** 入口链与标题同一句；灰卡 + 说明层收口。不重开 FXI 标题 |
| **OQ-CLG-06** | 徽章「按游记来做」改不改 | **不挡。** 建议 SHD-02；产品可下一稿改 |
| **OQ-CLG-07** | 线框未改字前可否签 DOC-CLG-01 | **不可。** 先回写文案再勾 |

---

## 7. 与前序合同如何和解

| 前序 | 当时 | 本场 |
|------|------|------|
| FXI §7.2 六种都能选 | 复用游记点法 | **改判开导范围**（D-CLG-01/02）· **点法**仍是选→确定→Dock |
| FXI §7.2 确定钮「导出长图」 | 与游记同一主钮 | **仅 F2 改判标签**（BLK-07）· 游记零改 |
| FXI「C 端不用拼贴」 | F2 副句也禁 | **副句遵守**；CLG 原文越界，BLK-06 收回 |
| D-FXI-07 过河不改身份 | 不 POST /edition | **保持** · 帧 D 只开 F3 问句 |
| PIS 两本可同时留 | 覆盖只盖自身份 | **保持** · 去做一本 = 新建 journal |
| PFM ISO-04 | 微信群不得拍 page-* | **几何门保持** · Studio 开导改判（BLK-10） |
| D-PFM-10 换种分享能力 | 作品集仍可出社交图 | **能力半句保持** · 落点仍是过河 · **不含**微信长图 |
| BLK-FXI-01 游记快照 | 红则打回 | **延续为 BLK-CLG-01** |

---

## 8. 线框

| 帧 | 本场 | 处置 |
|----|------|------|
| **A 第一眼** | **结构签 · 文案未签** | 两卡灰、默认小红书、按章不出现 —— 对。金子按钮改字（BLK-07）；副句去拼贴（BLK-06） |
| **B 已有游记** | **结构签 · 文案未签** | 主钮「打开那本」对。去「卷轴」（BLK-06）；说明层叠在网格上（SHD-01） |
| **C 去做一本** | **结构签 · 文案未签** | 主钮「去做一本」、次钮「先出小红书」对。去「卷轴」 |
| **D 改这本书** | **结构签 · 缺顶条** | 主钮只开 F3、不在层内 POST —— 对。补顶条（SHD-01） |
| 拍板清单 | **先不勾** | 等 v0.1.2 线框改字后再签 DOC-CLG-01 |

---

## 9. 本场关闭 / 保持

| 项 | 处置 |
|----|------|
| 过河只开导 ECC 四平台 | **保持 · 主线成立** |
| 灰卡留下、点开说明 | **保持** |
| 有游记打开那本 / 无游记去做一本 | **保持** |
| 过河不 POST /edition | **保持** |
| 不做 sidecar / 双开 / 统一模板 | **保持** |
| 游记六平台 / F1 / F3 | **不改** |
| F2 标题与底链 | **保持** |
| F2 确定钮「导出长图」 | **否决（仅 F2）** |
| C 端拼贴 / 卷轴 | **否决** |
| 删掉两张微信卡 | **否决（不准删）** |

---

## 10. 编码门（回写 v0.1.2 + 线框改字后）

| 波次 | 回写前 | 回写后 |
|------|--------|--------|
| **W0** 线框签 | 须 BLK-06/07 进线框 + 产品勾四帧 | 才算 DOC-CLG-01 |
| **W1** 闸 + 拒 + 去向 | 须 BLK-01～10 | 可开工 |
| **W2** 华农 / 无游记夹狗粮 | W1 | 才谈 Conditional Go 升无条件 |
| 无条件 Go | 全部 BLK 关 + 狗粮两夹 + 游记快照仍绿 | — |

---

## 11. 变更记录

| 版本 | 日期 | 说明 |
|------|------|------|
| 本纪要 | 2026-08-27 | 八席 Conditional Go。维持 BLK-CLG-01～05。新增 BLK-CLG-06～10。加席两条否决（F2 导出长图、拼贴/卷轴）。待回写 CLG v0.1.2 + 线框改字。 |
| 回写 | 2026-08-27 | Must-Fix 已写入 CLG v0.1.2 §0.3 / §6 / §7 / §8.4 / §9.2；线框改字并改为叠层。待产品重勾 DOC-CLG-01。 |
