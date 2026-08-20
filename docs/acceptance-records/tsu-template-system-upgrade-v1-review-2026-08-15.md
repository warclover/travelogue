# PRD-TEMPLATE-SYSTEM-UPGRADE-V1 · 七席评审纪要

| 属性 | 内容 |
|------|------|
| **文档** | [PRD-TEMPLATE-SYSTEM-UPGRADE-V1.md](../PRD-TEMPLATE-SYSTEM-UPGRADE-V1.md)（**TSU** · 模板体系升级）**v1.1.0**（BLK-TSU-01～08 已回写） |
| **线框** | [tsu-template-admin-series-editor-v1-wireframe.html](../wireframes/tsu-template-admin-series-editor-v1-wireframe.html)（§5.3 F1–F1b–F6 · BLK-07 已改） |
| **设计理由** | [TEMPLATE-SYSTEM-UPGRADE.md](../templates/TEMPLATE-SYSTEM-UPGRADE.md) v2.3 |
| **附录** | [A 数据包](../templates/PAGE-PACKET-CATALOG.md) · [B 角色对照](../templates/ROLE-FACE-MAP.md) |
| **相邻挡门** | [EDC](../PRD-EDITORIAL-COMPILER-V1.md) · [LTE P16](../PRD-PHASE16-layout-template-engine.md) · [TPC](../PRD-TEMPLATE-CONTRACT-V1.md) · [MTSO](../PRD-MOSAIC-TEMPLATE-SELECTION-OPTIMIZATION-V1.md) · [ECC](../PRD-EXPORT-CARD-COMPOSE-V1.md) · [ADR-021](../adr/021-export-compose-dual-engine.md) · [AEL](../PRD-ALBUM-EDITORIAL-LAB-V1.md) · [ABE](../PRD-ALBUM-EXPORT-BOOKENDS-V1.md) · [CAL](../PRD-COVER-CALLIGRAPHY-TITLE-V1.md) · [ADR-020](../adr/020-narrative-contract.md) |
| **日期** | 2026-08-15 |
| **结论** | **有条件通过（Conditional Go）**。主线可冻结。**BLK-TSU-01～08 已回写 v1.1.0**。文档/schema/glyph 合同可 Kickoff。**W1 仍挡产品 A1–A7 + B7 金样**。**W2 仍挡 AC-06a/b 与 D-U-15 包边**。**W3/W4 仍挡 A7 签核**。未勾 A7/B7 前 **不批无条件 Go · 不批匹配器合码 · 不批编排器合码**。 |
| **编码** | ☑ 策划回写 v1.1（BLK-TSU-01～08）　☐ W0 schema+glyph 合同　☐ W1 系列 YAML　☐ W2 匹配器　☐ W3 界面 V0　☐ W4 界面 V1 |
| **参评角色（七席）** | 产品 · 算法 · 架构 · 开发 · 测试/QA · 视觉/排版（LTE·装裱）· 用户体验（狗粮手测） |
| **评审方式** | 分席只读 PRD v1.0.3 §0～§8 + 附录 A/B + 线框 F1–F6 · 对照现网（`lte_policy.yaml` 统一窗、`/templates-admin`、ADR-021 画册两卡 3:4、EDC `program`↔`narrativeRole`、ECC `CARD_TEMPLATES`、ABE/CAL 书衣） |
| **记录人** | 七席联合纪要（跨职能模拟联评 · 2026-08-15） |
| **本纪要状态** | **已结案 · Conditional Go** · **Must-Fix 已回写 PRD v1.1.0** |
| **审查基线** | 引擎是资产面不是第四套算法 · 不重写 MCS/Curate · 不打开 MSA · 运行时不发明拓扑 · 零步不增加 · **不把现网双舞台写成已经统一** · **不把未勾的产品待办当成已冻结金样** |

---

## 0. 会前宣读（主持人）

