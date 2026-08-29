# Travelogue · 过河长图闸 V1 产品需求文档（PRD）

| 属性 | 内容 |
|------|------|
| **产品代号** | Travelogue Studio |
| **文档版本** | **v0.1.2**（Draft · [八席](./acceptance-records/clg-crossing-longshot-gate-v1-review-2026-08-27.md) Conditional Go · **BLK-CLG-06～10 已回写** · [帧 A/B/C/D 已签](./acceptance-records/clg-frame-bcd-signoff-2026-08-27.md) · **W1 已落** · [W2 狗粮 2026-08-29](./acceptance-records/clg-w2-dogfood-2026-08-29.md)） |
| **状态** | **Draft · W1 已落 · W2 狗粮已走**。升 Go 仍是产品裁决。**BLK-CLG-01 为合入第一门**（游记导出快照红则整 PR 打回） |
| **DOC-STATUS** | **active** |
| **主题代号** | 「过河长图闸」— **CLG**（Crossing Longshot Gate） |
| **界面用词** | 过河面沿用 FXI：**发到微信、小红书…** · **这不是在导出作品集** · **返回，继续导出作品集**。本波新词：**长图要在游记里做** · **打开那本游记** · **去做一本游记** · **先出小红书** · **要先有一本游记** · **用这些照片**。确定钮跟平台走（默认 **导出小红书**）。禁止对 C 端说 sidecar / 拼贴 / 卷轴 / 同夹 / ISO-04 / kept_stack / index-longshot / Writer / edition / 闸。**禁止** F2 确定钮写「导出长图」（游记面板仍写） |
| **文档类型** | **加法合同**：只改作品集 **F2 过河面** 的可达平台与缺卷轴时的去向。改判 FXI §7.2 的「六种都能导」半句。**不改**游记导出 / 精修，**不改** F1 / F3，**不改**装配 |
| **触发来源** | 2026-08-27 狗粮后实测：作品集过河选微信群「按章」，仍出一整张单张竖条。讨论收口见 [作品集管线简化讨论备忘录](./作品集管线简化讨论备忘录.md)。产品赞同：过河灰掉吃卷轴的两卡，其余四种可导；点灰卡则去那本游记或去做一本 |
| **评审** | [八席 2026-08-27](./acceptance-records/clg-crossing-longshot-gate-v1-review-2026-08-27.md) **8/8 Conditional Go**。Must-Fix 已回写。**待产品重勾**改字后的帧 A–D |
| **前置条件** | [FXI](./PRD-FRONTEND-IDENTITY-ISOLATION-V1.md) W1–W3 已落地 · [PIS](./PRD-PORTFOLIO-IDENTITY-STARS-V1.md) 同夹双本已落地 · [ECC](./PRD-EXPORT-CARD-COMPOSE-V1.md) / ADR-021 四平台 GA · [DPI](./PRD-DUAL-PIPELINE-ISOLATION-V1.md) W0–W3 |
| **线框** | [crossing-longshot-gate-v1-wireframe.html](./wireframes/crossing-longshot-gate-v1-wireframe.html) **待签**（帧 A 第一眼 · B 有游记 · C 去做一本 · D 认不到文件夹）。本文 **§6 为合同底稿**；ASCII 与 HTML 不一致时以 HTML 为准 |
| **关联文档** | [FXI](./PRD-FRONTEND-IDENTITY-ISOLATION-V1.md)（F2 面源 · 本文改判其「六种都能导」）· [PIS](./PRD-PORTFOLIO-IDENTITY-STARS-V1.md)（同夹双本 · 覆盖只发生在同一身份）· [PFM](./PRD-PORTFOLIO-FOLIO-MODE-V1.md) D-PFM-10 / ISO-04（能力仍在，Studio F2 不再走微信 Writer）· [备忘录](./作品集管线简化讨论备忘录.md) |
| **验收** | 本文 **§13 为源** |
| **实施** | 本文 **§11 为源** |
| **更新日期** | 2026-08-29 |

> **定位**
>
> FXI 已经把作品集默认面藏干净，过河复用游记点法。狗粮证明小红书能出门，微信按章不能：作品集 trip 没有 `index-longshot.html`，`dispatch` 对作品集 × 微信群走 kept 竖叠（ISO-04），面板上的按章是假的。
>
> 六种不是一类。微信群 / 朋友圈吃游记卷轴；小红书 / 公众号 / 单张海报 / 印刷跨页吃 kept + ECC，不需要游记预览。
>
> **一句话目标**：过河只能导不依赖游记预览的四种；长图两卡可见但不可用，点了就去那本游记，或去做一本。用户还在作品集里。
>
> **产品铁律**
>
> 1. **过河不是改身份。** 不 `POST /edition`，不换精修面，Dock 仍是「导出作品集」。  
> 2. **不改游记那份面板。** 闸只打在 F2 包装层。`journalExportPanelSnapshot` 红则整 PR 打回（**BLK-CLG-01**，延续 BLK-FXI-01）。  
> 3. **灰卡仍在网格里。** 禁止从过河面删掉微信群 / 朋友圈（人找不到入口）。禁止做成第二套社交 UX。  
> 4. **有游记就不说「新建」当唯一出路。** 同夹已有游记 →「打开那本游记」。没有 →「去做一本游记」（新 trip，PIS 两本可同时留）。禁止在已有一本时默默做出第三本。  
> 5. **默认不得落在灰卡上。** 打开 F2 时主选必须是可用的 ECC 平台。  
> 6. **F2 不得开导微信群 / 朋友圈。** 前端禁、后端拒。不再用 kept 竖条冒充按章长图。  
> 7. **不在 `dock.js` / `chapters.py` 铺 `is_portfolio`。** 闸写在 `portfolio-export-logic` / `portfolio-dock-logic` / 已有 `isPortfolioSocialExportFace` 缝。  
> 8. **不做 sidecar，不导入默认双开，不统一模板。** 那些分叉见备忘录，本波不立项。

