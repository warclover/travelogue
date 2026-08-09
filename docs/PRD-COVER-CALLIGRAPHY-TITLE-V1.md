# Travelogue · 封面艺术字标题 V1 产品需求文档（PRD）

| 属性 | 内容 |
|------|------|
| **产品代号** | Travelogue Studio |
| **文档版本** | **v0.6.26** |
| **状态** | **Kickoff · W2 已收口 · W3 已评分（AC-CAL-BLIND 通过，单一评委协议）· D-CAL-05 默认已改为开**（分支 `feat/cover-calligraphy-title-v1`）· [七席评审](./acceptance-records/cal-cover-calligraphy-title-v1-review-2026-08-06.md) · [W1 视觉验收](./acceptance-records/cover-calligraphy-title-v1-w1-visual-review-2026-08-07.md) · [W2 白名单](./acceptance-records/cover-calligraphy-title-v1-w2-whitelist-expand-2026-08-07.md) · [AC-04/05/06/13](./acceptance-records/cover-calligraphy-title-v1-ac04-05-06-13-2026-08-08.md) · [AC-01/02/10](./acceptance-records/cover-calligraphy-title-v1-ac01-02-10-2026-08-08.md) · [D-CAL-23 衬底](./acceptance-records/cover-calligraphy-title-v1-d-cal-23-backdrop-2026-08-08.md) · [D-CAL-24 路线B可读性自检（已关闭·不实现）](./acceptance-records/cover-calligraphy-title-v1-d-cal-24-route-b-legibility-plan-2026-08-09.md) · [W3 盲评方案](./acceptance-records/cover-calligraphy-title-v1-w3-blind-plan-2026-08-08.md) · [W3 盲评进度](./acceptance-records/cover-calligraphy-title-v1-w3-blind-2026-08-08.md) · **v0.6.21**：**AC-CAL-BLIND 已通过**（单一评委协议——产品负责人放宽原 ≥5 人门槛，独立完成 12 对盲评，艺术字侧胜率 91.7%）；随即拍板将 `TitleArtConfig.enabled` 默认值由 `false` 改为 `true`（D-CAL-05 收口）：Studio「生成装帧标题」按钮默认可见，仍为**用户点击触发**，非自动批量渲染；**v0.6.23**：D-CAL-26 装帧身份线前封回声从首批 4 款风格扩展到全部 10 款，逐款真实渲染截图核对通过；**v0.6.24**：veil-footer 长标题贴纸字号微调（W3 b06 留痕跟进）；**v0.6.25**：type-monument 长标题镂空巨字重叠错位修复（D-CAL-26 §8.4 顺带发现跟进）；**v0.6.26**：D-CAL-27 title_art 漏斗埋点（修复白名单漏登记导致事件静默丢弃） |
| **DOC-STATUS** | **kickoff-w1** |
| **主题代号** | 「点睛」— **CAL**（Calligraphy Title） |
| **触发来源** | 2026-08-06 产品讨论：用户希望游记封面标题达到「即梦」文生图那种手写体艺术感；经过对既有内部 demo（`arttext-miniapp`）的实证分析，确认了可落地路径 |
| **前置条件** | [CHARTER.md](./CHARTER.md) §7；[PRD-COVER-STYLES-V6.md](./PRD-COVER-STYLES-V6.md) Opening Registry 可用；现网 `cover-opening.hbs` / `meta.title` 可渲染。**不依赖** CAD 已落地（见 D-CAL-04 / D-CAL-09） |
| **关联文档** | [PRD-COVER-ART-DIRECTION-V1.md](./PRD-COVER-ART-DIRECTION-V1.md)（CAD · 姊妹策划，非硬依赖）· [PRD-AI-RETURN-V1.md](./PRD-AI-RETURN-V1.md)（AIR · **解耦**，CAL 不消耗 LLM）· [PRD-COVER-STYLES-V6.md](./PRD-COVER-STYLES-V6.md) · [PRD-CHAPTER-NAMING.md](./PRD-CHAPTER-NAMING.md) · [PRD-EXPORT-CARD-COMPOSE-V1.md](./PRD-EXPORT-CARD-COMPOSE-V1.md) · 证据 `docs/acceptance-records/attachments/cover-calligraphy-title-evidence-2026-08-06/` · [七席纪要](./acceptance-records/cal-cover-calligraphy-title-v1-review-2026-08-06.md) |
| **验收** | 启动开发时拆 `ACCEPTANCE-COVER-CALLIGRAPHY-TITLE-V1.md`；本文 §12 为源 |
| **实施清单** | 启动开发时拆 `IMPLEMENTATION-COVER-CALLIGRAPHY-TITLE-V1.md` |
| **更新日期** | 2026-08-08（v0.6.14） |

> **v0.6.0 相对 v0.5.0（§6.2 定位策略复核 · 2026-08-07 · 讨论向，本版未改动代码）**
>
> - **背景**：W1 视觉验收（v0.5.0）暴露 `veil-footer` 贴纸曾与主体/文案重叠，产品追问「文字位置如何选取，结合目前 5 款封面样式如何无缝融合」。复核 `travelogue/cover_engine/registry.py`/`catalog.py` 发现：V6 Opening Registry 早已给**全部 10 款风格**（5 款 active + 5 款 retired）定义了 `text_safe_regions`（`CoverStyleProfile` 字段），且已在生产链路（`travelogue/cover_engine/opening/title_safe.py::mark_title_safe`，自动选图环节判断镜头主体是否落进文案留白区）中使用；对照真实渲染 CSS（`.cover-opening__title`/`.cover-opening__panel` 实际坐标）核实，该数据与各风格真实版式高度吻合。**结论**：CAL 自建的 `WHITELIST`/`PlacementPreset`（`whitelist.py`）应改为从 `text_safe_regions` 派生，而非另起一份手搓矩形——这比 D-CAL-13「自建最小信号集」的原始假设（现网无 `textSafe` 数据）更进一步：数据本身**已经存在**，只是此前未被 CAL 复用。
> - **逐风格结论**（详见 D-CAL-20）：
>   1. `veil-footer`（已上线）：现有矩形 `{x:0.08,y:0.14,w:0.84,h:0.22}` 与该风格 `prefer.focal_y_max:0.55`（主体常驻上半区）存在潜在冲突——此前视觉验收中贴纸压到头饰即此风险的实例；建议收窄矩形或接入 `mark_title_safe` 的 focal 校验信号作为落地前的最后一道闸门。
>   2. `folio-overlap`（W2 计划开放）：现有矩形 `{x:0.10,y:0.42,w:0.80,h:0.20}` 与 registry 候选 `{x:0,y:0.58,w:0.7,h:0.2}` 大致重叠但数值不精确；建议直接对齐 registry 候选，不再自造数值。
>   3. `band-cut`（现网真实出现，非白名单）：registry 矩形 `{x:0,y:0.60,w:0.55,h:0.14}` 与真实渲染的 `--cover-band-center:63%` 断带位置精确吻合，且宽高比对横版画布友好——**评估为下一个最应开放的白名单风格**。
>   4. `contact-stamp`（非白名单）：registry 给了左右两块候选（`{x:0,y:0.72,w:0.55,h:0.28}` 对应真实 `<h1>` 位置 / `{x:0.62,y:0.72,w:0.38,h:0.28}` 对应 hook/日戳号位置），建议贴纸仅占左块，不与右块 hook/archive 抢位。
>   5. `scroll-head`（非白名单）：唯一采用 `writing-mode: vertical-rl` 竖排的风格，registry 安全区为窄高竖列，与 Route B/C 现有横版画布假设不兼容——建议明确排除在近期开放范围外，待竖排模板能力补齐再评估。
> - **新增方法论建议**（落入 D-CAL-20，均为 W2 待办，本版未改代码）：placement 候选应统一从 `text_safe_regions` 派生；一个风格有多候选区域时应让 `placement_score` 真正参与打分择优，而非固定绑死单一矩形；`text_safe_regions` 只保证"避开镜头主体"不保证"未被本风格自身文案占用"，需补一层面板占位排除校验；落地前复用既有 `mark_title_safe` 的 focal 校验信号作为统一闸门，避免两套逻辑对同一张照片给出矛盾结论。
> - **本版无代码变更**；结论落为 D-CAL-20（§3）+ §5.4/§6.2 更新 + W2 里程碑细化（§11）+ OQ-CAL-08（§12.2）。

> **v0.6.1 相对 v0.6.0（落地 D-CAL-20 优先顺位①② · 2026-08-07 · [验收记录](./acceptance-records/cover-calligraphy-title-v1-w2-whitelist-expand-2026-08-07.md)）**
>
> - `travelogue/cover_engine/title_art/whitelist.py` 改造：新增 `_registry_rect()`，矩形坐标改为直接读取 `travelogue.cover_engine.registry.get_profile(style_id).text_safe_regions`，不再手搓数值；`folio-overlap`（仍默认关闭）顺带对齐到更贴切的候选区域。
> - **新开放白名单**：`band-cut`（registry 候选 #0）、`contact-stamp`（registry 候选 #0 左块，避让右块 hook/日戳号）加入 `DEFAULT_ENABLED_STYLES`。
> - **真实 trip 视觉核对**：`demo-0ebda73294`（`coverOpeningStyle=band-cut`）跑通 CLI → render → Playwright 实测，贴纸落在断带区域，未遮挡人脸/hook 文案；`contact-stamp` 用同一真实照片临时改风格核对通过（未提交临时数据，仓内暂无真实 contact-stamp 样例，建议后续补留痕）。
> - **过程中发现并修复 1 处集成缺口**：`journal.css` 存在一份独立于 `whitelist.py` 的 CSS 侧白名单（`.cover-opening__title-art` 默认 `display:none`，仅 `veil-footer` 一行覆盖为 `display:block`）——Python 侧加了新风格，CSS 侧未同步，贴纸 DOM 元素正确但不可见；已补 `band-cut`/`contact-stamp` 两行选择器并在 CSS 中注释标注这是手动维护点。
> - **veil-footer 现有矩形**（D-CAL-20 优先顺位④）与 `folio-overlap` 默认开启（优先顺位③）本版**未处理**，维持 v0.6.0 结论。
> - 新增/更新测试：`test_title_art_whitelist.py`（新增 `band-cut`/`contact-stamp` 白名单断言 + 矩形与 registry 一致性回归 + 避让 hook 区域断言）；`tests/unit/cover_engine/` 129 passed；`ruff check` 全绿。

