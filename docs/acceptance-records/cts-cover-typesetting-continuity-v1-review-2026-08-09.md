# PRD-COVER-TYPESETTING-CONTINUITY-V1 · 七席评审纪要

| 属性 | 内容 |
|------|------|
| **文档** | [PRD-COVER-TYPESETTING-CONTINUITY-V1.md](../PRD-COVER-TYPESETTING-CONTINUITY-V1.md)（**CTS** · 封面成册感 · 成册） |
| **关联** | [PRD-COVER-CALLIGRAPHY-TITLE-V1.md](../PRD-COVER-CALLIGRAPHY-TITLE-V1.md)（CAL · v0.6.27）· [PRD-COVER-STYLES-V6.md](../PRD-COVER-STYLES-V6.md) · [PRD-SHARE-FACE-INTEGRITY-V1.md](../PRD-SHARE-FACE-INTEGRITY-V1.md)（D-SFI-13）· [cal-cover-calligraphy-title-v1-review-2026-08-06.md](./cal-cover-calligraphy-title-v1-review-2026-08-06.md) |
| **评审版本** | PRD **v0.1.0** → Must-Fix 回写后升 **v0.2.0** ✅ |
| **日期** | 2026-08-09 |
| **结论** | **有条件通过（Conditional Go · 可冻结策划；W1 文档可 Kickoff；扩白名单仍受 W0/W3 门禁）** |
| **编码** | ☑ **策划冻结（v0.2.0 · BLK 已关）**　□ **W0 CAL 合入**（现网未合）　□ **W1 Spec + 身份线**　□ W2 hint　□ W3 埋点解读 / 扩白名单 go-no-go |
| **参评角色（七席）** | 产品 · 算法 · 架构 · 开发 · 测试/QA · 视觉/排版 · 用户体验（狗粮手测） |
| **评审方式** | 分席只读 PRD §0～§12 · D/OQ/AC 表 + **对照现网**（`feat/cover-calligraphy-title-v1` @ `1412dff1` · `title_art/` · `cover_opening.py` · `journal.css` · `studio_events`） |
| **记录人** | 七席联合纪要（跨职能模拟联评 · 基于 2026-08-09 PRD v0.1.0 + 代码事实核查） |
| **本纪要状态** | **已结案 · Conditional Go** · **PRD v0.2.0 已回写 BLK-CTS-01～05** |
| **审查基线** | 契约先于特效 · 宁缺勿滥 · 人话引导不做算法品味 · 路线 C 维持高级项 · 印章不做 · 合入听数据再扩 |

---

## 0. 会前宣读（主持人）

1. **切口**：CTS = 封面作为**一页编辑结果**的连续性（Spec + 字数档引导 + 身份线一本感 + 扩白名单政策），**不是**新开艺术字路线、不是第 11 款风格、不是可读性算法。
2. **与 CAL 关系**：CAL（点睛）已交付艺术字默认开、字体调性、身份线、埋点、质量审计；CTS 承接「成册」，不重做 CAL。
3. **勿重开**：路线 C 默认开（已否）；印章图形（已否）；D-CAL-24 可读性自检（已关）；10 款全开艺术字（已否）。
4. **本场必拍**：前置「CAL 已合入」是否属实 · 问题叙事是否oversell（风格×照片×标题）· 字数档与 monument / CAL ≤8 截断是否同源 · Spec 真相源如何防双源漂移 · W3 冷启动数据门禁是否可执行。
5. **列车**：关 BLK → v0.2 冻结策划；W0 合 CAL 可独立；W1 Spec/身份线可在策划冻结后开工；**G-CTS-03 扩白名单不得早于 G-CTS-05**。

---

## 1. 总评（一句话）

