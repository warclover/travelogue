# Travelogue · Cover Art Direction V1 产品需求文档（PRD）

| 属性 | 内容 |
|------|------|
| **产品代号** | Travelogue Studio |
| **文档版本** | **v0.1.0** |
| **状态** | **Draft · Ready for Review** |
| **DOC-STATUS** | **active** |
| **主题代号** | 「封面装帧导演」— **CAD**（Cover Art Direction） |
| **触发来源** | 2026-07-29 产品策略：用户期望「AI 封面/封底」，但章程与信任要求**真照片优先**；用装帧导演替代默认文生图假景点 |
| **前置条件** | [PRD-BOOKENDS-ENGINE-V1](./PRD-BOOKENDS-ENGINE-V1.md) Opening/Closing 可换图换样式；Cover Styles V6 Registry 可用；`pick_cover_asset_id` / closing 解析稳定；Studio「封面与封底」合页可预览 |
| **关联文档** | [PRD-BOOKENDS-ENGINE-V1.md](./PRD-BOOKENDS-ENGINE-V1.md) · [PRD-COVER-STYLES-V6.md](./PRD-COVER-STYLES-V6.md) · [cover-selection-plan.md](./cover-selection-plan.md) · [PRD-PHASE23-peak-moment.md](./PRD-PHASE23-peak-moment.md) · [DESIGN-PHOTO-AESTHETIC-EVALUATION.md](./DESIGN-PHOTO-AESTHETIC-EVALUATION.md) · [PRD-HERO-INTEREST-TASTE-V1.md](./PRD-HERO-INTEREST-TASTE-V1.md) · [PRD-AI-RETURN-V1.md](./PRD-AI-RETURN-V1.md) · [CHARTER.md](./CHARTER.md) |
| **验收** | Kickoff 后拆 `ACCEPTANCE-COVER-ART-DIRECTION-V1.md`；本文 §10 为源 |
| **实施清单** | Kickoff 后拆 `IMPLEMENTATION-COVER-ART-DIRECTION-V1.md` |
| **更新日期** | 2026-07-29 |

> **定位**
>
> CAD 解决「第一眼 / 最后一眼」的**装帧完成度**，不是用文生图伪造旅行。  
> 导演对象 = **用户实拍照片 × 开屏/封底样式 × 裁切重心 × 字色字重遮罩 ×（可选）非风景装饰层**。  
> 与 Bookends 关系：**扩展决策与 Studio 导演面**，不另起平行选图引擎；不接管正文 Screen Planner。
>
> **一句话目标**：用户一键得到「更像杂志封面」的真照片成稿；需要创意时，只能显式打开装饰/插画模式，且**默认路径永远是真照片**。
>
> **战略原则（拟冻结）**
>
> 1. **真照片默认** — Opening / Closing 主视觉像素必须来自 trip 资产（或用户显式上传替换）。  
> 2. **禁止假景点默认** — 文生「当地风景 / 地标写实」不得作为默认封面或封底。  
> 3. **规则 + 可选轻模型** — V1 以可解释规则 / 既有 cover score 为主；MLLM 短名单重排默认 **关**。  
> 4. **装饰可生成、风景不可冒充** — 纸纹、粒噪、抽象雾、邮戳、路线线稿允许；写实风景/人脸生成禁止默认。  
> 5. **可解释可改** — 每次自动导演须可展示「为何这张 / 可换图 / 可换样式」。  
> 6. **与 HIT 分工** — HIT 管拼图主槽品味；CAD 管书衣（封面封底）装帧。公式可复用，开关与 AC 分离。

---

## 0. 读者指南

| 章节 | 澄清什么 |
|------|----------|
| §0.1 | 术语与模式 |
| §0.2 | 相邻边界 |
| §1 | 背景与问题 |
| §2 | 目标 / 非目标 |
| §3 | 冻结决策 D-CAD-* |
| §4 | 导演管线与模式规格 |
| §5 | 数据模型 |
| §6 | Studio 体验 |
| §7 | 生成装饰（可选） |
| §8 | 里程碑 |
| §9 | 风险与 OQ |
| §10 | 验收 AC-CAD-* |

