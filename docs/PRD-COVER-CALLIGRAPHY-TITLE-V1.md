# Travelogue · 封面艺术字标题 V1 产品需求文档（PRD）

| 属性 | 内容 |
|------|------|
| **产品代号** | Travelogue Studio |
| **文档版本** | **v0.2.0** |
| **状态** | **Draft · Conditional Go（W0 策划已冻结）** · [七席评审](./acceptance-records/cal-cover-calligraphy-title-v1-review-2026-08-06.md) · **BLK-CAL-01～05 已回写** · **不 Kickoff** |
| **DOC-STATUS** | **planning-paused** |
| **主题代号** | 「点睛」— **CAL**（Calligraphy Title） |
| **触发来源** | 2026-08-06 产品讨论：用户希望游记封面标题达到「即梦」文生图那种手写体艺术感；经过对既有内部 demo（`arttext-miniapp`）的实证分析，确认了可落地路径 |
| **前置条件** | [CHARTER.md](./CHARTER.md) §7；[PRD-COVER-STYLES-V6.md](./PRD-COVER-STYLES-V6.md) Opening Registry 可用；现网 `cover-opening.hbs` / `meta.title` 可渲染。**不依赖** CAD 已落地（见 D-CAL-04 / D-CAL-09） |
| **关联文档** | [PRD-COVER-ART-DIRECTION-V1.md](./PRD-COVER-ART-DIRECTION-V1.md)（CAD · 姊妹策划，非硬依赖）· [PRD-AI-RETURN-V1.md](./PRD-AI-RETURN-V1.md)（AIR · **解耦**，CAL 不消耗 LLM）· [PRD-COVER-STYLES-V6.md](./PRD-COVER-STYLES-V6.md) · [PRD-CHAPTER-NAMING.md](./PRD-CHAPTER-NAMING.md) · [PRD-EXPORT-CARD-COMPOSE-V1.md](./PRD-EXPORT-CARD-COMPOSE-V1.md) · 证据 `docs/acceptance-records/attachments/cover-calligraphy-title-evidence-2026-08-06/` · [七席纪要](./acceptance-records/cal-cover-calligraphy-title-v1-review-2026-08-06.md) |
| **验收** | 启动开发时拆 `ACCEPTANCE-COVER-CALLIGRAPHY-TITLE-V1.md`；本文 §12 为源 |
| **实施清单** | 启动开发时拆 `IMPLEMENTATION-COVER-CALLIGRAPHY-TITLE-V1.md` |
| **更新日期** | 2026-08-06 |

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
> **战略原则（已冻结）**
>
> 1. **路线锁定：字库合成，不做实时文生图** — V1 100% 本地 Pillow 渲染，零 LLM / 零扩散模型调用。
> 2. **克制胜过堆砌** — demo 实证：干净合成 > 笔锋特效 > 骨架引擎；**越少干预越好**。
> 3. **移植优于重造** — 移植 `arttext-miniapp` 干净管线 + 补齐自动配色/定位与现网表面合同。
> 4. **画龙点睛，不是主视觉** — 文字装饰层 ≠ 伪造风景；与 Charter / CAD 信任叙事兼容。
> 5. **权利清晰** — 字库须商用授权；印章 V1 自制/公版，不移植 wanx 批次。
> 6. **本阶段不动代码** — `planning-paused`；仅在产品显式拉起「封面装帧增强」窗口时 Kickoff（**不**绑定 AIR）。

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
| §5 | 渲染管线规格（移植方案） |
| §6 | 自动配色与自动定位（自建 placement_score） |
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
| **干净管线** | 字体直出 → 副标 → 印章；**禁止**笔锋滤镜 / 骨架物理模拟 |
| **路线 A / Mode D · 文生图** | 扩散模型现场生成；**本 PRD 不实现** |
| **路线 B** | 字库合成；**本 PRD 实现路线** |
| **Opening 白名单** | 允许叠加贴纸的 `coverOpeningStyle` id 集合（§5.4 / D-CAL-10） |
| **placement_score** | CAL 自建的落点评分（亮度/留白/脸距）；**不**假设现网已有 `textSafe` API |

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

### 2.2 非目标

| 不做 | 理由 |
|------|------|
| 实时文生图 | 远期；另立 PRD |
| brush_effects / engine v3/v4 | D-CAL-02 红线 |
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
| **D-CAL-01** | **路线 = 字库合成** | 无文生图入口、无实验旗标 |
| **D-CAL-02** | **干净管线红线** | 仅三层合成；合入审查若出现笔锋滤镜 / 骨架引擎路径 → **拒收** |
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

## 5. 渲染管线规格（移植方案）

### 5.1 干净管线（唯一路径）

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

### 5.4 Opening 白名单与 placement preset（BLK-CAL-04）

| `coverOpeningStyle` | V1 | placement preset（示意） |
|---------------------|-----|-------------------------|
| `veil-footer` | **白名单 · 首发** | 贴纸偏上中或雾带上方留白区；避开底栏 meta |
| `folio-overlap` | **白名单 · 可选第二款**（默认关，W2 开） | 叠在 folio 题区约定矩形内 |
| 其它（含竖排/题带横切等） | **非白名单** | `titleArt` 不生效；HTML 标题照旧 |

非白名单时即使 `meta.titleArt.enabled=true`，渲染层也**必须**忽略贴纸（防错误叠加）。

---

## 6. 自动配色与自动定位