> **七席一致 Conditional Go：主题切口正确、战略六原则可冻结、里程碑与非目标克制得当；但 v0.1 有五处策划缺口会在 Kickoff 后翻车——（1）前置条件写「CAL 已合入」与现网不符（分支仍领先 master）；（2）§1.2 把「风格×照片×标题分家」写成核心缺口，交付却几乎只做标题×风格 hint，因果oversell；（3）字数档三档命名与 `resolve_monument_title_layout` 的 compact/wrapped/wrapped-long、以及 CAL `MAX_MAIN_CHARS=8` 截断关系未钉死映射表；（4）字数计算口径（`resolve_display_title` 的 limit/标点/NFC）未写成合同；（5）D-CTS-06「Spec 真相源」缺可测 AC，易重演 CAL 白名单与 CSS 漂移。关 BLK-CTS-01～05 后升 v0.2；允许 W1 文档与身份线审计开工；扩艺术字仍卡 W0+W3。**

---

## 2. 分席表决

| 席位 | 表决 | 一句话 |
|------|------|--------|
| **产品** | **Conditional Go** | 「成册」叙事对：翻开即信任靠契约与引导，不是再开一条生成线。成功标志写「失败样例变少」比「风格数变多」正确。须收窄 §1.2.3：本主题不承诺修 joint 选图×风格配型；若要做，另立薄切片或降级为「问题背景、非本主题交付」。W0 合 CAL 是产品门禁，勿与 CTS Kickoff 绑死（D-CTS-07 方向对，但前置条件表述须改）。 |
| **算法** | **Conditional Go** | 不做品味算法（NG-CTS-03）正确。字数档是规则表不是模型——但「字」的定义必须冻结（NFC 码点？是否去空白/标点？是否用 `resolve_display_title` 截断后的串？）。艺术字主串仍 ≤8（`contract.MAX_MAIN_CHARS`）：long 档（≥8）在 hint 与 sticker 截断之间易让用户误解「生成了完整长标题」——Spec / 文案须明示。失败率 &lt;5% 在 n&lt;20 改人工：合理，写入 D 表勿只放 §8。 |
| **架构** | **Conditional Go** | Spec 落地路径（acceptance-records 短文）可接受（OQ-CTS-04）。风险在双源：`journal.css` / `whitelist.py` / `FONT_VOICE` / monument layout 四处已有隐式 Spec。D-CTS-06 须配「冲突裁决句 + AC」及变更记录义务，否则 W2 hint 常量会再长出第五源。hint 事件进前后端白名单模式沿用 D-CAL-27——对。禁止把 CTS 实现堵在 CAD Draft 上（PRD 已写姊妹非硬依赖，保持）。 |
| **开发** | **Conditional Go** | 现网：四款艺术字白名单；monument 已有 4/7 分档；`horizon-split` **无** title-art CSS；hint 代码零。W2 字数函数若前端私算会炸——§5.3 同源要求须落成「共享模块或 BE 下发 tier」二选一写进 D 表。W3 开放 `horizon-split` 艺术字 = 新 placement + CSS + 指纹回归，工作量被 §6 写轻了；AC-CTS-06 条件通过可接受，但须在 Must-Fix 标明「开放 = 独立小切片，不是改一行 whitelist」。 |
| **测试 / QA** | **Conditional Go** | AC-CTS-01/02/03/04/05/07 大体可测；AC-CTS-06 条件项清晰。缺：**字数档金样**（固定标题串 → 期望 tier）；**hint 不阻断**的负向用例；**D-CTS-06 漂移**至少「Spec 表与 whitelist 集合一致性」抽检。G-CTS-05「≥30 impression」在合入前无法满足——W0 未完成时 W3 不得假绿。mobile 回落（OQ-CTS-05）须有一条狗粮或标「V1 不验」。 |
| **视觉 / 排版** | **Conditional Go** | §4.3 初稿气质表方向对：`type-monument` 宠短、`horizon-split` 宠长，与现网版式直觉一致。定稿时每格必须补「字号策略 / 是否劝退艺术字 / 文案 key」，否则工程师无法实现 hint。身份线「一本感」核对清单可签；注意前封 10px/opacity 量级是基线不是新设计。下一款艺术字候选 `horizon-split` 同意；竖排 `scroll-head` 延后正确。 |
| **用户体验 · 狗粮** | **Conditional Go** | 「只提示不强迫」（D-CTS-03）对。示例文案已近 28 字上限，易超——原则改为「一句人话，优先 ≤28 字，硬顶 36」。无「一键切风格」（OQ-CTS-02）可接受，但 hint 须说清用户下一步（改字 or 换版式），不能只抱怨。冷启动：合入后 dogfood 周若 impression 不足，产品应允许「书面说明后暂缓扩白名单」——PRD 已写，须升为成功定义的一部分（成功 ≠ 必须开 horizon-split）。 |

