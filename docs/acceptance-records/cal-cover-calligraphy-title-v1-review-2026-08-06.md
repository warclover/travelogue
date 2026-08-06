# PRD-COVER-CALLIGRAPHY-TITLE-V1 · 七席评审纪要

| 属性 | 内容 |
|------|------|
| **文档** | [PRD-COVER-CALLIGRAPHY-TITLE-V1.md](../PRD-COVER-CALLIGRAPHY-TITLE-V1.md)（**CAL** · 封面艺术字标题 · 点睛） |
| **关联** | [PRD-COVER-ART-DIRECTION-V1.md](../PRD-COVER-ART-DIRECTION-V1.md)（CAD）· [PRD-COVER-STYLES-V6.md](../PRD-COVER-STYLES-V6.md) · [PRD-AI-RETURN-V1.md](../PRD-AI-RETURN-V1.md)（AIR）· [PRD-CHAPTER-NAMING.md](../PRD-CHAPTER-NAMING.md) · 证据 [cover-calligraphy-title-evidence-2026-08-06/](./attachments/cover-calligraphy-title-evidence-2026-08-06/) |
| **评审版本** | PRD **v0.1.0** → Must-Fix 回写后升 **v0.2.0** |
| **日期** | 2026-08-06 |
| **结论** | **有条件通过（Conditional Go · 仅冻结策划，不 Kickoff 工程）** |
| **编码** | ☑ **W0 策划已冻结（v0.2.0 · BLK 已关）**　□ **W1 合码**（须产品显式拉起「封面装帧增强」）　□ W2　□ W3 |
| **参评角色（七席）** | 产品 · 算法 · 架构 · 开发 · 测试/QA · 视觉/排版 · 用户体验（狗粮手测） |
| **评审方式** | 分席只读 PRD §0～§12 · D/OQ/AC 表 + **对照现网**（`cover_engine/` · `cover-opening.hbs` · `journal.css` · CAD/AIR 文档状态 · demo 证据四图） |
| **记录人** | 七席联合纪要（跨职能模拟联评 · 基于 2026-08-06 PRD v0.1.0 + 代码事实核查） |
| **本纪要状态** | **已结案 · Conditional Go** · **PRD v0.2.0 已回写 BLK-CAL-01～05** |
| **审查基线** | 真照片优先 · 装饰可生成风景不可冒充 · 干净管线实证优先 · 本阶段不动代码 · 零用户介入 |

---

## 0. 会前宣读（主持人）

1. **切口**：CAL = 封面标题的**视觉呈现**（透明 PNG 贴纸），不是选图、不是假风景文生图、不是章名文案生成。
2. **产品定调**：路线锁定字库合成（干净管线）；文生图远期；当前 `planning-paused`，只评审策划，不批工程排期。
3. **勿重开**：是否要做实时即梦级文生图（已否）；是否再投 `brush_engine_v3/v4`（已否）；是否本周开工写代码（已否）。
4. **本场必拍**：CAD 依赖是否倒挂 · 标题文案合同（渲染哪段字）· PNG 贴纸 vs 现网 HTML 标题/内联编辑/长图 CSS · 与 V6 五款 Opening 的落点冲突 · 「挂 AI 能力建设列车」语义是否误导。
5. **列车**：W0 冻结 → 暂停；W1 仅在产品显式拉起后开工。

---

## 1. 总评（一句话）

> **七席一致 Conditional Go（仅 W0）：问题真实、路线选择与 demo 实证对齐、干净管线锁定正确、暂停排期合理；但 v0.1 有五处策划缺口会在未来 Kickoff 时翻车——（1）数据模型挂在尚未落地的 CAD `artDirection` 上，复用的 `textSafe`/`typeTheme` 现网不存在；（2）未钉死渲染哪段标题文案及字数/字形覆盖合同；（3）现网封面标题是 HTML/CSS（含内联编辑与五款 Opening 差异布局），PNG 贴纸叠加的表面合同未写；（4）把 CAL 绑在「AI 能力建设」列车上与「零 LLM」实现矛盾，易与 AIR 抢位；（5）印章素材来自 wanx 生成，与归因文案「非 AI 绘图」张力未解。关 BLK-CAL-01～05 后升 v0.2 冻结策划；不 Kickoff 工程。**

---

## 2. 分席表决