---

## 0. 读者指南

| 章节 | 澄清什么 |
|------|----------|
| §1 | 现网为什么裂开（对照事实） |
| §2 | 目标 / 非目标 / 成功标准 |
| §3 | 对 FXI / PFM 的正式改判 |
| §4 | 原则与平台分类 |
| §5 | 同夹游记怎么认、怎么去 |
| §6 | 交互与页面（线框合同） |
| §7 | 文案表 |
| §8 | 前端行为 |
| §9 | 后端 / API |
| §10 | 工程缝与禁止项 |
| §11 | 任务拆解 |
| §12 | 里程碑 |
| §13 | 验收 AC-CLG-* |
| §14 | 风险与开放问题 |

### 0.1 术语

| 术语 | 定义 | C 端 |
|------|------|------|
| **过河 / F2** | FXI 作品集社交面。`data-export-face=portfolio:social` | 发到微信、小红书… |
| **卷轴** | 游记 `index-longshot.html` + `section.chapter`。按章、拼图、朋友圈切片都吃它 | （不出现） |
| **闸卡** | 过河面上可见但不可用作本次导出的平台卡 | 要先有一本游记 |
| **可用卡** | 过河面上可勾选、可确定导出的平台 | 小红书等 |
| **同夹游记** | 与当前作品集同一 `albumRoot`、`edition=journal` 的另一 trip | 那本游记 |
| **去做一本** | 同一文件夹再导入一本游记（新 `tripId`），不改当前作品集 | 去做一本游记 |

### 0.2 编号

任务前缀 `FE-CLG-*` / `BE-CLG-*` / `QA-CLG-*` / `DOC-CLG-*`。验收 `AC-CLG-*`。Must-Fix `BLK-CLG-01～10`（01～05 产品预占 · 06～10 八席回写）。**本文不出现与 FXI 撞号的 W 编号以外的新列车名**；里程碑用 W0 / W1 / W2。

### 0.3 八席 Must-Fix（已回写 v0.1.2）

| ID | 回写落点 |
|----|----------|
| **BLK-CLG-06** | §6 / §7 去「拼贴 / 卷轴 / 同夹」；D-CLG-03 副句改平台名 |
| **BLK-CLG-07** | §6.2 / §7 / §8.3：F2 确定钮走 `shortCtaLabelForPlatform`；改判 FXI §7.2 仅 F2 标签 |
| **BLK-CLG-08** | §6.2 / §6.7 / AC-CLG-01：`data-clg-locked` + `aria-describedby`，不用 `aria-disabled` |
| **BLK-CLG-09** | §8.4：有 `albumPath` 则跳过 `restoreSessionIfAny` |
| **BLK-CLG-10** | §9.2 / §9.3：`dispatch.py` + `export_handlers.py` 双拒；点名改 `test_handle_longshot_portfolio_explicit_wechat_allowed` |

---

## 1. 现网缺口

| 事实 | 证据 |
|------|------|
| 作品集预览不写 `index-longshot.html` | 长图桥只挂游记 screens 面 |
| 作品集 × `wechat_chat` → `export_portfolio_wechat_from_kept` | `dispatch.py` ISO-04；`segmented=False`；不传 `segment_mode`；拼图资产剔除 |
| 作品集 × `wechat_moments` → `export_platform_longshot` | 要拍卷轴 HTML；作品集上没有合格卷轴 |
| 小红书 / 公众号 / 海报 / 印刷 | `collage_pack` / `poster_bric`，kept + ECC，W3 华农已出门 |
| F2 面板仍展示按章 / 密度 | 复用游记 `buildPanelHtml`，未按 Writer 能力裁 |

用户可见症状：过河勾「按章」、导微信群，得到一张单张连贴。这不是回归，是 **面板承诺了游记 Writer，dispatch 走了另一条**。

---

## 2. 目标 / 非目标 / 成功标准

### 2.1 目标

1. 过河打开时，微信群、朋友圈为闸卡；其余四卡可导。  
2. 点闸卡：说明「长图要在游记里做」，并给出 **打开那本** 或 **去做一本**。  
3. 确定钮只对可用卡生效；后端拒绝作品集 trip 上的两家长图。  
4. 游记打开导出：六种零回归。

### 2.2 非目标

| 不做 | 为什么 |
|------|--------|
| 过河 sidecar 排一份游记 HTML | 备忘录 B，另列 |
| 导入默认双开 / 取消「这次做」 | 备忘录 §2，另列 |
| 统一 `screen-*` 与 `page-*` | 备忘录 §3 |
| 页图改 Pillow、取消预览 HTML | 备忘录 §4，另列 |
| 改游记六平台面板 HTML / 文案 | BLK-CLG-01 |
| F2 `POST /edition` 把本书改成游记 | 过河 ≠ 改身份；改身份仍在 F3 |
| 从过河面删除两卡 | 人找不到「长图去哪做」 |
| 复活 kept 竖条当「将就的微信群」 | 继续骗人 |

### 2.3 成功标准