**汇总**：**七席 7/7 Conditional Go**。

- **W0**：CAL 合入主干 + 埋点落盘确认（现网未完成 → **BLK-CTS-01**）。
- **策划冻结**：关 BLK-CTS-01～05 → PRD **v0.2.0**。
- **W1**：Spec + 身份线审计 —— 策划冻结后可 Kickoff（不依赖扩白名单）。
- **W2/W3**：维持原计划；W3 允许 no-go。

**对齐评分**

| 维度 | 分（/10） | 说明 |
|------|-----------|------|
| 问题→方案因果完整度 | **7** | 成册切口强；「照片×风格」oversell 拉分 |
| 与 CAL / V6 边界 | **9** | 继承表清晰；非目标克制 |
| 工程可开工性（W1） | **8** | Spec/审计可开工；W2/W3 依赖字数合同与合入 |
| AC 可测性 / 防假绿 | **7** | 主体可测；缺 tier 金样与 Spec 漂移 AC |
| 视觉/敢发可签核性 | **8** | 宁缺勿滥 + horizon-split 优先级可签 |

---

## 3. 事实核查（对照现网）

| # | 断言 | 会中核查 |
|---|------|---------|
| **F-01** | CAL 主干能力「已合入或等价可用」 | ⚠️ **半属实**：能力在 `feat/cover-calligraphy-title-v1`（`1412dff1`）齐全；**未**合入 `origin/master`（分支领先，非 ancestor） |
| **F-02** | 艺术字默认白名单四款 | ✅ `whitelist.DEFAULT_ENABLED_STYLES` = veil-footer / band-cut / contact-stamp / folio-overlap |
| **F-03** | D-CAL-27 impression / resolve 通道可用 | ✅ `studio_events.py` + `analytics.js` 均已登记；合入前 master 无此通道 |
| **F-04** | D-CAL-28 换封面指纹 / CAS 外计算已收口 | ✅ 分支内已修；随 W0 合入生效 |
| **F-05** | `resolve_monument_title_layout` 与 D-CTS-01 阈值对齐 | ✅ 阈值 ≤4 / ≤7 / else 对齐；**命名**为 compact / wrapped / wrapped-long，≠ regular / long |
| **F-06** | CAL 艺术字主串 ≤8 | ✅ `title_art/contract.py` `MAX_MAIN_CHARS = 8`；long 档标题贴纸仍截断 |
| **F-07** | `resolve_display_title` 可直接当字数源 | ⚠️ 默认 `limit=20`；与艺术字 ≤8、展示主串清洗规则并存——**须钉合同** |
| **F-08** | 身份线前封 10 款已接线 | ✅ `worksBrandLine` + `.cover-opening__brand`；一本感核对仍缺验收记录 |
| **F-09** | `horizon-split` 已有 title-art CSS / placement | ❌ **不属实**：`journal.css` title-art 仅四款；开放 = 新工作，非改白名单一行 |
| **F-10** | `cover_title_length_hint_*` 已有实现 | ❌ **不属实**：仅 PRD 规划 |
| **F-11** | Typeface Voice Matrix / 路线 C 高级项 | ✅ 分支内；C 默认关 |

**新增事实（评审发现 · 挡门级）**