### 0.1 术语

| 术语 | 含义 |
|------|------|
| **Opening** | 封面：图 × `coverOpeningStyle` |
| **Closing** | 封底：图 × 封底样式 / Colophon |
| **Art Direction Decision** | 一次导演结果：assetId、styleId、crop/focal、typeTheme、overlay、decor（可选） |
| **Mode A · 智能装帧** | 默认：真照片 + 样式 + 裁切 + 字色；无文生图 |
| **Mode B · 装饰底** | 可选：抽象/纸纹等非写实底，照片仍叠真图 |
| **Mode C · 插画封底** | 可选：路线/邮戳/城市剪影等矢量或可控生成；**不得**替换为写实假风景主图 |
| **Mode D · 文生写实风景** | **V1 禁止作为产品默认或推荐项** |
| **双封面** | `public` / `private` 两套 Opening 决策（脸敏感分流） |

### 0.2 相邻边界

| 主题 | CAD 拥有 | CAD 不碰 |
|------|----------|----------|
| **Bookends** | 导演字段、合页「一键优化装帧」、装饰层合同 | 不推翻 B1/B2 挂点与 Pairing 硬规则；扩展而非分叉引擎包 |
| **Cover Styles V6** | 样式选择策略可加权 | 不删 Registry 五款；不重做 CSS 基线除非 AC 要求 |
| **HIT / PA** | 可复用 `purpose_overall("cover")` 等 | 不改 mosaic main eligibility |
| **AIR** | 封面钩子文案仍由 narrate/用户；CAD 可读 hook 做压字避让 | 不负责渠道包 |
| **P23 Moment** | 封底可避开 moment 主图（软） | 不重做 peak 池算法 |

---

## 1. 背景与问题

### 1.1 As-Is

| 能力 | 现状 | 缺口 |
|------|------|------|
| 封面选片 | `cover_scoring_v2` / Bookends | 「技术合格」多于「装帧感」；用户难理解为何选这张 |
| 开屏样式 | V6 五款 + joint | 缺「一键导演」把图×字×遮罩当一次决策 |
| 封底 | Closing + Pairing | 收束感弱；少「旅程护照」类完成度 |
| 市场预期 | 用户口头要「AI 出封面」 | 若上写实文生图 → 信任与「这是我的旅行」冲突 |
| MLLM | Bookends 默认关；遗留 logit boost | 未产品化为短名单重排开关 |

### 1.2 问题陈述（P-CAD-*）

| ID | 问题 | 严重度 |
|----|------|--------|
| **P-CAD-01** | 「AI 封面」若做成假风景，伤害本地真实游记定位 | 阻塞 |
| **P-CAD-02** | 选图与样式、压字、裁切割裂，用户要多次试错 | 严重 |
| **P-CAD-03** | 缺可解释「为何这张封面」 | 中等 |
| **P-CAD-04** | 公开分享与私密正脸未分流 | 中等 |
| **P-CAD-05** | 装饰层与真照片图层契约未定义，易做成脏贴图 | 中等 |

---

## 2. 目标与非目标

### 2.1 目标（In Scope）

| ID | 目标 |
|----|------|
| **G-CAD-01** | 定义 **Mode A** 默认导演管线：选图 → 样式 → focal/crop → typeTheme → 压字安全 |
| **G-CAD-02** | Studio 合页提供 **「优化装帧」** 与解释条；可换图/换样式/锁定 |
| **G-CAD-03** | 产出结构化 `artDirection` 决策，写入 trip，渲染可消费 |
| **G-CAD-04** | 明确 **Mode B/C** 为可选增强；**Mode D 禁止默认** |
| **G-CAD-05** | **双封面（W2）**：`audience=public|private` 两套 Opening，一键切换 |
| **G-CAD-06** | 与 Bookends Pairing 兼容：导演不得违反成对硬规则；冲突时提示重选 |
| **G-CAD-07** | 盲评：Mode A vs 现网 Bookends 默认，偏好 ≥55% 才可默认开导演 |

