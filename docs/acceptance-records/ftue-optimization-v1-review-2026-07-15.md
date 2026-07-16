# PRD-FTUE-OPTIMIZATION-V1 · 跨职能评审纪要

| 属性 | 内容 |
|------|------|
| **文档** | [PRD-FTUE-OPTIMIZATION-V1.md](../PRD-FTUE-OPTIMIZATION-V1.md) |
| **评审版本** | **v1.0.0 Draft** |
| **日期** | 2026-07-15 |
| **结论** | **有条件通过（Conditional Go）** · **Must-Fix 已回写 [PRD v1.1.0](../PRD-FTUE-OPTIMIZATION-V1.md)** · 可 Kickoff W0 |
| **跟进** | 2026-07-15：线框 [ftue-optimization-v1-wireframe.html](../wireframes/ftue-optimization-v1-wireframe.html) · [IMPLEMENTATION](../IMPLEMENTATION-FTUE-OPTIMIZATION-V1.md) · Installer F-INS-FIRST-01′ |
| **参评角色** | 产品 · 交互/UI-UX · 用户体验 · 典型用户（分享者 · 轻度编辑者）· 架构 · 开发 |
| **评审方式** | 分席只读评审（对照 PRD + 现网代码 / 相邻合同：Help · Export Facade · L0G · Installer） |
| **记录人** | 产品 / UX / 工程联合纪要 |

---

## 1. 总评（一句话）

> **方向正确、问题来自可复现狗粮、W0 切口可独立交付；阻塞不在愿景，而在四处合同打架：① 能力卡 CTA 文案覆盖 L0G/Help 未声明；② 示例入口「仅向导」与 Installer/§3.1 自相矛盾；③ 长图成功面加严易另起平行 UI，且发群句与 Help 未对齐；④ 安装路径假 P0 越界。修完 Must-Fix 后可开 W0。**

---

## 2. 分席表决

| 席位 | 表决 | 一句话 |
|------|------|--------|
| **产品** | Conditional Go | 消解 L0G/Installer 双合同 + 踢掉假 P0 后可 Kickoff |
| **交互 / UI-UX** | Conditional Go | 缺线框、示例层级、成功面验收窗口、发群句对齐 |
| **用户体验** | Conditional Go | 对准愿分享；W0 只修入口不够，成稿后信任不能断 |
| **用户 · 分享者** | Conditional Go | 要示例敢试、最后一步会发群；怕双长图和乱码 |
| **用户 · 轻度编辑者** | Conditional Go | 示例→改标题→长图；系统句泄漏会直接不想发 |
| **架构** | Conditional Go | W1 只做 Help/Facade 缺口闭合，禁止新成功面栈 |
| **开发** | Conditional Go | 六条断言与代码对齐；W0 ≈ 2.5–3.5 人日 |

**汇总**：**七席一致 Conditional Go**。未回写 Must-Fix 前 **不批无条件 Go / 不标 Ready for Kickoff**。

---

## 3. 全场共识

1. **铁律对**：空态不像坏产品、示例一等公民、落盘≠完成、冷启动可解释、文件名 ASCII——可裁决。  
2. **不做 Tour / 不重开精修 / 不代付 LLM**：范围克制，赞成。  
3. **代码断言基本属实**：灰「继续上次」、中文 title 进文件名、向导无 `useDemoAlbum` UI、`publishGuide` 已有但多入口不齐、env trips 名存实亡。  
4. **W0 可独立狗粮**：藏继续上次 + 示例 CTA + 文件名 + README 三步；**W0 ≠ 主题完成**（发群闭环在 W1）。  
5. **系统句泄漏 = 信任事故**（比「stub 文案略弱」严重），可见面须挡，不宜只丢给 Copy 另轨。

---

## 4. Must-Fix（阻塞 Kickoff · 合入 v1.1）