| 席位 | 表决 | 一句话 |
|------|------|--------|
| **产品** | **Conditional Go** | 「画龙点睛」定位对；预期管理靠实证是对的。但「挂 AI 阶段启动」容易让人以为要上 LLM/文生图——须改成「封面装帧增强窗口」或与 CAD 同列车，避免与 AIR（文案解冻）抢叙事。零介入目标与 §8「换版式/换印章」高级面板需写清：高级面板非默认、不挡零介入主路径。 |
| **算法** | **Conditional Go** | 干净管线 > 特效 > 骨架引擎的单调降质结论成立，D-CAL-02 应升红线。自动配色/定位是真增量，但 PRD 把定位写成「复用 CAD textSafe」——现网无此 API；须写明 W2 自建最小 `placement_score`（亮度/留白/脸距）或显式依赖 CAD W1 交付。字形覆盖校验（缺字 fail-open）须进 AC。 |
| **架构** | **Conditional Go** | D-CAL-04 落 `cover_engine/title_art/` 方向对。**阻塞**：§6 把 `titleArt` 嵌在 CAD `artDirection` 内，而 CAD 仍是 Draft、代码零字段。须二选一冻结：**(A)** CAL 独立 `meta.titleArt`（不堵 CAD）或 **(B)** W1 硬门禁「CAD W1 Decision 已合入」。禁止以「移植 demo」为由把 `arttext-miniapp/` 留在 travelogue 根目录当运行时依赖。 |
| **开发** | **Conditional Go** | 现网事实：`cover-opening.hbs` 用 `{{title}}` HTML；`copy_patch` 可改 `meta.title`；长图 CSS 大量特化 `.cover-opening__title`；V6 五款 Opening 标题布局不同。PNG 贴纸会打断内联编辑、无障碍与密度规则——PRD 须补「渲染表面合同」：贴纸是否替换 DOM 文字、编辑时是否回退 HTML、长图/导出是否同一 asset。Pillow Card 管线是否消费贴纸未写。 |
| **测试 / QA** | **Conditional Go** | AC-01/03/05～07 可测；AC-02「不劣于 demo」主观，需金样哈希或固定 fixture 对比；AC-04 WCAG「近似」须钉数字阈值。须补 AC：缺字降级、`enabled=false` 金样、五款 Opening 各至少 1 册不遮挡主体。盲评 ≥55% 可沿用 CAD 口径，但对比基线须写清是「现网 CSS 标题」而非 CAD Mode A。 |
| **视觉 / 排版** | **Conditional Go** | clean 样本（证据②）作为上限预期可接受，达不到即梦场景融合——产品须在 Studio 归因说清。三套 D 款模板对「杂志 Opening」可能过「贴纸感」；须按 V6 样式给出**允许叠加白名单**（例如仅 `veil-footer`/`folio-overlap`），禁止在竖排大字 Opening 上硬贴横排书法 PNG。印章朱红与浅色封面对比成立，与深色封面需 §5.1 真跑色。 |
| **用户体验 · 狗粮** | **Conditional Go** | 零介入正确。最大风险是用户改标题后贴纸不同步、或贴纸不可读却仍显示。须狗粮脚本：改 `meta.title` → 预览/长图贴纸更新或明确「需重新优化装帧」。预期话术：「书法贴纸」≠「AI 画封面」。 |

**汇总**：**七席 7/7 Conditional Go（W0 仅）**。

- **W0**：文档冻结 ✅（本纪要）；**关 BLK-CAL-01～05 后升 PRD v0.2.0**。
- **W1**：不批开工；须产品显式拉起 + 落点拍板（BLK-01）+ 授权门禁。
- **W2/W3**：维持 PRD 原计划，不提前。

**对齐评分**

| 维度 | 分（/10） | 说明 |
|------|-----------|------|
| 问题→方案因果完整度 | **8** | 实证驱动路线选择强；文案合同与表面合同缺口拉分 |
| 与 CAD / V6 / AIR 边界 | **6** | 叙事上对齐 CAD「装饰可生成」；工程依赖倒挂；AI 列车语义混 |
| 工程可开工性（未来） | **7** | 干净管线可移植；配色/定位与 DOM 叠加未规格化 |
| AC 可测性 / 防假绿 | **7** | 有 fail-open 思想；AC-02 主观、缺字/多 Opening 覆盖不足 |
| 视觉/敢发可签核性 | **8** | 证据四图可签「不做特效」红线；即梦预期已管理 |