1. **切口**：缺的是成册层 + 模板资产面，不是第 48 张拼图脸。逐步升级，合同一次切干净。  
2. **已拍（勿重开）**：档位按页；左侧胶装；不做 `spread-*`；16:9 新脸；`card-*` 本波不并入社交柜；先开发者；不开放自由画几何。  
3. **勿重开**：47 套全重画、引擎换代、骑缝/出血、C 端 Mixbook、把 CAL 题字写进成册编译器。  
4. **本场必拍**：D-U-09「Web 与画册共用 `page-*`」和 ADR-021 两卡 3:4 怎么切；四页签里博物馆去哪了；`program` 与 EDC/ADR-020 是否双真相；D-U-10 留白裁切打不打穿现网 cover；W0 产品待办未勾能不能开工；线框 F1/F4 会不会教错 IA。  
5. **C14** 本场关闭：这场就是七席。

---

## 1. 总评（一句话）

> **七席一致 Conditional Go：主线立得住——三类算法单向合同、成册先开口、引擎当资产面、活目录只认诚实 `page-*`、界面是开发者工具不是 C 端填图器，比「再加一批 YAML」可验收。但 v1.0.3 有八处按原文 Kickoff 会假绿或打穿现网：（1）D-U-09 把 Web 16:9 屏和画册 3:4 两卡写成已经同一套脸，与 ADR-021 / ECC / AEL 事实不符；（2）设计理由三柜有博物馆，PRD 四页签没有；（3）`program` 只写「与 EDC 共用」未挂 ADR-020 映射；（4）D-U-10 三条留白若落到现网 `screen-*` / ECC 铺满像素会改气质并打红 AC-ECC-01；（5）W0 A1–A7 / B7 全空，金样页序不存在却写了 W1 完成标志；（6）`/series-editor` 写 YAML 的路径与「不改 trip」未钉；（7）线框 F1 把撒谎 id 画在活目录、F4 封面砖与 16 页计数视觉黏连；（8）匹配器没有模块落点，容易再塞进 LTE/MCS。关 BLK 后升 v1.1；W0 可做 schema 与 glyph 合同；W1 必须等产品交出 20 页金样页序。**

---

## 2. 分席表决

| 席位 | 表决 | 一句话 |
|------|------|--------|
| **产品** | **Conditional Go** | 切口对：会装页不会成书，是真问题。8/16/20 先做、18 非档、封面只登记，同意。对外不能说「画册已经按页用 `page-*`」——用户导出的仍是 3:4 两卡。W0 清单 A/B 未勾，不能假装金样已有。线框方向对，F4 要让人一眼看出「16 是中间页」。 |
| **算法** | **Conditional Go** | 三层单向、只在匹配器见面，能执行。成册先开口对。派不上的降级链（兄弟→flex→靠档）要写成接口，不能停在散文。匹配器若为了装下而改页数，就是 MSA 故事重演。D-U-10 只许作用在新 `page-*`；现网朝向硬门与 crop_solver 默认路径不动。 |
| **架构** | **Conditional Go** | 资产面 ≠ 第四算法，同意。D-U-09 必须改写成「目标」或「分波」：V1 先 Web `page-*` + 系列；画册仍 ECC，直到另立切面。禁止把 MCS/成册编译塞进 LTE 包。`program` 必须是 EDC 枚举的引用 + `narrativeRole` 映射表，禁止第三套主编词。博物馆是柜，不是备注。 |
| **开发** | **Conditional Go** | 现网 `/templates-admin` 已有五态与 store，四柜是改 IA 不是从零。glyph 从 YAML 出 SVG、CI 对账，可开工。匹配器没有家：新包，挂在 layout 之上、MCS 之外。`series-editor` 写文件必须是 Studio 本机仓库路径 + `template_admin`，**禁止**写进 `trip.json` 当运行时模板。关旗回贪心要有逐屏金样，否则 AC-06 假绿。 |
| **测试 / QA** | **Conditional Go** | AC-01～22 方向对，但 AC-06「逐页一致」未定义页=Web 屏还是画册卡。AC-13/14 是文档验收，不能当代码绿。AC-ECC-01（卡必须铺满）与 D-U-10 留白互斥，必须写「测哪条出口」。博物馆 `get` 要有旧 trip fixture，不能只测新 id。线框 F1 反例行若进实现，活目录用例会脏。 |
| **视觉 / 排版** | **Conditional Go** | 账徽 `3P`/`2L1P` + 竖红横蓝，能读槽账。成册用密度条、不和密网撞车，对。16:9 页砖不对页画布，与 D-U-01 一致。F4 封面金框和中间页混排，设计师会数成 18 块。留白裁切若上到现网满幅三竖，会从「磁砖」变成「明信片」——只许新脸，旧脸博物馆保持原 fit。 |
| **用户体验 · 狗粮** | **Conditional Go** | 这是内部工具，零步不变，同意。不要把 `/series-editor` 链到首页或预览 Dock。预演页不要出现算法缩写当用户文案。18 页顶栏「非档」够显眼。F1 红底撒谎行会让维护者以为活目录还能看到退役脸——实现时活目录根本没有那一行。 |