| # | 事实 | 影响 |
|---|------|------|
| **F-12** | §1.2.3「风格×照片×标题」无对应 G-CTS | → 问题叙事与交付不符，须收窄或加 NG |
| **F-13** | Studio 总闸 `TitleArtConfig.enabled` 默认 True ≠ trip `meta.titleArt.enabled` 占位 False | → 埋点解读须区分「未生成」与「总闸关」；写进 G-CTS-05 解读备忘模板 |
| **F-14** | W0 未完成则无法积累真实 impression | → W3 / D-CTS-04 不得在合入前用空数据假绿 |

---

## 4. 全场共识

1. **CTS 切口正确**：契约 + 字数档 + 轻提示 + 身份线一本感；成功 ≠ 扩白名单。
2. **战略六原则可冻结**（契约先于特效、宁缺勿滥、人话引导、C 不升默认、印章不做、听数据再扩）。
3. **CAL 合入是 W0 硬门禁**，但 **不**阻塞 v0.2 策划冻结，也 **不**阻塞 W1 Spec 文档起草（可用分支 dogfood）；**阻塞** G-CTS-05 / 扩白名单。
4. **必须收窄「照片×风格」叙事**，避免 Kickoff 时被当成 joint 引擎改造。
5. **必须钉死字数档合同**：展示串来源、计数规则、与 monument 命名映射、与 CAL ≤8 截断的用户可见关系。
6. **D-CTS-06 必须可验收**：至少一条 AC 防 Spec / CSS / whitelist 长期双源。
7. **开放 `horizon-split` 艺术字是条件切片**，不是 W3 默认交付；允许书面 no-go。

---

## 5. Must-Fix（阻塞 · 升 v0.2 前关闭）

| ID | 议题 | 要求（冻结一字面） | 挡 | 状态 |
|----|------|-------------------|----|------|
| **BLK-CTS-01** | CAL 合入前置表述 | 前置条件改为：**（A）已合入 master**，或 **（B）等价：以本分支 dogfood / 预发为准，但 G-CTS-05 与扩白名单仍须 master（或正式环境）可读 jsonl**。删除含糊「已合入或等价可用」单行混写。D-CTS-07 补一句：W1 Spec 允许在（B）下开工。 | W0→v0.2 | ✅ **已回写 v0.2.0** |
| **BLK-CTS-02** | 问题叙事 oversell | §1.2 删除或改写「风格×照片×标题分家」为**背景观察**；新增 **NG-CTS-08**：本主题不做 joint 选图×Opening 配型改造。若未来要做，另立主题。 | W0→v0.2 | ✅ **已回写 v0.2.0** |
| **BLK-CTS-03** | 字数档计数合同 | 冻结：tier 输入 = `resolve_display_title(meta)` 返回串，经 NFC 后按 Unicode 码点计长（去首尾空白；**不去**中间标点，除非 Spec 另表）。禁止前端用 raw `meta.title` 私算。写入 §4 或新 §4.0，并加 **AC-CTS-08**（金样标题→期望 tier）。 | W0→v0.2 | ✅ **已回写 v0.2.0** |
| **BLK-CTS-04** | 三档命名映射表 | 在 PRD 正文（非仅 OQ）冻结映射：`compact≡monument.compact` · `regular≡wrapped` · `long≡wrapped-long`；OQ-CTS-01 关闭为「全局三档 + Spec 格内用首选/谨慎表达更严」。并注明：艺术字主串仍 `MAX_MAIN_CHARS=8`，long 档 hint 文案须避免暗示「贴纸会排完整长标题」。 | W0→v0.2 | ✅ **已回写 v0.2.0** |
| **BLK-CTS-05** | Spec 真相源可测 | 新增 **AC-CTS-09**：W1 Spec 定稿须含「与 `DEFAULT_ENABLED_STYLES` / title-art CSS 选择器集合一致性」核对句；冲突时按 D-CTS-06 留变更记录。§6.3 补一句：开放新风格 = placement + CSS + 指纹回归，**不只**改 `enabled_styles`。 | W0→v0.2 | ✅ **已回写 v0.2.0** |