华农作品集过河：默认小红书（或上次可用平台）；微信两卡灰；点微信 → 能打开 `demo-65db8fd377`（或当时同夹游记）的导出面板。无同夹游记的夹：点微信 →「去做一本游记」走进向导，确认句含「不会覆盖这本作品集」。游记 `journalExportPanelSnapshot` 仍绿。

---

## 3. 改判

| 原条款 | 原判 | **CLG 改判** | 新 ID |
|--------|------|----------------|-------|
| FXI §7.2 Writer | 过河走现网 ECC / Slice | **过河只开导 ECC 四平台。** 微信群 / 朋友圈在 F2 不开导 | **D-CLG-01** |
| FXI §7.2 平台网格 | 复用游记六卡点法，六种都能选 | **六卡仍在、卡序不变。** 两张闸卡 `data-clg-locked`，点开说明层，不进入选中 | **D-CLG-02** |
| FXI §7.2 顶条副句 | 「会用同一批照片，按游记的方式做成能发的图。」 | **主句不动。** 副句改为：「小红书、海报和印刷可以在这里做。长图要在游记里做。」 | **D-CLG-03** |
| FXI §7.2 确定钮 | 过河主钮必须叫「导出长图」（点法对齐） | **点法对齐保留**（选平台 → 确定 → Dock）。**标签仅 F2 改判**：跟 `shortCtaLabelForPlatform`。游记主钮零改 | **D-CLG-07** |
| FXI §7.2 按章 / 密度 | 过河按游记规则出现 | **仅当主选为可用卡时**，按该平台现网规则显隐。闸卡为「当前主选」时不得露出按章 / 密度 / 要不要字 | **D-CLG-04** |
| PFM ISO-04 / `portfolio_wechat` | 作品集显式微信群走 kept 竖条 | **Studio F2 不再调用。** CLI / 旧客户端打到作品集 × 这两平台 → `E_CLG_NEEDS_JOURNAL`。ISO-04 单测改为断言 Studio 路径拒，或标 `@deprecated` 仅 CLI | **D-CLG-05** |
| PIS 同夹双本 | 两本可同时留；覆盖只发生在同一身份 | **去做一本 = 新建 journal trip。** 禁止 force 覆盖当前作品集 | **D-CLG-06** |

### 3.1 明确不改

FXI F1 / F3、BLK-FXI-01、D-FXI-07（过河不改身份）、D-PFM-10 能力半句（作品集用户仍可出社交图，落点仍是过河）、PFO 页数规格、ECC 卡序、游记 `buildPanelHtml` 输出。

---

## 4. 原则与平台分类

### 4.1 分类（冻结）

| 平台 id | C 端卡名 | 过河 | Writer |
|---------|----------|------|--------|
| `wechat_chat` | 微信群 | **闸卡** | 游记 `export_journal_longshot`（只在 journal trip） |
| `wechat_moments` | 朋友圈 | **闸卡** | 游记 `export_platform_longshot`（只在 journal trip） |
| `xiaohongshu` | 小红书 | 可用 | ECC |
| `wechat_official` | 公众号 | 可用 | ECC |
| `poster_bric` | 单张海报 | 可用 | ECC |
| `album_spread` | 画册印刷 | 可用 | ECC；副文仍 D-PFM-30 |

禁止把 `portfolio_pages` 勾进 F2 `platforms[]`（N-PFM-15 延续）。F2 仍禁止批量（FXI 已落）。

### 4.2 为什么朋友圈也闸

朋友圈 Writer 拍 HTML 再切片，和微信群一样依赖卷轴。作品集页不是卷轴。与微信群同一闸，避免「一种能点一种不能」的第二种假承诺。

---

## 5. 同夹游记：怎么认、怎么去

### 5.1 认

打开 F2 或首次点闸卡时，请求 `GET /__travelogue/trips/{id}/sibling-journal`。

服务端取当前 trip 的 `media.albumRoots[0]`（无则尝试资产 `sourceRef.albumRoot`），再按下面顺序调用现网 `peek_existing_album_trip(..., edition="journal")`。只返回 **edition 确为 journal** 的另一本。

| 字段 | 含义 |
|------|------|
| `present` | 是否有同夹游记 |
| `tripId` | 那本的 slug |
| `title` | 展示书名 |
| `albumRoot` | 文件夹路径（去做一本时回填向导；无则 `null`） |
| `canCreateSibling` | `albumRoot` 可读则为 true |

**title / place 必须与向导 album-preview 对齐**，否则会漏认同夹游记（slug 吃这两个参数）：

1. `title_hint` = `Path(albumRoot).name`，`place_hint` = `"旅途"`（与 `import_handlers` album-preview 同）。  
2. 先 `peek(..., edition="journal", title=title_hint, place=place_hint)`。  
3. 若空，再用当前 trip 的 `meta.displayTitle` / `meta.place`（缺省仍是文件夹名 / `"旅途"`）再 peek 一次。  
4. 两次都空 → `present=false`。

禁止新写「扫全部 trip 的 albumRoots」算法。禁止把当前 portfolio trip 当成游记。

认失败（无根、目录不可读、peek 抛错）：`200` + `present=false`；`canCreateSibling` 仅当 `albumRoot` 仍是可读目录。无根则两字段皆假，走 §6.4 降级，不崩面板。

响应形（字段冻结）：

```json
{
  "ok": true,
  "present": true,
  "tripId": "demo-65db8fd377",
  "title": "凯哥拍摄精选 · 旅行",
  "albumRoot": "D:/photos/华南农大",
  "canCreateSibling": true
}
```

