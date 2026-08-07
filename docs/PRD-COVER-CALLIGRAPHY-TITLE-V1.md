# Travelogue · 封面艺术字标题 V1 产品需求文档（PRD）

| 属性 | 内容 |
|------|------|
| **产品代号** | Travelogue Studio |
| **文档版本** | **v0.6.3** |
| **状态** | **Kickoff · W1 开发中**（分支 `feat/cover-calligraphy-title-v1`）· [七席评审](./acceptance-records/cal-cover-calligraphy-title-v1-review-2026-08-06.md) · [W1 真实素材视觉验收](./acceptance-records/cover-calligraphy-title-v1-w1-visual-review-2026-08-07.md) · **BLK-CAL-01～05 已回写**；**v0.4 产品显式拉起「封面装帧增强」窗口，路线 B + 路线 C 引擎均已实现（`travelogue/cover_engine/title_art/`），路线 C 走 W0.5-lite 现场实测（非完整 20～30 条样本 Spike，见 v0.4.0 变更记录）**；**v0.5 真实素材视觉验收发现并修复 3 处集成缺口（字库资产路径 / 贴纸容器定位 / stale 未接线），AC-CAL-03/07/08/09/12 转为通过**；**v0.6 产品复核 §6.2 定位策略（讨论向，未动代码），确认 Opening Registry `text_safe_regions` 应作为 placement 候选区的权威数据源，收窄 D-CAL-13 并新增 D-CAL-20，W2 白名单开放顺序定为 band-cut → contact-stamp → folio-overlap → veil-footer 修复 → scroll-head 暂缓**；**v0.6.1 落地 D-CAL-20 优先顺位①②：`whitelist.py` 改为从 `text_safe_regions` 派生坐标，开放 `band-cut`/`contact-stamp` 白名单，真实 trip 视觉核对通过，过程中发现并修复 CSS 侧白名单未同步的集成缺口**；**v0.6.2 用户实测反馈 contact-stamp 贴纸文字读不出来，追查为自动配色未考虑该风格固定深色渐罩，已修复（[验收记录](./acceptance-records/cover-calligraphy-title-v1-w2-whitelist-expand-2026-08-07.md)）**；**v0.6.3 开放前排查 4 款风格 CSS 暗坑（[验收记录 §5](./acceptance-records/cover-calligraphy-title-v1-w2-whitelist-expand-2026-08-07.md#5-前瞻审计开放前排查其余风格的-css-暗坑2026-08-07-追加)）：veil-footer/band-cut 排查通过非阻断；发现 `folio-overlap` 两条候选矩形均不能直接套用贴纸流程，新增 OQ-CAL-09，本版未改代码** |
| **DOC-STATUS** | **kickoff-w1** |
| **主题代号** | 「点睛」— **CAL**（Calligraphy Title） |
| **触发来源** | 2026-08-06 产品讨论：用户希望游记封面标题达到「即梦」文生图那种手写体艺术感；经过对既有内部 demo（`arttext-miniapp`）的实证分析，确认了可落地路径 |
| **前置条件** | [CHARTER.md](./CHARTER.md) §7；[PRD-COVER-STYLES-V6.md](./PRD-COVER-STYLES-V6.md) Opening Registry 可用；现网 `cover-opening.hbs` / `meta.title` 可渲染。**不依赖** CAD 已落地（见 D-CAL-04 / D-CAL-09） |
| **关联文档** | [PRD-COVER-ART-DIRECTION-V1.md](./PRD-COVER-ART-DIRECTION-V1.md)（CAD · 姊妹策划，非硬依赖）· [PRD-AI-RETURN-V1.md](./PRD-AI-RETURN-V1.md)（AIR · **解耦**，CAL 不消耗 LLM）· [PRD-COVER-STYLES-V6.md](./PRD-COVER-STYLES-V6.md) · [PRD-CHAPTER-NAMING.md](./PRD-CHAPTER-NAMING.md) · [PRD-EXPORT-CARD-COMPOSE-V1.md](./PRD-EXPORT-CARD-COMPOSE-V1.md) · 证据 `docs/acceptance-records/attachments/cover-calligraphy-title-evidence-2026-08-06/` · [七席纪要](./acceptance-records/cal-cover-calligraphy-title-v1-review-2026-08-06.md) |
| **验收** | 启动开发时拆 `ACCEPTANCE-COVER-CALLIGRAPHY-TITLE-V1.md`；本文 §12 为源 |
| **实施清单** | 启动开发时拆 `IMPLEMENTATION-COVER-CALLIGRAPHY-TITLE-V1.md` |
| **更新日期** | 2026-08-07 |

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
| **D-CAL-05** | **默认关** | `meta.titleArt.enabled` 默认 `false`；盲评 ≥55% 方可默认开 |
| **D-CAL-06** | **贴纸非背景** | 永不替换封面实拍主图 |
| **D-CAL-07** | **字库授权门禁** | 未核查字库不得进生产候选池 |
| **D-CAL-08** | **暂停工程排期** | 直至产品显式拉起 §11 启动条件 |
| **D-CAL-09** | **独立数据挂载（BLK-01 · 方案 A）** | `titleArt` 落 `trip.meta.titleArt`；**不**嵌入未落地的 CAD `artDirection`。CAD 落地后可再嵌，非 V1 门禁 |
| **D-CAL-10** | **Opening 白名单（BLK-04）** | 首发仅 **`veil-footer`**；可选第二款 **`folio-overlap`**（W2 狗粮后再开）。其它 styleId → 强制不叠加贴纸，保持现网 HTML 标题 |
| **D-CAL-11** | **与 AIR 解耦（BLK-05）** | 启动窗口名「封面装帧增强」；零 LLM；不进 AIR AC |
| **D-CAL-12** | **印章自制/公版（BLK-05）** | V1 **不**移植 demo wanx 印章批次；自制矢量/扫描公版朱红印 |
| **D-CAL-13** | **自建 placement_score** | 不假设现网存在 `textSafe`/`typeTheme` API；算法见 §6 |
| **D-CAL-14**（v0.3 新增） | **路线 C 仅为候选，非替代** | 路线 C 未通过 W0.5 Spike（§11）前，不进任何默认路径；即便通过 Spike，路线 B 仍作为兜底永久保留，不因路线 C 上线而下线 |
| **D-CAL-15**（v0.3 新增） | **固定提示词模板，禁止开放 prompt** | 路线 C 仅消费风格库 Registry（§5.5.1）中的固定模板；仅允许替换标题/副标文字与色彩占位符；**禁止**运行时拼接用户自由文本进 prompt 主体 |
| **D-CAL-16**（v0.3 新增） | **分层 fallback 强制** | 路线 C 生成失败 / 超时 / 内容审核不过 / 字形 OCR 校验不过 → 必须静默降级路线 B → 路线 B 也失败 → fail-open 现网 HTML；**禁止**在任一环节展示错误态或半成品贴纸（原则 8） |
| **D-CAL-17**（v0.3 新增） | **色彩后处理，不在 prompt 里描述颜色** | 路线 C 固定生成「白底黑字」高对比稿；目标墨色由 §6.1 算法在生成后对笔迹层重新填色决定，默认白色兜底（与路线 B 共用同一配色算法） |
| **D-CAL-18**（v0.3 新增） | **模型优先级** | 技术验证与落地优先测 **阿里云通义万相（DashScope wanx）**；即梦（火山引擎 API，若能申请到）/腾讯混元生图作为陪跑对比；**不采用 DeepSeek**（无成熟商用文生图 API，中文书法准确率未验证） |
| **D-CAL-19**（v0.3 新增） | **字形 OCR 校验门禁** | 路线 C 输出必须过 OCR 回读校验（识别结果与 `mainRendered` 一致）方可判定为「有效贴纸」；未过校验 → 触发 D-CAL-16 fallback，不计入生产可用素材 |
| **D-CAL-20**（v0.6 新增 · 收窄 D-CAL-13） | **placement 候选须从 Opening Registry `text_safe_regions` 派生，不再自建独立矩形表** | D-CAL-13「不假设现网存在 `textSafe` API」的前提已不成立——`travelogue/cover_engine/registry.py`/`catalog.py` 的 `CoverStyleProfile.text_safe_regions` 已覆盖全部 10 款风格且已被 `opening/title_safe.py::mark_title_safe` 生产使用，与真实渲染坐标高度吻合。W2 落地时：**① `whitelist.py` 的 `PlacementPreset.rect` 改为从对应风格的 `text_safe_regions` 派生而非手搓数值 —— ✅ 已完成（v0.6.1）**；**② 开放 `band-cut`/`contact-stamp` 白名单 —— ✅ 已完成（v0.6.1，真实 trip 视觉核对通过）**；③ 一个风格有多个候选区域时，`placement_score` 须对候选逐一打分择优，而非固定绑死一个矩形 —— ⏳ 未做；④ 补一层「候选区域是否已被本风格自身文案（hook/trip-meta/archive）占用」的排除校验 —— ⏳ 未做（对应 OQ-CAL-08，`veil-footer` 现有矩形未动）；⑤ 落地前复用 `mark_title_safe` 已算出的 focal 校验信号作为统一闸门 —— ⏳ 未做。v0.6.3 开放前排查（[验收记录 §5](./acceptance-records/cover-calligraphy-title-v1-w2-whitelist-expand-2026-08-07.md#5-前瞻审计开放前排查其余风格的-css-暗坑2026-08-07-追加)）发现 `folio-overlap` 两条候选矩形均不能直接套用贴纸流程（候选 #0 被 `__place` 地点标签占用；候选 #1 横跨纸面/骑缝渐变照片两种背景且冲突原生双色断字设计），新增 **OQ-CAL-09**，不再按原计划走"矩形派生+翻开关"直给流程。白名单开放顺序：`band-cut` ✅ → `contact-stamp` ✅ → `folio-overlap`（⚠️ 阻断，见 OQ-CAL-09）→ `veil-footer`（收紧现有矩形/接入 focal 校验）→ `scroll-head`（暂缓，待竖排模板能力） |

---

## 4. 标题文案合同（BLK-CAL-02）

| 项 | 规格 |
|----|------|
| **主串来源** | 默认 `trip.meta.title`（与 `cover-opening.hbs` 的 `{{title}}` 同源） |
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
| `ZhiMangXing-Regular.ttf` | SIL OFL | 默认可入池 |
| `Aa剑豪体.ttf` | 待核查 | 核查通过前不得生产默认 |
| `鸿雷板书简体-测试版.ttf` | 待核查 + 确认非仅测试版 | 同上 |

### 5.4 Opening 白名单与 placement preset（BLK-CAL-04；v0.6 更新见 D-CAL-20）

| `coverOpeningStyle` | V1 状态 | placement preset（v0.6 更新：应对齐 registry `text_safe_regions`） |
|---------------------|-----|-------------------------|
| `veil-footer` | **白名单 · 首发**；现有矩形有主体碰撞风险，待修复 | 现矩形 `{x:0.08,y:0.14,w:0.84,h:0.22}` 与 `prefer.focal_y_max:0.55` 冲突；W2 收窄或接入 focal 校验 |
| `folio-overlap` | **白名单 · 可选第二款**（默认关） | ⚠️ v0.6.3 排查发现两条候选矩形均不能直接套用贴纸流程（候选 #0 被地点标签占用；候选 #1 横跨纸面/骑缝渐变照片两种背景，且冲突原生双色断字设计），见 OQ-CAL-09；**暂缓开放，不再是简单的"派生矩形+翻开关"** |
| `band-cut` | ✅ **白名单 · v0.6.1 新开**（真实 trip 视觉核对通过） | registry `{x:0,y:0.60,w:0.55,h:0.14}`，实测与真实断带位置（`--cover-band-center:63%`）精确吻合 |
| `contact-stamp` | ✅ **白名单 · v0.6.1 新开**（临时改风格核对通过，仓内暂无真实样例） | registry 左块 `{x:0,y:0.72,w:0.55,h:0.28}`（仅占左块，避让右块 hook/archive） |
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

**模型子选型（v0.4.0 · D-CAL-18 更新）**：2026-08-07 用户提供真实 Key 现场实测「拾光」二字——`wanx2.1-t2i-turbo` 出现「光」字形笔画错误；`wanx2.1-t2i-plus` 实测字形正确。据此 `route_c.py` **默认模型定为 `wanx2.1-t2i-plus`**（`turbo` 成本/速度更优但字形风险更高，仅作显式指定时的备选，不作默认）。⚠️ 这只是 2 组标题的现场抽测，**不等同于** §11 W0.5 里程碑要求的 20～30 条系统性样本验证，见 OQ-CAL-07。

#### 5.5.5 待验证事项（v0.4.0 更新：路线 C 已实现但默认关闭，以下仍是「正式默认开启」前的门槛）

| 事项 | 状态 |
|------|----------|
| 字形准确率（尤其生僻字/多笔画字） | ⚠️ 未完成完整 Spike——仅 2026-08-07 现场实测 2 组标题（见 v0.4.0/D-CAL-18）；正式开启 `route_c_enabled` 前须补齐 20～30 条真实/边界标题系统性验证 |
| 单次生成成本与延迟 | 未系统统计；仅有单次调用的定性观察 |
| 内容审核拒绝率 | 未系统统计 |
| 5 款风格的具体 `promptTemplate` 文案定稿 | ✅ 已定稿，见 §5.5.1 与 `style_registry.py` |
| OCR 回读校验机制 | ✅ 已实现（`ocr_verify.py`，复用 `vision_chat_completion` + `qwen-vl-plus`），但校验通过率阈值（AC-CAL-11）尚未用大样本钉定 |
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

**v0.6 更新（D-CAL-20，W2 待落地，本版未改代码）**：`placement preset 矩形`（信号 3）不应继续由 `whitelist.py` 手搓维护，应改为直接读取该 `coverOpeningStyle` 在 Cover Style Registry 中的 `text_safe_regions`（`travelogue/cover_engine/catalog.py`）；风格有多个候选区域时（如 `folio-overlap`/`contact-stamp`），四项信号应对每个候选逐一打分，取最高分而非固定绑死一个矩形。此外建议新增第 5 项信号：**该候选区域是否落在本风格自身既有文案（hook/trip-meta/archive-strip）的实际渲染范围内**——`text_safe_regions` 只保证避开镜头主体，不保证未被现有文案占用，这正是 v0.5 视觉验收发现重叠问题的根因之一；可直接复用 `opening/title_safe.py::mark_title_safe` 已经计算的 focal 校验结果作为落地前的统一闸门，避免选图与选位置两套逻辑对同一张照片给出矛盾结论。

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
      "mainSource": "meta.title",
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
| **归因** | 「使用你的照片装帧 · 未生成风景」+ 按实际引擎区分文案：路线 B 展示时用「标题为**程序化字库合成**，非 AI 绘图」；**路线 C 展示时须改为**「标题字迹由 AI 书法风格生成」（v0.3 新增，不得沿用路线 B 文案掩盖生成事实）。若未来印章来源变更，须单独注明，不得混称「全非 AI」而掩盖生成素材 |

---

## 11. 里程碑

| 里程碑 | 交付 | 门禁 |
|--------|------|------|
| **W0** | PRD v0.2 + 七席 BLK 关闭；v0.3 新增路线 C 候选设计 | ✅ |
| **W0.5**（不占用工程排期，先于启动触发） | 路线 C 技术验证 Spike：通义万相为主，即梦（若可申请）/腾讯混元陪跑；用 20～30 个真实/边界标题（含生僻字）测字形准确率（OCR/人审）+ 成本 + 延迟 + 审核拒绝率 | ⚠️ **未完整完成**——仅现场实测 2 组标题（v0.4.0），得出「plus 优于 turbo」的方向性结论，**不足以**支撑 20～30 条样本量的正式验收；`route_c_enabled` 配置默认仍为 `false` |
| **启动触发** | 产品显式拉起 **「封面装帧增强」** 窗口 | ✅ **2026-08-07 已拉起**（本次对话）；不绑定 AIR |
| **W1**（**Kickoff · 开发中**，分支 `feat/cover-calligraphy-title-v1`） | `cover_engine/title_art/` 干净管线（路线 B）+ 授权字库 + 自制/公版印章；固定配色/位；`meta.titleArt`；仅 `veil-footer`；路线 C 引擎 + 风格库 Registry（初始 5 款）同步实现（因 W0.5 未完整完成，`route_c_enabled` 默认关闭，代码路径已具备） | ✅ 代码已落地：`travelogue/cover_engine/title_art/` 全模块 + CLI `title-art` + 渲染表面 §7 接入 + 83 条单测；✅ AC-CAL-03/07/08/09/12 已用真实素材人工核对（见 [W1 视觉验收](./acceptance-records/cover-calligraphy-title-v1-w1-visual-review-2026-08-07.md)，过程中发现并修复 3 处集成缺口）；⏳ AC-CAL-11 仍待完整 W0.5 Spike |
| **W2** | placement_score + 自动配色（路线 B/C 共用，已随 W1 一并落地）；`enabled` 默认 false；按 D-CAL-20 顺序开放白名单：✅ ① `whitelist.py` 改为从 `text_safe_regions` 派生 preset（不再手搓矩形，v0.6.1）✅ ② 开 `band-cut`（v0.6.1）✅ ③ 开 `contact-stamp`（v0.6.1）⚠️ ④ 开 `folio-overlap` —— 开放前排查（v0.6.3）发现两条候选矩形均不能直接套用，改列为 OQ-CAL-09 待专门方案 ⏳ ⑤ 修复 `veil-footer` 现有矩形（接入 `mark_title_safe` focal 校验）；`scroll-head` 暂缓 | AC-CAL-01～06、09、13（待补验收记录）；band-cut/contact-stamp 视觉核对 + folio-overlap 排查见 [W2 验收记录](./acceptance-records/cover-calligraphy-title-v1-w2-whitelist-expand-2026-08-07.md) |
| **W3** | 盲评：现网 CSS Opening 标题 vs `titleArt=on`（含路线 B/C 分别对比）≥55% | AC-CAL-BLIND（未开始） |

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
| **OQ-CAL-06**（v0.3 新增） | 路线 C 何时从「候选」升级为「默认主路径」？ | 倾向：W0.5 Spike 通过 **且** W3 盲评达标才可；否则长期作为可选高级项，不默认开启 |
| **OQ-CAL-07** | 路线 C 的 5 款风格 `promptTemplate` 具体文案何时定稿？ | ✅ **已关闭（v0.4.0）**：5 款已定稿，见 §5.5.1 与 `style_registry.py`。**新开放问题**：W0.5 完整 Spike（20～30 条真实/边界标题系统性验证）何时补齐？— 在此之前 `route_c_enabled` 保持默认 `false`，不建议默认对用户开启 |
| **OQ-CAL-08**（v0.6 新增） | `whitelist.py` 改为从 `text_safe_regions` 派生后，是否需要保留一份「CAL 专属排除子区域」标注（用于扣除被 hook/trip-meta/archive 占用的部分），还是直接靠 `mark_title_safe` 的 focal 校验兜底即可？ | 倾向：W2 先只接 focal 校验（成本低，复用现成信号）；若上线后仍观测到与文案重叠的案例，再补排除子区域标注 |
| **OQ-CAL-09**（v0.6.3 新增） | `folio-overlap` 如何安全开放？候选 #0（左纸列）被 `.cover-opening__place` 地点标签常驻占用；候选 #1（此前拟用矩形）横跨纸面纯色栏 / 骑缝渐变照片区两种背景，且原生 `<h1>` 用双色 `clip-path` 叠字实现"书名骑缝切开压进画面"效果，单色贴纸做不出来 | 倾向：不复用 band-cut/contact-stamp 的直给流程；需要专门方案（如矩形收窄到只落纯纸面栏内并让开 `__place`，或做双色渡色贴纸）定案后再开放，见 [W2 验收记录 §5.4](./acceptance-records/cover-calligraphy-title-v1-w2-whitelist-expand-2026-08-07.md#54-新发现folio-overlap-两条候选矩形都不能直接套用同一套贴纯色-png-流程oq-cal-09) |

### 12.3 验收（AC-CAL-*，Kickoff 后生效）

| ID | 断言 |
|----|------|
| **AC-CAL-01** | `enabled=false`（或无字段）时 Opening ≡ 现网 HTML/CSS 金样 |
| **AC-CAL-02** | 干净管线输出对照证据②；W1 起可用固定 fixture + 感知哈希容差（SHD-CAL-01） |
| **AC-CAL-03** ✅ | 代码审查：无 brush_effects / engine v3/v4 生产路径（[核对记录](./acceptance-records/cover-calligraphy-title-v1-w1-visual-review-2026-08-07.md)） |
| **AC-CAL-04** | 测试集封面上对比度达书面阈值（W2 钉数） |
| **AC-CAL-05** | placement 遮挡主体显著区 ≤35%（自测口径） |
| **AC-CAL-06** | 默认路径无用户参数即可完成生成与叠加 |
| **AC-CAL-07** ✅ | 生产字库/印章均有授权或公版溯源记录（核对时发现 `ZhiMangXing-Regular.ttf` 未随包分发导致生产环境不可加载，已修复 + 补 `LICENSE-NOTES.md`，见验收记录 §1.1） |
| **AC-CAL-08** ✅ | 缺字形或非白名单 style → 不叠加贴纸且 h1 可见正常（真实非白名单 trip 实测通过） |
| **AC-CAL-09** ✅ | 修改 `meta.title` 后 `stale`（或等价）生效，禁止继续展示旧文案贴纸为「已更新」（核对时发现 `mark_title_art_stale` 从未接线，`copy_patch.py` 改标题不会置 stale——已修复 + 端到端验证 + 3 条回归测试，见验收记录 §1.3） |
| **AC-CAL-10** | Web 预览与长图引用同一 `assetPath` |
| **AC-CAL-11**（v0.3 新增 · 路线 C 生效） | 路线 C 输出的 OCR 回读校验通过率达 W0.5 Spike 钉定阈值方可进入生产候选池；未达标不得默认启用 |
| **AC-CAL-12** ✅（v0.3 新增 · 路线 C 生效） | 路线 C 失败（超时/审核不过/OCR 不过）→ 必定按 D-CAL-16 降级路线 B 或 fail-open HTML，**不允许**任何情况下展示错误态或半成品贴纸（真实条件下——未设置 `DASHSCOPE_API_KEY`——强制路线 C 实测通过） |
| **AC-CAL-13**（v0.3 新增 · 路线 C 生效） | 路线 C 抠字重上色结果同样满足 §6.1 对比度合同，默认兜底白色路径可复现 |
| **AC-CAL-BLIND** | vs **现网 CSS Opening 标题**（非 CAD Mode A）偏好 ≥55% 才可默认 `enabled=true`（路线 B/C 分别计） |

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