> demo 无此能力；且现网**无** CAD `textSafe`/`typeTheme` 实现 → V1 自建最小算法（D-CAL-13）。

### 6.1 自动配色

```text
封面资产 → 落点 ROI 局部亮度
    → 对比度不达标则换色（深/浅字）或半透明底衬
    → 仍不达标 → fail-open 不贴纸
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

| 条件 | 行为 |
|------|------|
| 无字段 / `enabled=false` / `stale=true` / 非白名单 style | ≡ 现网 HTML/CSS 标题 |
| CAD 未来落地 | 可将本对象**复制或引用**进 `artDirection.opening.titleArt`；迁移另笔，不挡 CAL W1 |

---

## 9. 素材权利与合规

| 项 | 要求 |
|----|------|
| 字库 | 商用授权核查留痕（`LICENSE-NOTES.md` 或等价） |
| 印章 | **V1 自制或公版**（D-CAL-12）；禁止默认入库 wanx 批次 |
| 追溯 | manifest / 拒收清单可查 |
| demo 仓 | `arttext-miniapp/` 仅分析参考；Kickoff 前建议移出主仓或 gitignore（SHD-CAL-04） |

---

## 10. Studio 体验（目标态）

| 元素 | 规格 |
|------|------|
| **默认路径** | 随「优化装帧」或等价一键触发；**零额外开关、零必点按钮** |
| **结果** | 直接反映在封面预览 |
| **L2 高级（可选 · SHD-03）** | 折叠区：「换版式」「换印章」；**非默认露出**；不提供手动画字/调笔锋 |
| **归因** | 「使用你的照片装帧 · 未生成风景」+「标题为**程序化字库合成**，非 AI 绘图」。若未来印章来源变更，须单独注明，不得混称「全非 AI」而掩盖生成素材 |

---

## 11. 里程碑（暂停 · 待启动）

| 里程碑 | 交付 | 门禁 |
|--------|------|------|
| **W0** | PRD v0.2 + 七席 BLK 关闭 | ✅ 本版 |
| **启动触发** | 产品显式拉起 **「封面装帧增强」** 窗口 | **不**绑定 AIR /「AI 能力建设」语义；零 LLM 亦可开工 |
| **W1** | `cover_engine/title_art/` 干净管线 + 授权字库 + 自制/公版印章；固定配色/位占位；`meta.titleArt`；仅 `veil-footer` | ≥3 文案贴纸；AC-CAL-03/07/08；表面合同最小路径 |
| **W2** | placement_score + 自动配色；`enabled` 默认 false；可选开 `folio-overlap` | AC-CAL-01～06、09 |
| **W3** | 盲评：现网 CSS Opening 标题 vs `titleArt=on` ≥55% | AC-CAL-BLIND |

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

### 12.2 开放问题（OQ-CAL-*）

| ID | 问题 | 状态 / 倾向 |
|----|------|-------------|
| **OQ-CAL-01** | mobile / 竖版独立版式？ | **收窄关闭**：V1 仅白名单 web Opening preset；mobile 延期 |
| **OQ-CAL-02** | 扩到章标题/长图分段？ | **维持否**：仅封面 Opening |
| **OQ-CAL-03** | 印章自制？ | **已关闭**：V1 自制/公版（D-CAL-12） |
| **OQ-CAL-04** | 远期文生图？ | **维持**：另立 PRD |
| **OQ-CAL-05** | ECC/Card 是否二期消费贴纸？ | 默认倾向：二期可选；不挡 V1 |

### 12.3 验收（AC-CAL-*，Kickoff 后生效）

| ID | 断言 |
|----|------|
| **AC-CAL-01** | `enabled=false`（或无字段）时 Opening ≡ 现网 HTML/CSS 金样 |
| **AC-CAL-02** | 干净管线输出对照证据②；W1 起可用固定 fixture + 感知哈希容差（SHD-CAL-01） |
| **AC-CAL-03** | 代码审查：无 brush_effects / engine v3/v4 生产路径 |
| **AC-CAL-04** | 测试集封面上对比度达书面阈值（W2 钉数） |
| **AC-CAL-05** | placement 遮挡主体显著区 ≤35%（自测口径） |
| **AC-CAL-06** | 默认路径无用户参数即可完成生成与叠加 |
| **AC-CAL-07** | 生产字库/印章均有授权或公版溯源记录 |
| **AC-CAL-08** | 缺字形或非白名单 style → 不叠加贴纸且 h1 可见正常 |
| **AC-CAL-09** | 修改 `meta.title` 后 `stale`（或等价）生效，禁止继续展示旧文案贴纸为「已更新」 |
| **AC-CAL-10** | Web 预览与长图引用同一 `assetPath` |
| **AC-CAL-BLIND** | vs **现网 CSS Opening 标题**（非 CAD Mode A）偏好 ≥55% 才可默认 `enabled=true` |

---

## 13. 附录：demo 证据与移植指针

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

---

## 修订记录

| 版本 | 日期 | 说明 |
|------|------|------|
| **v0.1.0** | 2026-08-06 | 初稿：字库合成 · 干净管线 · 暂停排期 |
| **v0.2.0** | 2026-08-06 | 七席回写 BLK-CAL-01～05：独立 `meta.titleArt` · 文案/表面合同 · V6 白名单 · 与 AIR 解耦 · 印章自制/公版 · placement_score · D-CAL-09～13 · AC-08～10 |