`present=false` 时 `tripId` / `title` 为 `null`。`albumRoot` 仅 Studio 本机可信；禁止写进账本 / 遥测。

### 5.2 去

| 情况 | 主钮 | 行为 |
|------|------|------|
| `present=true` | **打开那本游记** | `/{tripId}/index.html?exportPanel=1`。那本是游记，六种全开。不带 `exportFace=social` |
| `present=false` 且 `canCreateSibling` | **去做一本游记** | 回首页，打开**现网**向导（扩展 `openImportWizard` 的 opts，禁止第二套向导）。预填同一 `albumPath`，Step 2 **预选游记**。确认句走 PIS：无 Self、有 Other →「将新建一本游记，不会覆盖已有作品集《{other}》。两本可以同时留在书架上。」`force=false` |
| 两皆假 | **想改做成一本游记？** | **次要。** 关 F2，打开 F3 身份问句。文案必须说清：这是 **把这本书改成游记**，不是再留一本。用户取消则回到 F1 |

禁止：F2 直接 `POST /trips/{id}/edition`。

打开那本失败（404）：toast「那本游记打不开」，主钮改成「去做一本游记」（若可）或降级句。

**防误覆盖（BLK-CLG-05）**：去做一本走进向导后，若 album-preview 的 `existingJournal` 有值，**禁止**走覆盖该游记。说明层当时漏认了。处理：关闭覆盖确认、toast「书架上已经有一本游记」，并改走「打开那本」（`/{existingJournal.tripId}/index.html?exportPanel=1`）。作品集 tripId 仍不得被 force。

---

## 6. 交互与页面

线框源：[crossing-longshot-gate-v1-wireframe.html](./wireframes/crossing-longshot-gate-v1-wireframe.html)。四帧改字待签。视觉令牌对齐 FXI：`--bg #e6e2db`、`--paper #fffdf8`、强调色 `#3d6b5a`、主钮金 `#c4a15a`。闸卡对比度约 `opacity: 0.48`，**禁止** `pointer-events: none`。说明层 **叠在** 六卡网格上，不拆掉网格。

### 6.1 F1 进入（不改）

底链仍是「想发到微信或小红书？」。整面替换为 F2。徽章改为「用这些照片」（仅 F2）。

### 6.2 帧 A · 过河第一眼

```
┌ 发到微信、小红书…                    [用这些照片] ┐
│  这不是在导出作品集。                             │
│  小红书、海报和印刷可以在这里做。长图要在游记里做。│
│                                                   │
│  微信群     要先有一本游记          （灰，可点）  │
│  朋友圈     要先有一本游记          （灰，可点）  │
│  小红书     3:4 海报                （选中）      │
│  公众号     3:4 配图                              │
│  单张海报   3:4                                   │
│  画册印刷   给印刷公司的跨页，不是这本作品集      │
│                                                   │
│  （张数 / 文案包 / 清晰度 · 跟小红书现网）        │
└───────────────────────────────────────────────────┘
 [ 返回，继续导出作品集 ]              [ 导出小红书 ]
```

| 元素 | 合同 |
|------|------|
| 徽章 | **用这些照片**（改 FXI「按游记来做」仅 F2；游记徽章不动） |
| 顶条主句 | **这不是在导出作品集。**（FXI 不改） |
| 顶条副句 | **小红书、海报和印刷可以在这里做。长图要在游记里做。** |
| 闸卡外观 | 降低对比度；`data-clg-locked="1"`；`aria-describedby` 指向「要先有一本游记」；**可聚焦、可点**。禁止 `aria-disabled` / `disabled` / `pointer-events:none` |
| 闸卡点按 | 不切换 `aria-pressed`，不写入 draft 主平台；打开帧 B / C / D |
| 可用卡 | 点法与游记同一套 checkbox；单选主平台（F2 仍不批量） |
| 默认主选 | 见 §8.2 |
| 按章 / 密度 / 要不要字 | 主选为可用卡时按该平台现网。主选不得为闸卡，故这些控件在第一眼不应出现 |
| 确定 | 主选为可用卡才可点。文案 = 现网 `shortCtaLabelForPlatform`（小红书 → **导出小红书**；公众号 → **导出公众号**；海报 → **导出海报**；印刷 → **导出画册**）。**禁止**写「导出长图」。主选若被脏数据落成闸卡，确定禁用，并自动纠正到默认可用卡 |
| 返回 / 取消 | 回 F1，与 FXI 同 |

### 6.3 帧 B · 点闸卡 · 已有同夹游记

同一 popover **内**加一层说明（`role="dialog"`，焦进层内）。不新开浏览器窗。

叠在六卡之上（网格仍在，略降对比）。书名与作品集相同时用 `sheetHasBodySameTitle`，不复读两个《同一书名》。

```
┌ 长图要在游记里做                              ✕ ┐
│  微信群和朋友圈的长图，要打开游记那本才能做。   │
│  书架上已经有一本《{title}》。                  │
│                                                 │
│  [ 打开那本游记 ]     [ 留在作品集 ]            │
└─────────────────────────────────────────────────┘
```

「留在作品集」关层，仍停在 F2，主选仍是打开层之前的可用卡。

### 6.4 帧 C · 点闸卡 · 没有同夹游记

```
┌ 长图要在游记里做                              ✕ ┐
│  要用微信群或朋友圈发长图，得先做一本游记。     │
│  做好之后，这本作品集还在，两本都可以留在书架上。│
│                                                 │
│  [ 去做一本游记 ]     [ 先出小红书 ]            │
└─────────────────────────────────────────────────┘
```