### 2.2 非目标（Out of Scope · V1）

| 不做 | 理由 |
|------|------|
| 默认文生写实风景/地标封面 | 信任；P-CAD-01 |
| AI 换脸、美颜、身份替换 | 伦理与检测成本 |
| 正文拼图 / hero HIT 默认逻辑 | HIT 另轨 |
| 完整 Admin 样式工场 | Bookends 已否 |
| 官方云端渲染农场 | 本地优先 |
| 自动重绘用户人脸或证件 | 隐私 |

### 2.3 成功画像

| 角色 | 成功 |
|------|------|
| **分享者** | 点一次「优化装帧」，封面更像杂志，仍认出是自己的照片 |
| **谨慎用户** | 能看到「使用了你的照片 · 未生成风景」；可选关闭装饰 |
| **工程师** | Decision 可测、可金样；与 Bookends 挂点单一 |

---

## 3. 冻结决策（D-CAD-*）

| ID | 决策 | 说明 |
|----|------|------|
| **D-CAD-01** | **默认 Mode A** | 新导入 / 「优化装帧」默认只跑 A |
| **D-CAD-02** | **Mode D 产品禁止默认** | UI 不提供「生成当地风景封面」主按钮；若未来实验须独立 flag + 水印「AI 生成 · 非实拍」+ 默认关 |
| **D-CAD-03** | **主视觉像素来源** | Opening/Closing **hero 图层** = `assetId` 指向实拍（或用户替换文件）；装饰层不得盖住 >35% 主体显著区（可配） |
| **D-CAD-04** | **引擎落点** | 扩展 `cover_engine` / Bookends facade；**禁止**新建平行 `ai_cover_engine` 包 |
| **D-CAD-05** | **MLLM** | V1 默认 off；可选对 cover top-K（≤8）缩略重排 + 一句 reason；fail-open |
| **D-CAD-06** | **HIT 公式复用** | 允许复用 beauty×interest 思想于封面合格集，但配置键独立（如 `bookends.art_direction`），默认变更须过 CAD 盲评 |
| **D-CAD-07** | **压字** | 继承 Bookends 压字硬闸分期；导演必须尊重 `textSafe`；不安全则换样式或降字号策略，禁止硬叠不可读 |
| **D-CAD-08** | **双封面** | W1 可只做数据预留；W2 交付切换；`private` 允许正脸；`public` 降权大脸 / 优先风景或背影 |
| **D-CAD-09** | **封底护照页** | W2 可选模板：统计 + 路线折线 + 小图；折线用 GPS/地名，**不**文生假地图照片 |
| **D-CAD-10** | **发布门禁** | `art_direction.enabled` 可先 merge 默认 false；默认 true 须 AC-CAD-BLIND ≥55% |
| **D-CAD-11** | **AIR 解耦** | 无 Key 亦可跑 Mode A；装饰生成若需云 API，须 L1 且默认关 |
| **D-CAD-12** | **用户锁** | 用户手动锁定的 cover/closing asset 或 style，优化装帧不得静默覆盖（可提示「已锁定 · 仅调字色」） |

---

## 4. 导演管线与模式规格

### 4.1 Mode A · 智能装帧（默认）

```text
candidates = cover_score 短名单（既有 top-N）
    → （可选）MLLM 重排  [default off]
    → pick assetId
    → pick openingStyle（Registry × 图特征联合，复用/扩展 joint）
    → resolve focalPoint / crop for layout（mobile/web）
    → typeTheme = { titleColor, metaColor, veilStrength } from luma/palette
    → textSafe check → 不行则 fallback style 或 veil
    → emit ArtDirectionDecision + explain[]
```

**explain 示例（用户可见，短）**

- 「横图、天空干净，适合雾底书名」  
- 「人脸偏左，选用右下书名卡」  
- 「与封底已避开同一张」