**汇总**：**7/7 Conditional Go**。未回写 Must-Fix 前 **不批无条件 Go** · **不批 W2 匹配器合码** · **不批 W4 编排器合码**。

**对齐评分**

| 维度 | 分（/10） | 说明 |
|------|-----------|------|
| 问题→方案因果完整度 | **8** | 成册缺位 + 目录撒谎是真问题；切口对 |
| 与现网能力对齐 / 防假绿 | **5** | D-U-09 / 四柜缺博物馆 / 裁切三条写成已统一 |
| 与 EDC/ECC/ADR-021 边界 | **6** | 不重写 MCS 对；画册双舞台与 program 映射未钉 |
| 工程可开工性 | **7** | glyph/治理台 IA 清晰；匹配器无落点 |
| AC 可测性 | **7** | 界面 AC 好；AC-06/10 出口未分 |
| 线框可签核性 | **7** | 五表面都画到了；F1/F4 两处会教错 |

---

## 3. 事实核查（对照现网 · 影响结论）

| # | PRD v1.0.3 假设 | 代码 / 合同事实（2026-08-15） | 会中 |
|---|-----------------|------------------------------|------|
| **F-01** | Web 预览与画册导出共用 `page-*`（D-U-09） | Web 拼图走 LTE `screen-*` + `MOSAIC_*_PATTERN_IDS`。画册 `album_spread` 走 ECC 3:4 `card-*` + 两卡 gutter（ADR-021 D2）。AEL 试验床也在卡上 | **修正**：这是目标，不是 As-Is。V1 必须写切面，不能当已落地 |
| **F-02** | `/templates-admin` 改四页签即可 | 现网已有五态、admin store、metrics；平铺的是 **screen 模板行**，无成册对象、无书衣登记、无博物馆柜 | **属实缺口**；四页签是新 IA，不是换皮 |
| **F-03** | 四种对象分柜 = 四页签 | 设计理由三柜是活目录/观察室/博物馆。PRD FE-1 是活目录/观察室/书衣柜/成册。博物馆只出现在 AC-15 的「可 get」 | **双模型**。博物馆必须有柜或明确挂在活目录过滤器 |
| **F-04** | `program` 与 EDC 共用即够 | EDC D-EDC-22：`program` 可空，由 `narrativeRole`+`patternId` 推导；映射表在 EDC §6.2.1 | **修正**：TSU 必须引用该表，禁止第三枚举 |
| **F-05** | 裁切全库相对槽三条（D-U-10） | 现网 mosaic 以 cover/contain/auto + `crop_solver` 为主；ECC Renderer 断言铺满无底色（AC-ECC-01） | **修正**：只约束新 `page-*`；博物馆与 `card-*` 不改 |
| **F-06** | 关旗 = 现网贪心逐页一致 | 现网是分镜开窗数≈页数，无系列。画册页数是卡数+书衣，不是 16 页 `page-*` | **AC-06 须分出口写金样** |
| **F-07** | W1 七本系列能预演 | §5.1 A/B 全 ☐；没有一页手写序列进仓库 | **W1 未具备开工条件** |
| **F-08** | 保存 = 写系列 YAML | 现网 `patternId` 写在 `trip.json`（D-P16-05）。编辑器若写 trip 就是运行时改库 | **必须钉：只写系列文件，不写 trip** |
| **F-09** | 匹配器是见面点 | 代码里没有该包；MCS / CardGrouper / screen planner 是现网选型 | **新模块；禁止并入 LTE 或 MCS** |
| **F-10** | 线框 F1 活目录含撒谎行「仅作反例」 | 实现者会按表抄。活目录实现若出现该行即违反 D-U-08 | **线框 Must-Fix** |
| **F-11** | 封面在轨上不计入 16 | F4 封面砖与页 1 并列，页码从 1 起，视觉上全书块数 > 16 | **线框 Must-Fix**：中间页码带「1/16」或书衣区隔 |
| **F-12** | 不打开 MSA / 不发明拓扑 | 与章程、EDC、AEL 一致 | **属实 · 保持** |
| **F-13** | ABE/CAL 已占书衣 | CAL 是标题贴纸；ABE 是画册首尾页；V6 Opening 是 Web 封面风格 | **属实**；书衣柜要登记三家，不是只写 ABE |