「先出小红书」关层，并把主选设为 `xiaohongshu`（即使上次 prefs 是别的可用卡，本钮语义就是小红书）。

### 6.5 帧 D · 点闸卡 · 认不到文件夹（`canCreateSibling=false`）

帧 D **补顶条**（与帧 A 同主句 / 副句）。说明层叠在网格上。

```
┌ 长图要在游记里做                              ✕ ┐
│  找不到原来的照片文件夹，没法再做一本新的游记。 │
│  也可以把这本书改做成游记——那会重排这一本，     │
│  不是再留一本。                                 │
│                                                 │
│  [ 想改做成一本游记？ ]     [ 留在作品集 ]      │
└─────────────────────────────────────────────────┘
```

主钮只关 F2、打开 F3 现网问句，**不**在说明层里直接 `POST /edition`。次钮关层，停在 F2。

### 6.6 成功面 / Dock

可用卡导完：平台自己的成功句（FXI §7.3）。再点 Dock → F1。闸卡路径不产生作品集 trip 上的微信 / 朋友圈账本记录。

### 6.7 无障碍

闸卡必须能读到「要先有一本游记」（`aria-describedby`）。说明层 Esc / ✕ =「留在作品集」。焦从闸卡进入层，关闭后回到该闸卡。禁止 `aria-disabled`、禁止 `pointer-events:none`。

### 6.8 帮助

不新开帮助编号。W1 扫作品集帮助 / FirstSuccess：若仍写「过河能发微信长图 / 出社交图」，改成「过河可以出小红书、海报和印刷；长图要在游记里做」。游记帮助条（怎么把长图发到微信群）**零改**。

### 6.9 加载与失败（说明层）

打开 F2 即请求 sibling，**第一眼不转圈**（默认主选不依赖它）。点闸卡时：

| sibling 状态 | 说明层 |
|--------------|--------|
| 已返回 | 立刻帧 B / C / D |
| 进行中 | 标题仍「长图要在游记里做」；主钮暂时 disabled，副文「正在找书架上的游记…」（3s 内应落定） |
| 网络失败 / 5xx | 按 `present=false`；`canCreateSibling` 用打开 F2 时缓存的 albumRoot 是否有值。toast 不报路径 |
| 超时（建议 4s） | 同失败 |

禁止因 sibling 慢而挡住可用卡的确定钮（如「导出小红书」）。

---

## 7. 文案表（冻结到签核）

| id | 场景 | 原文（C 端冻结） |
|----|------|------------------|
| `badge` | F2 徽章 | 用这些照片 |
| `leadSecondary` | F2 顶条副句 | 小红书、海报和印刷可以在这里做。长图要在游记里做。 |
| `gateSub` | 闸卡副文 | 要先有一本游记 |
| `sheetTitle` | 说明层标题 | 长图要在游记里做 |
| `sheetHasBody` | 书架上已有游记 | 微信群和朋友圈的长图，要打开游记那本才能做。书架上已经有一本《{title}》。 |
| `sheetHasBodySameTitle` | 两本书名相同 | 微信群和朋友圈的长图，要打开游记那本才能做。这个文件夹已经做过一本游记。 |
| `sheetHasCta` | 主钮 | 打开那本游记 |
| `sheetStay` | 次钮 | 留在作品集 |
| `sheetNoneBody` | 还没有游记 | 要用微信群或朋友圈发长图，得先做一本游记。做好之后，这本作品集还在，两本都可以留在书架上。 |
| `sheetNoneCta` | 主钮 | 去做一本游记 |
| `sheetXhs` | 次钮 | 先出小红书 |
| `sheetConvertBody` | 找不到文件夹 | 找不到原来的照片文件夹，没法再做一本新的游记。也可以把这本书改做成游记——那会重排这一本，不是再留一本。 |
| `sheetConvertCta` | 主钮 | 想改做成一本游记？ |
| `confirmXhs` | 主选小红书 | 导出小红书 |
| `confirmOfficial` | 主选公众号 | 导出公众号 |
| `confirmPoster` | 主选海报 | 导出海报 |
| `confirmAlbum` | 主选印刷 | 导出画册 |
| `toastOpenFail` | 打开那本 404 | 那本游记打不开 |
| `toastBlockedExport` | 脏客户端仍请求长图 | 长图要在游记里做 |
| `sheetLoading` | sibling 未返回 | 正在找书架上的游记… |
| `toastSiblingSurprise` | 向导 peek 到游记（BLK-CLG-05） | 书架上已经有一本游记 |

禁止：F2 确定钮「导出长图」；「新建游记」当 `present=true` 的主钮；C 端「拼贴 / 卷轴 / 同夹 / 换种分享 / sidecar」。

确定钮 **复用** 现网 `shortCtaLabelForPlatform`，禁止新造第四套短句。

向导确认句 **复用 PIS**，不在本波新造覆盖话术。

---

## 8. 前端行为

### 8.1 闸写在哪

| 做 | 文件（所有权） |
|----|----------------|
| 闸卡集合、文案、默认主选纯函数 | `portfolio-export-logic.js` |
| F2 spec 带 `lockedPlatforms` / sibling 拉取 | `portfolio-dock-logic.js` |
| 灰态、点闸开层、藏按章 | `longshot-export-panel.js` 的 `syncPanelUI`，**仅** `isPortfolioSocialExportFace(pop)` |
| `_applyDraft` 若主平台为闸卡则中止 | `longshot.js` 作品集 social 早退 |
| sibling GET、打开那本、向导深链 | `longshot.js` / 现有 studio fetch 助手 |