| ID | 议题 | 来源席位 | 要求 |
|----|------|----------|------|
| **BLK-01** | **能力卡文案覆盖权威未声明** | 产品 / 交互 | D-FTUE-06 / §4.2 改「开始制作」等，须正文声明 **覆盖 COPY-L0G / AC-L0G-10 / Help§12.4**，并回写交叉引用；CTA 冻结唯一字符串（或 ≤2 白名单）。 |
| **BLK-02** | **示例入口合同拍板** | 产品 / 交互 / Installer | 消解 OQ-01 vs F-INS-FIRST-01 vs §3.1「首页示例」矛盾。**定案（评审建议）**：首页主 CTA「开始制作」→ 向导；**试用示例仅在向导 pick 一等显眼**；修订 Installer「首页可见示例」为「首页进向导且向导必有示例」。删掉 §3.1 含糊句。 |
| **BLK-03** | **P-FTUE-01 假 P0 外置** | 产品 | 「非开发者 pip」降级/改归属 Installer；G-FTUE-06 标明 **开发者路径**，不得冒充干净机非开发者成功。 |
| **BLK-04** | **长图成功面：复用 + 发群主句优先** | 产品 / 架构 / 交互 | 加严 G-EXP-05 **不得**压过发群第一可读行；**禁止**新造成功面平行栈；复用 `resolvePublishGuide` + Task Dock `showSuccess`；书架/`formatLongshotResult` 对齐（BLK-E-07）。 |
| **BLK-05** | **发群冻结句与 Help 对齐** | 交互 / Help | To-Be「选图→发送」改为与 `publishGuideFallback` / D-HELP-09 **同一套三要素**；禁止两套 COPY。 |
| **BLK-06** | **成功面可验收合同** | 交互 / UX | AC-FTUE-08 补：**展示窗口**（反对仅「闪过」）或「自动收起后仍可经再点长图/H4 找回」；写清观测方式，避免 8s auto-hide 导致假失败。 |
| **BLK-07** | **示例已存在去重对齐现网** | 交互 / 开发 | §3.2「默认打开预览」vs 现网 `E_DEMO_EXISTS` 仅覆盖/取消 → **回写为：默认打开已有示例；次要「重新生成（覆盖）」**。 |
| **BLK-08** | **向导示例视觉层级** | 交互 | 「试用示例相册」与「选文件夹」同屏次主；**不得**塞进「其他导入方式」旁「小文件夹试用」（命名撞车）。上传入口改名去「试用」。 |
| **BLK-09** | **空态不渲染「继续上次」DOM** | 开发 / UX | 非仅 `disabled`；有作品回归 AC-FTUE-R01。 |
| **BLK-10** | **文件名 `tripId-chNN` + 中文 title 单测** | 开发 / 用户 | W0 Must；UI/成功面仍展示中文标题。 |
| **BLK-11** | **W0/W1 完成定义写死** | 产品 / UX | W0 Go = 敢试、不灰、不乱码；**W1 Go = 敢发**（成功面+发群）才算主题主链过门。 |
| **BLK-12** | **线框 F1–F3/F6 最低集** | 交互 | W0 UI 合入前至少：空态、向导示例、示例已存在、长图成功面（对齐 Help 评审先例）。 |

---

## 5. Should-Fix（建议 v1.1 合入，不单独挡纪要）

1. 冷启动 `stageHint` 枚举 / 触发条件写进合同（否则 AC-FTUE-07 验不稳）。  
2. 埋点：`ftue_*` 与现网 `capability_card_*` / `longshot_success_share_hint_shown` 映射表。  
3. 成功指标 ≥90%/≥85% 标为狗粮目标非发布硬 KPI；或补 N≥5。  
4. 示例成稿后补「用自己的照片再做一本」出口文案（防试完就走）。  
5. 双长图：文内「保存长图」保留降强调；AC 写明 tip/pulse **不得**打在文内钮。  
6. trips 优先级文档：`--trips-dir` > config > default；env 现状写清楚（W2 再改 loader）。  
7. 系统句泄漏挡在 W1 可见面；stub「碎片」类润色 W2，不阻塞 W1 Go。

