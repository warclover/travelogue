# 调研报告 · Photo / Zine Agent Skills 与 Travelogue 参考价值

| 属性 | 内容 |
|------|------|
| **DOC-STATUS** | active |
| **日期** | 2026-08-12 |
| **类型** | 外部 Skill 生态调研 + 对本项目映射分析 |
| **范围** | 摄影→编辑纸面（海报 / 明信片 / 抽象编辑页）类开源 Agent Skills |
| **关联现网** | [PRD-EXPORT-CARD-COMPOSE-V1](./PRD-EXPORT-CARD-COMPOSE-V1.md) · [PRD-COVER-CALLIGRAPHY-TITLE-V1](./PRD-COVER-CALLIGRAPHY-TITLE-V1.md) · [PRD-COVER-ART-DIRECTION-V1](./PRD-COVER-ART-DIRECTION-V1.md)（若存在）· ADR-021 |

---

## 1. 摘要

近一年 Agent Skills 生态里出现一批「把用户照片变成可收藏纸面作品」的规范包。它们大多不是可执行产品，而是 **SKILL.md + 版式约束 +（可选）prompt / 脚本**，依赖宿主的图像生成或本地渲染能力。

按「原图是否进入成品」可分成三条路线：

| 路线 | 一句话 | 代表 |
|------|--------|------|
| **A · 原图锚点** | 成品上方保留真实照片，下方做编辑层 | `photo-to-zine-postcard` · `photo-abstract-editorial` · gathered-scenes 实景拼贴 |
| **B · 语义蒸馏** | 照片只作语义来源，成品不含照片像素 | `scene-distillation-zine` · `photo-distill` · `gc-minimal-zine-poster`（多数模式） |
| **C · 功能明信片** | 正反面可邮寄结构 + 原图优先 | `photo-to-zine-postcard`（含背面） |

对本项目的核心判断：

1. **不宜直接替换**现有 ECC / Pillow 确定性导出管线（成本、可复现、合规均不匹配）。
2. **高价值在于版式语法与产品切口**：固定信息架构、留白纪律、主元素选择、色块合同、手绘/抽象注释层——可映射到「高光单页 / 封面装帧 / 分享面」的下一波策划。
3. **商用许可是硬门槛**：`photo-abstract-editorial` 与 `gathered-scenes-zine-skill` 均为个人非商用；产品内嵌或改写分发前必须授权。MIT 系（明信片、minimal zine poster、muted 变体）更适合作为可落地参考。

---

## 2. 调研对象总表

数据截至 2026-08-12（GitHub API）。