禁止改 `templates/studio/js/journal-dock-logic.js`、`buildPanelHtml` 的 journal 默认输出、`dock.js` 本体。

闸卡判定必须是 **纯函数**（平台 id 集合），便于单测，禁止读 DOM 猜。

```
isCrossingLongshotLocked(platform) → wechat_chat | wechat_moments
nextCrossingDefaultPlatform(prefs, enabled) → 上次可用否则 xiaohongshu
```

### 8.2 默认主选

打开 / hydrate F2：

1. 读 `portfolioSocialPrefs.v1` 的 `platform`。  
2. 若属于可用卡且在 enabled 列表 → 用它。  
3. 否则 → `xiaohongshu`（旗关则下一张可用 ECC）。  
4. `platforms[]` 只含这一个可用 id。  
5. **禁止**把闸卡写回 `portfolioSocialPrefs`。点闸卡开层不算改选。

### 8.3 确定与脏状态

`_applyDraft` 在 `applyFace==="social"` 时：若 `isCrossingLongshotLocked(platform)`，不写 prefs、不 `startLongshot`，打开说明层。确定钮在闸卡为主选时 `disabled`。确定钮文案走 `shortCtaLabelForPlatform`，**禁止**回落到「导出长图」/「发微信群」。

### 8.4 「去做一本」握手（禁止新造 URL 合同当主路径）

现网首页 **没有** `/?import=1&album=` 消费端。落地必须复用 `openImportWizard(opts)`：

1. 预览写下一次性会话（`sessionStorage`，键名 `travelogue.studio.clgCreateJournal.v1`）：

```
{ albumPath, edition: "journal", fromTripId, ts }
```

2. 跳转首页 `/`（可带现网已有无关参数；**不要**发明第二套向导 query 当唯一入口）。  
3. 首页 `initImportSheet` 之后读键、**读完即删**，调用：

```
openImportWizard({ edition: "journal", albumPath })
```

4. **FE-CLG-04 扩展现网 opts（BLK-CLG-09）**：`albumPath` 有值则 **跳过** `restoreSessionIfAny`，走现网 `afterFolderPicked(albumPath)`，再 `setActiveEdition("journal")`。禁止旧草稿盖掉夹。禁止跳过确认页。禁止 `force=true`。  
5. 向导 peek 到 `existingJournal` → §5.2 BLK-CLG-05，不覆盖。

作品集预览 tab 可留在后台。用户关掉向导 = 留在首页书架，不自动跳回作品集（R-CLG-02 同原则）。

### 8.5 测试锁

| 测 | 断言 |
|----|------|
| `journalExportPanelSnapshot` | 逐字节不变 |
| F2 HTML | 含六平台节点；两闸 `data-clg-locked="1"`（无 `aria-disabled`）；默认无 `wechat_chat` pressed；确定钮非「导出长图」 |
| `nextCrossingDefaultPlatform({platform:"wechat_chat"})` | `xiaohongshu` |
| `syncPanelUI` F2 + 误传 wechat 多选 | 无「批量导出」；按章区 hidden |
| 游记 `buildPanelHtml` | 两卡可点，无「要先有一本游记」 |

---

## 9. 后端 / API

### 9.1 `GET /__travelogue/trips/{id}/sibling-journal`

- 入：当前 trip id（作品集）。  
- 出：§5.1 JSON。`404` 仅当本书不存在。认不到游记 → `200` + `present=false`。  
- 复用 `peek_existing_album_trip`，**禁止**新 slug 算法。  
- 不写磁盘。

### 9.2 导出拒闸

**双落点（BLK-CLG-10）**：`travelogue/export/dispatch.py` **和** `travelogue/web/studio_handlers/export_handlers.py`。只改一处，现网 handler 单测会打脸。

`is_portfolio_trip` 且 `platform ∈ {wechat_chat, wechat_moments}` → **不要**再进 `export_portfolio_wechat_from_kept` / `export_platform_longshot`。handler 里作品集微信的 `skip_client_fallback` 枝改为先 409。

返回结构化错误：

| 字段 | 值 |
|------|-----|
| `code` | `E_CLG_NEEDS_JOURNAL` |
| `message` | 与 `toastBlockedExport` 同句 |
| `sibling` | 与 GET 同形，可省略 |

HTTP：Studio JSON `409`。CLI 非零退出 + 同一 code。

### 9.3 明确不改

`export_journal_longshot`、`collage_pack`、`portfolio_pages`、`compose_trip`、`editorial_series`、`trip.json` schema、`mosaic/**`。

ISO-04 **几何门保持**：`test_iso04_portfolio_wechat_does_not_flatten_page_geometry` **不改**（函数可留，禁止再拍 `page-*`）。

Studio 开导改判：同 PR 改 `tests/unit/web/handlers/test_studio_handlers_import_export.py` 的 `test_handle_longshot_portfolio_explicit_wechat_allowed` → 断言 `409` + `E_CLG_NEEDS_JOURNAL`。[PFM 验收页](./ACCEPTANCE-PORTFOLIO-FOLIO-MODE-V1.md) 挂一句「Studio 微信开导改判见 CLG」。

### 9.4 遥测（可选，不挡 W1）

`clg_gate_open`（has_sibling）· `clg_open_journal` · `clg_create_journal` · `clg_stay`。禁止打路径明文。

---

## 10. 工程缝

改文件前：`python scripts/lint_dual_pipeline_ownership.py --explain <file>`。