### 4.2 Mode B · 装饰底（可选）

- 输入：主色 / 季节标签 / 影调。  
- 输出：抽象渐变、纸纹、粒噪、雾；**禁止**可辨认地标写实。  
- 合成：装饰在照片下或侧栏；hero 仍为实拍。  
- 需显式开关「添加纸感装饰」；默认关。

### 4.3 Mode C · 插画封底（可选）

- 路线折线、邮戳、日期章、极简城市剪影（几何/SVG 优先）。  
- 若用生成模型：仅矢量/扁平插画 prompt；输出须过「非写实风景」抽检。  
- Colophon 文案仍走 stub/AIR，不由 CAD 编故事。

### 4.4 Mode D · 写实文生风景（禁止默认）

- V1：**无入口**或仅 `TRAVELOGUE_CAD_EXPERIMENTAL=1` 工程旗标。  
- 任何曝光路径必须：水印「AI 生成 · 非实拍」+ 不可设为 trip 默认 Opening。

### 4.5 双封面（W2）

| audience | 选图倾向 | 用途 |
|----------|----------|------|
| **private** | 允许合影正脸、高回忆 | 家庭相册、私密预览 |
| **public** | 降权大脸清晰正脸；风景/背影/细节 | 发群、小红书、外链 |

切换只换 Opening Decision（及可选 hook 是否显示人名）；不强制重跑全文 curate。

---

## 5. 数据模型（示意）

写入 `trip.meta` 或 Bookends Decision 扩展（IMPLEMENTATION 定权威字段名）：

```json
{
  "artDirection": {
    "version": 1,
    "mode": "A",
    "enabled": true,
    "opening": {
      "audience": "public",
      "assetId": "...",
      "styleId": "veil-footer",
      "focal": { "x": 0.42, "y": 0.38 },
      "typeTheme": { "titleColor": "#f7f2ea", "veilStrength": 0.55 },
      "explain": ["横图留白足，适合雾底书名"]
    },
    "closing": {
      "assetId": "...",
      "template": "colophon" | "passport",
      "decor": null
    },
    "locks": { "openingAsset": false, "openingStyle": false },
    "byAudience": {
      "private": { "assetId": "...", "styleId": "..." },
      "public": { "assetId": "...", "styleId": "..." }
    }
  }
}
```

渲染：`cover-opening.hbs` / closing 模板读 Decision；无字段时行为 ≡ 现网 Bookends。

---

## 6. Studio 体验

### 6.1 合页「封面与封底」

| 元素 | 规格 |
|------|------|
| 主按钮 | 「优化装帧」（Mode A） |
| 次级 | 「添加纸感装饰」（Mode B，默认折叠） |
| 解释 | 1～2 句 explain；链「换封面图」「换样式」 |
| 锁定 | 锁定图 / 锁定样式 |
| 双封面 | W2：「公开分享封面 / 私密封面」切换 |
| 归因 | 固定脚注：「使用你的照片装帧 · 未生成风景」 |

### 6.2 忙碌与失败

- 导演中：局部 loading，不阻断正文预览滚动。  
- 失败 fail-open：保留原 Bookends 结果 + toast「装帧未更新」。

### 6.3 Help

- 复用 / 扩展 H6「怎么换封面封底」：补充「优化装帧」与「不会 AI 假风景」一句。

---

## 7. 生成装饰（可选实现约束）

| 项 | 合同 |
|----|------|
| 运行位置 | 优先本机程序化（噪点/渐变/SVG）；云 API 仅 Mode B/C 且默认关 |
| 缓存 | 按 `tripId + palette sig + mode` 缓存衍生层，不写回用户相册原图 |
| 导出 | 长图 / HTML 须嵌入已合成结果或可解析层；禁止导出后丢装饰却留「已优化」态 |
| 水印 | Mode B/C **不**强制「AI 生成」大水印；Mode D 强制 |

---

## 8. 里程碑