---

## 4. Must-Fix（回写前不批无条件 Go）

| ID | 挡哪一波 | 要求 |
|----|----------|------|
| **BLK-TSU-01** | W2 / 画册出口 | 重写 D-U-09：标明 **As-Is**（Web=`screen-*`，画册=`card-*` 两卡）与 **To-Be**。V1 默认：**系列 + `page-*` 先服务 Web 预览**；画册继续 ECC，切面另立（或写明「画册只消费系列页序、渲染仍 3:4 卡」的编译合同）。禁止再写「已经共用」 |
| **BLK-TSU-02** | W3 界面 V0 | 柜模型收口：博物馆是第几柜。建议五态过滤 + 五入口：活目录 / 观察室 / **博物馆** / 书衣柜 / 成册。AC-15 与线框 F1 同步 |
| **BLK-TSU-03** | W2 | 增 `program`↔`narrativeRole` 映射，**引用 EDC §6.2.1**，不新开枚举。角色表（附录 B）每行补一列 narrativeRole |
| **BLK-TSU-04** | W3 换脸 | D-U-10 作用域：仅 `status=designed/ga` 的 `page-*`。博物馆 `screen-*` 保持原 `fit`。`card-*` / AC-ECC-01 本波不动 |
| **BLK-TSU-05** | W1 | 产品未交 B7（至少 20 页金样页序）+ A1–A7 前，**禁止**把「7 本系列能预演」当 W1 出门。文档波可先做 schema |
| **BLK-TSU-06** | W4 | 写死：`/series-editor` 只写仓库内系列 YAML；权限 `template_admin`；**不**写 `trip.json` / 不改 `patternId` 运行时权威 |
| **BLK-TSU-07** | W3/W4 线框 | F1：撒谎 id 移出活目录帧，改到博物馆帧。F4：书衣区与中间 1–16 区隔；中间砖显示「3/16」而不是与封面抢序号 |
| **BLK-TSU-08** | W2 | 匹配器模块落点：新包（建议 `travelogue/layout_engine/series/` 或并列 `editorial_series`），**禁止**并入 `layout_templates` 与 `mosaic` 选型核。import-linter 预留边 |

**v1.1.0 回写核对（2026-08-15）**

| ID | 落点 | 状态 |
|----|------|------|
| BLK-01 | D-U-09 分波 · PRD §2.4 As-Is/To-Be | 已关 |
| BLK-02 | FE-1 五柜 · AC-TSU-15 · 线框 F1/F1b | 已关 |
| BLK-03 | PRD §3.5 映射表 · 附录 B `narrativeRole` 列 | 已关 |
| BLK-04 | D-U-10 只约束 `page-*` designed/beta/ga · AC-TSU-24 | 已关 |
| BLK-05 | W1 出门绑 A1–A7 + B7 金样 | 已关（产品勾选仍 ☐） |
| BLK-06 | D-U-16 · FE-T10 · AC-TSU-17 | 已关 |
| BLK-07 | 线框 v1.1：F1 无撒谎行、F1b 博物馆、F4 书衣条 + 1/16 | 已关 |
| BLK-08 | D-U-15 · `editorial_series` · AC-TSU-23 | 已关 |