| 允许 | 禁止 |
|------|------|
| `portfolio-export-logic.js` 增加闸纯函数 | `dock.js` 里 `if (isPortfolio)` 禁两卡 |
| `isPortfolioSocialExportFace` 已有缝上灰态 | 改 `buildPanelHtml` 默认 journal 分支 |
| `dispatch.py` 作品集 × 两平台拒（已是 edition 缝） | `longshot.py` 游记函数体内加 edition 分支 |
| 新 GET 挂 `studio_dispatch` / trip_handlers | 新 import-linter 空壳 |

Studio JS 未注册 dual-pipeline 标记，不要为闸去注册。

---

## 11. 任务拆解（实施源）

### W0 · 线框签核（编码门）

| ID | 席 | 做什么 | 出门 |
|----|----|--------|------|
| **DOC-CLG-01** | 产品 / 视觉 | 签帧 A / B / C / D | [签核](./acceptance-records/) 一篇；四帧勾 |

### W1 · 闸 + 可选四平台 + 去向

| ID | 层 | 做什么 | 出门 |
|----|----|--------|------|
| **FE-CLG-01** | 前端 | 闸纯函数 + 默认主选 + 文案表 | 单测 |
| **FE-CLG-02** | 前端 | F2 `syncPanelUI`：`data-clg-locked` / 点卡开层 / 藏按章；确定钮走 `shortCtaLabelForPlatform` | F2 测；journal 快照绿 |
| **FE-CLG-03** | 前端 | `_applyDraft` 拒闸；确定 disabled；禁止回落「导出长图」 | 点确定不 `startLongshot` |
| **FE-CLG-04** | 前端 | sibling GET + 打开那本 + session 握手 + `openImportWizard({ edition, albumPath })` **跳过草稿** + F3 降级 + BLK-CLG-05 | 华农能跳到凯哥导出面；漏认时不覆盖游记 |
| **FE-CLG-05** | 前端 | 帮助 / FirstSuccess 扫一句（§6.7） | 游记帮助零 diff |
| **BE-CLG-01** | 平台 | `GET sibling-journal` | 华农作品集 → 凯哥 journal id |
| **BE-CLG-02** | 平台 | `dispatch.py` + `export_handlers.py` 双拒；改 `test_handle_longshot_portfolio_explicit_wechat_allowed` | 作品集 × wechat_chat → 409；ISO-04 几何测仍绿 |
| **QA-CLG-01** | 测 | journal 快照 + F2 闸 + peek 单测 | CI 绿 |
| **DOC-CLG-02** | 文档 | FXI §7.2 / §18 挂改判指针 | 已挂 v0.1.7 |

### W2 · 狗粮

| ID | 做什么 | 出门 |
|----|--------|------|
| **QA-CLG-02** | 华农作品集过河：四平台抽一（建议小红书）仍能出门；两卡灰；点微信打开同夹游记导出 | `acceptance-records/clg-w2-dogfood-YYYY-MM-DD.md` |
| **QA-CLG-03** | 无同夹游记的夹：去做一本，PIS 确认句；作品集 tripId 不变 | 记录 |

---

## 12. 里程碑与编码门

| 里程碑 | 出门标准 | 编码门 |
|--------|----------|--------|
| **W0** | 帧 A/B/C/D 产品勾 | 未签不得合功能 PR |
| **W1** | FE+BE 绿；**BLK-CLG-01～10** | ☑ W0 |
| **W2** | 狗粮两夹 | ☑ [2026-08-29](./acceptance-records/clg-w2-dogfood-2026-08-29.md) |
| **升 Go** | 产品裁决 | W2 |

**BLK（01～05 预占 · 06～10 八席 · 均已回写正文）**

| ID | 句 | 何时 |
|----|----|------|
| **BLK-CLG-01** | 游记导出 / 精修快照红则打回 | 每里程碑 |
| **BLK-CLG-02** | F2 不能成功开导 `wechat_chat` / `wechat_moments` | W1 |
| **BLK-CLG-03** | F2 不 `POST /edition` | W1 |
| **BLK-CLG-04** | `present=true` 主钮不是「去做一本 / 新建」 | W1 |
| **BLK-CLG-05** | 「去做一本」走进向导后若 peek 到游记，不得覆盖该游记 | W1 |
| **BLK-CLG-06** | C 端无「拼贴 / 卷轴 / 同夹」 | W0 文案 / W1 |
| **BLK-CLG-07** | F2 确定钮不得写「导出长图」；游记主钮零改 | W0 文案 / W1 |
| **BLK-CLG-08** | 闸卡可点，不用 `aria-disabled` | W1 |
| **BLK-CLG-09** | 有 `albumPath` 时跳过向导草稿恢复 | W1 |
| **BLK-CLG-10** | dispatch + handler 双拒；点名改 Studio 微信可出单测 | W1 |

---

## 13. 验收