| Skill / 仓库 | Stars | License | 运行时 | 原图角色 | 成品形态 | skills.sh |
|--------------|------:|---------|--------|----------|----------|-----------|
| [LiamGvchi/gc-minimal-zine-poster](https://github.com/LiamGvchi/gc-minimal-zine-poster) | ~5.7k | MIT | Codex 生图 + 质检 | 可选（edit / reference） | 极简纸感竖海报 | 有（v0.1 / v0.3） |
| [Zeejay0/gathered-scenes-zine-skill](https://github.com/Zeejay0/gathered-scenes-zine-skill) | ~2.8k | 个人非商用 | Codex 生图 | 实景保留 **或** 仅语义 | 拾景纸刊海报 | 有 |
| [ZzzLc0405/photo-abstract-editorial](https://github.com/ZzzLc0405/photo-abstract-editorial) | ~2.7k | 个人非商用 | Codex 生图 | **必须保留** | 摄影区 + 抽象记忆面板 | 未见收录 |
| [Whiplashzeb/photo-to-zine-postcard](https://github.com/Whiplashzeb/photo-to-zine-postcard) | ~74 | MIT | ChatGPT / 通用生图 | **必须保留** | 2:3 明信片正+反 | 未见收录 |
| [Whiplashzeb/photo-to-zine-postcard-doubao](https://github.com/Whiplashzeb/photo-to-zine-postcard-doubao) | ~3 | 未标 | 豆包 Seedream | 保留正面 | 正面编辑页（强化验图） | 无 |
| [yangcodingmaster/photo-distill](https://github.com/yangcodingmaster/photo-distill) | ~55 | 方法/代码可自由用* | HTML/CSS/SVG + Chrome | 仅语义（成品无像素） | 本地可打印海报 | 无 |
| [moonlin1213/muted-zine-poster-v01](https://github.com/moonlin1213/muted-zine-poster-v01) | ~52 | MIT | 生图 | 主题/照片 | muted 低饱和海报 | 间接 |
| [notEhEnG/still-scenes](https://github.com/notEhEnG/still-scenes) | ~1 | MIT | Codex | 可保留 | 明信片 / 安静 zine | 无 |

\* `photo-distill` README：方法与代码随意使用；照片版权归作者。

---

## 3. 分 Skill 要点

### 3.1 Photo to Zine Postcard（Whiplashzeb）

**定位**：个人摄影 → 可打印 Zine 明信片正反面。

**版式合同（固定，禁止重设计）**

- 竖版 2:3，参考 100×150 mm，暖象牙白纸
- 正面：上半原图（保比例、细框）→ 大留白 → 左下元数据 → 右下一枚手绘主元素 → 恰好 3 个色块
- 背面：分割线 / 邮票区 / 地址线 / 留言区（可写）
- 主元素 **hand_drawn_first**；人脸/文字等才允许裁切回退

**工程形态**：单文件 `SKILL.md` + 定制指南；无脚本、无 API。针对 ChatGPT 生图优化，强调可 4× 超分。

**对本项目**：最清晰的「单张高光 → 可邮寄物件」产品叙事；MIT 可商用参考。背面合同对「真实社交物件」有启发，但与现网 3:4 ECC 比例不同，宜另开产品切片而非塞进 collage。

---

### 3.2 Photo Abstract Editorial（ZzzLc0405）

**定位**：原图 + **抽象记忆面板** + 诗意英文标题的竖向编辑作品。作者声明强调非滤镜、非风格迁移、非重绘原片。

**工作流摘要**

1. 内部提取 3–6 条空间事实（关系、轴、节奏、光色、留白）
2. 照片留在上方/主区，仅允许比例缩放或轻微构图裁切
3. 下方象牙平面重建为稀疏抽象母题（非缩略图、非描摹、非矢量图标）
4. ≤1 主标记族 + ≤2 辅族；调色仅来自照片
5. 仅一个原创英文标题（2–5 词）落在抽象面板；默认不返回分析文案

**护栏**：人物压成短竖向不规则块，禁止画脸手脚；地标最多 1–3 个身份线索。

**许可**：个人 / 教育 / 非商用；商业需授权。Stars 高、传播快，但**不能未授权进产品**。

**对本项目**：与 CAL「贴纸不换底图」同构——**实拍权威 + 派生装饰层**。抽象面板语法可启发「封面下缘 / 章节扉页 / 分享封套」的非摄影装饰，但实现应走自研确定性或自有模型链路，勿复制其 prompt 商用。

---

### 3.3 Gathered Scenes Zine（Zeejay0 · 拾景）

**双路径**

| 路径 | Skill 名 | 照片角色 |
|------|----------|----------|
| 实景拼贴 | `scenes-gathered-zine-v1-3` | 真实视觉锚 + 撕纸 / 高纯度色场 |
| 影像蒸馏 | `scene-distillation-zine-v1-3` | 仅语义与情绪，成品无原片 |

**美学原则**：真景为锚、插画成场、色彩成结构、纸面呼吸、边界有触感。另有站点 [zeejayzine.com](https://zeejayzine.com/)。

**许可**：个人非商用（与 abstract-editorial 同类风险）。

**对本项目**：双路径产品语言可借鉴（「保留现场」vs「重新想象」）。撕纸纤维、单一高纯度色锚适合作为 CAD / 封面方向的灵感，不宜整包嵌入。

---

### 3.4 GC Minimal Zine Poster（LiamGvchi）

生态里安装量与 Stars 最高的「安静极简海报」编译器。

- 默认 3:5 旧纸、70–90% 留白、单一高彩度色锚、印刷瑕疵词
- 模式：Generate / Photo Input / Reference Analysis / Prompt-only / Analyze+Generate
- 模块化 `references/` + quality-gate；MIT

**Muted 变体**（moonlin1213）：去掉高饱和锚点，走灰度/淡 wash，更日记/档案感。

**对本项目**：适合作为「意图→视觉系统」的参考架构（变量轴、反模式清单、质检清单），而非直接出用户资产。与现网「杂志封面 / 海报拼贴」气质有重叠但更 indie-print。

---

### 3.5 Photo Distill（yangcodingmaster）

**关键差异**：不用图像生成模型；手写 HTML/CSS/SVG + 无头 Chrome；成品零照片像素。

- 用户点名 2–3 元素；交互式改稿；`finalize_poster.py` 四项印刷指标 fail-closed
- 高饱和色锚面积脚本实测；真实 EXIF/机身参数上纸（禁编造）

**对本项目**：与 Travelogue「确定性渲染优先」（ADR-016 / ECC Pillow 路径）**最同构**。若未来要做「蒸馏海报 / 符号封面」而不烧生图成本，应优先研究此路径的设计系统 + 可测印刷指标，而不是扩散模型。

---

### 3.6 其他相关

- **still-scenes**：灵活明信片/安静 zine + 精确文案；体量小，可作补充阅读。
- **echtpost-postcards**（Membrane）：实体明信片投递 API skill，偏履约集成，不是视觉语言。
- **iMini / Toolaze 等在线封装**：多为 gathered-scenes / minimal-zine 的产品化壳，调研时注意与开源仓库许可是否一致。

---

## 4. 横向对比

### 4.1 设计语法

| 维度 | Postcard | Abstract Editorial | Gathered（实景） | Distillation | Minimal Poster | Photo Distill |
|------|----------|--------------------|------------------|--------------|----------------|---------------|
| 原图进成品 | 是 | 是 | 是 | 否 | 可选 | 否 |
| 下半区语言 | 手绘主元素 | 抽象关系面板 | 撕纸+插画色场 | 全幅纸刊插画 | 稀疏主题簇 | SVG 印刷符号 |
| 色系统 | 固定 3 swatch | 照片提取 muted | 单高纯度锚 | 表达优先 | 单高彩度锚 | 单色锚+实测 |
| 文字 | 极简元数据 | 英诗意标题 | 自由短文 | 自由短文 | 稀疏印刷字 | 档案微字+真实参数 |
| 背面 | 有 | 无 | 无 | 无 | 无 | 无 |
| 留白纪律 | 强 | 强 | 强 | 强 | 极强（70–90%） | 极强 |
| 质检 | checklist | checklist | 轻提示 | 直接交付倾向 | quality-gate | 脚本四项实测 |

### 4.2 工程与合规

| 维度 | 生图依赖 | 本地可复现 | 商用友好度 | 安装门槛 |
|------|----------|------------|------------|----------|
| Postcard | 高 | 低 | 高（MIT） | 低（贴 SKILL） |
| Abstract Editorial | 高 | 低 | **低（需授权）** | 低 |
| Gathered Scenes | 高 | 低 | **低（需授权）** | 中 |
| Minimal Poster | 高 | 低 | 高（MIT） | 中（Codex skills） |
| Photo Distill | 无（Chrome） | **高** | 方法可用 | 中（渲染环境） |

---

## 5. 对 Travelogue 的参考价值分析

### 5.1 现网能力锚点

| 现网模块 | 现状 | 与 Skills 的距离 |
|----------|------|------------------|
| ECC 导出卡片 | 3:4 确定性拼贴，纯图、无文案层 | 比例与叙事不同；Skills 偏「单张编辑页」 |
| 封面 Opening / Styles | 实拍底 + CSS 版式 | 已实践「底图权威」 |
| CAL 书法标题 | 透明贴纸叠加，不换主图 | 与 Abstract / Postcard「派生层」同构 |
| CAD / 封面艺术方向 | 策划层视觉系统 | 可吸收 minimal / gathered 的变量轴语言 |
| AI 叙事 / 意图 | 文本与布局批评为主 | 尚未有「单张照片→纸刊物件」出口 |

### 5.2 价值分层（建议采纳深度）

#### P0 · 可立即吸收为「设计合同语言」（不引依赖）

来自各 skill 的共识规则，可写入未来 PRD / UI Detail，无需 fork 仓库：

1. **原图权威**：不重绘、不扩图、不风格迁移底图（对齐 CAL D-CAL-06）。
2. **一主元素**：下半区只保留一个 source-defining motif，禁止样本网格 / keyword 墙。
3. **留白是结构**：中间静默带（Postcard / Abstract 的 14–18% 级空隙）是版式装置，不是待填充空白。
4. **色合同**：3 色（主色 / 结构暗色 / 浅中性）或单色锚；禁止时尚互补色胡编。
5. **元数据白名单**：title / location / date / index；缺省留空，禁止 `Unknown` 编造（与 share-face 纯度方向一致）。
6. **反模式清单**：Polaroid 框、厚卡纸阴影、样机桌面、圆角悬浮卡、徽章印章堆叠。

#### P1 · 产品切口候选（需独立 PRD，勿并入 ECC）

| 切口 | 灵感源 | 为何适合 Travelogue | 主要风险 |
|------|--------|---------------------|----------|
| **高光明信片包** | Postcard + Doubao 变体 | 游记「敢发」后的实体/数字礼物；正反面完整 | 生图成本；原图保真不稳定 |
| **抽象记忆扉页** | Abstract Editorial | 章节/画册书衣：实拍 + 关系抽象 | **非商用许可**；英诗意标题与中文产品语气 |
| **保留 vs 蒸馏双模式** | Gathered Scenes | Studio 一键：现场感 / 艺术再创作 | 许可；用户预期管理 |
| **符号蒸馏封面** | Photo Distill | 无生图、可测、可贴合现网确定性哲学 | 交互改稿重；与书法标题抢戏 |

#### P2 · 工程模式借鉴（架构级）

| 模式 | 来源 | 映射建议 |
|------|------|----------|
| Prompt 编译器 + variation-engine | Minimal Zine | 若做可选生图出口：意图 → 固定字段 prompt，而非自由文案 |
| Reference analysis 分 fixed/variable/residue | Minimal v0.3 | 可对齐「封面风格 profile / 可调变量」文档结构 |
| Fail-closed 印刷指标脚本 | Photo Distill | ECC / 导出 PNG 可增加 ink coverage、色锚面积等回归测 |
| 宿主能力自检 + 盲画协议 | Photo Distill | Desktop / 无视觉环境 agent 的改稿策略可复用 |
| Doubao 表面分流（Work Task vs 普通对话） | Postcard-doubao | 多模型出口时的「能力探测 → prompt 降级」 |

### 5.3 明确不建议做的事

1. **把任一非商用 Skill 的 SKILL.md / prompt 原文拷进仓库或发行包**（Abstract Editorial、Gathered Scenes）。
2. **用生图重做 ECC 三出口**：与 ADR-021「确定性 Compose」冲突，且成本/一致性不可控。
3. **让生图替换封面实拍主图**：与 CAL、Opening Registry 的产品承诺冲突。
4. **在无用户点名元素时全自动「蒸馏」整本游记**：Photo Distill 强调作者选择是方法一部分；批量会得到同质符号墙。

### 5.4 推荐落地顺序（若产品要开窗）

```text
阶段 0（本报告）     吸收 P0 设计合同进未来 PRD 术语表
阶段 1（Spike）      用 MIT 系 Postcard + Minimal 对 8–12 张真实 trip 高光做盲测
                     并行：Photo Distill 对同一批图做本地符号海报对照
阶段 2（许可）       若 Abstract / Gathered 气质胜出 → 商务授权谈判；否则自研同构规范
阶段 3（PRD）        「高光纸刊物件」独立 PRD：比例、是否生图、是否实体打印、与 ECC/CAL 边界
阶段 4（实现）       优先确定性路径（Distill 式或 Pillow 拼版）；生图仅作可选高级档
```

---

## 6. 与本项目气质的匹配度评分（主观）

评分 1–5，5 = 高度契合当前 Travelogue 方向（实拍叙事游记、可分享、可导出、确定性优先）。

| Skill | 视觉差异化 | 工程可落地 | 许可安全 | 用户故事清晰度 | 综合参考优先级 |
|-------|------------|------------|----------|----------------|----------------|
| photo-to-zine-postcard | 4 | 3（生图） | 5 | 5 | **高** |
| photo-distill | 5 | 5 | 4 | 4 | **高**（工程） |
| gc-minimal-zine-poster | 4 | 3 | 5 | 3 | 中高（规范） |
| photo-abstract-editorial | 5 | 2 | **1** | 4 | 中（灵感，先授权） |
| gathered-scenes | 5 | 2 | **1** | 5 | 中（灵感，先授权） |
| muted-zine-poster | 3 | 3 | 5 | 2 | 低 |
| still-scenes | 3 | 3 | 5 | 3 | 低 |

---

## 7. 结论

这批 Skills 证明市场对「旅行/日常照片 → 克制纸刊物件」有强烈审美共识：**实拍权威、大留白、单主元素、可追溯色彩、少字**。Travelogue 已在封面与导出侧具备「底图不撒谎」的产品基因；缺口是缺少一个 **单张高光的纸刊化出口**，以及把「派生装饰层」从书法贴纸扩展到更广义的编辑注释层。

最稳妥策略：

- **学合同、学反模式、学质检**（全员适用）；
- **商用实现优先 MIT + 确定性渲染**（Postcard 叙事 × Distill 工程）；
- **高星非商用库只作审美标杆**，产品化前完成授权或彻底自研同构。

---

## 8. 参考链接

- https://github.com/Whiplashzeb/photo-to-zine-postcard
- https://github.com/Whiplashzeb/photo-to-zine-postcard-doubao
- https://github.com/ZzzLc0405/photo-abstract-editorial
- https://github.com/Zeejay0/gathered-scenes-zine-skill
- https://github.com/LiamGvchi/gc-minimal-zine-poster
- https://github.com/yangcodingmaster/photo-distill
- https://github.com/moonlin1213/muted-zine-poster-v01
- https://github.com/notEhEnG/still-scenes
- https://skills.sh/