SHD-01/02/03/05/06 一并收进 v1.1（AC-06a/b、AC-25、journal 禁写、F2 三行业主、F6 人话 reason）。SHD-04（补满 16 灰砖）线框用 1/16…7/16 + 16/16 示意，不逐砖画满。

---

## 5. Should-Fix（不挡文档 Kickoff）

| ID | 说明 |
|----|------|
| **SHD-TSU-01** | AC-06 拆成 Web 屏序列金样 / 画册卡序列金样两条，关旗各对一条 |
| **SHD-TSU-02** | `photo_span` 与 PPC 闭合公式写入 AC，避免每本系列口算 |
| **SHD-TSU-03** | 附录 B `journal` 无顶岗：W1 金样禁止写该角色，或先指定 editorial 顶岗 |
| **SHD-TSU-04** | 线框 F4 补满 16 中间砖的缩略（可灰块），避免「只有 6 页」的误读 |
| **SHD-TSU-05** | 书衣柜 F2 列出 V6 Opening + CAL + ABE 三行业主，与 F-13 一致 |
| **SHD-TSU-06** | 预演 F6 的 reason 用产品语言（「横图进不了三竖」），不用 MCS 内部码 |

---

## 6. 线框分帧结论

| 帧 | 结论 | 要改 |
|----|------|------|
| **F1 活目录** | 方向对 · **改** | 删除活目录里的撒谎行；博物馆另帧或另页签（BLK-02/07） |
| **F2 书衣柜** | **同意** | 补 CAL/Opening 业主列（SHD-05） |
| **F3 成册** | **同意** | 密度条不是密网，保持 |
| **F4 编排器** | 方向对 · **改** | 书衣与 1–16 区隔；主拖角色保持（BLK-07） |
| **F5 18 页非档** | **同意** | 顶栏文案可直接进实现 |
| **F6 预演** | **同意** | reason 人话（SHD-06） |

签核表 W-01～W-06：七席建议产品在线框改完 BLK-07 后一次性勾。本场 **不代替 A7 产品签核**。

---

## 7. 本场关闭 / 保持

| 项 | 处置 |
|----|------|
| D-U-01～08、10 作用域收紧后、11～14 | **保持**（10 须按 BLK-04 收窄） |
| 不重写 MCS / Curate / 不打开 MSA | **保持** |
| C 端填图器不做 | **保持**（W-06 七席同意） |
| 封面只登记 | **保持** |
| C14 七席 | **关闭 · 本场即是** |
| OQ | 本场不新开；切面细节进 BLK-01 回写 |

---

## 8. 出门顺序（回写后）

```
v1.1 回写 BLK-01～08  ✅ 2026-08-15
  → W0：schema / glyph 合同 / 博物馆柜 IA（文档+接口，可合）
  → 产品 A7 签核改后线框 + B7 金样页序
  → W1：系列 YAML 预演（旧脸顶岗）
  → W2：匹配器新包 + 父开关（AC-06a/06b）
  → W3：page-* 换脸 + 界面 V0
  → W4：编排器可拖
```

画册真正改用 `page-*` 渲染 **不在本 PRD V1 默认出门**（D-U-09 分波：须另立编译合同 + 独立 AC）。

---

## 9. 修订

| 版本 | 日期 | 说明 |
|------|------|------|
| 1.0 | 2026-08-15 | 首场七席。7/7 Conditional Go。BLK-TSU-01～08。PRD 仍为 v1.0.3，待回写 v1.1。 |
| 1.1 | 2026-08-15 | 策划回写：PRD 升 v1.1.0；附录 B 补 `narrativeRole`；线框增 F1b、改 F1/F4。编码勾「策划回写」。产品 A7/B7 仍 ☐。 |