| ID | 断言 | 里程碑 |
|----|------|--------|
| **AC-CLG-01** | F2 六平台节点都在；微信群、朋友圈 `data-clg-locked="1"` 且 **无** `aria-disabled`；副文「要先有一本游记」；闸卡可聚焦可点 | W1 |
| **AC-CLG-02** | 打开 F2 时 `aria-pressed` 的主平台不是闸卡 | W1 |
| **AC-CLG-03** | 点闸卡不改变主选；出现说明层标题「长图要在游记里做」 | W1 |
| **AC-CLG-04** | 华农类同夹：说明层主钮打开 journal trip，且该页 `data-edition` 非 portfolio（或缺省），导出六种可点 | W2 |
| **AC-CLG-05** | 无同夹：主钮进向导预选游记；作品集 `tripId` 不被 force 覆盖 | W2 |
| **AC-CLG-06** | F2 确定 + 可用卡仍走出 ECC（小红书张数 / 成功句） | W2 |
| **AC-CLG-07** | 游记 `journalExportPanelSnapshot` 与合入前一致 | W1 |
| **AC-CLG-08** | 作品集 × `wechat_chat` Studio 导出 → `E_CLG_NEEDS_JOURNAL`，无新的 kept_stack 文件 | W1 |
| **AC-CLG-09** | F2 网络日志无 `POST .../edition` | W1 |
| **AC-CLG-10** | 再点 Dock 回 F1；主 CTA「导出作品集」 | W1 |
| **AC-CLG-11** | 顶条副句为 D-CLG-03 原文；主句仍是「这不是在导出作品集。」；确定钮在主选小红书时为「导出小红书」，全文无 F2「导出长图」 | W1 |
| **AC-CLG-12** | F2 `data-export-face=portfolio:social` 主选小红书时按章区 `hidden`；**不是** journal 快照缺字 | W1 |
| **AC-CLG-13** | 「去做一本」向导确认句含「将新建一本游记」且含「不会覆盖已有作品集」；网络无 `force=true` | W2 |
| **AC-CLG-14** | 向导若返回 `existingJournal`，不出现「覆盖并重新导入」该游记；改为打开那本 | W1 |
| **AC-CLG-15** | `canCreateSibling=false` 时说明层主钮是「想改做成一本游记？」；点下后无 `POST /edition`，F3 问句出现 | W1 |

---

## 14. 风险与开放问题

| ID | 风险 | 收法 |
|----|------|------|
| **R-CLG-01** | 人以为过河坏了（微信灰） | 副句 + 闸卡副文 + 说明层 |
| **R-CLG-02** | 打开那本后找不到返回作品集 | 游记预览现网「返回」回书架；不本波做「跳回作品集」 |
| **R-CLG-03** | 向导深链参数与现网不一致 | **不发明** `/?import=1` 主路径；扩展 `openImportWizard` opts + session 握手 |
| **R-CLG-04** | `albumRoots` 空（老 trip） | §6.4 降级到 F3 问句，说清会改这本书 |
| **R-CLG-05** | 同夹多本游记 | peek 现网只回一本（slug 算法）。本波不选列表。OQ |
| **R-CLG-06** | 帮助 / FirstSuccess 仍暗示过河能发微信长图 | W1 扫作品集帮助一句 |

| ID | 问题 | 本波默认 | 挡门？ |
|----|------|----------|--------|
| **OQ-CLG-01** | 同夹多本游记怎么选 | 沿用 peek 那一本 | 不挡 |
| **OQ-CLG-02** | 「去做一本」是回首页还是预览内嵌向导 | **回首页**（少造面） | 不挡 |
| **OQ-CLG-03** | F2 主钮在只有 ECC 时是否改叫「导出拼贴」 | **改判**：可用卡走 `shortCtaLabelForPlatform`；禁止「导出长图」「导出拼贴」 | 已关 · BLK-07 |
| **OQ-CLG-04** | CLI 作品集微信是否彻底删除 `portfolio_wechat.py` | W1 只拒 Studio/dispatch；文件可留 Deprecated | 不挡 |
| **OQ-CLG-05** | F2 标题还叫不叫「发到微信、小红书…」 | **维持**（入口链同一句） | 已关 |
| **OQ-CLG-06** | 徽章「按游记来做」改不改 | **改为「用这些照片」**（仅 F2） | 已关 · v0.1.2 |
| **OQ-CLG-07** | 线框未改字前可否签 DOC-CLG-01 | **不可**；改字后产品重勾 | 线框已改字 · 待勾 |

---

## 15. 文档关系

```
要改过河「六种里哪些能导」
  → 本文 CLG（改判 FXI §7.2）

要改 F1 / F3 / 游记导出
  → FXI / 现网冻结；不走本文

要改同夹两本怎么存、覆盖谁
  → PIS（本文只消费 peek）

要改页图是否还拍预览 HTML
  → 备忘录 §4，另开主题

要改装配 / 统一模板
  → 不走本文
```

---

## 16. 变更记录

| 版本 | 日期 | 说明 |
|------|------|------|
| v0.1.0 | 2026-08-27 | 初稿。产品赞同闸卡方案并吸收补充：有游记先打开、默认不落灰卡、F2 不改身份、游记面板零改。帧 A/B/C 待签。 |
| v0.1.1 | 2026-08-27 | 落地缝：peek 与 album-preview 对齐；去做一本用 session + 现网向导 opts（不造 URL）；防漏认后覆盖游记（BLK-CLG-05）；加载/失败态；帧 D；挂 FXI / DOC-STATUS。 |
| v0.1.2 | 2026-08-27 | 八席 Must-Fix 回写。去拼贴/卷轴/同夹；F2 确定钮跟平台（默认导出小红书）；闸卡不用 aria-disabled；向导握手跳过草稿；dispatch+handler 双拒并点名改测。线框改字待产品重勾。 |
| v0.1.2 | 2026-08-29 | W1 缺口：F2 藏「点长图开始导出」摘要、补主句「这不是在导出作品集。」。W2 狗粮见 [clg-w2-dogfood-2026-08-29](./acceptance-records/clg-w2-dogfood-2026-08-29.md)。 |