| 里程碑 | 交付 | 门禁 |
|--------|------|------|
| **W0** | PRD 评审；与 Bookends 字段所有权签字 | Review Go |
| **W1** | Mode A 决策 + explain + Studio「优化装帧」+ `enabled` 默认 false | AC-CAD-01～08 |
| **W2** | 双封面 + 护照封底模板 + Mode B 程序化装饰 | AC-CAD-09～12 |
| **W3** | 盲评 ≥55% → 考虑默认 on；Mode C SVG 路线；文档封板 | AC-CAD-BLIND · Done |

MLLM 短名单为 **W2 可选**，不挡 W1。

---

## 9. 风险与开放问题

### 9.1 风险

| 风险 | 缓解 |
|------|------|
| 用户仍索要「AI 画一张当地」 | 产品文案引导装帧；Mode D 不给默认入口 |
| 装饰脏、廉价感 | Mode B 默认关；设计约束 ΔE/透明度 |
| 与 Pairing 冲突 | 导演后跑 pairing 校验；冲突提示 |
| 盲评不达标强开 | D-CAD-10 |

### 9.2 开放问题（OQ-CAD-*）

| ID | 问题 | 默认倾向 |
|----|------|----------|
| **OQ-CAD-01** | mobile 竖封面是否独立 typeTheme？ | 是，跟 `coverByLayout` |
| **OQ-CAD-02** | Mode B 是否进 Community 默认？ | 否，高级折叠 |
| **OQ-CAD-03** | 公开封面是否联动 AIR `family` 语气隐藏人名？ | W2 联调另议 |
| **OQ-CAD-04** | 护照封底是否依赖 GPS？ | 无 GPS 用 places 文字路线，不造假坐标 |

---

## 10. 验收（AC-CAD-*）

| ID | 断言 |
|----|------|
| **AC-CAD-01** | `art_direction.enabled=false` 时成书 ≡ 现网 Bookends（金样/回归） |
| **AC-CAD-02** | Mode A 输出 Decision 含 assetId + styleId + typeTheme；渲染可见差异或 explain |
| **AC-CAD-03** | Opening hero 像素可追溯至 trip `assets[]`（非文生写实主图） |
| **AC-CAD-04** | 默认可达 UI **无**「生成风景封面」主 CTA |
| **AC-CAD-05** | 压字不安全时不出现不可读书名（抽检样张） |
| **AC-CAD-06** | 用户锁定 asset 后，「优化装帧」不更换 assetId |
| **AC-CAD-07** | Pairing 硬冲突时有提示且不静默提交非法对 |
| **AC-CAD-08** | 无 LLM Key 时可完成 Mode A |
| **AC-CAD-09** | 双封面切换：`audience` 变化导致 opening asset 可不同（fixture 含大脸册） |
| **AC-CAD-10** | Mode B 开启时仍存在实拍 hero 层；抽检无「仅假风景」 |
| **AC-CAD-11** | 脚注「使用你的照片装帧 · 未生成风景」在合页可见 |
| **AC-CAD-12** | 导出长图含导演后 Opening（或文档声明的降级策略一致） |
| **AC-CAD-BLIND** | 偏好盲评 Mode A vs 基线 ≥55%（N 与册集 Kickoff 定）方可默认 enabled=true |

---

## 11. 附录

### A. 与「AI 出封面」话术对照

| 用户说的 | 产品做的 |
|----------|----------|
| AI 帮我做封面 | Mode A 装帧导演 |
| AI 画一张丽江 | **不做默认**；解释用你的丽江照片装帧 |
| 封面好看一点 | typeTheme + 样式 + 裁切 |
| 封底有仪式感 | 护照模板 / Colophon + Pairing |

### B. 修订记录

| 版本 | 日期 | 说明 |
|------|------|------|
| **v0.1.0** | 2026-07-29 | 初稿：Mode A/B/C/D 边界 · 双封面 · Bookends 扩展 · 盲评门禁 · AC-CAD |