**Should-Fix（不阻塞 v0.2 冻结，挡未来里程碑）**

| ID | 建议 | 状态 |
|----|------|------|
| **SHD-CTS-01** | hint 文案原则：优先 ≤28 字，硬顶 36；示例按硬顶重写 | 待 v0.2 或 W2 |
| **SHD-CTS-02** | G-CTS-05 解读备忘模板区分：总闸关 / 非白名单 disabled / 未点击 / error|network | 待 W3 |
| **SHD-CTS-03** | OQ-CTS-05 mobile 回落：V1 标「不验」或补 1 条狗粮 | 待 W2 |
| **SHD-CTS-04** | W0 合入清单显式排除 `字体/`、`README - 副本.md`、`arttext-miniapp/`（与 §8.1 呼应，合入 PR 检查） | 待 W0 |
| **SHD-CTS-05** | `acted` 事件：V1 明确「不做」写入 NG 或 OQ 关闭，避免半实现白名单 | 待 v0.2 |

---

## 6. 对 OQ 的会中倾向（不替代产品终裁）

| OQ | 会中倾向 | 是否升 BLK |
|----|----------|------------|
| **OQ-CTS-01** | 全局三档统一 + Spec 格表达更严；映射表进正文 | **是 → BLK-CTS-04** |
| **OQ-CTS-02** | V1 不做一键切风格；`acted` 延后或 NG | SHD-CTS-05 |
| **OQ-CTS-03** | 对齐 `horizon-split` 原生标题锚点；开放时单独立项 | 否（W3 条件） |
| **OQ-CTS-04** | W1 先挂 acceptance-records | 否 |
| **OQ-CTS-05** | 按属性风格提示；V1 可不验窄屏文案 | SHD-CTS-03 |

---

## 7. 里程碑裁定

| 里程碑 | 本场裁定 |
|--------|----------|
| **策划冻结（v0.2）** | **批准**：关 BLK-CTS-01～05 后 |
| **W0 CAL 合入** | **批准为独立门禁**（可先于或并行于 v0.2 回写）；未完成则 W3 不可 go |
| **W1 Spec + 身份线** | **有条件批准 Kickoff**：须 v0.2 已回写；允许在分支 dogfood |
| **W2 hint** | **不批开工**直至 W1 Spec 定稿（字数合同依赖 Spec 表） |
| **W3 扩白名单** | **维持 go/no-go**；成功允许 no-go |

---

## 8. 签核

| 席位 | 签字（模拟） | 日期 |
|------|--------------|------|
| 产品 | Conditional Go · 收窄叙事 · 合入门禁说清 | 2026-08-09 |
| 算法 | Conditional Go · 字数合同与 ≤8 截断明示 | 2026-08-09 |
| 架构 | Conditional Go · Spec 防漂移 AC | 2026-08-09 |
| 开发 | Conditional Go · horizon-split = 切片非一行 | 2026-08-09 |
| 测试 / QA | Conditional Go · tier 金样 + 防假绿 | 2026-08-09 |
| 视觉 / 排版 | Conditional Go · §4.3 定稿列齐全 | 2026-08-09 |
| 用户体验 | Conditional Go · 提示有下一步 · 成功≠扩白名单 | 2026-08-09 |

---

## 9. 下一步（主持人交办）

1. ✅ **BLK-CTS-01～05 已回写** PRD **v0.2.0**（OQ-CTS-01 关闭；NG-CTS-08 / D-CTS-08 / AC-CTS-08 / AC-CTS-09）。
2. **并行**：安排 `feat/cover-calligraphy-title-v1` → master 合入（W0），勿夹带杂物（SHD-CTS-04）。
3. **下一步**：拆 `ACCEPTANCE-COVER-TYPESETTING-CONTINUITY-V1.md` / 实施清单；拉起 W1 Spec（允许前置轨 B）。