---

## 6. OQ 拍板汇总

| OQ | 决议 |
|----|------|
| **OQ-FTUE-01** | **仅向导一等示例**；首页主 CTA 进向导；并修订 Installer 字面（见 BLK-02） |
| **OQ-FTUE-02** | 文内「保存长图」**保留、降强调、不脉冲、不进首访 tip** |
| **OQ-FTUE-03** | V1 **强制 `tripId-chNN`**；拼音 slug 不做 |
| **OQ-FTUE-04** | 改 example/bootstrap/文档默认；**不强制**改个人 `config.yaml` |
| **OQ-FTUE-05** | README 顶部三步 + 折叠深链 |

---

## 7. 代码对齐摘要（架构 / 开发）

| 断言 | 现网 | 结论 |
|------|------|------|
| 空态继续上次 | `disabled` 仍渲染 | 属实 → BLK-09 |
| 长图中文文件名 | `_slug_title` 保留中文 | 属实 → BLK-10 |
| publishGuide | Task Dock 有；书架/formatter 弱 | 部分属实 → BLK-04 |
| useDemoAlbum | API/CLI 有；向导无 | 属实 → BLK-08 |
| vision 默认 | example/代码 false；开发机可 true | 叙事须拆开 |
| trips env | Studio 加载后几乎无效；CLI 最高 | 属实 → DOC |

**W0 估时**：约 **2.5–3.5 人日**（建议按 3 人日排）。

---

## 8. 用户代表原话摘要

| 代表 | 态度 | 要点 |
|------|------|------|
| **分享者** | 条件支持 | 「有示例我肯定先点；做成了不告诉我怎么发群，我就当软件卡了；两个长图我会犹豫。」 |
| **轻度编辑者** | 条件支持 | 「示例→改标题→长图；封面写『备选有限』我就不想发；别提 API。」 |

**试用示例 vs 真实相册转化**：中低风险、利大于弊；须在成稿后给「换自己的照片」出口。

---

## 9. 建议狗粮门禁（人手 · 5 步）

1. 空态首页 30 秒能说出下一步；**无**灰「继续上次」。  
2. 开始制作 → **试用示例**（不选自有文件夹）；等待可解释。  
3. 卷轴预览：一个主「长图」强调；封面无系统句。  
4. 导出：成功面可见；能开文件夹；有发群句；文件名无乱码。  
5. 探针：「换成自己的旅行照片下一步点哪？」答得出才过转化关。

---

## 10. 后置（不进本主题 Kickoff）

- Desktop Installer 完整分发 / 签名 / Gate  
- stub 叙事深度润色（Copy 另轨）  
- 全站 Tour  
- trips env 真正接入 loader（W2）  
- 拼音 slug 文件名  

---

## 11. 下一步

| # | 动作 | 状态 |
|---|------|------|
| 1 | 回写 PRD **v1.1.0**（消化 BLK-01～12 + OQ 定案） | ✅ 2026-07-15 |
| 2 | 补线框 F1–F8（W0 挡门 F1–F3/F7） | ✅ |
| 3 | 拆 `IMPLEMENTATION-FTUE-OPTIMIZATION-V1.md` | ✅ |
| 4 | Installer F-INS-FIRST-01′ | ✅ |
| 5 | **Kickoff W0** 编码 | ⬜ Ready |
| 6 | W1 与 Help / Export Facade 回归同周 | ⬜ |

---

## 12. 版本记录

| 日期 | 说明 |
|------|------|
| 2026-07-15 | MF 回写完成：PRD v1.1.0 + 线框 + IMPLEMENTATION → **可 Kickoff W0** |
| 2026-07-15 | 首版纪要：七席 Conditional Go；BLK-01～12；OQ 拍板 |