> **v0.6.2 相对 v0.6.1（contact-stamp 深色渐罩配色修复 · 2026-08-07 · [验收记录 §1.3](./acceptance-records/cover-calligraphy-title-v1-w2-whitelist-expand-2026-08-07.md#13-已修复contact-stamp-自动配色未考虑固定深色渐罩--深墨读不出来)）**
>
> - **用户实测反馈**：v0.6.1 宣布完成后，用户直接截图反馈 `contact-stamp` 贴纸「文字都被遮挡了，且颜色一致，看不出来」。
> - **根因**：`contact-stamp` 在 `journal.css` 里用 `::after` 给整张封面叠加一层与照片内容无关的黑色渐变（不透明度约 0.3～0.72），原生 `<h1>` 因此固定用浅色 `#f5f2ec`；但 §6.1 自动配色的 `roi_average_color` 采样的是**渐罩叠加前**的原始照片像素，真实照片在候选区域偏亮，算法据此选了深墨，`contrast_ratio` 达标判定也是拿深墨去跟这个**虚高**的亮度估计比对——实际渲染背景已被渐罩压近全黑，深墨读不出来。
> - **修复**：`PlacementPreset` 新增 `assume_dark_veil: bool` 字段，`contact-stamp` 标记为 `True`（其余三款白名单风格均无此类全幅渐罩，为 `False`）；`engine.py` 命中该字段时改用近黑背景估计，让对比度算法必然回落白色。
> - **验证**：同一真实照片临时改风格重新生成，`titleArt.mainColor` 由深色变为 `#ffffff`；Playwright 截图确认标题在黑色面板区域清晰可辨。
> - 新增测试：`test_assume_dark_veil_flag`（`test_title_art_whitelist.py`）+ `test_contact_stamp_dark_veil_forces_white_ink_despite_bright_photo`（`test_title_art_engine.py`）；`tests/unit/cover_engine/` 134 passed；`ruff check` 全绿。

> **v0.5.0 相对 v0.4.0（W1 真实素材视觉验收 · 2026-08-07 · [验收记录](./acceptance-records/cover-calligraphy-title-v1-w1-visual-review-2026-08-07.md)）**
>
> - 用真实 trip（非 fixture/mock）跑通 `title-art` CLI → `render` → Playwright 实际渲染核对 AC-CAL-03/07/08/09/12，过程中发现并修复 **3 处 83 条单测未捕获的真实集成缺口**：
>   1. **字库资产未随包分发**：`ZhiMangXing-Regular.ttf` 裸文件名交给 Pillow，未装该字体的机器会静默退化到 `msyh.ttc`（微软雅黑），产品核心卖点「书法感」不生效但不报错——已随包分发字体资产（`assets/fonts/`）+ 核实并留痕 SIL OFL 1.1 授权。
>   2. **贴纸容器嵌套错误**：`<img class="cover-opening__title-art">` 嵌在雾带底部文案面板 `.cover-opening__panel` 内部（该面板矮高度由 hook 文案撑起），CSS 百分比定位对不上 §6.2 rect 语义，实测与 hook 文案物理重叠；且 §6.2 算出的 `position.x/y` 从未接进渲染上下文（死代码，CSS 一直用写死的 `50%/28%`）——已把贴纸挪到 `.cover-opening` 直接子层，接通真实定位坐标，`render_b.py` 新增出稿前裁剪到墨迹 bbox（避免居中锚点对齐到大片透明留白的几何中心而非可见字形中心）。
>   3. **`meta.title` 编辑不触发 `titleArt.stale`**：`mark_title_art_stale()` 此前是死代码，`copy_patch.py` 从未调用——用户改标题后旧贴纸会继续展示（AC-CAL-09 实测不通过）；已接线并补 3 条回归测试。
> - AC-CAL-03/07/08/09/12 转为 ✅ 通过；AC-CAL-11 仍待完整 W0.5 Spike，`route_c_enabled` 维持默认 `false`。
> - 新增/更新测试：`test_title_art_render_b.py`（裁剪相关断言）、`test_copy_patch.py`（3 条 stale 回归）；关键子集回归 359 passed, 6 skipped。

> **v0.4.0 相对 v0.3.0（Kickoff 落地 · 2026-08-07 · 分支 `feat/cover-calligraphy-title-v1`）**
>
> - **产品显式拉起「封面装帧增强」窗口**（§11 启动触发达成），本版起 DOC-STATUS 由 `planning-paused` 转为 `kickoff-w1`。
> - **路线 B 已实现**：`travelogue/cover_engine/title_art/`（`contract.py` 文案合同 §4、`fonts.py` 字库池+字形覆盖检查、`render_b.py` 干净合成管线含长标题自适应收缩防溢出、`color.py` §6.1 对比度算法、`placement.py`+`whitelist.py` §6.2/§5.4、`models.py` §8 数据模型）；真实 demo trip（`demo-1547c68851`）跑通生成→写 `trip.meta.titleArt`→渲染表面叠加全链路，人工核对贴纸未溢出画布、配色对比度生效。
> - **路线 C 已实现**：`route_c.py`（DashScope 通义万相异步提交+轮询）、`style_registry.py`（5 款风格 `promptTemplate` 定稿，见 §5.5.1 更新）、`ocr_verify.py`（复用现网 `travelogue.llm.client.vision_chat_completion` 多模态接口做 OCR 回读校验，模型 `qwen-vl-plus`）；`engine.py` 编排两条路线的分层 fallback（D-CAL-16）。
> - **W0.5 Spike 未完整跑（仅现场实测 2 组标题）**：2026-08-07 用户提供真实 API Key 现场验证——`wanx2.1-t2i-turbo` 对"拾光"二字出现"光"字形笔画错误；`wanx2.1-t2i-plus` 实测字形正确。据此**暂定 `wanx2.1-t2i-plus` 为默认模型**（D-CAL-18 更新），但这**不构成** §11 W0.5 里程碑要求的 20～30 条真实/边界标题系统性验证——`route_c_enabled` 配置默认仍为 `false`（`travelogue/config/title_art.py`），正式开启前必须补齐完整 Spike（见 OQ-CAL-07 更新）。
> - **CLI**：新增 `python -m travelogue title-art <trip>`（`--route-c/--no-route-c` / `--style` / `--force`），供人工触发生成与验收核对。
> - **配置**：新增 `AppConfig.title_art`（`TitleArtConfig`），`enabled`/`route_c_enabled` 均默认 `false`——本版落地代码但**不**默认开启生产流量，需产品/运营显式开关。
> - **渲染表面**：`cover-opening.hbs` 按 §7 接入 `<img class="cover-opening__title-art">` + `<h1 class="... sr-only">`；`journal.css` 新增对应样式，仅 `veil-footer` 白名单生效。
> - **单测**：新增 83 条（`tests/unit/cover_engine/test_title_art_*.py`），覆盖文案合同、配色/抠字重上色、白名单、字形覆盖、Route B 渲染防溢出、placement_score、风格库、Route C 网络失败态（mock）、engine 分层 fallback、数据模型序列化；回归跑过既有 `tests/unit/config` + `tests/unit/render`（274 passed）确认未破坏现网。
> - **未完成**：Studio 高级面板触发入口（一次性生成，非用户可反复调参）、`folio-overlap` 第二白名单样式（仍按 D-CAL-10 保持默认关闭）、真实 W0.5 Spike 报告文档。

> **v0.3.0 相对 v0.2.0（产品复议 · 2026-08-07）**
>
> - **复议范围**：产品提出「不要求开放式文生图，而是固定几套提示词模板、仅替换标题文字」的受限方案；经分析后判定这与 D-CAL-01/D-CAL-02 字面冲突，但当时的实证（§1.3）评的是 demo 内骨架引擎/笔锋滤镜，**并未真正测过真实 diffusion API 的固定提示词效果**，故按复议流程处理，而非直接推翻冻结决策。
> - **结论：新增「路线 C：固定提示词分层生图」为候选路线**，与路线 B（字库合成）并列，形成**主 + 备**分层架构（路线 C 优先尝试 → 失败/超时/审核不过/字形校验不过 → 兜底路线 B → 仍失败 → fail-open 现网 HTML），**不**是替代关系。D-CAL-01/D-CAL-02 的适用范围收窄为「默认兜底与字库合成红线」，新增 D-CAL-14～D-CAL-19。
> - **新增 §5.5**：路线 C 引擎规格（风格库 Registry、5 款初始风格占位、色彩后处理管线——生成阶段固定「白底黑字」高对比稿，落地时复用 §6.1 对比度算法「抠字重上色」，而非在提示词里现场描述颜色）。
> - **新增 W0.5 里程碑**：技术验证 Spike（先测通义万相，即梦/腾讯混元陪跑对比），核对字形准确率与成本延迟后再决定路线 C 是否升级为默认候选。
> - **数据模型**：`meta.titleArt.engine` 新增枚举 `diffusion-fixed-prompt-v1`；新增 `styleId` / `modelProvider` / `promptVersion` / `ocrVerified` / `fallbackFrom` 字段。
> - **合规**：新增 API 生成内容版权、内容安全审核相关条目（§9）。
> - 本版**未**变更 D-CAL-03～13 对路线 B 本身的既有约束；路线 B 继续作为兜底路径，投入不作废。

> **v0.2.0 相对 v0.1.0（七席回写 · 2026-08-06）**
>
> - **BLK-CAL-01**：`titleArt` 落独立 `trip.meta.titleArt`（方案 A）；不挂未落地的 CAD `artDirection`；删除「复用现网 textSafe/typeTheme」措辞；自建最小 `placement_score`。
> - **BLK-CAL-02**：新增 §4 标题文案合同（主串 `meta.title` · ≤8 字 · 副标可选 · 缺字 fail-open）；补 AC-CAL-08。
> - **BLK-CAL-03**：新增 §7 渲染表面合同（img + sr-only · 改 title 失效/重生 · 长图同源 · ECC/Card V1 不进）。
> - **BLK-CAL-04**：V6 Opening **白名单**首发仅 `veil-footer`（可选加 `folio-overlap`）；非白名单强制 `enabled=false`；收窄 OQ-CAL-01。
> - **BLK-CAL-05**：启动触发改为「封面装帧增强窗口」，与 AIR 解耦；印章 V1 **自制/公版**，不移植 wanx 批次；归因文案区分字库合成与印章来源。
> - **D-CAL-02** 升红线；顺手处理 SHD-CAL-03（高级面板标 L2）。

> **定位**
>
> CAL 解决的是封面「**标题字本身的艺术感**」这一个具体缺口——免费字库直出显得平庸，但用户又明确不想现在引入实时文生图。
> CAL **不是**给游记封面造一张假风景图，也**不是**重新做一套排版引擎；它只产出**一枚可复用的透明标题贴纸**（PNG-RGBA），由现网 Opening（及未来可选 CAD）决定是否叠加。
>
> **一句话目标**：**零用户介入**，根据封面照片自动选定位置与配色，把游记标题渲染成一枚有笔锋感的书法/手写体贴纸，作为封面的「画龙点睛」，而不是主视觉本身。
>
> **战略原则（已冻结 + v0.3 复议收窄）**
>
> 1. **路线 B 锁定为默认兜底：字库合成** — 100% 本地 Pillow 渲染，零 LLM / 零扩散模型调用，**任何情况下必须可用**。
> 2. **克制胜过堆砌** — demo 实证：干净合成 > 笔锋特效 > 骨架引擎；**越少干预越好**（对路线 B 仍是红线）。
> 3. **移植优于重造** — 移植 `arttext-miniapp` 干净管线 + 补齐自动配色/定位与现网表面合同。
> 4. **画龙点睛，不是主视觉** — 文字装饰层 ≠ 伪造风景；与 Charter / CAD 信任叙事兼容（对路线 B / C 均适用）。
> 5. **权利清晰** — 字库须商用授权；印章 V1 自制/公版，不移植 wanx 批次；路线 C 生成内容需核对模型服务商的商用授权条款（§9）。
> 6. **Kickoff 门槛** — 仅在产品显式拉起「封面装帧增强」窗口时动代码（**不**绑定 AIR）；**v0.4：该窗口已于 2026-08-07 拉起，进入 W1**。
> 7. **受控生成优先于开放生成（v0.3 新增）** — 路线 C **不**提供开放式 / 自由 prompt 入口；仅固定风格库（§5.5）+ 变量占位替换标题文字；任何新风格入库须过轻量评审，禁止运行时现场编排提示词。
> 8. **主 + 备分层，不是二选一（v0.3 新增）** — 路线 C 是"效果更佳"的候选主路径，路线 B 永远是兜底；路线 C 失败（超时/审核不过/字形校验不过）必须静默降级到路线 B，再不行 fail-open 到现网 HTML 标题，**禁止**因路线 C 失败而展示错误或半成品贴纸。

---

## 0. 读者指南

| 章节 | 澄清什么 |
|------|----------|
| §0.1 | 术语 |
| §0.2 | 与 CAD / V6 / AIR 的边界 |
| §1 | 背景、问题与实证依据 |
| §2 | 目标 / 非目标 |
| §3 | 冻结决策 D-CAL-* |
| §4 | 标题文案合同（BLK-CAL-02） |
| §5 | 渲染管线规格（路线 B 移植方案 + §5.5 路线 C 候选） |
| §6 | 自动配色与自动定位（自建 placement_score；路线 B/C 共用） |
| §7 | 渲染表面合同（BLK-CAL-03） |
| §8 | 数据模型（独立 `meta.titleArt`） |
| §9 | 素材权利与合规 |
| §10 | Studio 体验 |
| §11 | 里程碑与启动触发 |
| §12 | 风险 · OQ · 验收 AC-CAL-* |
| §13 | 附录：demo 证据 |

### 0.1 术语

| 术语 | 含义 |
|------|------|
| **标题艺术字 / 标题贴纸** | 透明背景 PNG-RGBA：「主标题（书法/手写体）+ 可选副标 + 可选朱红印章」 |
| **干净管线** | 字体直出 → 副标 → 印章；**禁止**笔锋滤镜 / 骨架物理模拟（路线 B 红线） |
| **路线 A / Mode D · 文生图** | 用户自由 prompt / 开放式文生图；**本 PRD 不实现**（区别于路线 C 的固定模板） |
| **路线 B** | 字库合成；**默认兜底路线**，V1 首个可交付路径 |
| **路线 C（v0.3 新增 · 候选）** | 固定提示词模板 + 仅替换标题文字的分层文生图；见 §5.5；**未通过 W0.5 Spike 前不进默认路径** |
| **风格库 / Calligraphy Style Registry** | 路线 C 的固定 prompt 模板表，初始 5 款风格，新增走轻量评审（§5.5.1） |
| **分层 fallback** | 路线 C → 失败/超时/审核不过/字形校验不过 → 路线 B → 仍失败 → fail-open 现网 HTML（原则 8） |
| **Opening 白名单** | 允许叠加贴纸的 `coverOpeningStyle` id 集合（§5.4 / D-CAL-10）；路线 B/C 共用同一白名单与表面合同 |
| **placement_score** | CAL 自建的落点评分（亮度/留白/脸距）；**不**假设现网已有 `textSafe` API；路线 B/C 共用 |

### 0.2 与 CAD / V6 / AIR 的边界

| 主题 | CAL 拥有 | CAL 不碰 |
|------|----------|----------|
| **CAD** | 姊妹策划；未来可将 `meta.titleArt` **再嵌**进 `artDirection`（可选迁移，非 V1 门禁） | **不**硬等 CAD W1；**不**声称复用尚未存在的 `textSafe`/`typeTheme` 代码 |
| **Cover Styles V6** | 仅在白名单 style 上替换/叠加标题视觉 | 不删 Registry；非白名单保持现网 HTML/CSS 标题 |
| **AIR** | 无耦合；不消耗 LLM Key；不进 AIR 验收 | 不占用「AI 用户面回归」叙事与排期 |
| **PRD-CHAPTER-NAMING** | 只管视觉呈现 | 不改标题文案生成规则 |

---

## 1. 背景与问题

### 1.1 用户诉求的由来

用户上传「即梦」文生图截图，希望封面标题有类似手写体艺术感，认为是差异化闪光点。

### 1.2 判断收敛

| 轮次 | 判断 |
|------|------|
| 1 | 路线 A（文生图）vs 路线 B（字库合成） |
| 2 | **当前只做 B**；文生图远期；免费字库平庸；旧 demo 加特效失败 |
| 3 | `arttext-miniapp` 干净管线实证可用；特效/引擎单调降质 |
| 4 | 七席 Conditional Go（W0）；BLK-CAL-01～05 → 本版回写 |
| 5 | 产品复议（v0.3）：提出「固定提示词 + 只换标题文字」的受限文生图；收敛为新增**路线 C 候选**（主+备于路线 B），非推翻 D-CAL-01/02 |

### 1.3 实证依据（已归档）

| 版本 | 做法 | 效果 | 证据 |
|------|------|------|------|
| ① 字库直出 | 三款字库零后处理 | 可用 | `01-font-grid-comparison.png` |
| ② **干净合成（采用）** | 字库 + 副标 + 印章，零特效 | **最佳** | `02-clean-composite-sample.png` |
| ③ 笔锋特效 | 叠加做旧滤镜 | 更差 | `03-brushed-effect-degraded-sample.png` |
| ④ 骨架引擎 v4 | MakeMeAHanzi 路径盖章 | 最差 | `04-stroke-engine-v4-degraded-sample.png` |

路径：`docs/acceptance-records/attachments/cover-calligraphy-title-evidence-2026-08-06/`。

### 1.4 与信任原则的契合

标题艺术字是**文字装饰层**，不伪造风景/地标，与「装饰可生成、风景不可冒充」兼容；实现为零 LLM，与「真照片优先」零冲突。

### 1.5 问题陈述（P-CAL-*）

| ID | 问题 | 严重度 |
|----|------|--------|
| **P-CAL-01** | 现网 Opening 标题偏平庸（`--font-brush` 常回退 UI 字体） | 中等 |
| **P-CAL-02** | 标题色/位未跟封面照片自适应 | 中等 |
| **P-CAL-03** | 干净管线停留在独立 demo，未接现网 Opening 表面 | 中等 |
| **P-CAL-04** | 字库授权未闭环；印章若用 wanx 批次有合规/归因张力 | 中等 |
| **P-CAL-05** | 即梦级预期需管理 | 低（实证已收敛） |
| **P-CAL-06** | （七席）文案合同 / 表面合同 / V6 白名单在 v0.1 缺失 | **已由 v0.2 关闭** |
| **P-CAL-07** | 路线 B 效果上限受字库/印章素材质量约束，与「即梦级」预期仍有观感差距 | 中等（v0.3 新增；路线 C 候选拟收窄） |

### 1.6 复议记录（v0.3 · 2026-08-07）

产品重新提出诉求，但**收窄**为受限方案：不做开放式文生图，而是固定 5 套提示词模板、仅替换标题文字；并提供参考样本（见 §13 附录 · `cover-calligraphy-title-route-c-refs-2026-08-07/`）。

| 复议点 | 结论 |
|--------|------|
| 是否与 D-CAL-01/02 冲突？ | 字面冲突（两者均写「不做实时文生图 / 零扩散模型调用」），但 §1.3 的实证**从未测试过真实 diffusion API**，仅测了 demo 内骨架引擎/笔锋滤镜；信息不足以支撑"diffusion 路线本身不可行"的结论 |
| 是否直接推翻冻结决策？ | **不**。改为新增路线 C 作为**候选**，与路线 B 并列（主 + 备），不删除路线 B 的既有投入与红线 |
| 最大新增风险是什么？ | diffusion 生成中文字形**不保证笔画正确**（缺笔/多笔/错字），这是路线 B 用真实字体文件天然规避的问题；需要 W0.5 Spike 用真实标题（含生僻字）实测字形准确率后才能决定路线 C 能否进入常规候选池 |
| 处理方式 | 新增 D-CAL-14～19（§3）；新增 §5.5 路线 C 规格；新增 W0.5 技术验证 Spike（§11）；两条路线共用 §6～§8 的配色/定位/数据模型/表面合同骨架 |

---

## 2. 目标 / 非目标

### 2.1 目标（未来 Kickoff 后）

| ID | 目标 |
|----|------|
| **G-CAL-01** | 移植干净管线进 `travelogue/cover_engine/title_art/`，产出透明标题贴纸 |
| **G-CAL-02** | 自动配色（对比度阈值） |
| **G-CAL-03** | 自动定位（自建 `placement_score`；白名单 Opening 内） |
| **G-CAL-04** | 默认路径零用户介入 |
| **G-CAL-05** | 写入独立 `trip.meta.titleArt`；Opening 渲染消费 |
| **G-CAL-06** | 字库授权核查 + 自制/公版印章入库 |
| **G-CAL-07** | 满足 §4 文案合同与 §7 表面合同（改 title 可失效/重生） |
| **G-CAL-08**（v0.3 新增） | 完成 W0.5 技术验证 Spike：固定 prompt 模板对真实标题（含生僻字）的字形准确率、成本、延迟出结论 |
| **G-CAL-09**（v0.3 新增 · Spike 通过后生效） | 路线 C 引擎落地：风格库 Registry（5 款起）+ 抠字重上色管线 + fallback 到路线 B |

### 2.2 非目标

| 不做 | 理由 |
|------|------|
| **开放式 / 自由 prompt 文生图** | 用户自定义措辞不可控，字形/风格漂移风险不可测；本 PRD 仅接受固定模板路线 C |
| brush_effects / engine v3/v4（路线 B） | D-CAL-02 红线 |
| 本阶段工程排期 | D-CAL-08 |
| 默认路径上的手动创作面板 | 零介入；L2 可选见 §10 |
| 标题文案内容生成 | 只消费 `meta.title` |
| 硬等 CAD W1 / 消费 AIR Key | D-CAL-09 / D-CAL-11 |
| V1 进 ECC/Card 封面 | §7；另案 |
| 移植 wanx 印章批次 | D-CAL-12 |
| 把 `arttext-miniapp/` 并进主树运行时 | 仅分析参考；证据已归档 |

### 2.3 成功画像

| 角色 | 成功 |
|------|------|
| **用户** | 无操作即见可读、有笔锋感的封面标题贴纸；改标题后行为可预期 |
| **产品** | 差异化亮点，不与「真照片 / 非假风景」冲突，不与 AIR 抢叙事 |
| **工程师** | 不依赖未落地 CAD API；表面合同可测 |

---

## 3. 冻结决策（D-CAL-*）

| ID | 决策 | 说明 |
|----|------|------|
| **D-CAL-01** | **路线 B = 默认兜底 · 字库合成**（v0.3 收窄适用范围） | 路线 B 内**无**文生图入口、无实验旗标；路线 C 见 D-CAL-14～19，为并列候选，不受本条约束 |
| **D-CAL-02** | **路线 B 干净管线红线**（v0.3 收窄适用范围） | 路线 B 内仅三层合成；合入审查若出现笔锋滤镜 / 骨架引擎路径 → **拒收**；本条**不**约束路线 C 的 diffusion 生成步骤 |
| **D-CAL-03** | **移植 clean 路径** | 复用 demo `brush_renderer.py --no-effects` 与三套模板比例；不移植 v2/v3/v4 engine |
| **D-CAL-04** | **引擎落点** | `travelogue/cover_engine/title_art/`；禁止平行顶层 AI/装饰包 |
| **D-CAL-05** | **默认关 → 默认开**（2026-08-09） | `meta.titleArt.enabled` 曾默认 `false`；盲评 ≥55% 方可默认开。**AC-CAL-BLIND 已通过**（91.7%，单一评委协议）后，产品负责人拍板：`TitleArtConfig.enabled` 默认改为 `true`。**影响范围明确边界**：这只控制 Studio「生成装帧标题」按钮 + Route C 勾选框是否默认展示（`studio_config_expose` → `titleArtCfg.enabled` → 前端 `titleArtBlock.hidden`）；`resolve_title_art` 仍是**用户点击按钮才触发**的单次操作，不是渲染管线自动批量生成，非白名单风格/空标题/字形不覆盖/focal 冲突仍 fail-open 静默回落现网 CSS 标题 |
| **D-CAL-06** | **贴纸非背景** | 永不替换封面实拍主图 |
| **D-CAL-07** | **字库授权门禁** | 未核查字库不得进生产候选池 |
| **D-CAL-08** | **暂停工程排期** | 直至产品显式拉起 §11 启动条件 |
| **D-CAL-09** | **独立数据挂载（BLK-01 · 方案 A）** | `titleArt` 落 `trip.meta.titleArt`；**不**嵌入未落地的 CAD `artDirection`。CAD 落地后可再嵌，非 V1 门禁 |
| **D-CAL-10** | **Opening 白名单（BLK-04）** | 首发仅 **`veil-footer`**；W2 陆续开放 `band-cut`/`contact-stamp`/`folio-overlap`（D-CAL-20，均 ✅ 已开）。其它 styleId（`scroll-head` 等）→ 强制不叠加贴纸，保持现网 HTML 标题 |
| **D-CAL-11** | **与 AIR 解耦（BLK-05）** | 启动窗口名「封面装帧增强」；零 LLM；不进 AIR AC |
| **D-CAL-12** | **印章自制/公版（BLK-05）** | V1 **不**移植 demo wanx 印章批次；自制矢量/扫描公版朱红印 |
| **D-CAL-13** | **自建 placement_score** | 不假设现网存在 `textSafe`/`typeTheme` API；算法见 §6 |
| **D-CAL-14**（v0.3 新增） | **路线 C 仅为候选，非替代** | 路线 C 未通过 W0.5 Spike（§11）前，不进任何默认路径；即便通过 Spike，路线 B 仍作为兜底永久保留，不因路线 C 上线而下线 |
| **D-CAL-15**（v0.3 新增） | **固定提示词模板，禁止开放 prompt** | 路线 C 仅消费风格库 Registry（§5.5.1）中的固定模板；仅允许替换标题/副标文字与色彩占位符；**禁止**运行时拼接用户自由文本进 prompt 主体 |
| **D-CAL-16**（v0.3 新增） | **分层 fallback 强制** | 路线 C 生成失败 / 超时 / 内容审核不过 / 字形 OCR 校验不过 → 必须静默降级路线 B → 路线 B 也失败 → fail-open 现网 HTML；**禁止**在任一环节展示错误态或半成品贴纸（原则 8） |
| **D-CAL-17**（v0.3 新增） | **色彩后处理，不在 prompt 里描述颜色** | 路线 C 固定生成「白底黑字」高对比稿；目标墨色由 §6.1 算法在生成后对笔迹层重新填色决定，默认白色兜底（与路线 B 共用同一配色算法） |
| **D-CAL-18**（v0.3 新增） | **模型优先级** | 技术验证与落地优先测 **阿里云通义万相（DashScope wanx）**；即梦（火山引擎 API，若能申请到）/腾讯混元生图作为陪跑对比；**不采用 DeepSeek**（无成熟商用文生图 API，中文书法准确率未验证） |
| **D-CAL-19**（v0.3 新增） | **字形 OCR 校验门禁** | 路线 C 输出必须过 OCR 回读校验（识别结果与 `mainRendered` 一致）方可判定为「有效贴纸」；未过校验 → 触发 D-CAL-16 fallback，不计入生产可用素材 |
| **D-CAL-21**（v0.6.8 新增） | **路线 C 标题预筛选（Spike 数据驱动，降本增效非安全机制）** | W0.5 完整 Spike（26 条样本）发现含生僻字标题 OCR 通过率显著低于常用字标题（55.6% vs 100%）；`char_frequency.title_has_only_common_chars()` 在真正调用路线 C API 前先判断标题是否只含 GB2312 一级常用汉字（数字/英文/标点不阻断），命中「含生僻字」直接短路到路线 B，省一次注定大概率失败的 15～28s 调用。**不改变 D-CAL-19 的地位**——被本条拦下与"调用了但 OCR 没过"最终展示效果完全等价，都是路线 B；本条只影响调用与否，不是新的安全闸门。对 26 条 Spike 样本回测：允许尝试 17/26，尝试中的通过率由 57.7%（全量）升至 64.7%，**仍未达 AC-CAL-11 的 90% 门槛**，不单独构成"解锁默认开启"的依据，纯粹降本 |
| **D-CAL-22**（v0.6.9 新增） | **Studio 需要真正的一次性生成触发入口，不能只有 CLI** | v0.4.0 落地路线 B/C 引擎与 CLI `title-art` 命令后一直遗留「未完成」项——产品能通过 `meta.coverOpeningStyle` copy-patch 换版式，但没有任何 Studio 按钮能触发 `resolve_title_art` 重算；OQ-CAL-06 结论「路线 C 长期定位用户可选高级项」若无 UI 入口就只是纸面结论，没人能真正碰到。新增 `POST /__travelogue/trips/{tripId}/title-art/resolve`（挂在「封面版式」面板下，一次性生成语义，`force` 默认 `true`）；`routeC` 请求参数须与服务端 `config.title_art.route_c_enabled` 总闸相与，总闸关闭时静默按路线 B 处理（不报错，不依赖前端诚实）；`GET /__travelogue/config` 新增 `titleArt.{enabled,routeCEnabled}` 供前端决定是否展示按钮/勾选框；未知异常按 D-CAL-16 fail-open 原则写回禁用占位并 200 返回，绝不 500 |
| **D-CAL-25**（v0.6.20 新增 · 已落地） | **Typeface Voice Matrix：路线 B 按 Opening 风格调性挑字体，不再全部共用同一款** | 产品复盘发现 4 款白名单风格调性差异明显（`veil-footer` 电影感抒情 / `band-cut` 风景天际线 / `contact-stamp` 纪实档案 / `folio-overlap` 书信对页，见 `catalog.py` 各 `studio_blurb`），但路线 B 此前无差别全用 `pick_default_font()`（`ZhiMangXing`）。**明确边界**：这是**纯编辑决策**，不是可读性判定——D-CAL-24 已证伪"哪款字体更可读"这类算法信号不可靠，本条**不**重蹈覆辙，不引入任何自动化"哪个更好认"的判断。落地：`fonts.py` 新增 `FONT_VOICE_BY_STYLE` 映射（`veil-footer`/`band-cut` → `ZhiMangXing`；`contact-stamp`/`folio-overlap` → `鸿雷板书体`）+ `pick_font_for_style(style_id)`（未命中/未知风格落回 `pick_default_font()`，零回归）；`engine.py::resolve_title_art` 改用 `pick_font_for_style(style_id)` 而非固定默认字体。真实效果核对：同一标题「初中毕业照」在 `band-cut`（`ZhiMangXing`）下"毕"字连笔明显更紧，`contact-stamp`（`鸿雷板书体`）下笔画分离更清楚（[对比图](./acceptance-records/attachments/cover-calligraphy-title-v1-d-cal-24-route-b-legibility-plan-2026-08-09/d-cal-25-typeface-voice-matrix-demo.png)）——巧合印证了 D-CAL-24 §6.4 的推断（鸿雷板书体确实笔画分离度更高），但**不**因此重新定义为可读性机制，仍只是调性搭配。新增测试：`test_title_art_fonts.py`（映射表字体名均在授权池内 + 4 款风格映射断言 + 未知风格回退默认）+ `test_title_art_engine.py`（4 款风格端到端 `resolve_title_art` 产出字体断言）；顺手清理 1 处此前遗留的重复测试函数定义（`test_route_c_risk_digit_mix_skips_api_call`，与本次改动无关的技术债）。回归：`tests/unit/cover_engine/` 230 passed；`tests/unit/render`+`tests/unit/config`+`tests/unit/domain/test_copy_patch.py`+`tests/unit/curation/test_cover_opening.py` 301 passed, 6 skipped；ruff 全绿 |
| **D-CAL-27**（v0.6.26 新增 · 已落地） | **title_art 漏斗埋点：路线 B/C 使用率与失败率可观测** | `titleArt.enabled` 默认开启后，线上完全看不到谁点了生成、走了 B 还是 C、C 是否回退、失败比例——是默认开启后的真实盲区。**历史缺口**：`features.js` 在 D-CAL-22 就写了 `trackStudioEvent("title_art_resolve")`，但前后端白名单（`analytics.js` ALLOWED + `studio_events.py`）都没收录，事件被静默丢弃；且只在成功路径发一次。落地：登记 `title_art_impression`（面板曝光）+ `title_art_resolve`（全 outcome：`success`/`disabled`/`error`/`network`）；meta 含 `engine`/`routeCRequested`/`fallback`/`ocrVerified`/`coverOpeningStyle`，可算入口转化、B/C 使用率、C 回退率、失败率。复用既有 Studio homepage jsonl 通道，不引新存储、不记标题原文。详见[决策记录](./acceptance-records/cover-calligraphy-title-v1-d-cal-27-title-art-telemetry-2026-08-09.md) |
| **D-CAL-26**（v0.6.22 新增，v0.6.23 扩展至全部 10 款 · 已落地，**默认开启**） | **装帧身份线：前封回声（D-SFI-13 扩容）** | 产品复盘 backlog 两条：①三层排版规范化含「印记」层——产品负责人澄清"印记"特指印章/图形，此前已主动决定不做（审美风险太高），本条不涉及；②装帧身份线——复用已有 D-SFI-13 署名三态（`works_brand.py`，默认 `Travelogue`），原仅驱动 `cover-closing__brand`（封底）+ `longshot-boundary-footer__brand`（长图脚）两处，本条扩展为第三处：前封 `cover-opening`。**跨 PRD 边界**：`PRD-SHARE-FACE-INTEGRITY-V1.md` §3.7 原文明确"两处格式统一"，本条扩容为"三处"已经产品负责人确认。**踩坑**：第一轮试点只加文档流元素，`band-cut` 正常但 `veil-footer`/`contact-stamp`/`folio-overlap` 全部飘位——根因这三款风格标题/hook 全用 `position:absolute` 脱离文档流，新元素脱离被搬空的兄弟节点后塌到面板顶部；修复为按风格逐个写绝对定位覆盖，锚点跟随该风格标题/hook 现有坐标。首批 **4 款风格**验证通过并默认开启后，同日又把剩余 **6 款**（`cameo-aperture`/`type-monument`/`scroll-head`/`portal-arch`/`horizon-split`/`diptych-seam`）逐个核对纳入——新发现两类坑：trip 输出目录会缓存陈旧 `journal.css`（改完源文件需显式同步才能验证）；`type-monument`/`horizon-split`/`diptych-seam` 右下角锚点跟阅读器自带的 `screenplay-toolbar`（复制文案/长图按钮）撞位，改为左下角或抬高避让。**10 款风格真实渲染截图验证全部通过**（见[决策记录](./acceptance-records/cover-calligraphy-title-v1-d-cal-26-front-cover-identity-line-2026-08-09.md) §5、§8）。落地：`assemble.py::_COVER_OPENING_BRAND_STYLES`（**现覆盖全部 10 款**）+ `showCoverOpeningBrand` context 字段；`cover-opening.hbs` 面板末尾追加 `.cover-opening__brand`；`journal.css` 基础样式 + 10 款风格各自绝对定位覆盖。`test_cover_opening_identity_line.py`（15 条，覆盖全部 10 款）。顺带发现 `type-monument` 对 7 字长标题渲染会重叠错位，是跟本条无关的既有排版问题，另行记录不在本条处理，**已在 v0.6.25 修复**（见决策记录 §8.6）。回归：`tests/unit/render` 15 passed；ruff 全绿。详见[决策记录](./acceptance-records/cover-calligraphy-title-v1-d-cal-26-front-cover-identity-line-2026-08-09.md) |
| **D-CAL-24**（v0.6.18 提案 → **v0.6.19 已评估关闭，不实现**） | **路线 B 不上自动可读性门禁**（原提案：连通域启发式；已被 Phase 1 数据证伪） | 起因：W3 真实样本（`demo-0ebda73294`「初中毕业照」）人工核对时，"毕"字在默认字库 `ZhiMangXing` 连笔下被肉眼读成"华"。v0.6.18 提出的机制是**纯本地**连通域启发式（明确排除了照搬路线 C `ocr_verify` 的方案，因为那会给路线 B 接入 LLM/网络调用，违反 D-CAL-01/02「零 LLM、任何情况下必须可用」红线——这条边界判断本身保留，仍然成立）。**v0.6.19 Phase 1 用 [验证脚本](../scripts/title_art_d_cal_24_legibility_probe.py) 实测 7 个汉字后证伪该机制**：同句里未被误读的"业"/"照"，`ZhiMangXing` 连通域比值（0.33/0.29）反而**低于**真正被误读的"毕"（0.67）——算法会把没问题的字判定成比有问题的字更危险，信号方向直接排反；根因是草书连笔普遍降低连通域计数，这是字体设计常态而非缺陷特例，拿来当风险探测器噪声远大于信号。**结合更根本的反驳**：原始"证据"来自旁观者脱离上下文逐字拼认，而真实用户读的是自己写的标题，靠词组级整体识别+强先验，孤立单字误读不能外推成真实误读风险——问题本身被高估。**结论：不给路线 B 增加任何自动可读性门禁**；若未来有真实用户反馈看不懂标题，再针对具体字/字体人工判断，不预先建机制。详见 [决策记录](./acceptance-records/cover-calligraphy-title-v1-d-cal-24-route-b-legibility-plan-2026-08-09.md) |
| **D-CAL-23**（v0.6.11 新增） | **贴纸须烧入跟风格呼应的衬底，不能是裸字直贴** | 产品实测反馈（`band-cut` 真机截图）：贴纸此前是纯透明 PNG，直接盖在照片上——但现网每款风格的原生 `<h1>` 从来不是裸字盖在照片上的，都嵌在各自设计好的衬底里（`band-cut` 左对齐纸签渐变面板、`veil-footer` 柔光投影、`contact-stamp` 全幅暗渐罩+说明卡）；纯透明贴纸跳过了这层视觉语言，看起来像"后期贴上去的贴纸"而非"设计里长出来的标题"，且 CSS `max-width/max-height` 用共享近似值（60%/20%）明显宽于 `band-cut`/`contact-stamp` 真实候选矩形，会把贴纸放大到溢出断带线/日戳留白区。**方案（在 `render_b.py` 生成阶段直接烧进 PNG，不改路线 C/不改 placement 定位模型）**：`band-cut` 改主字左对齐 + 烧入左对齐纸签渐变面板（呼应 `--cover-band-paper` 底色 + 向右淡出尾巴 + 柔和投影）；`veil-footer` 烧入柔光垫底（呼应原生 `text-shadow`，色调按主字明暗自适应——深墨主字配暖白柔光、浅色主字配暖黑柔光，保证落在画面任何一块背景上都有保底对比度）；`contact-stamp` 烧入微旋转说明卡片（呼应现网日戳徽标"手工贴卡"语言）；`folio-overlap`（本身坐在纸面栏背景上）与未知风格保持原有纯透明行为，零回归（新增回归测试断言字节级相同）。同时收紧 `journal.css` 里 `band-cut`/`contact-stamp` 的 `max-width/max-height` 贴近真实候选矩形比例，不再沿用共享近似值。三款新增衬底均用真实 trip 素材核对通过（`demo-0ebda73294` band-cut、`demo-3ee2727aea` veil-footer、`demo-1547c68851` 临时切换 contact-stamp 并已还原），Playwright 实测渲染尺寸未溢出候选区（[验收记录](./acceptance-records/cover-calligraphy-title-v1-d-cal-23-backdrop-2026-08-08.md)） |
| **D-CAL-20**（v0.6 新增 · 收窄 D-CAL-13） | **placement 候选须从 Opening Registry `text_safe_regions` 派生，不再自建独立矩形表** | D-CAL-13「不假设现网存在 `textSafe` API」的前提已不成立——`travelogue/cover_engine/registry.py`/`catalog.py` 的 `CoverStyleProfile.text_safe_regions` 已覆盖全部 10 款风格且已被 `opening/title_safe.py::mark_title_safe` 生产使用，与真实渲染坐标高度吻合。W2 落地时：**① `whitelist.py` 的 `PlacementPreset.rect` 改为从对应风格的 `text_safe_regions` 派生而非手搓数值 —— ✅ 已完成（v0.6.1）**；**② 开放 `band-cut`/`contact-stamp` 白名单 —— ✅ 已完成（v0.6.1，真实 trip 视觉核对通过）**；③ 一个风格有多个候选区域时，`placement_score` 须对候选逐一打分择优，而非固定绑死一个矩形 —— ✅ **完成（v0.6.5）**：`whitelist.py` 新增 `placement_presets(style_id)`（主候选+已知安全备选），`engine.py` 淘汰占用/冲突候选后交给 `best_placement` 真正打分；contact-stamp 落地了首个双候选（左块主 + 右下角备选），其余风格暂无第二个已验证安全的候选，行为跟原先单候选等价，不引入随机性；④ 补一层「候选区域是否已被本风格自身文案（hook/trip-meta/archive）占用」的排除校验 —— **结论修正（v0.6.4，OQ-CAL-08）**：这个问题跟 focal 校验是两件事，focal 校验管不了「被自身 UI 占用」；veil-footer 已确认 registry 唯一候选跟自身面板结构性冲突，放弃切换派生，继续用 v0.5 手工收窄矩形，该项就此关闭，不建自动化排除机制——**但 v0.6.5 给 contact-stamp 的备选候选补了这层占用检查**（`PlacementPreset.conditional_occupant` + `engine._contact_stamp_hook_or_archive_present`，复用 `cover_opening.build_cover_archive_strip`），只是范围局限在这一个风格；⑤ 落地前复用 `mark_title_safe` 已算出的 focal 校验信号作为统一闸门 —— ✅ **完成（v0.6.4 focal 安全网 + v0.6.5 多候选切换）**：`focal_conflict()` 对每个候选逐一做焦点碰撞检测，淘汰后仍有候选存活时换到下一个，全部淘汰才整体 fail-open。v0.6.3 开放前排查（[验收记录 §5](./acceptance-records/cover-calligraphy-title-v1-w2-whitelist-expand-2026-08-07.md#5-前瞻审计开放前排查其余风格的-css-暗坑2026-08-07-追加)）发现 `folio-overlap` 两条候选矩形均不能直接套用贴纸流程（候选 #0 被 `__place` 地点标签占用；候选 #1 横跨纸面/骑缝渐变照片两种背景且冲突原生双色断字设计），新增 **OQ-CAL-09**；③ **关闭（v0.6.6）**：深挖发现阻断根因比"选错候选"更底层——`text_safe_regions` 是**照片自身坐标系**里的焦点安全区（`mark_title_safe` 只拿它比对 `asset.focalPoint`），跟 folio-overlap DOM 里"左侧纸面栏根本不显示 `.cover-hero` 照片"这件事完全是两个坐标系，对该风格无论怎么挑候选都绕不开；改为**不再派生**，直接手工写纸面栏矩形（跟 veil-footer OQ-CAL-08 收尾同思路），新增 `PlacementPreset.assume_paper_bg` 告知 §6.1 自动配色改用固定纸色（`--cover-folio-paper` #f4f1ea）而非采样照片，`placement.focal_conflict`/亮度方差/人脸惩罚三项信号对这类候选一并跳过（这些信号对"跟照片无关的固定色块"概念上不成立）；仿照contact-stamp 注册"纸面栏下半段（主候选，不管地点标签是否占用都安全）+ 全高（备选，仅无占用时用，覆盖面更大）"双候选，`best_placement` 新增按面积打破平分的次序（否则两候选 openness 恒同分，`max()` 平分总选第一个，备选形同虚设）；`folio-overlap` 转入 `DEFAULT_ENABLED_STYLES`，真实 trip 视觉核对通过，见 [验收记录 §8](./acceptance-records/cover-calligraphy-title-v1-w2-whitelist-expand-2026-08-07.md#8-oq-cal-09-收尾folio-overlap-纸面栏专门方案)。白名单开放顺序：`band-cut` ✅ → `contact-stamp` ✅ → `folio-overlap` ✅（v0.6.6）→ `veil-footer`（✅ focal 安全网，v0.6.4）→ `scroll-head`（暂缓，待竖排模板能力） |

---

## 4. 标题文案合同（BLK-CAL-02）

| 项 | 规格 |
|----|------|
| **主串来源** | 与封面 DOM 同源：`resolve_display_title(meta)`（写入 `mainSource=displayTitle`，OQ-CAL-10 已关闭）。不再直接渲染 `meta.title` 原文——`<h1>` / `img alt` 早已走展示名（会剥尾部序号等），贴纸若仍用原文会跟可见标题不一致 |
| **最大字数** | 渲染用主串 **≤ 8 个汉字/字符**（按 NFC 规范化后计；空白 trim）。超出 → **截断至 8** 并记 `truncated=true`；若截断后空 → fail-open 不贴纸 |
| **副标** | **可选**。有显式 `meta.titleArtSubtitle`（或未来规则生成的 py/en）则合成；**无则省略**，不强制拼音、不自动瞎译 |
| **字形覆盖** | 渲染前对选定字库做 glyph 存在性检查；任一缺字 → **fail-open 跳过贴纸**，保留现网 HTML 标题（AC-CAL-08） |
| **禁止** | CAL 不改写/润色 `meta.title` 语义（不「青梅→寺里的雨」） |

---

## 5. 渲染管线规格

> §5.1～5.4 为**路线 B**（字库合成，默认兜底，V1 首个可交付路径）；§5.5 为**路线 C**（分层生图，候选，Kickoff 前须通过 W0.5 Spike）。

### 5.1 干净管线（路线 B 唯一路径）

```text
按 §4 解析 main（+ 可选副标）
    → 字形覆盖校验（失败则 abort）
    → 已授权字库池选 1 款
    → 字体直出主字（RGBA）
    → 可选副标层
    → 可选印章层（自制/公版库）
    → 导出 PNG-RGBA
    → 写入 trip-derived + 更新 meta.titleArt
```

**明确不做**：飞白、墨点、随机旋转、骨架盖章、任何笔锋做旧。

### 5.2 版式模板

| 模板 | 定义 |
|------|------|
| `inline_seal` | 主字居中 → 副标+印章同行 |
| `inline_seal_wide` | 同上，副标字距加宽 |
| `seal_corner` | 主字居中 → 印章右上 → 副标下方 |

比例参数沿用 demo（字号抖动、印章约主字高 20%～25%）。

### 5.3 字库候选池

| 字库 | 授权 | V1 |
|------|------|-----|
| `ZhiMangXing-Regular.ttf` | SIL OFL | 生产默认；已随包分发 |
| `鸿雷板书体（简+繁）3.001.ttf` | 作者免费商用（含嵌入式应用） | ✅ 可入池、已随包分发（替换原「测试版」） |
| `Aa剑豪体.ttf` | 通用商用≠嵌入授权 | 核查通过嵌入条款前不得生产默认 / 不随包 |

### 5.4 Opening 白名单与 placement preset（BLK-CAL-04；v0.6 更新见 D-CAL-20）

| `coverOpeningStyle` | V1 状态 | placement preset（v0.6 更新：应对齐 registry `text_safe_regions`） |
|---------------------|-----|-------------------------|
| `veil-footer` | ✅ **白名单 · 首发**；v0.6.4 补齐 focal 安全网 | 矩形 `{x:0.08,y:0.14,w:0.84,h:0.22}`（v0.5 视觉验收后手工收窄，非 registry 派生——registry 唯一候选在雾带底部跟自身面板结构性冲突，见 OQ-CAL-08 结论）；新增 `placement.focal_conflict()`：镜头焦点落在这个矩形内时回退纯 HTML 标题，不再硬贴可能压脸的艺术字 |
| `folio-overlap` | ✅ **白名单 · v0.6.6 收尾开放**（OQ-CAL-09 已关闭） | 手工纸面栏矩形（不再从 `text_safe_regions` 派生——那是照片自身坐标系，跟该风格"纸面栏不显示照片"的 DOM 语义不是同一件事）：主候选 `{x:0.03,y:0.46,w:0.27,h:0.49}`（纸面栏下半段，不管地点标签是否占用顶部都安全）+ 备选 `{x:0.03,y:0.05,w:0.27,h:0.90}`（全高，仅无地点标签占用时用）；均带 `assume_paper_bg=True`（自动配色改用固定纸色 `--cover-folio-paper` #f4f1ea，跳过 focal/亮度/人脸三项照片信号） |
| `band-cut` | ✅ **白名单 · v0.6.1 新开**（真实 trip 视觉核对通过） | registry `{x:0,y:0.60,w:0.55,h:0.14}`，实测与真实断带位置（`--cover-band-center:63%`）精确吻合 |
| `contact-stamp` | ✅ **白名单 · v0.6.1 新开**（临时改风格核对通过，仓内暂无真实样例） | 主候选 registry 左块 `{x:0,y:0.72,w:0.55,h:0.28}`；v0.6.5 新增右下角备选 `{x:0.62,y:0.72,w:0.38,h:0.28}`（`conditional_occupant`：仅当该 trip 无 hook/档案条文案时可用，实测几乎总被占用，触发窗口很窄） |
| `scroll-head` | **非白名单 · 暂缓** | registry 安全区为竖排窄列，与横版画布假设不兼容，待竖排模板能力 |
| 其它（cameo-aperture/type-monument/portal-arch/horizon-split/diptych-seam，均已 retired） | **非白名单** | `titleArt` 不生效；HTML 标题照旧 |

非白名单时即使 `meta.titleArt.enabled=true`，渲染层也**必须**忽略贴纸（防错误叠加）。

### 5.5 路线 C：固定提示词分层生图（v0.3 新增 · 候选，未过 Spike 不启用）

> 目标观感对齐用户提供的即梦参考样本（已归档 `docs/acceptance-records/attachments/cover-calligraphy-title-route-c-refs-2026-08-07/`），但**不**做开放式文生图（D-CAL-15）。

#### 5.5.1 风格库 Registry（Calligraphy Style Registry）

固定表，仅可通过轻量评审（几张样图 + 小样本人审）增补，禁止运行时动态编排：

| 字段 | 说明 |
|------|------|
| `styleId` | 风格唯一 id，如 `cascade-seal` / `flowing-brush` |
| `promptTemplate` | 固定提示词全文，`{{title}}` / `{{subtitle}}` 为唯一可替换变量；**不**含颜色措辞（见 5.5.3） |
| `negativePrompt` | 如模型支持，固定负向词（防止多余装饰元素/背景杂色） |
| `aspectRatio` | 参考样本均为 4:3；需按目标 Opening 落点区域比例校正 |
| `modelProvider` | 见 5.5.4，记录该风格在哪个模型上验证通过 |
| `promptVersion` | 模板版本号，改动需留痕（避免"和上次效果不一样"却无法追溯） |

初始 5 款风格**已定稿**（v0.4.0 · 实现见 `travelogue/cover_engine/title_art/style_registry.py`；文案系参考用户样本原创改写，不照抄参考图内嵌"口令"，见 §9 Prompt 模板版权条款）：

| `styleId` | 参考来源 | 风格描述 |
|---|---|---|
| `cascade-seal` | `ref-01-cascade-seal.png` | 上下错落双行行书，字号大小对比强，收尾拖尾舒展 |
| `flowing-brush` | `ref-02-flowing-brush.png` | 洒脱飘逸行书，运笔顿挫，长笔画飞白毛边明显 |
| `loose-running-script` | `ref-03-loose-running-script.png` | 行楷结合、松弛随性，笔触细腻清晰锐利，干湿质感兼具 |
| `bold-vigorous` | `ref-04-bold-vigorous.png` | 大气刚劲行书，纯黑浓墨，笔画粗细对比强烈，长撇捺舒展 |
| `casual-handwritten` | `ref-05-casual-handwritten.png` | 软头笔随性连笔，生活化随笔手写质感，笔锋边缘清晰 |

五款均固定要求「纯黑墨迹 + 白色/宣纸底 + 无印章/无边框/无其他文字或装饰」——生成阶段统一产出可后处理的白底黑字原图（呼应 D-CAL-17），印章由 §5.5.2 后处理阶段用路线 B 同款自制印章逻辑统一叠加，不让模型自行生成印章（避免颜色/位置不可控，也避免与 D-CAL-12 冲突）。`negativePrompt` 固定包含「印章,图章,红色装饰,边框,多余文字,水印,插画,卡通,人物,风景」。

#### 5.5.2 生成与后处理管线

```text
选定 styleId → promptTemplate 注入 {{title}}（+ 可选 {{subtitle}}）
    → 调用模型 API 生成「固定白底黑字」高对比稿（D-CAL-17：不在 prompt 里指定最终墨色）
    → OCR 回读校验：识别结果 vs mainRendered 是否一致（D-CAL-19）
        → 不一致 → 判定失败 → 走 D-CAL-16 fallback
    → 去背景 + 笔迹二值化 → 得到透明背景笔迹 alpha 层
    → 复用 §6.1 对比度算法，按封面 ROI 选墨色 → 对笔迹层重新填色（默认白色兜底）
    → 印章层：默认维持朱红 #B03A2E（自制/公版，同 D-CAL-12），不参与换色
    → 导出 PNG-RGBA，写入 trip-derived + 更新 meta.titleArt（engine=diffusion-fixed-prompt-v1）
```

任一步骤失败（生成超时/内容审核不过/OCR 校验不过）→ 立即触发 D-CAL-16 分层 fallback，**不重试到用户可感知的等待，也不展示半成品**。

#### 5.5.3 与路线 B 的复用关系

§6（配色/定位算法）、§7（渲染表面合同）、§8（数据模型骨架）、§9（字库/印章条目除外）**均为路线 B / C 共用**，路线 C 只是替换了「主字生成」这一步的引擎实现，不改变下游合同。

#### 5.5.4 模型候选与优先级（D-CAL-18）

| 候选 | 中文文字渲染口碑 | 国内商用 API 可得性 | 结论 |
|------|------|------|------|
| **阿里云通义万相（DashScope wanx）** | 官方主打文字/Logo 生成专项优化 | 有，文档最完善；**用户已有阿里百炼云订阅可直接调用（2026-08-07 现场验证通过）** | **已实现为默认接入路径**（`travelogue/cover_engine/title_art/route_c.py`） |
| **即梦（火山引擎 API）** | 用户参考样本即其产出，效果已验证 | 需确认能否申请到 | 未接入；若可得可作为陪跑对比 |
| **腾讯混元生图** | 中文字符渲染专项优化口碑较好 | 有 | 陪跑对比，非首选，未接入 |
| **DeepSeek（Janus-Pro 等）** | 无成熟商用文生图 API，准确率未验证 | 弱 | **不采用** |

**模型子选型（v0.4.0 · D-CAL-18 更新）**：2026-08-07 用户提供真实 Key 现场实测「拾光」二字——`wanx2.1-t2i-turbo` 出现「光」字形笔画错误；`wanx2.1-t2i-plus` 实测字形正确。据此 `route_c.py` **默认模型定为 `wanx2.1-t2i-plus`**（`turbo` 成本/速度更优但字形风险更高，仅作显式指定时的备选，不作默认）。⚠️ 这只是 2 组标题的现场抽测，v0.6.7 已用 26 条系统性样本补齐（见下）——**结论不变**（plus 仍是默认），但通过率数字远比 2 组抽测时乐观。

**W0.5 完整 Spike 结论（v0.6.7 · 2026-08-08）**：26 条真实/边界标题（覆盖极短/极长、生僻字地名、多音字、数字英文混排、标点、叠字、古诗词句），`wanx2.1-t2i-plus` 生成 100% 成功（无超时/审核拒绝）、延迟均值 18s，但 **OCR 回读通过率仅 57.7%**（常见地名/纯数字 100% 稳定，生僻字/古诗词句/标点/叠字系统性出错，非局部缺笔而是整字被换成不相关字形）。详见 [验收记录](./acceptance-records/cover-calligraphy-title-v1-w05-route-c-spike-2026-08-08.md)。

#### 5.5.5 待验证事项（v0.6.15 更新：W0.5b 冲质量代码已落地，真实 API 矩阵待 Key）

| 事项 | 状态 |
|------|----------|
| 字形准确率（尤其生僻字/多笔画字） | ✅ **已完成完整 Spike**（26 条真实/边界标题，2026-08-08）——OCR 回读通过率 57.7%，**未达 AC-CAL-11 钉定阈值（≥90%）**，判定不通过；`route_c_enabled` 继续默认 `false` |
| 单次生成成本与延迟 | ✅ 已系统统计：延迟均值 18.0s（15.3s～28.3s，P95 19.2s）；成本无 API 计费字段，需人工对照阿里云百炼账单核算单价 |
| 内容审核拒绝率 | ✅ 本批次 26 条实测 0%（样本量有限，非长期统计） |
| 5 款风格的具体 `promptTemplate` 文案定稿 | ✅ 已定稿，见 §5.5.1 与 `style_registry.py`；**v2** 增加逐字准确约束（默认） |
| OCR 回读校验机制 | ✅ 已实现（`ocr_verify.py`，复用 `vision_chat_completion` + `qwen-vl-plus`）；校验通过率阈值（AC-CAL-11）✅ **已钉定为 ≥90%**，本次实测 57.7% 不达标 |
| 标题预筛选（降本，非安全机制） | ✅ **已落地（v0.6.8，D-CAL-21）**：`char_frequency.py` 拦截含表外生僻字的标题，尝试子集通过率 57.7%→64.7%，仍不足以解锁默认开启 |
| OCR 失败重试 / Prompt v2 / 风险规则（W0.5b） | ✅ **代码 + 真实 Spike 已完成（v0.6.15/16）**：`after_retry_rate=90.0%`（30 次尝试，v2+重试1+风险短路），见 [结果](./acceptance-records/cover-calligraphy-title-v1-route-c-w05b-result-2026-08-08.md)。**AC-CAL-11 在该协议下达标**；`route_c_enabled` 默认仍 `false`，仅允许显式高级项开启 |
| 生成内容版权与模型服务条款 | 待核查各候选服务商的商用条款（§9），未完成 |

---

## 6. 自动配色与自动定位

> demo 无此能力；且现网**无** CAD `textSafe`/`typeTheme` 实现 → V1 自建最小算法（D-CAL-13）。**本节算法为路线 B / C 共用**：路线 B 直接决定渲染色；路线 C 在生成后对抠出的笔迹层做同一套换色（§5.5.2 / D-CAL-17）。

### 6.1 自动配色

```text
封面资产 → 落点 ROI 局部亮度
    → 对比度不达标则换色（深/浅字）或半透明底衬
    → 仍不达标 → fail-open 不贴纸（路线 C 同时触发 D-CAL-16 fallback 至路线 B）
默认兜底色：白色（对比度算法找不到更优解时优先回落白色，而非任意深色）
印章默认朱红 #B03A2E；极端底色可降饱和保可读
```

对比度数值阈值 Kickoff 时写入 AC（SHD-CAL-02）；策划阶段要求「可读、可测」。

### 6.2 自动定位（placement_score）

评分信号（V1 最小集）：

1. ROI 平均亮度方差 / 边缘密度（留白代理）
2. 与已检测人脸框 IoU（有脸则惩罚；无检测则跳过该项）
3. 与白名单 Opening 的 **placement preset 矩形** 的中心距离
4. 遮挡「主体显著区」面积比（阈值 35%，与 CAD 精神对齐，**自实现**）

取最高分候选；全员不达标 → fail-open。

**v0.6.1～v0.6.6 更新（D-CAL-20，✅ 已落地）**：`placement preset 矩形`（信号 3）已改为优先从 Cover Style Registry `text_safe_regions` 派生（`whitelist.py`）；多候选风格（`contact-stamp` / `folio-overlap`）由 `placement_score` / `best_placement` 打分择优。veil-footer / folio-overlap 因坐标系或自身 UI 占用冲突改用手工矩形（见 OQ-CAL-08/09）。另落地 `focal_conflict` 与条件占用检查（`conditional_occupant`），避免选图与选位置对同一照片给出矛盾结论。

---

## 7. 渲染表面合同（BLK-CAL-03）

现网事实：`cover-opening.hbs` 用 HTML `<h1 class="cover-opening__title">{{title}}</h1>`；长图 CSS 大量绑定该类；标题可经 patch 修改。

| 项 | V1 合同 |
|----|---------|
| **DOM 策略** | 白名单 Opening 且贴纸有效时：**叠加** `<img class="cover-opening__title-art">` 展示贴纸；原 `h1` 改为 **视觉隐藏 + 保留可访问文本**（sr-only / 等价），保证读屏与 SEO 仍有文字 |
| **非白名单 / 无效贴纸** | 不输出 img；h1 可见行为 ≡ 现网 |
| **Web 预览与长图** | **同一** `assetPath`（trip-derived PNG）；Playwright 截长图吃同一 DOM，禁止长图另渲染一套字 |
| **改 `meta.title` 后** | 将 `titleArt.stale=true`（或清除 `assetPath`）；预览显示回退 HTML 标题或展示「标题已改 · 下次装帧更新」弱提示；**下次**跑 CAL（随「优化装帧」/显式重生）按新 title 生成。禁止静默继续展示旧文案贴纸 |
| **内联编辑** | 编辑中以 HTML 标题为准；提交后走「改 title → stale」同上 |
| **ECC / Card / 小红书卡** | **V1 不进**：Card 封面继续用现有文字排版。覆盖导出卡另案评估 |
| **导出朋友圈/群长图** | 走 HTML 长图路径 → **含**贴纸（同源 asset） |

---

## 8. 数据模型（BLK-CAL-01 · 方案 A）

写入 **`trip.meta.titleArt`**（独立字段，不嵌 `artDirection`）：

```json
{
  "meta": {
    "title": "拾光",
    "titleArt": {
      "version": 1,
      "enabled": false,
      "stale": false,
      "engine": "clean-pipeline-v1",
      "template": "inline_seal_wide",
      "font": "ZhiMangXing-Regular",
      "mainSource": "displayTitle",
      "mainRendered": "拾光",
      "truncated": false,
      "subtitle": null,
      "mainColor": "#1a1a1a",
      "sealColor": "#B03A2E",
      "openingStyleId": "veil-footer",
      "position": { "x": 0.5, "y": 0.28 },
      "assetPath": "trip-derived/title-art/xxx.png",
      "sourceTitle": "拾光",
      "explain": ["veil-footer 白名单 · 上区留白足"]
    }
  }
}
```

**v0.3 新增字段**（`engine` 取值为 `diffusion-fixed-prompt-v1` 时适用；路线 B 下这些字段为 `null`/省略）：

```json
{
  "engine": "diffusion-fixed-prompt-v1",
  "styleId": "flowing-brush",
  "promptVersion": "v1",
  "modelProvider": "wanxiang",
  "ocrVerified": true,
  "fallbackFrom": null
}
```

| 字段 | 说明 |
|------|------|
| `styleId` | 命中的风格库条目（§5.5.1） |
| `promptVersion` | 使用的模板版本，便于追溯效果变化 |
| `modelProvider` | 实际调用的模型服务商（如 `wanxiang` / `jimeng` / `hunyuan`） |
| `ocrVerified` | 字形 OCR 回读校验结果（D-CAL-19）；`false` 时该资产不应被判定为有效贴纸 |
| `fallbackFrom` | 若本次实际展示的是路线 B/HTML 兜底结果，记录"原本尝试过路线 C 但降级"，用于观测降级率 |

| 条件 | 行为 |
|------|------|
| 无字段 / `enabled=false` / `stale=true` / 非白名单 style | ≡ 现网 HTML/CSS 标题 |
| 路线 C 生成失败（超时/审核不过/`ocrVerified=false`） | 按 D-CAL-16 降级路线 B；`fallbackFrom` 记录降级来源 |
| CAD 未来落地 | 可将本对象**复制或引用**进 `artDirection.opening.titleArt`；迁移另笔，不挡 CAL W1 |

---

## 9. 素材权利与合规

| 项 | 要求 |
|----|------|
| 字库 | 商用授权核查留痕（`LICENSE-NOTES.md` 或等价） |
| 印章 | **V1 自制或公版**（D-CAL-12）；禁止默认入库 wanx 批次 |
| 追溯 | manifest / 拒收清单可查 |
| demo 仓 | `arttext-miniapp/` 仅分析参考；Kickoff 前建议移出主仓或 gitignore（SHD-CAL-04） |
| **路线 C · 模型服务条款**（v0.3 新增） | 核查通义万相/即梦/混元的**生成内容商用授权条款**（生成图是否可商用、是否需标注 AI 生成）；未核查清楚不得作为生产候选 |
| **路线 C · 内容安全审核**（v0.3 新增） | API 侧通常自带内容审核；需记录拒绝率与拒绝原因分类，纳入 D-CAL-16 fallback 观测 |
| **路线 C · Prompt 模板版权**（v0.3 新增） | 风格库固定模板本身视为产品资产，不直接照抄第三方案例文案；参考样本仅用于风格归纳，定稿模板需原创改写 |
| **路线 C · 参考样本归档**（v0.3 新增） | 用户提供样本已存档 `docs/acceptance-records/attachments/cover-calligraphy-title-route-c-refs-2026-08-07/`；仅作风格参考，不进生产资产 |

---

## 10. Studio 体验（目标态）

| 元素 | 规格 |
|------|------|
| **默认路径** | 随「优化装帧」或等价一键触发；**零额外开关、零必点按钮** |
| **结果** | 直接反映在封面预览 |
| **L2 高级（可选 · SHD-03）** | 折叠区：「换版式」「换印章」；**非默认露出**；不提供手动画字/调笔锋 |
| **归因** | 「使用你的照片装帧 · 未生成风景」+ 按实际引擎区分文案：路线 B 展示时用「标题为**程序化字库合成**，非 AI 绘图」；**路线 C 展示时须改为**「标题字迹由 AI 书法风格生成」（v0.3 新增，不得沿用路线 B 文案掩盖生成事实）。**v0.6.13 已落地**：Studio 面板常驻归因行 + 封面封底 / 长图页脚（`titleArtAttribution`，按 `titleArt.engine` 分派）。若未来印章来源变更，须单独注明，不得混称「全非 AI」而掩盖生成素材 |

---

## 11. 里程碑

| 里程碑 | 交付 | 门禁 |
|--------|------|------|
| **W0** | PRD v0.2 + 七席 BLK 关闭；v0.3 新增路线 C 候选设计 | ✅ |
| **W0.5**（不占用工程排期，先于启动触发） | 路线 C 技术验证 Spike：通义万相为主，即梦（若可申请）/腾讯混元陪跑；用 20～30 个真实/边界标题（含生僻字）测字形准确率（OCR/人审）+ 成本 + 延迟 + 审核拒绝率 | ✅ **已完整完成（v0.6.7，2026-08-08）**：26 条真实/边界标题系统性验证，`wanx2.1-t2i-plus` 生成 100% 成功、延迟均值 18s，**OCR 回读通过率 57.7%**——未达 AC-CAL-11 钉定阈值（≥90%），**判定不通过**；`route_c_enabled` 配置默认继续为 `false`；即梦/腾讯混元陪跑对比因未接入，未纳入本次 Spike（见 [验收记录](./acceptance-records/cover-calligraphy-title-v1-w05-route-c-spike-2026-08-08.md)） |
| **启动触发** | 产品显式拉起 **「封面装帧增强」** 窗口 | ✅ **2026-08-07 已拉起**（本次对话）；不绑定 AIR |
| **W1**（**Kickoff · 开发中**，分支 `feat/cover-calligraphy-title-v1`） | `cover_engine/title_art/` 干净管线（路线 B）+ 授权字库 + 自制/公版印章；固定配色/位；`meta.titleArt`；仅 `veil-footer`；路线 C 引擎 + 风格库 Registry（初始 5 款）同步实现（因 W0.5 未完整完成，`route_c_enabled` 默认关闭，代码路径已具备） | ✅ 代码已落地：`travelogue/cover_engine/title_art/` 全模块 + CLI `title-art` + 渲染表面 §7 接入 + 83 条单测；✅ AC-CAL-03/07/08/09/12 已用真实素材人工核对（见 [W1 视觉验收](./acceptance-records/cover-calligraphy-title-v1-w1-visual-review-2026-08-07.md)，过程中发现并修复 3 处集成缺口）；❌ AC-CAL-11 已跑完整 W0.5 Spike，判定不通过（57.7% < 90%），`route_c_enabled` 维持默认 `false` |
| **W2** | placement_score + 自动配色（路线 B/C 共用，已随 W1 一并落地）；`enabled` 默认 false；按 D-CAL-20 顺序开放白名单：✅ ① `whitelist.py` 改为从 `text_safe_regions` 派生 preset（不再手搓矩形，v0.6.1）✅ ② 开 `band-cut`（v0.6.1）✅ ③ 开 `contact-stamp`（v0.6.1）✅ ④ 开 `folio-overlap` —— 开放前排查（v0.6.3）发现两条候选矩形均不能直接套用（OQ-CAL-09），v0.6.6 找到根因（照片坐标系 vs DOM 语义不是同一件事）并用手工纸面栏矩形 + `assume_paper_bg` 专门方案收尾开放 ✅ ⑤ 修复 `veil-footer` 已知矩形风险（v0.6.4，新增 `focal_conflict` 安全网，OQ-CAL-08 结论修正并关闭）；`scroll-head` 暂缓；✅ 额外落地 D-CAL-20 多候选打分择优（v0.6.5，contact-stamp 首个双候选；v0.6.6 补 `best_placement` 按面积打破平分次序 + folio-overlap 双候选） | AC-CAL-01～06、09、13——✅ **全部已补齐验收记录**；band-cut/contact-stamp/folio-overlap 视觉核对 + veil-footer focal 安全网 + 多候选打分见 [W2 验收记录](./acceptance-records/cover-calligraphy-title-v1-w2-whitelist-expand-2026-08-07.md)；AC-CAL-04/05/06/13 见 [专项验收记录](./acceptance-records/cover-calligraphy-title-v1-ac04-05-06-13-2026-08-08.md)；AC-CAL-01/02/10 见 [专项验收记录](./acceptance-records/cover-calligraphy-title-v1-ac01-02-10-2026-08-08.md)（v0.6.13 正式钉死，修正此前「口头已补齐」） |
| **W3** | 盲评：现网 CSS Opening 标题 vs `titleArt=on`（含路线 B/C 分别对比）≥55% | AC-CAL-BLIND · **✅ 已通过**（单一代表性评委协议，2026-08-09；[方案](./acceptance-records/cover-calligraphy-title-v1-w3-blind-plan-2026-08-08.md) · [进度/结论](./acceptance-records/cover-calligraphy-title-v1-w3-blind-2026-08-08.md#5-结论单一评委协议--2026-08-09)）；路线 B 12 对，艺术字侧胜率 91.7%（11/12），四款白名单风格均 ≥55%；路线 C 本轮延期；`enabled` 默认是否改为 `true` 另行决定，见 D-CAL-05 |

---

## 12. 风险 · OQ · 验收

### 12.1 风险

| 风险 | 缓解 |
|------|------|
| 即梦预期 | 定位「画龙点睛」+ 证据四图 |
| 授权拖期 | D-CAL-07 前置 W1 |
| 缺字 / 超长 title | §4 截断 + fail-open |
| 配色失败 | fail-open |
| 重投特效 | D-CAL-02 红线 + 证据附录 |
| 改 title 贴纸不同步 | §7 stale 合同 |
| 非白名单硬贴 | D-CAL-10 渲染层强制忽略 |
| **路线 C：diffusion 字形错误**（缺笔/多笔/错字，v0.3 新增） | D-CAL-19 OCR 回读校验 + D-CAL-16 强制降级路线 B，不允许错字上线 |
| **路线 C：API 成本/延迟波动**（v0.3 新增） | 路线 B 永久兜底（原则 8）；生成结果落 `trip-derived` 缓存复用，不重复调用 |
| **路线 C：内容审核拒绝**（v0.3 新增） | D-CAL-16 fallback 链路；记录拒绝率用于 W0.5 结论 |
| **路线 C：归因文案与实际引擎不符**（v0.3 新增） | §10 按 `engine` 字段区分归因文案，禁止路线 C 沿用「非 AI 绘图」措辞 |

### 12.2 开放问题（OQ-CAL-*）

| ID | 问题 | 状态 / 倾向 |
|----|------|-------------|
| **OQ-CAL-01** | mobile / 竖版独立版式？ | **收窄关闭**：V1 仅白名单 web Opening preset；mobile 延期 |
| **OQ-CAL-02** | 扩到章标题/长图分段？ | **维持否**：仅封面 Opening |
| **OQ-CAL-03** | 印章自制？ | **已关闭**：V1 自制/公版（D-CAL-12） |
| **OQ-CAL-04** | 远期文生图？ | **v0.3 收窄关闭并部分回收**：不做开放式文生图（维持否）；但**受限的固定提示词文生图**已作为路线 C 候选纳入本 PRD §5.5，不再另立 PRD |
| **OQ-CAL-05** | ECC/Card 是否二期消费贴纸？ | 默认倾向：二期可选；不挡 V1（路线 B/C 均适用） |
| **OQ-CAL-06**（v0.3 新增，v0.6.7 结论钉定） | 路线 C 何时从「候选」升级为「默认主路径」？ | **结论（v0.6.7）**：W0.5 完整 Spike 实测 OCR 通过率仅 57.7%，远未达 AC-CAL-11 阈值（≥90%），**明确不升级**；且鉴于扩散模型生成结果本身非确定性（同标题不同次采样可能不同），不认为未来某次小样本达标就能一次性判定"通过"——长期定位为**用户可选的高级项**（需产品/运营显式开关 + 建议 UI 上告知有概率静默回退默认样式），不追加 W3 盲评作为升级前提（W0.5 数据已经足够下结论） |
| **OQ-CAL-07** | 路线 C 的 5 款风格 `promptTemplate` 具体文案何时定稿？ | ✅ **已关闭（v0.4.0）**：5 款已定稿，见 §5.5.1 与 `style_registry.py`。**W0.5 完整 Spike 已于 v0.6.7 补齐**（26 条真实/边界标题，OCR 通过率 57.7%，未达标）——问题本身已解决，见 [验收记录](./acceptance-records/cover-calligraphy-title-v1-w05-route-c-spike-2026-08-08.md)；`route_c_enabled` 保持默认 `false` |
| **OQ-CAL-08**（v0.6 新增，v0.6.4 结论修正并关闭） | `whitelist.py` 改为从 `text_safe_regions` 派生后，是否需要保留一份「CAL 专属排除子区域」标注（用于扣除被 hook/trip-meta/archive 占用的部分），还是直接靠 `mark_title_safe` 的 focal 校验兜底即可？ | **结论修正（v0.6.4）**：原倾向"先接 focal 校验"的前提有误——`mark_title_safe`/focal 校验解决的是「镜头主体是否落在候选区」，跟"候选区本身有没有被本风格自身 UI 元素（面板/文案）占用"是两个完全不同的问题，focal 校验解决不了后者。已确认 veil-footer registry 唯一候选（雾带底部）跟自身面板 DOM 占位**结构性冲突**，不打算再尝试切换派生——v0.5 视觉验收后改用的手工收窄矩形（雾带上方）继续作为该风格的既定候选区，不再是"临时占位待替换"。真正落地的是 focal 校验能解决的那一半问题：新增 `placement.focal_conflict()`，检查镜头焦点是否落在**实际使用的候选框**内（不是 registry 原始候选），命中时回退纯 HTML 标题而非硬贴可能压脸的艺术字，见 [验收记录](./acceptance-records/cover-calligraphy-title-v1-w2-whitelist-expand-2026-08-07.md#6-veil-footer-已知矩形风险修复d-cal-20-优先顺位④--oq-cal-08)。「候选区是否被自身 UI 占用」这个更难的问题目前只能靠人工设计矩形时主动避让（如本次 veil-footer 的做法），暂不建立自动化排除机制——留给 D-CAL-20 优先顺位⑤ 多候选打分落地时一并考虑 |
| **OQ-CAL-09**（v0.6.3 新增，v0.6.6 关闭） | `folio-overlap` 如何安全开放？候选 #0（左纸列）被 `.cover-opening__place` 地点标签常驻占用；候选 #1（此前拟用矩形）横跨纸面纯色栏 / 骑缝渐变照片区两种背景，且原生 `<h1>` 用双色 `clip-path` 叠字实现"书名骑缝切开压进画面"效果，单色贴纸做不出来 | **结论（v0.6.6）**：根因比"选错候选"更底层——`text_safe_regions` 是照片自身坐标系里的焦点安全区，folio-overlap 左侧纸面栏根本不显示照片，两个坐标系对不上，无论怎么挑候选都跳不出这个坑；不再尝试派生，改用手工矩形直接描述 DOM 语义（跟 veil-footer OQ-CAL-08 同思路），新增 `assume_paper_bg` 让自动配色/`focal_conflict`/亮度方差/人脸惩罚都改走"这是固定纸色，不是照片"的路径；仿 D-CAL-20 优先顺位⑤机制注册纸面栏下半段（主候选）+ 全高（备选，视地点标签占用情况切换）双候选，真实 trip 两种场景视觉核对通过，见 [W2 验收记录 §8](./acceptance-records/cover-calligraphy-title-v1-w2-whitelist-expand-2026-08-07.md#8-oq-cal-09-收尾folio-overlap-纸面栏专门方案) |
| **OQ-CAL-10**（v0.6.10 新增，v0.6.13 关闭） | 艺术字贴纸与原生 `<h1>`/`alt` 标题字段不一致 | **✅ 已关闭（v0.6.13）**：贴纸主串改走 `resolve_display_title(meta)`（`mainSource=displayTitle`），与封面 DOM 同源；`title`/`displayTitle` 皆空仍 fail-open，不消费地点兜底文案。见 §4 与 `contract.py` |
| **OQ-CAL-11**（v0.6.18 新增，**v0.6.19 关闭**） | D-CAL-24 拟用 `鸿雷板书体（简+繁）3.001` 作为「可读性备胎」——但两款字体都是连笔手写体，鸿雷是否天然笔画分离度更高、真的比 `ZhiMangXing` 更易读，目前只是假设，未经真人核对 | **✅ 已关闭（v0.6.19，随 D-CAL-24 一并关闭）**：判定"是否更易读"依赖的正是被证伪的连通域机制，机制本身不可用 → 这个问题在没有可靠判定手段的前提下**不再需要回答**，也不建备用字重切换机制。两款字体本身仍都留在 `FONT_POOL`，只是不接自动切换逻辑 |

### 12.3 验收（AC-CAL-*，Kickoff 后生效）

| ID | 断言 |
|----|------|
| **AC-CAL-01** ✅ | `enabled=false`（或无字段）时 Opening ≡ 现网 HTML/CSS 金样（[验收记录](./acceptance-records/cover-calligraphy-title-v1-ac01-02-10-2026-08-08.md)） |
| **AC-CAL-02** ✅ | 干净管线输出对照证据②；固定 fixture + 感知哈希容差（SHD-CAL-01 已落地，Hamming 0 ≤ 16） |
| **AC-CAL-03** ✅ | 代码审查：无 brush_effects / engine v3/v4 生产路径（[核对记录](./acceptance-records/cover-calligraphy-title-v1-w1-visual-review-2026-08-07.md)） |
| **AC-CAL-04** ✅ | 测试集封面上对比度达书面阈值（W2 钉数）（14 条真实 trip 封面照片实测 32/32 达标，`MIN_CONTRAST_RATIO=3.0` 确认定稿，见[验收记录](./acceptance-records/cover-calligraphy-title-v1-ac04-05-06-13-2026-08-08.md)） |
| **AC-CAL-05** ✅ | placement 遮挡主体显著区 ≤35%（自测口径）（4 款白名单风格全部候选矩形面积占比 7.7%~24.3%，均达标；14 条真实照片跑 `score_candidate` 0 例违规） |
| **AC-CAL-06** ✅ | 默认路径无用户参数即可完成生成与叠加（真实 trip 零参数 CLI `title-art` → Studio 渲染路径 → 浏览器实测叠加生效，见验收记录） |
| **AC-CAL-07** ✅ | 生产字库/印章均有授权或公版溯源记录（核对时发现 `ZhiMangXing-Regular.ttf` 未随包分发导致生产环境不可加载，已修复 + 补 `LICENSE-NOTES.md`，见验收记录 §1.1） |
| **AC-CAL-08** ✅ | 缺字形或非白名单 style → 不叠加贴纸且 h1 可见正常（真实非白名单 trip 实测通过） |
| **AC-CAL-09** ✅ | 修改 `meta.title` 后 `stale`（或等价）生效，禁止继续展示旧文案贴纸为「已更新」（核对时发现 `mark_title_art_stale` 从未接线，`copy_patch.py` 改标题不会置 stale——已修复 + 端到端验证 + 3 条回归测试，见验收记录 §1.3） |
| **AC-CAL-10** ✅ | Web 预览与长图引用同一 `assetPath`（真实 trip `index.html` / `index-longshot.html` 同源核对通过） |
| **AC-CAL-11**（v0.3 新增 · 路线 C 生效） ✅（v0.6.16 · W0.5b 协议） | 阈值 ≥90%。W0.5 裸跑全量单次仅 57.7%（❌）。**W0.5b**（Prompt v2 + 生僻字/标点/叠字短路 + OCR 失败重试 1 次）尝试子集 **30** 次采样：`after_retry_rate=90.0%` → **达标**（见 [结果](./acceptance-records/cover-calligraphy-title-v1-route-c-w05b-result-2026-08-08.md)）。**不**因此改 `route_c_enabled` 默认值（OQ-CAL-06）；仅允许配置层显式开启高级项 |
| **AC-CAL-12** ✅（v0.3 新增 · 路线 C 生效） | 路线 C 失败（超时/审核不过/OCR 不过）→ 必定按 D-CAL-16 降级路线 B 或 fail-open HTML，**不允许**任何情况下展示错误态或半成品贴纸（真实条件下——未设置 `DASHSCOPE_API_KEY`——强制路线 C 实测通过） |
| **AC-CAL-13**（v0.3 新增 · 路线 C 生效） ✅ | 路线 C 抠字重上色结果同样满足 §6.1 对比度合同，默认兜底白色路径可复现（复用 W0.5 Spike 真实产出图核对，6/6 达标 + 3 组中性灰边界场景核对回落白色分支，见验收记录） |
| **AC-CAL-BLIND** ✅（2026-08-09 · 单一评委协议） | vs **现网 CSS Opening 标题**（非 CAD Mode A）偏好 ≥55% 才可默认 `enabled=true`（路线 B/C 分别计）。**已通过**：艺术字侧胜率 **91.7%（11/12）**；分风格 `band-cut` 100% / `veil-footer` 75% / `contact-stamp` 100% / `folio-overlap` 100%，均 ≥55%（[方案](./acceptance-records/cover-calligraphy-title-v1-w3-blind-plan-2026-08-08.md) · [结论](./acceptance-records/cover-calligraphy-title-v1-w3-blind-2026-08-08.md#5-结论单一评委协议--2026-08-09)）。**如实标注**：本次评审是产品负责人主动放宽后的简化协议（n=1 · 评委即产品负责人），非原方案 ≥5 人独立评审；**通过只解除 D-CAL-05 的阻塞条件，不自动改默认值** |

---

## 13. 附录：demo 证据与移植指针

### 13.1 路线 B · demo 证据（2026-08-06）

| 编号 | 说明 | 归档路径 |
|------|------|----------|
| ① | 字库网格 | `.../01-font-grid-comparison.png` |
| ② | 干净合成基准 | `.../02-clean-composite-sample.png` |
| ③ | 特效降质 | `.../03-brushed-effect-degraded-sample.png` |
| ④ | 引擎降质 | `.../04-stroke-engine-v4-degraded-sample.png` |

移植时只取：

- `arttext-miniapp/tools/brush_renderer.py` 的 **`--no-effects`** 路径与模板常量
- 已授权字库文件（核查后）
- **不**取：`brush_engine_v*`、`brush_effects` 生产调用、wanx 印章 `_approved` 批次

### 13.2 路线 C · 风格参考样本（v0.3 新增 · 2026-08-07）

用户提供的即梦产出样本，用于归纳 §5.5.1 初始 5 款风格；归档路径：`docs/acceptance-records/attachments/cover-calligraphy-title-route-c-refs-2026-08-07/`

| 编号 | 对应 `styleId`（占位） | 文件 |
|------|------|------|
| ref-01 | `cascade-seal` | `ref-01-cascade-seal.png` |
| ref-02 | `flowing-brush` | `ref-02-flowing-brush.png` |
| ref-03 | `loose-running-script` | `ref-03-loose-running-script.png` |
| ref-04 | `bold-vigorous` | `ref-04-bold-vigorous.png` |
| ref-05 | `casual-handwritten` | `ref-05-casual-handwritten.png` |

**仅作风格归纳参考，不直接进生产 prompt 文案**（§9 · Prompt 模板版权）；若用户补充更多样本，追加归档到同一目录并在此表补录。

---

## 修订记录

| 版本 | 日期 | 说明 |
|------|------|------|
| **v0.1.0** | 2026-08-06 | 初稿：字库合成 · 干净管线 · 暂停排期 |
| **v0.2.0** | 2026-08-06 | 七席回写 BLK-CAL-01～05：独立 `meta.titleArt` · 文案/表面合同 · V6 白名单 · 与 AIR 解耦 · 印章自制/公版 · placement_score · D-CAL-09～13 · AC-08～10 |
| **v0.3.0** | 2026-08-07 | 产品复议：新增**路线 C（固定提示词分层生图）**为候选（与路线 B 主+备，非替代）；新增 D-CAL-14～19；新增 §5.5 路线 C 规格（风格库 Registry、抠字重上色管线、模型优先级=通义万相优先）；新增 W0.5 技术验证 Spike 里程碑；数据模型新增 `styleId`/`modelProvider`/`promptVersion`/`ocrVerified`/`fallbackFrom`；新增 AC-11～13、OQ-06～07、P-CAL-07；§9/§10/§13 补充路线 C 合规与归因文案条目；归档路线 C 参考样本 `cover-calligraphy-title-route-c-refs-2026-08-07/` |
| **v0.4.0** | 2026-08-07 | **Kickoff**：产品拉起「封面装帧增强」窗口，分支 `feat/cover-calligraphy-title-v1` 落地路线 B + 路线 C 全模块（`travelogue/cover_engine/title_art/`）、CLI `title-art`、渲染表面 §7 接入、`AppConfig.title_art` 配置（默认关闭）、83 条单测；§5.5.1 五款风格 `promptTemplate` 定稿（关闭 OQ-CAL-07）；D-CAL-18 模型选型更新为 `wanx2.1-t2i-plus`（现场实测优于 turbo，但**非**完整 W0.5 Spike，`route_c_enabled` 保持默认 `false`）；真实 demo trip 人工核对路线 B 全链路可用 |
| **v0.5.0** | 2026-08-07 | **W1 真实素材视觉验收**（[记录](./acceptance-records/cover-calligraphy-title-v1-w1-visual-review-2026-08-07.md)）：用真实 trip 跑通 AC-CAL-03/07/08/09/12，发现并修复 3 处 83 条单测未捕获的真实集成缺口——① 字库资产未随包分发致生产环境静默退化成微软雅黑（补 `assets/fonts/` + `LICENSE-NOTES.md`）；② 艺术字贴纸误嵌雾带文案面板致与 hook 文案重叠 + §6.2 定位坐标从未接进渲染上下文（死代码）+ 出稿未裁剪致居中锚点对不上可见字形（三处一并修）；③ `mark_title_art_stale` 从未被 `copy_patch.py` 调用致改标题不触发 stale（AC-CAL-09 实测不通过，已接线）。AC-CAL-03/07/08/09/12 转为 ✅；AC-CAL-11 仍待完整 W0.5 Spike |
| **v0.6.0** | 2026-08-07 | **§6.2 定位策略复核**（讨论向，本版未改代码）：复核 Opening Registry 发现 `CoverStyleProfile.text_safe_regions` 已覆盖全部 10 款风格且已被 `title_safe.py::mark_title_safe` 生产使用，与真实渲染坐标高度吻合——收窄 D-CAL-13 并新增 **D-CAL-20**：placement 候选须从 `text_safe_regions` 派生而非自建独立矩形表；多候选须真正打分择优；补文案占位排除校验；复用 `mark_title_safe` 信号做统一闸门。逐风格结论：`veil-footer` 现矩形与 `focal_y_max:0.55` 冲突待修；`folio-overlap` 应对齐 registry 候选；`band-cut`/`contact-stamp` registry 矩形与真实渲染坐标精确吻合，评估为 W2 优先开放对象；`scroll-head` 竖排版式与现有横版画布不兼容，暂缓。更新 §5.4/§6.2/§11 W2 里程碑；新增 OQ-CAL-08 |
| **v0.6.1** | 2026-08-07 | **落地 D-CAL-20 优先顺位①②**（[验收记录](./acceptance-records/cover-calligraphy-title-v1-w2-whitelist-expand-2026-08-07.md)）：`whitelist.py` 改为从 `text_safe_regions` 派生矩形（不再手搓数值）；新开放 `band-cut`/`contact-stamp` 白名单；真实 trip（`demo-0ebda73294`）跑通视觉核对，`contact-stamp` 因仓内无真实样例改用临时改风格核对（未提交）。过程中发现并修复 1 处集成缺口：`journal.css` 存在独立于 `whitelist.py` 的 CSS 侧白名单（`display:none` 默认，仅 `veil-footer` 一行覆盖），新风格加入后未同步导致贴纸 DOM 正确但不可见——已补 `band-cut`/`contact-stamp` 两行选择器。`veil-footer` 现有矩形（优先顺位④）与 `folio-overlap` 默认开启（优先顺位③）本版未处理。新增/更新 `test_title_art_whitelist.py`；`tests/unit/cover_engine/` 129 passed；ruff 全绿 |
| **v0.6.2** | 2026-08-07 | **contact-stamp 深色渐罩配色修复**（用户实测反馈发现，[验收记录 §1.3](./acceptance-records/cover-calligraphy-title-v1-w2-whitelist-expand-2026-08-07.md)）：`contact-stamp` 的全幅深色渐罩（`journal.css` `::after`）与照片内容无关，但 §6.1 自动配色采样的是渐罩叠加前的原始照片，误判够亮选了深墨，实际渲染读不出来。`PlacementPreset` 新增 `assume_dark_veil` 字段，`engine.py` 命中时改用近黑背景估计强制回落白色；同一真实照片验证 `mainColor` 由深色变白色，视觉核对清晰可辨。新增 2 条回归测试；`tests/unit/cover_engine/` 134 passed；ruff 全绿 |
| **v0.6.3** | 2026-08-07 | **开放前 CSS 暗坑排查**（[验收记录 §5](./acceptance-records/cover-calligraphy-title-v1-w2-whitelist-expand-2026-08-07.md#5-前瞻审计开放前排查其余风格的-css-暗坑2026-08-07-追加)）：呼应 v0.6.2 contact-stamp 那次教训，逐一排查 `veil-footer`/`band-cut`/`contact-stamp`/`folio-overlap` 4 款已注册风格是否还有类似「实际渐罩/filter 让渲染结果跟原始照片采样不一致」或「候选矩形跟既有 DOM 元素冲突」的坑。结论：`veil-footer`/`band-cut` 共用的低不透明度暖色渐罩绘制顺序在贴纸之下，非阻断；`contact-stamp` 已在 v0.6.2 修复。**新发现**：`folio-overlap` 两条 `text_safe_regions` 均不能直接套用「派生矩形+翻开关」流程——候选 #0 被 `.cover-opening__place` 地点标签常驻占用；候选 #1 横跨纸面纯色栏与骑缝渐变照片区两种背景，且冲突原生 `<h1>` 用双色 `clip-path` 叠字实现的「书名骑缝切开压进画面」设计语言，单色贴纸做不出来。新增 **OQ-CAL-09**；`whitelist.py` 补充详细 TODO 注释但**不改** rect 数值与默认关闭状态；仅新增代码注释，`tests/unit/cover_engine/` 134 passed 不变 |
| **v0.6.4** | 2026-08-07 | **落地 D-CAL-20 优先顺位④，修正并关闭 OQ-CAL-08**（[验收记录 §6](./acceptance-records/cover-calligraphy-title-v1-w2-whitelist-expand-2026-08-07.md#6-veil-footer-已知矩形风险修复d-cal-20-优先顺位④--oq-cal-08)）：重新审视发现 OQ-CAL-08 原倾向"接 focal 校验即可安全切回 registry 派生"的前提有误——focal 校验只能判断镜头主体是否落在候选区，管不了候选区本身有没有被本风格自身面板/文案占用；veil-footer registry 唯一候选（雾带底部）跟自身面板 DOM 占位是结构性冲突，不再尝试切换派生，v0.5 手工收窄的雾带上方矩形转为既定候选区。真正落地的是 focal 校验能解决的那一半：新增 `placement.focal_conflict()`，检查镜头焦点是否落在**实际使用的候选框**内，命中时回退纯 HTML 标题（`disabled_meta_dict` 新增可选 `reason` 字段留痕）而非硬贴可能压脸的贴纸。新增 7 条测试（`focal_conflict` 4 条 + engine fail-open/正常路径各 1 条 + `disabled_meta_dict(reason=...)` 1 条）；`tests/unit/cover_engine/` 141 passed；ruff 全绿 |
| **v0.6.5** | 2026-08-07 | **落地 D-CAL-20 优先顺位⑤：多候选打分择优**（[验收记录 §7](./acceptance-records/cover-calligraphy-title-v1-w2-whitelist-expand-2026-08-07.md#7-落地-d-cal-20-优先顺位⑤多候选打分择优)）：`whitelist.py` 新增 `PlacementPreset.conditional_occupant` 字段 + `FALLBACK_PRESETS` + `placement_presets(style_id)`（主候选+已知安全备选，主候选永远在前）；`placement.PlacementCandidate` 新增 `preset` 字段，让调用方知道具体是哪个候选赢了打分。`engine.py` 接线两层淘汰（条件占用检查 → focal 冲突检查）后把剩余候选交给 `best_placement` 真正打分，全部淘汰才整体 fail-open。contact-stamp 落地首个双候选：右下角备选（`conditional_occupant="contact_stamp_hook_or_archive"`），仅当该 trip 没有 hook 且没有档案条文案时才安全——占用检查复用从 `assemble.py` 抽出的 `render.cover_opening.build_cover_archive_strip()`（避免"两处各自维护一份数据"重演）。**实测发现**：`format_trip_meta` 的天数兜底文案（"N 天"）几乎总是非空，导致这个备选候选在现网几乎总被判定占用——设计正确/安全，但真实触发窗口很窄，非 bug，如实记录。其余风格（veil-footer/band-cut）目前无第二个已验证安全候选，`placement_presets` 返回值跟原单候选行为完全等价，无回归。新增 10 条测试（`placement_presets`/`conditional_occupant` 相关 6 条 + engine 多候选切换/fail-open 4 条）+ `cover_opening.build_cover_archive_strip` 抽取回归 3 条；`tests/unit/cover_engine/` 151 passed；`tests/unit/curation/test_cover_opening.py` + `tests/unit/render/` + `tests/unit/domain/test_copy_patch.py` 42 passed；ruff 全绿 |
| **v0.6.6** | 2026-08-08 | **W0.5 完整 Spike（AC-CAL-11）待补 API Key；OQ-CAL-09 收尾：folio-overlap 专门方案开放**（[验收记录 §8](./acceptance-records/cover-calligraphy-title-v1-w2-whitelist-expand-2026-08-07.md#8-oq-cal-09-收尾folio-overlap-纸面栏专门方案)）：深挖 OQ-CAL-09 发现阻断根因比"选错候选"更底层——`CoverStyleProfile.text_safe_regions` 描述的是**照片自身坐标系**里的焦点安全区（`opening/title_safe.py::mark_title_safe` 只拿它比对 `asset.focalPoint`），跟 folio-overlap DOM 里"`.cover-hero` 只占据 `--cover-folio-margin` 右侧那部分、左侧纸面栏 33% 根本不显示照片"这件事完全是两个坐标系；对全幅铺满照片的三款风格两个坐标系刚好重合能直接派生，对 folio-overlap 无论怎么挑候选都跳不出这个坑。**方案**：不再尝试派生，改用手工矩形直接描述 DOM 语义（跟 veil-footer OQ-CAL-08 收尾同思路）——`PlacementPreset` 新增 `assume_paper_bg` 字段，命中时 §6.1 自动配色改用固定纸色（`--cover-folio-paper` #f4f1ea）估计而非采样原始照片；`placement.score_candidate` 对该字段候选跳过亮度方差/人脸惩罚（openness 恒满分，因为纸面区块跟照片内容概念上无关，不是"数值恰好合理"）；`engine.py` 对该字段候选跳过 `focal_conflict`（矩形对应的不是照片内容，镜头主体不可能视觉上出现在纸面上）。仿 D-CAL-20 优先顺位⑤同款机制注册双候选：主候选"纸面栏下半段"（不管地点标签 `.cover-opening__place` 是否占用顶部都安全）+ 备选"纸面栏全高"（`conditional_occupant="folio_place_present"`，仅无地点标签占用时用，复用从 `assemble.py` 抽出的 `cover_opening.resolve_show_cover_place()`）。**顺手修的一个通用问题**：`assume_paper_bg` 候选之间 openness 恒打平分，`best_placement` 原先 `max()` 平分总选列表第一个（主候选），会让"无占用时换更宽裕的备选"这条设计路径在打分层面永远选不中——加一层按面积（`box[2]*box[3]`）打破平分的次序，对任何未来出现真正打平分的多候选风格通用有益，不影响现有 contact-stamp 场景（该场景下淘汰后通常只剩一个候选，平分无意义）。`journal.css` 补 CSS 侧白名单同步（老毛病）+ folio-overlap 专属 `max-width:26%`（纸面栏仅 33% 宽，沿用共享的 60% 会溢出到骑缝渐变/照片区）。`folio-overlap` 转入 `DEFAULT_ENABLED_STYLES`，**D-CAL-20 收尾，OQ-CAL-09 关闭**。真实 trip（`demo-0ebda73294` 临时改风格，验证后删除未提交）两种场景（有/无地点标签）Playwright 视觉核对通过：贴纸清晰落在纸面栏内、不溢出骑缝/照片区、不与地点标签重叠。新增 12 条测试（whitelist 4 条 + placement 2 条 + engine 5 条 + cover_opening 抽取回归 3 条，注：部分与既有测试合并统计）；相关子集 `tests/unit/cover_engine` + `tests/unit/render` + `tests/unit/config` + `tests/unit/domain/test_copy_patch.py` + `tests/unit/curation/test_cover_opening.py` 465 passed, 6 skipped；ruff 全绿。**W0.5 完整 Spike（AC-CAL-11）本版未启动**——需要 `DASHSCOPE_API_KEY`，待用户提供后补齐 20～30 条真实/边界标题样本测试 |
| **v0.6.7** | 2026-08-08 | **补齐 W0.5 完整 Spike，AC-CAL-11 判定不通过**（[验收记录](./acceptance-records/cover-calligraphy-title-v1-w05-route-c-spike-2026-08-08.md)）：用户提供 API Key，新增 `scripts/title_art_route_c_spike.py` 跑 26 条真实/边界标题（覆盖极短/极长、生僻字地名——本 app 是游记工具，地名生僻字是真实高频场景、多音字、数字英文混排、标点、叠字、古诗词句、8 字上限），5 款风格轮转，`wanx2.1-t2i-plus` 逐条调用 + 复用 `vision_chat_completion`（`qwen-vl-plus`）OCR 回读。**结果**：生成 100% 成功（无超时/审核拒绝）、延迟均值 18.0s（P95 19.2s）；**OCR 回读通过率仅 57.7%（15/26）**——常见地名/纯数字稳定 100%，生僻字（55.6%）/古诗词句/标点/叠字系统性出错（整字被替换为不相关形近字，非局部缺笔，肉眼可辨，D-CAL-19 能可靠拦截）。据此**钉定 AC-CAL-11 阈值为「单次 OCR 通过率 ≥90%」**，本次实测远未达标，**判定不通过**；回答 **OQ-CAL-06**——路线 C 明确不升级为默认主路径，长期定位为用户可选高级项；**OQ-CAL-07** 完整关闭。`route_c_enabled` 继续默认 `false`（`config/title_art.py` 注释同步更新，标注具体通过率数字而非"未测"）。识别到 3 条未落地的后续方向（标题内容预筛选/重试机制收益/标点叠字规则化处理），记入验收记录 §5，留给后续排期，本版不实现。测试 key 使用后已从进程环境变量清除，未落盘、未提交 |
| **v0.6.8** | 2026-08-08 | **落地 v0.6.7 验收记录 §5 提出的「标题预筛选」思路，新增 D-CAL-21**：新增 `travelogue/cover_engine/title_art/char_frequency.py::title_has_only_common_chars()`——用标准库 `codecs` 在导入时从 GB2312 编码本身派生一级常用汉字表（3755 个，零外部依赖、零网络请求，40 年未变的国标），非汉字字符（数字/英文/标点）永不阻断。`engine.py` 在 `route_c_enabled=True` 分支里，真正调用 `generate_raw` 之前先跑这层预筛选：命中「含表外生僻字」→ 直接短路到路线 B（不发 API 请求），`fallback_from="diffusion-fixed-prompt-v1"` + `explain` 记录"预筛选：标题含生僻字"，跟"调用了但 OCR 没过"最终展示效果完全等价，**不新增安全语义**，D-CAL-19 OCR 回读校验依旧是唯一真正的闸门。对 26 条 Spike 样本回测：过滤器允许 17/26 尝试，尝试子集通过率由 57.7%（全量）升至 64.7%——**仍未达 AC-CAL-11 的 90% 门槛，不改变 `route_c_enabled` 默认关闭的结论**，本条价值在于"少花几次注定失败的调用成本/延迟"，不是"解锁默认开启"。如实记录局限：字表召回不完美（`黟`/`硇`/`邺` 等二级字在 Spike 里实际生成正确却会被本过滤器错杀，纯效率损失非安全问题）。新增 `test_title_art_char_frequency.py`（21 条：字表大小断言 + 常用/生僻标题分类 + 空串/纯数字英文 + codec 缺失兜底）+ `test_title_art_engine.py` 新增 2 条（预筛选短路验证 `generate_raw` 未被调用 + 常用字标题不受影响的回归）；`tests/unit/cover_engine/` 188 passed；`tests/unit/render`+`tests/unit/config`+`tests/unit/domain/test_copy_patch.py`+`tests/unit/curation/test_cover_opening.py` 300 passed, 6 skipped；ruff 全绿 |
| **v0.6.9** | 2026-08-08 | **补齐 Studio 高级面板触发入口，新增 D-CAL-22**（回应 v0.4.0 变更记录遗留的「未完成」项）：新增 `travelogue/web/studio_handlers/title_art_handlers.py::handle_post_resolve_title_art`，挂路由 `POST /__travelogue/trips/{tripId}/title-art/resolve`（比照 `bookends_handlers.py` 的 mutator + rerender 模式）；请求体 `{force, routeC, styleId}`，`force` 默认 `true`（一次性生成语义，等价 CLI `title-art --force`），`routeC` 与服务端 `config.title_art.route_c_enabled` 总闸相与，总闸关时静默按路线 B 处理（`routeCAllowedByConfig` 字段回传，不依赖前端诚实）；`resolve_title_art` 抛未知异常时按 D-CAL-16 fail-open，写回 `disabled_meta_dict(reason="E_TITLE_ART_UNEXPECTED")` 并 200 返回，不 500。`studio_config_expose()` 新增 `titleArt.{enabled,routeCEnabled}` 字段供前端判断是否展示入口。前端在 `features.js::mountCoverStyleControls`（「封面版式」面板，bookends 面板会复用它）追加「生成装帧标题」按钮 + 「尝试 AI 手写体」勾选框（读服务端总闸决定是否展示），成功后复用既有 `reloadPreviewAfterLayout()`/`showToolbarToast()` 刷新预览，不另起一套逻辑。新增 `test_title_art_handlers.py`（6 条：总闸相与两态、fail-open 不 500、`force` 默认 `true`、rerender 失败 500）+ `test_studio_title_art_routes.py`（路由匹配/注册 3 条）+ `test_title_art_frontend_wiring.py`（前端接线字符串级校验 3 条）+ `test_studio_config_happy_path.py` 新增 1 条；聚焦子集 33 passed；`tests/unit/cover_engine/` 188 passed 不变；ruff 全绿 |
| **v0.6.10** | 2026-08-08 | **补齐 AC-CAL-04/05/06/13 验收记录**（[验收记录](./acceptance-records/cover-calligraphy-title-v1-ac04-05-06-13-2026-08-08.md)）：§11 W2 里程碑表最后 4 项「待补验收记录」清零。新增 `scripts/verify_title_art_ac04_05_13.py`，从仓内 14 条真实 trip（非 fixture）解析真实封面原图，组成测试集；对 4 款白名单风格（`veil-footer`/`band-cut`/`contact-stamp`/`folio-overlap`）的全部候选矩形（含备选）逐一实测：**AC-CAL-04** 对比度 32/32 达标（ratio 区间 4.27~19.80，均有充足冗余），`MIN_CONTRAST_RATIO=3.0` 确认可维持定稿，关闭 **SHD-CAL-02**（`color.py` 注释同步更新）；**AC-CAL-05** 候选矩形面积占比 7.7%~24.3%，14 条真实照片跑 `score_candidate` 0 例触发遮挡惩罚分支。**AC-CAL-06**：选一条从未生成过 `titleArt` 的真实 trip（`demo-3ee2727aea`），走零可选参数默认路径（`title-art` 不带 `--route-c/--style/--force`），核对 CLI 成功 → `rerender_draft_trip`（Studio 触发按钮走的同一函数）渲染 → Playwright 实测浏览器叠加，全链路可用；顺手发现原生 CLI `render` 命令因仓内其它进行中工作（screens 版式迁移）留下的 `screenId` 校验缺口报错，跟本次改动无关，改用 Studio 实际触发路径核对不受影响。**AC-CAL-13**：复用路线 C W0.5 Spike 的 6 张真实产出图（非 mock），走 `pick_readable_color`→`recolor_ink_on_white` 链路，核对重上色产物像素跟挑选出的目标墨色逐位一致，6/6 达标；另用 3 组中性灰边界背景核对默认兜底白色分支可复现。核对过程中发现 1 处非阻塞观察项（艺术字贴纸与 `<h1>`/`alt` 取的标题字段来源不一致，新增 **OQ-CAL-10**，留待后续评估）。回归：`tests/unit/cover_engine/` 188 passed；ruff 全绿 |
| **v0.6.11** | 2026-08-08 | **贴纸烧入风格衬底，新增 D-CAL-23**（用户反馈"贴纸跟封面配合不好"真机截图触发）：`render_b.py` 新增 `_band_cut_backdrop`/`_veil_footer_backdrop`/`_contact_stamp_backdrop`，`render_title_art` 按 `opening_style_id` 分发——`band-cut` 主字改左对齐 + 烧入左对齐纸签渐变面板（呼应 `--cover-band-paper` + 向右淡出尾巴 + 柔和投影，主字宽度收紧到 62% 给淡出尾巴留画布余量）；`veil-footer` 烧入柔光垫底（呼应原生 `text-shadow`，色调按主字明暗自适应，实测固定暖暗色调在浅色天空区域几乎看不出效果才改自适应）；`contact-stamp` 烧入微旋转说明卡片（呼应现网日戳徽标语言，主字宽度同样收紧到 62%，否则卡片加内边距+旋转后会超出工作画布被硬裁出直边缺口）；`folio-overlap`/未知风格保持原有纯透明行为（新增回归测试断言字节级相同，零回归）。`engine.py` 调用处新增一行 `opening_style_id=style_id` 完成接线。`journal.css` 收紧 `band-cut`（52%/13%）/`contact-stamp`（34%/26%，取主候选与备选中更紧的宽度）的 `max-width/max-height` 到贴近真实候选矩形比例，不再沿用共享的 60%/20% 近似值（此前偏宽会把烧好的衬底放大到溢出断带线/日戳留白区）。新增 4 条测试（3 款衬底非全透明 + band-cut 左对齐验证 + 未知风格零回归断言）；用真实 trip 素材（`demo-0ebda73294` band-cut、`demo-3ee2727aea` veil-footer，均走 CLI 重生成 + Studio 渲染管线 + 本地 PIL 按 CSS 定位/缩放规则合成核对）与模拟合成（`contact-stamp`，仓内暂无该风格真实样例）视觉核对，三款均从"裸字贴照片"改善为"文字嵌在设计好的衬底里"。回归：`tests/unit/cover_engine/` 193 passed + `-k "title_art or cover_engine or studio_config"` 220 passed；ruff 全绿 |
| **v0.6.12** | 2026-08-08 | **补齐 D-CAL-23 验收记录**（[验收记录](./acceptance-records/cover-calligraphy-title-v1-d-cal-23-backdrop-2026-08-08.md)）：`band-cut` 用同一条真实 trip（`demo-0ebda73294`）改造前用户报告截图 vs 改造后真机截图直接对比，证据链最直观；`veil-footer`（`demo-3ee2727aea`）与 `contact-stamp`（`demo-1547c68851`，临时切换验证后已完整还原）均补做 Playwright `getBoundingClientRect()` 实测（非估算），核对贴纸实际渲染宽高占比未超出 `journal.css` 收紧后的 `max-width/max-height` 上限；`contact-stamp` 借此把 v0.6.11 遗留的"模拟合成"升级为真实 trip 实测，仓内暂无该风格真实样例的限制不再是结论依据。发现 1 处非阻塞观察项：`band-cut` 纸签实际渲染宽度远小于候选矩形宽度，衬底左边缘未完全贴合候选区左边界（视觉上仍清晰可读，不阻塞验收，记为后续可选优化）。回归：`tests/unit/cover_engine -q` 全部通过；ruff 全绿 |
| **v0.6.13** | 2026-08-08 | **清账：AC-CAL-01/02/10 + §10 归因 + OQ-CAL-10 + W3 方案**。对照 PRD 发现 W2 口头「AC-01～06 已补齐」但 §12.3 未打勾——补 [`scripts/verify_title_art_ac01_02_10.py`](../scripts/verify_title_art_ac01_02_10.py) + [验收记录](./acceptance-records/cover-calligraphy-title-v1-ac01-02-10-2026-08-08.md)：① `enabled=false`/无字段/stale 不叠加；② 固定金样 aHash（SHD-CAL-01，Hamming 0）；③ 真实 trip `index.html`/`index-longshot.html` 同源 `assetPath`。落地 §10 归因（`attribution.py` + Studio 面板 + 封底/长图页脚，路线 B/C 区分措辞）。关闭 **OQ-CAL-10**：`contract.resolve_title_text` 改走 `resolve_display_title`（`mainSource=displayTitle`）。W3 盲评方案定稿（[方案](./acceptance-records/cover-calligraphy-title-v1-w3-blind-plan-2026-08-08.md)），执行未开始。修正 §6.2「W2 待落地」过期表述。回归：相关单测 + verify 脚本 PASS |
| **v0.6.14** | 2026-08-08 | **W3 盲评样本出图（评委前）**：[`scripts/title_art_w3_blind_shots.py`](../scripts/title_art_w3_blind_shots.py) 从 12 条真实 demo trip 产出路线 B 成对封面截图（`band-cut`×4 / `veil-footer`×4 / `contact-stamp`×2 / `folio-overlap`×2），写入 [附件目录](./acceptance-records/attachments/cover-calligraphy-title-v1-w3-blind-2026-08-08/)（`manifest` + `scores.csv` + `answer-key.csv` + `review.html`）。截图路径隐藏草稿工具栏与 `folio-plate-meta`（直出 trips HTML 无 Studio shell.css）。进度记录：[W3 盲评进度](./acceptance-records/cover-calligraphy-title-v1-w3-blind-2026-08-08.md)。**评委打分未开始；不宣称 AC-CAL-BLIND 通过；`enabled` 默认仍 `false`。** 路线 C 本轮延期。 |
| **v0.6.15** | 2026-08-08 | **路线 C 冲质量（W0.5b · 1A+2A）代码落地**：对 W0.5 的 11 张 OCR 失败图做人工审计（[审计](./acceptance-records/cover-calligraphy-title-v1-route-c-w05b-audit-2026-08-08.md)：9 glyph_wrong / 1 ambiguous / 1 ocr_false_reject）→ **不放松 D-CAL-19**。落地：`style_registry` Prompt **v2**（默认）、`engine` OCR mismatch **重试 1 次**、`risk_rules` 标点/叠字短路、`TitleArtConfig` 接线 `model_name`/`prompt_version`/`route_c_max_attempts`/`ocr_verify`（Studio+CLI）。新增矩阵脚本 [`title_art_route_c_w05b_spike.py`](../scripts/title_art_route_c_w05b_spike.py)（E1/E2/E3）；本机无 `DASHSCOPE_API_KEY`，仅完成 dry-run 分配（[落地记录](./acceptance-records/cover-calligraphy-title-v1-route-c-w05b-landing-2026-08-08.md)）。**AC-CAL-11 仍 ❌**；`route_c_enabled` 默认仍 `false`。 |
| **v0.6.16** | 2026-08-08 | **W0.5b 真实 Spike 完成，AC-CAL-11 在新协议下达标**（[结果](./acceptance-records/cover-calligraphy-title-v1-route-c-w05b-result-2026-08-08.md)）：`v2 + retries=1 + samples=2`，跳过生僻字/标点/叠字后尝试 **30** 次——首次 OCR 83.3%，**重试后 90.0%（27/30）**。残留失败：`厦门老城区`（非确定）、`重走318国道`×2（数字混排）。**默认 `route_c_enabled` 仍 false**；允许配置显式开高级项并告知可能回退 B。不启动 vendor bakeoff。 |
| **v0.6.17** | 2026-08-08 | **Studio 高级项 + 数字混排风险规则**：`route_c_enabled` 代码默认改为 `true`（仅控制勾选框是否出现；仍须用户勾选才走 AI，OQ-CAL-06）。UI 文案改为「尝试 AI 手写体」+「高级项 · 可能回退默认样式 · 约十几秒」。新增 `digit_mix` 风险规则（汉字后再嵌阿拉伯数字如「重走318国道」直接 B；「918公里」不拦）。样例配置 `config.user.example.yaml` / `config.yaml.example` 补 `title_art` 段。 |
| **v0.6.18** | 2026-08-09 | **新增 D-CAL-24（提案）：路线 B 可读性自检，本版不改代码**（[决策记录](./acceptance-records/cover-calligraphy-title-v1-d-cal-24-route-b-legibility-plan-2026-08-09.md)）：产品复盘 W3 真实样本时发现 `band-cut`「初中毕业照」在默认字库 `ZhiMangXing` 连笔下"毕"字肉眼可读错——路线 B 迄今无"渲染后是否可读"的验收，跟路线 C 的 `ocr_verify` 强门禁力度错配。定下决策边界：**不得**为此给路线 B 接 LLM/网络调用（D-CAL-01/02 红线），机制须是纯本地连通域启发式 + 静默切换到 `FONT_POOL` 已有的 `鸿雷板书体` 备用候选。新增 **OQ-CAL-11**（备用字体是否真的更可读待真人核对）。本版仅新增决策记录与 PRD 条目，无代码/测试改动。 |
| **v0.6.19** | 2026-08-09 | **D-CAL-24 Phase 1 验证完成 · 机制被证伪 · 决定关闭不实现**（[决策记录 §6](./acceptance-records/cover-calligraphy-title-v1-d-cal-24-route-b-legibility-plan-2026-08-09.md#6-phase-1-结果2026-08-09-已跑完)）：新增一次性验证脚本 [`title_art_d_cal_24_legibility_probe.py`](../scripts/title_art_d_cal_24_legibility_probe.py)（不进生产路径），用纯 Python flood fill 对 7 个汉字实测 `simhei`/`ZhiMangXing`/`鸿雷板书体` 连通域计数。**结果**：同句真实标题里未被误读的"业"/"照"，`ZhiMangXing` 连通域比值（0.33/0.29）反而**低于**真正被误读的"毕"（0.67）——v0.6.18 提出的"比值越低风险越高"规则被数据直接排反；根因是草书连笔普遍拉低连通域计数，这是字体设计常态，拿来当风险探测器噪声远大于信号。结合更根本的反驳（人类读自己写的标题靠词组级整体识别+强先验，不是旁观者逐字拼认，孤立单字误读不能外推成真实误读风险）——**决定关闭 D-CAL-24，不给路线 B 上任何自动可读性门禁**，随之关闭 **OQ-CAL-11**。本版新增验证脚本 + 1 张对比网格图，无生产代码改动。 |
| **v0.6.26** | 2026-08-09 | **新增 D-CAL-27：title_art 漏斗埋点**：修复历史缺口——`features.js` 早已调用 `title_art_resolve` 但前后端白名单均未登记，事件被静默丢弃；现登记 `title_art_impression` + `title_art_resolve`（覆盖 success/disabled/error/network 全 outcome），meta 含 engine / routeCRequested / fallback / ocrVerified，可算 B/C 使用率与失败率。新增接线测试锁住白名单与 outcome 覆盖面。详见[决策记录](./acceptance-records/cover-calligraphy-title-v1-d-cal-27-title-art-telemetry-2026-08-09.md) |
| **v0.6.25** | 2026-08-09 | **type-monument 长标题镂空巨字重叠错位修复（D-CAL-26 §8.4 顺带发现跟进）**：`--cover-monument-title-size: min(25vw, 45vh)` + `line-height: 0.88` 是给 2~4 字单行巨字设计的尺寸，长标题换行到 2~3 行后紧行高 + 大字重笔画纵向溢出导致相邻行真的视觉重叠。新增 `resolve_monument_title_layout(title)` 按字数分档（≤4 `compact` 原样不变 / 5~7 `wrapped` 降到 `min(15vw,27vh)`+`line-height:1.08` / ≥8 `wrapped-long` 降到 `min(10vw,18vh)`+`line-height:1.26`），`assemble.py` 接入 `coverMonumentTitleLayout` context 字段，`cover-opening.hbs` 追加 `data-monument-title-layout` 属性驱动 CSS。同一 demo 标题「斯里兰卡见闻录」（7 字）修复前后对比截图确认重叠消除；2 字短标题确认零回归。新增 3 条测试（分档边界值 + context 接线 + CSS token）；回归 `tests/unit/curation/test_cover_styles_v5.py` + `tests/unit/render/test_cover_opening_identity_line.py` 35 passed；ruff 全绿。详见[决策记录](./acceptance-records/cover-calligraphy-title-v1-d-cal-26-front-cover-identity-line-2026-08-09.md) §8.6 |
| **v0.6.24** | 2026-08-09 | **veil-footer 长标题贴纸字号微调（W3 b06 留痕跟进）**：`_MAIN_TEXT_MAX_WIDTH_RATIO_BY_STYLE` 给 `veil-footer` 单独放宽到 `0.94`（共享默认 `0.86`），让长标题触发的收缩循环少收一档；同一 7 字标题实测字号 157px→171px（+9%）。低风险参数级微调，不改两行排版等结构性方案；短标题本就不触发收缩循环，零回归（已用单测证明字形高度完全一致）。新增 3 条测试；回归 `tests/unit/cover_engine/test_title_art_render_b.py` 16 passed。详见[决策记录](./acceptance-records/cover-calligraphy-title-v1-veil-footer-long-title-tuning-2026-08-09.md) |
| **v0.6.23** | 2026-08-09 | **D-CAL-26 扩展：装帧身份线前封回声覆盖到全部 10 款风格**：把 `_COVER_OPENING_BRAND_STYLES` 从首批 4 款扩展到剩余 `cameo-aperture`/`type-monument`/`scroll-head`/`portal-arch`/`horizon-split`/`diptych-seam` 共 10 款。逐款用真实渲染截图核对，过程中发现两类坑：①trip 输出目录会缓存陈旧 `journal.css`，改完源文件不会自动同步，需显式复制才能验证到位；②`type-monument`/`horizon-split`/`diptych-seam` 若沿用跟 `hook` 同侧的右下角锚点会跟阅读器自带的 `screenplay-toolbar`（复制文案/长图按钮）撞位，改为左下角或抬高锚点规避。顺带发现 `type-monument` 对 7 字长标题渲染本身会重叠错位（跟本条无关的既有问题），已记录不处理。`test_cover_opening_identity_line.py` 参数化用例扩展到全部 10 款（15 条）；回归 `tests/unit/render` 15 passed；ruff 全绿。详见[决策记录](./acceptance-records/cover-calligraphy-title-v1-d-cal-26-front-cover-identity-line-2026-08-09.md) §8 |
| **v0.6.22** | 2026-08-09 | **新增 D-CAL-26：装帧身份线前封回声，已落地并默认开启**：复用 D-SFI-13 署名三态（`Travelogue`），把渲染位从「封底 + 长图脚」两处扩展到「+ 前封」三处；扩容另一主题（Share-Face-Integrity-V1）已定契约，已经产品负责人确认。4 款艺术字白名单风格真实渲染截图验证全部通过（`band-cut`/`veil-footer`/`contact-stamp`/`folio-overlap`）后，产品负责人拍板翻转默认值。过程中发现并修复一次真实 bug——`veil-footer` 等 3 款风格标题/hook 用绝对定位脱离文档流，新元素若沿用文档流会飘位，改为按风格逐个写绝对定位覆盖。`assemble.py::_COVER_OPENING_BRAND_STYLES` 现含全部 4 款；白名单外旧风格（`type-monument` 等未核对布局）仍不显示，避免盲开出同类 bug。新增 `test_cover_opening_identity_line.py`（9 条）；回归 464 passed, 6 skipped；ruff 全绿。详见[决策记录](./acceptance-records/cover-calligraphy-title-v1-d-cal-26-front-cover-identity-line-2026-08-09.md) |
| **v0.6.21** | 2026-08-09 | **AC-CAL-BLIND 已通过（单一评委协议）**（[结论](./acceptance-records/cover-calligraphy-title-v1-w3-blind-2026-08-08.md#5-结论单一评委协议--2026-08-09)）：产品负责人显式放宽 [W3 盲评方案](./acceptance-records/cover-calligraphy-title-v1-w3-blind-plan-2026-08-08.md) §3 原「评委 ≥5 人」门槛，改为「单一代表性评委（产品负责人）即可，样本标题本身来自真实用户产出、具有代表性」，并由产品负责人在不知晓 `answer-key.csv` 的情况下独立完成全部 12 对盲评打分（记入 `scores.csv`，`raterId=owner`）。**结果**：艺术字侧胜率 **91.7%（11/12）**，分风格 `band-cut` 100%/`veil-footer` 75%/`contact-stamp` 100%/`folio-overlap` 100%，均 ≥55% 门槛；唯一现网 CSS 胜出的 `b06`（veil-footer 长标题）留痕供后续字号调优参考，不建 OQ。如实标注协议简化程度（n=1、评委即产品负责人，非独立第三方），已被产品负责人接受为内部决策依据。**产品负责人随即拍板翻转默认值**：`travelogue/config/title_art.py::TitleArtConfig.enabled` 由 `False` 改为 `True`（`title_art_config_from_dict` 缺省同步改为 `True`），D-CAL-05 收口为「默认开」。**边界不变**：该开关只决定 Studio「生成装帧标题」按钮/Route C 勾选框默认是否展示，`resolve_title_art` 仍是用户点击才触发的单次操作；`enabled=True` 但用户不点按钮，trip 不会有任何变化。同步更新 `test_studio_config_expose_title_art_gate` 期望值；回归：`test_studio_config_happy_path`/`test_title_art_engine`/`test_title_art_handlers`/`test_title_art_frontend_wiring`/`test_title_art_ac01_02_10`/`test_title_art_fonts`/`test_copy_patch` 共 88 + 54 项 PASS，ruff clean。 |
| **v0.6.20** | 2026-08-09 | **新增 D-CAL-25：Typeface Voice Matrix，已落地**：`fonts.py` 新增 `FONT_VOICE_BY_STYLE`（`veil-footer`/`band-cut` → `ZhiMangXing`；`contact-stamp`/`folio-overlap` → `鸿雷板书体`）+ `pick_font_for_style(style_id)`；`engine.py::resolve_title_art` 接入，未命中风格落回原默认字体（零回归）。明确边界：纯编辑/调性决策，不是可读性判定，不重蹈 D-CAL-24 的算法信号覆辙。同一标题「初中毕业照」在 `band-cut`/`contact-stamp` 两种字体下的[真实渲染对比图](./acceptance-records/attachments/cover-calligraphy-title-v1-d-cal-24-route-b-legibility-plan-2026-08-09/d-cal-25-typeface-voice-matrix-demo.png)确认两款风格视觉调性明显不同。新增测试：`test_title_art_fonts.py`（映射表授权校验 + 4 款风格映射 + 未知风格回退）+ `test_title_art_engine.py`（4 款风格端到端字体断言）；顺手清理 1 处遗留重复测试定义（技术债，与本次改动无关）。回归：`tests/unit/cover_engine/` 230 passed；`tests/unit/render`+`tests/unit/config`+`tests/unit/domain/test_copy_patch.py`+`tests/unit/curation/test_cover_opening.py` 301 passed, 6 skipped；ruff 全绿。 |
