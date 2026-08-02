# Cover Styles V6 · 艺术指导 Delta（CAD-Craft）

| 属性 | 内容 |
|------|------|
| **文档版本** | v1.1.0 |
| **状态** | **已批准 · 十款上架**（线框签字 2026-08-02；H–L active 2026-08-02） |
| **DOC-STATUS** | active |
| **母文档** | [PRD-COVER-STYLES-V6.md](./PRD-COVER-STYLES-V6.md) v1.3.0 |
| **视觉真相源** | [wireframes/cover-styles-v6-art-direction-v2-wireframe.html](./wireframes/cover-styles-v6-art-direction-v2-wireframe.html) |
| **对照旧稿** | [wireframes/cover-styles-v6-craft-refine-v1-wireframe.html](./wireframes/cover-styles-v6-craft-refine-v1-wireframe.html)（参数微调版，已否决为落地基线） |
| **关联** | [IMPLEMENTATION-COVER-STYLES-V6.md](./IMPLEMENTATION-COVER-STYLES-V6.md) · [ACCEPTANCE-COVER-STYLES-V6.md](./ACCEPTANCE-COVER-STYLES-V6.md) |
| **更新日期** | 2026-08-02 |

> **定位**：本 Delta **不是**新产品 PRD，也不是 [PRD-COVER-ART-DIRECTION-V1](./PRD-COVER-ART-DIRECTION-V1.md)（装帧导演）。  
> 它冻结「同五款 id、换视觉手法」的取舍与 token，并将五款新提案上架为 **active**（十款可分配）。  
> 冲突裁决：视觉以本 Delta + art-direction-v2 线框为准；产品契约（引擎 / 联合选型 / Schema 写入）仍以 V6 PRD 为准；**可分配集合以 `list_assignable_styles()` 为真相源**（本轮 = 十款）。

---

## 1. 已批准决议（D-CSV6AD）

| ID | 决议 |
|----|------|
| **D-CSV6AD-01** | 首五款 active id **不变**：`veil-footer` / `folio-overlap` / `band-cut` / `cameo-aperture` / `type-monument` |
| **D-CSV6AD-02** | P0 落地 = **整包替换五款 CSS pack**（`journal.css` token + ≥1024px 规则）；**不**拆 `cover-opening.hbs` 为多模板 |
| **D-CSV6AD-03** | 允许最小 HBS 增强：`data-title`、section 上 `--cover-src` / `--focal-*`（供叠印与镂空）；禁止样式专属 DOM 分支；diptych 仅可选第二 `cover-hero--secondary` |
| **D-CSV6AD-04** | 新提案 H–L 以 **`active`** 注册；进入联合选型 / Studio 主选择器 / schema 写入枚举（`list_assignable_styles()` = 十款） |
| **D-CSV6AD-05** | L `diptych-seam`：**已上架**。主图 + 可选 `meta.coverSecondaryAssetId`（人像副图）；无副图时 CSS 同源回落双联 |
| **D-CSV6AD-06** | 胶片颗粒 / 缓慢推移动效：**P1 可选**；P0 不做生产默认动画与噪点层 |
| **D-CSV6AD-07** | 窄屏 `<1024px` 仍仅 CSS 回落 `veil-footer` 呈现；attribute 不变 |
| **D-CSV6AD-08** | 视觉真相源切换：hi-fi-adefg → **art-direction-v2**（本轮 craft）；V6 产品 AC 编号沿用 |
| **D-CSV6AD-09** | 分配策略：联合最优（assignable × Top-K）为默认；hash 回落在十款上 `hash % n`；Studio 可手动任选 |

---

## 2. P0 五款 · 可命名动作（必须落地）

| id | 显示名 | 动作一句话 | 实现要点 |
|----|--------|------------|----------|
| `veil-footer` | 暮光题签 | 光从字后面渗出来 | 暖光 `::before` + 6 停点雾（高约 66–70%）+ 更大衬线书名 + place 引线 |
| `folio-overlap` | 骑缝叠印 | 字被纸缝真正切开 | 纸栏 ≈33%；书名 `background-clip` 墨/白切分；可选 `data-title` 套印红影；书脊阴影；去掉厚白卡 |
| `band-cut` | 断带切线 | 带子断了，切线没断 | 左缘纸标签渐隐（非通栏）；1px 切线贯穿；hook 出带压在照片上；中线 ≈ **63%** |
| `cameo-aperture` | 记忆焦点 | 圆外虚掉，圆内清醒 | 全幅摄影 + 圆形 mask 毛玻璃；圆心跟 `--focal-x/y`；竖排题名；去金环石青底 |
| `type-monument` | 镂空巨字 | 字不是墨，是窗 | 底图压暗；书名 `background-clip:text` + `background-attachment:fixed` 透出同图；对角 place/hook |

---

## 3. Token 变更表（相对 V6 §4.7）