---

## 3. 事实核查（对照现网）

| # | 断言 | 会中核查 |
|---|------|---------|
| **F-01** | CAD `artDirection` / `typeTheme` / `textSafe` 已在代码可复用 | ❌ **不属实**：全库无 `artDirection`/`titleArt`/`typeTheme`/`textSafe` 实现；CAD 仍为 Draft Ready for Review |
| **F-02** | 现网封面标题为程序化艺术字贴纸 | ❌ **不属实**：`cover-opening.hbs` 输出 HTML `<h1 class="cover-opening__title">{{title}}</h1>`；样式走 CSS（含 `--font-brush`，现代路径常回退 `--font-ui`） |
| **F-03** | Cover Styles V6 Opening 已落地、可换样式 | ✅ 属实：`cover_engine/catalog.py` 注册多款；默认 `veil-footer`；`meta.coverOpeningStyle` 可 patch |
| **F-04** | 封面标题可被用户内联编辑 | ✅ 属实：hook 有 `data-editable`；title 经 `copy_patch`/`meta.title` 路径可改；长图 CSS 大量绑定 `.cover-opening__title` |
| **F-05** | demo 干净管线证据存在且可归档对照 | ✅ 属实：四图已入 `acceptance-records/attachments/cover-calligraphy-title-evidence-2026-08-06/` |
| **F-06** | demo 加特效 / v4 引擎效果劣于 clean | ✅ 属实（证据③④ vs ②）；支持 D-CAL-02 |
| **F-07** | AIR 是「AI 用户面回归」主列车 | ✅ 属实：AIR = 文案/渠道包解冻 + 自备 Key；明确不做假风景封面 |
| **F-08** | CAL 干净管线需要 LLM Key | ❌ **不需要**：Pillow 本地渲染；与 AIR 无强制耦合 |
| **F-09** | `arttext-miniapp/` 在 travelogue 根目录 | ✅ 属实（临时拷贝）；**不得**成为运行时依赖 |
| **F-10** | demo 印章素材含 wanx 生成批次 | ✅ 属实（Week1-checklist：印章 smoke/批量走 wanx）；合规与归因需处理 |

**新增事实（评审发现 · 挡门级）**

| # | 事实 | 影响 |
|---|------|------|
| **F-11** | V6 Opening 含竖排/题带/雾底等不同标题几何（如 split-mat 竖排 compact） | → 单一 `position {x,y}` + 横排 D 款贴纸不能无条件套全部样式 |
| **F-12** | 导出 Card / 长图两条栈（Pillow vs Playwright HTML） | → 贴纸若只进 HTML，Card 封面可能仍是平庸字；须在表面合同写清覆盖哪些出口 |
| **F-13** | 游记 `meta.title` 长度与 demo「2～4 字诗意词」分布不同 | → 无字数上限 + 字形覆盖，W1 会大量 fail-open 或挤爆构图 |

---

## 4. 全场共识

1. **干净管线是正确主路径**；特效/骨架引擎永久不进 V1（D-CAL-02 红线）。
2. **文生图保持远期**；本 PRD 不设实验旗标入口（维持 D-CAL-01）。
3. **本阶段只冻结策划，不 Kickoff**（维持 D-CAL-08）。
4. **CAL 是封面装饰层，不是假风景**；与 Charter / CAD 信任叙事兼容。
5. **必须先解依赖倒挂**：要么独立 `meta.titleArt`，要么硬等 CAD W1——写入 D 表，禁止含糊「扩展 artDirection」。
6. **必须补标题文案合同与渲染表面合同**，否则移植管线接不上现网 Opening。
7. **启动触发勿绑死「AI 能力建设」**：改为产品显式拉起的「封面装帧增强」窗口；实现本身为零 LLM。
8. **`arttext-miniapp/` 仅作分析参考**；证据已归档；Kickoff 时只移植 clean 所需代码/素材进 `cover_engine/title_art/`，不把整个 demo 仓并进主树。

---

## 5. Must-Fix（阻塞 · 升 v0.2 前关闭）