| Token | 旧值（生产） | 新值（本 Delta） |
|-------|--------------|------------------|
| `--cover-veil-fog` | 4 停点 · 偏实 | 6–7 停点缓入 · 底更沉 |
| `--cover-veil-fog-height` | `48%` | `68%` |
| `--cover-veil-panel-max` | `min(680px, 74%)` | `min(520px, 56%)` |
| `--cover-veil-title-size` | `clamp(2rem, 3.8vw, 2.75rem)` | `clamp(2.1rem, 4.5vw, 3.5rem)` |
| `--cover-folio-margin` | `11%` | `33%` |
| `--cover-folio-panel-width` | `min(54%, 540px)` | `min(48%, 520px)`（题名可压出纸栏） |
| `--cover-folio-fade` | 厚实白卡感 | 更快淡出或几乎不用实卡 |
| `--cover-folio-title-size` | `clamp(2.35rem, 4.6vw, 3.35rem)` | `clamp(2.4rem, 6vw, 4.4rem)` |
| `--cover-band-center` | `78%` | `63%`（切线位置；AC 窗 **60%–66%**） |
| `--cover-band-pad` | 通栏条内边距 | 标签内边距；标签最大宽 ≈52% |
| `--cover-cameo-size` | 圆窗直径 | 改为 `--cover-cameo-r: min(32vh, 236px)`（半径） |
| `--cover-cameo-ground` | 石青径向 | `#101113` 中性底（全幅图为主） |
| `--cover-cameo-ring` | 金环三层 | `1px` 白环 + 内阴影 |
| `--cover-monument-title-size` | `clamp(3.4rem, 7.5vw, 5.4rem)` | `clamp(4rem, 14vw, 9rem)` |
| `--cover-monument-dim` | 中等暗罩 | 更重（底图 ≈ brightness .32 等效） |

新增（可选 token）：

| Token | 用途 |
|-------|------|
| `--cover-veil-glow` | 题字后方暖光径向 |
| `--cover-folio-cut` | 骑缝切分用长度（`33vw`） |
| `--cover-folio-ghost` | 套印红 `rgba(178,58,47,.35)` |
| `--cover-band-label-max` | 断带标签最大宽 |
| `--cover-src` | section 内联，封面图 URL（镂空/叠印） |

---

## 4. 新提案（active · 已上架）

| id | 名 | sort | 备注 |
|----|----|------|------|
| `scroll-head` | 卷首竖题 | 60 | 中式卷首；纯排版 |
| `portal-arch` | 天窗 | 70 | 拱形门洞 |
| `horizon-split` | 地平线 | 80 | 上图下纸；长标题友好 |
| `contact-stamp` | 日戳档案 | 90 | 需 EXIF 文案时可降级隐藏 |
| `diptych-seam` | 双联断字 | 100 | 可选副图 `coverSecondaryAssetId`；无副图同源回落 |

分配：`pick_cover_style_and_asset` 在十款上联合最优；hash 回落 `hash % 10`；Studio 十选一。

---

## 5. 空状态 / 回落

| 样式 | 约束 |
|------|------|
| folio | 标题 >6 字或折行 → 允许单色墨字（不切分）；无 hook 去 accent |
| band | 无 hook：仅标签；切线仍在 |
| cameo | 无 backdrop-filter 时回落暗罩挖圆；圆心缺省 50%/45% |
| monument | 无 `--cover-src` 时回落白字 + 暗罩（旧行为） |
| 长书名 monument | 仍 ≤3 行；过长联合选型应偏好 veil |
| diptych | 无 `coverSecondary` → 右栏用主图同源（CSS `::before`） |

---

## 6. 非目标（本 Delta）

- 不改联合选型公式权重（仅 profile 文案/适图区可微调；diptych 增加 scene+person pair 加分）
- 不做胶片颗粒 / Ken Burns 生产默认
- 不改 Mobile 封面；不改封底
- 不重开完整 Cover Styles V7 PRD

---

## 7. 验收要点（增量）

| ID | 则 |
|----|-----|
| **AC-CSV6AD-01** | 十款宽屏一屏无溢出（沿用 Playwright） |
| **AC-CSV6AD-02** | 窄屏回落 veil；attribute 不变 |
| **AC-CSV6AD-03** | `band-cut` 题带/切线中线 ∈ **[60%, 66%]** |
| **AC-CSV6AD-04** | `cameo` 宽屏为全幅+圆窗，非色底贴头像卡 |
| **AC-CSV6AD-05** | `type-monument` 在具备 `--cover-src` 时书名为镂空（`background-clip: text`） |
| **AC-CSV6AD-06** | `list_assignable_styles()` 恰十款；H–L 均为 `active` 且 `is_assignable` |
| **AC-CSV6AD-07** | Dock 安全区不与题签主文重叠 |

---

## 8. 修订记录

| 版本 | 日期 | 变更 |
|------|------|------|
| v1.0.0 | 2026-08-02 | 线框批准；冻结五款动作 + draft 五提案；准予实施 |
| v1.1.0 | 2026-08-02 | H–L 升 active；十款可联合 / hash / Studio；diptych 副图可选 |