| ID | 议题 | 要求（冻结一字面） | 挡 | 状态 |
|----|------|-------------------|----|------|
| **BLK-CAL-01** | CAD 依赖倒挂 | 冻结方案 **(A)**：独立 `trip.meta.titleArt`；删除复用现网 textSafe/typeTheme；自建 placement_score；未来可再嵌 CAD | W0→v0.2 | ✅ **已回写 v0.2.0**（D-CAL-09/13 · §8） |
| **BLK-CAL-02** | 标题文案合同 | 主串 `meta.title` · ≤8 · 副标可选 · 缺字 fail-open · AC-CAL-08 | W0→v0.2 | ✅ **已回写 v0.2.0**（§4） |
| **BLK-CAL-03** | 渲染表面合同 | img + sr-only h1 · stale/重生 · 长图同源 · ECC/Card V1 不进 | W0→v0.2 | ✅ **已回写 v0.2.0**（§7 · AC-09/10） |
| **BLK-CAL-04** | 与 V6 Opening 兼容 | 白名单首发 `veil-footer` · 可选 `folio-overlap` · 非白名单强制不贴 | W0→v0.2 | ✅ **已回写 v0.2.0**（D-CAL-10 · §5.4） |
| **BLK-CAL-05** | 启动列车与归因 | 「封面装帧增强」窗口 · 与 AIR 解耦 · 印章自制/公版 · 归因区分 | W0→v0.2 | ✅ **已回写 v0.2.0**（D-CAL-11/12 · §10–11） |

**Should-Fix（不阻塞 v0.2 冻结，挡未来 W1/W2）**

| ID | 建议 | 状态 |
|----|------|------|
| **SHD-CAL-01** | AC-CAL-02 改为固定 fixture 金样对比（允许感知哈希容差），避免纯主观「不劣于」 | 待 W1（v0.2 已预留口径） |
| **SHD-CAL-02** | AC-CAL-04 钉对比度数值（如局部区域相对亮度差或近似 WCAG AA） | 待 W2 |
| **SHD-CAL-03** | §8 高级「换版式/换印章」标明 L2 可选，默认路径零按钮 | ✅ 已随 v0.2 §10 回写 |
| **SHD-CAL-04** | Kickoff 前从 travelogue 根目录移除或 `.gitignore` `arttext-miniapp/`，防误提交/误依赖 | 待仓库卫生 |
| **SHD-CAL-05** | 盲评基线写死：「现网 CSS `--font-brush`/Opening 标题」vs `titleArt=on` | ✅ 已随 v0.2 AC-CAL-BLIND 回写 |

---

## 6. 拍板 D / OQ（锁定）

| ID | 结论 |
|----|------|
| **D-CAL-01～03、05～08** | **维持**（路线/干净管线/移植/默认关/贴纸/授权/暂停排期） |
| **D-CAL-02** | **升红线**：V1 合入审查若出现 brush_effects / engine v3/v4 路径 → 拒收 |
| **D-CAL-04** | **维持落点** `cover_engine/title_art/`；**数据挂载以 BLK-CAL-01 为准重写** |
| **OQ-CAL-01** | **收窄**：由 BLK-CAL-04 用白名单关闭「全 layout 一视同仁」；mobile 独立版式延期 |
| **OQ-CAL-02** | **维持**：仅封面；章/长图分段标题另案 |
| **OQ-CAL-03** | **默认倾向**：V1 **不**移植 wanx 印章批次；自制或公版（BLK-CAL-05） |
| **OQ-CAL-04** | **维持**：文生图另立 PRD，本主题不讨论触发条件 |

---

## 7. 对 PRD 状态的裁定

| 项 | 裁定 |
|----|------|
| 工程 Kickoff | **否** |
| 策划冻结 | **是**（v0.2.0 · BLK-CAL-01～05 已关） |
| DOC-STATUS | 保持 **planning-paused** 直至产品显式拉起「封面装帧增强」 |
| 与 CAD 关系 | **姊妹策划**；数据独立 `meta.titleArt`（方案 A），非 CAD 子任务同船开工 |
| 与 AIR 关系 | **解耦**；CAL 不消耗 LLM Key，不进 AIR 验收 |

---

## 8. 修订记录

| 版本 | 日期 | 说明 |
|------|------|------|
| **v1.0** | 2026-08-06 | 七席 Conditional Go（W0）；BLK-CAL-01～05；事实核查 F-01～13；维持暂停排期 |
| **v1.1** | 2026-08-06 | PRD v0.2.0 回写结案：BLK-CAL-01～05 全部 ✅；SHD-03/05 已随版；W0 策划冻结 |
