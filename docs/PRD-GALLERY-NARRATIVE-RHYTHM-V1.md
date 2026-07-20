# Travelogue · 廊道×展室节奏系统 PRD（Gallery × Narrative Rhythm）

| 属性 | 内容 |
|------|------|
| **产品代号** | Travelogue |
| **文档版本** | v0.1.1-GNR |
| **状态** | **Superseded in direction** · 全书多级装裱默认方案已降级；呈现侧主需求见 [PRD-HIGHLIGHT-GALLERY-MOUNT-V1.md](./PRD-HIGHLIGHT-GALLERY-MOUNT-V1.md) |
| **代号** | 「廊道推进故事，展室制造凝视」— 隐喻仍可用；落地改为「仅高光轻布展」 |
| **试验载体** | `demo-65db8fd377`（凯哥拍摄精选）临时注入；脚本 `.tmp-gn-exp-console.js` |
| **前置条件** | 现有 `layout-screen` / `breath-pause-screen` / 章分隔 / Phase 23 `moment` 可读面可用 |
| **关联文档** | [PRD-PHASE6-ART-OPTIMIZATION.md](./PRD-PHASE6-ART-OPTIMIZATION.md)、[PRD-PHASE23-peak-moment.md](./PRD-PHASE23-peak-moment.md)、[PRD-EXPERIENCE-附录B-滚动动效.md](./PRD-EXPERIENCE-附录B-滚动动效.md)、[PRD-EXPERIENCE-附录C-Folio版式.md](./PRD-EXPERIENCE-附录C-Folio版式.md)、[PRD-AESTHETIC-ALIGNMENT.md](./PRD-AESTHETIC-ALIGNMENT.md) |
| **更新日期** | 2026-07-20 |

> **2026-07-20 方向修订**  
> 装裱分级试验结论：全书换肤会破坏统一和谐。后续讨论与需求以  
> **[PRD-HIGHLIGHT-GALLERY-MOUNT-V1.md](./PRD-HIGHLIGHT-GALLERY-MOUNT-V1.md)** 为准（仅高光轻布展，其余保持游记语法）。本文保留为隐喻与试验档案。

> **定位（历史）**
>
> Travelogue 的阅读体验同时承担两种合法期待：
>
> 1. **摄影展**：关键画面像被布展的作品，值得停顿凝视；  
> 2. **照片小说**：整卷像连续叙事，时间与情绪向前推进。
>
> 二者不能靠「统一加大屏间距」解决。本 PRD 引入 **装裱等级（Mount Level）** 与 **观看契约切换**，让约 80% 屏走廊道叙事、约 20% 屏进入展室凝视，并用章界 / 呼吸点完成展厅换场。

---

## 0. 决策提案（待拍板）

| ID | 议题 | 提案裁定 |
|----|------|----------|
| **DS-GNR-01** | 产品隐喻 | **可走动的展览叙事**：章=展厅，连作=廊道墙面，杰作=独立展室 |
| **DS-GNR-02** | 平衡策略 | **非平均分配**：默认廊道（L0/L1）；杰作稀疏（L2）；全书至多 1 个黑匣（L3） |
| **DS-GNR-03** | 间距本质 | 间距是装裱结果，不是主控件；主控件是 `mountLevel` |
| **DS-GNR-04** | 与 Phase 23 | `data-role="moment"` **默认映射 L3**（可降为 L2）；`role=peak` 默认映射 L2 |
| **DS-GNR-05** | breath | `breath-pause` 必须具备可读高度（C 级）；禁止塌成与 L1 同量级的 9px 装饰 |
| **DS-GNR-06** | 标注 UI | 读者面 **默认不显示** L0/L1/L2 角标；仅 Studio / 调试 / 试验模式可见 |
| **DS-GNR-07** | 导出 | 微信长图：L1/L2 气口 ×1.25；L3 保留暗场但避免超长纯黑条 |
| **DS-GNR-08** | 交互（V1.1） | V1 只做静态装裱节奏；**凝视模式**（停顿加深装裱）列为 V1.1 |

---

## 1. 背景与问题

### 1.1 现状摘要（2026-07-20 实测 · demo-65db8fd377）

| 现象 | 数据 / 观察 |
|------|-------------|
| 屏间默认缝 | `--screen-rhythm-gap ≈ 9px`（`clamp(8px, 1vh, 16px)`） |
| 纸色对比 | body `#faf8fc` vs plate `#e8e4df` 过近 → 9px 缝几乎不可读 |
| breath | `breath-pause-screen` 高度常塌至 ~9px，无法承担「换气」 |
| 章界 | 票根分隔已成立，是有效的 C/厅级标点 |
| 节奏扁平 | 31 屏几乎等权贴靠 → 既不够「展」，也不够「小说高潮」 |
| 已有高光语义 | 屏 18=`moment`，屏 23=`peak`，但装裱强度与邻屏几乎无差 |

### 1.2 问题陈述（GNR-P-*）

| ID | 问题 | 影响 |
|----|------|------|
| **GNR-P-01** | 艺术感与故事感被当成互斥的间距问题 | 调大缝 → PPT 感；调小缝 → 信息流感 |
| **GNR-P-02** | 所有 `layout-screen` 等权 | 杰作无法被「看见」，连作无法「连起来」 |
| **GNR-P-03** | breath 名存实亡 | 长卷中段疲劳、章内无段落感 |
| **GNR-P-04** | Phase 23 签名时刻缺少空间特权 | 「决定性瞬间」角标有了，展室气场不足 |
| **GNR-P-05** | 导出 / 播放 / 长滚未区分节奏预算 | 同一套缝在微信长图偏弱、在 snap 播放又可能偏紧 |

### 1.3 核心判断

- 用户要的不是「每屏都是作品」，而是 **在正确的时刻被作品击中**。  
- 用户要的不是「没有间隔的故事」，而是 **走廊一直在带我往前走**。  
- 因此产品应提供 **两种观看态**，并用装裱等级自动编排，而不是让作者在「展览风 / 小说风」之间二选一。

---

## 2. 目标与非目标

### 2.1 目标

| ID | 目标 | 验收口径 |
|----|------|----------|
| **G-GNR-01** | 建立装裱等级模型 | 每屏具备 `mountLevel ∈ {L0,L1,L2,L3,C}`（C 仅 breath） |
| **G-GNR-02** | 廊道占优 | 全书 L0+L1 ≥ 70% 内容屏；L2 ≤ 每章 2；L3 ≤ 全书 1 |
| **G-GNR-03** | 杰作可感知 | 盲测：在无角标情况下，受试者能指出「哪几屏被特别对待」命中率 ≥ 70% |
| **G-GNR-04** | 故事不断裂 | 连作段（L0 序列）内滚动不出现「卡片堆叠」主诉 |
| **G-GNR-05** | breath 可读 | C 级 min-height ≥ `clamp(64px, 10vh, 120px)` |
| **G-GNR-06** | 与现有图位对齐 | cover / chapter plate / moment / peak / closing 有明确 mount 映射 |
| **G-GNR-07** | Studio 可覆写 | 作者可将任一屏升/降一级（受配额约束） |
| **G-GNR-08** | 试验可复现 | 提供注入脚本与策展表，不改生产默认直至验收通过 |

### 2.2 非目标

- **不做** 每屏统一大间距或统一无缝  
- **不做** 读者面常驻 L0/L1/L2 调试角标  
- **不做** 为艺术感添加描边相框、贴纸、彩色分割条  
- **不做** 重绘/生成照片内容  
- **不做** V1 强制双速交互（凝视模式 → V1.1）  
- **不替代** Phase 23 选图算法；本 PRD 消费其结果并赋予空间特权  
- **不替代** 章节命名 / 封面选型 PRD  

---

## 3. 设计原则

| ID | 原则 | 说明 |
|----|------|------|
| **GNR-PR-01** | 廊道默认 | 连续叙事是底色；展览是高潮，不是默认态 |
| **GNR-PR-02** | 装裱分级 | 问「这一屏是廊道一步还是展室作品」，再决定气口 |
| **GNR-PR-03** | 气口是纸面 | 间隔露出纸/台面，不加线、不加卡片阴影作为主语言 |
| **GNR-PR-04** | 稀疏杰作 | 艺术权威感来自稀缺；L2/L3 过多即稀释 |
| **GNR-PR-05** | 章=展厅 | 票根/章门负责换厅；章内再用 L2/C 做段落 |
| **GNR-PR-06** | 语义复用 | 优先映射已有 `plate` / `moment` / `peak` / `breath`，少造新角色 |
| **GNR-PR-07** | 场景分轨 | web 长滚 / present snap / 微信长图 共享等级，分轨缩放数值 |
| **GNR-PR-08** | 失败降级 | 无法评分时全部 L1 + 章界保留；禁止随机撒 L3 |

---

## 4. 概念模型

### 4.1 两层隐喻

```text
游记整卷 = 一座可走的摄影展
├── 封面 / 封底     → 大门与辞别
├── 章（Chapter）   → 展厅
│   ├── plate       → 厅门主视觉（L1，可轻抬）
│   ├── sequence    → 廊道连作（L0…L0 → L1）
│   ├── object      → 展室杰作（L2）
│   ├── breath      → 厅内换气（C）
│   └── peak/moment → 高光（L2 / 全书 L3）
└── 票根分隔         → 换厅门廊
```

### 4.2 观看态

| 观看态 | 用户心理 | 对应 mount | 身体感 |
|--------|----------|------------|--------|
| **廊道态 Continuum** | 接下来发生了什么 | L0, L1, C | 往前走 |
| **展室态 Object** | 这一张值得停 | L2, L3 | 停住、凝视 |

### 4.3 装裱等级定义

| Level | 名称 | 何时用 | 视觉语法（V1 建议值） |
|-------|------|--------|----------------------|
| **L0** | 廊道连作 | 同一叙事节拍的连续屏、组图后的紧邻屏 | `margin-bottom: 4–8px`；无额外 padding |
| **L1** | 默认换页 | 普通屏、章门 plate、厅内常规单图 | `margin-bottom: clamp(24px, 3.2vh, 36px)` |
| **L2** | 展室杰作 | 每章 1–2 个决定性画面；`peak` 默认 | 上下气口 `clamp(48px, 7vh, 88px)`；轻增 padding；内容区可微收至 ~92% 轨宽；纸面略提亮 |
| **L3** | 黑匣签名 | 全书 ≤1；默认=`moment` | 暗场底 `#141311`；上下气口 `clamp(72px, 11vh, 128px)`；内容区 ~88%；保留 Phase 23 角标与 EXIF |
| **C** | 呼吸换气 | 既有 `breath-pause-screen` | `min-height: clamp(64px, 10vh, 120px)`；极淡中心渐变；`···` 可保留 |

> **注**：L2/L3 的「微收宽度」用于制造展台感；不得出现圆角大卡片阴影。

---

## 5. 编辑公式（策展节奏）

### 5.1 章内推荐节拍

```text
厅门（plate · L1）
→ 连作 2–4 屏（L0…）          ← 照片小说
→ 杰作 1 屏（L2）              ← 摄影展
→ 连作或收束（L0/L1）
→ 换气（C）                     ← 可选，章较短可省
→ （可选）次高光 L2 / peak
→ 厅末
→ 票根 → 下一厅
```

### 5.2 全书配额

| 单元 | 配额 |
|------|------|
| L3 | 0–1 / trip（有 `momentAssetId` 则 1） |
| L2 | 1–2 / chapter；全书建议 ≈ `chapterCount + peakCount`（上限约内容屏 20%） |
| C | 沿用规划器插入；**渲染时必须达到 C 级高度** |
| L0 | 仅出现在被识别为 sequence 的邻接屏 |

### 5.3 禁止模式

- 连续 3 个 L2（展览疲劳、故事断裂）  
- L3 紧贴另一个 L2（双重高潮打架；中间至少 1 个 L1/C）  
- 章门 plate 直接标 L3（大门≠签名时刻）  
- 全部 L1 却放大统一间距（回到假平衡）  

---

## 6. 与现有图位映射

| 现有语义 | 默认 mount | 说明 |
|----------|------------|------|
| `cover-opening` / `cover-closing` | （书衣，不进 mount 表） | 保持电影感切场 |
| `layout-screen--plate` 章首 | **L1** | 厅门；不做 L2，以免章章开场都「杰作化」 |
| 普通 `layout-screen` | **L1** | 再由序列检测降为 L0 或升为 L2 |
| 组图屏（stack/mosaic）及紧随的叙事延续 | **L0** | 连作 |
| `data-role="peak"` | **L2** | 池内次高光 |
| `data-role="moment"` | **L3** | 全书签名；小册或关闭 moment 时不产生 L3 |
| `breath-pause-screen` | **C** | 高度修复为硬要求 |
| 章分隔票根 | 厅级标点 | 票根前勿再叠大 C，避免「停两次」 |

---

## 7. 数据契约

### 7.1 屏级字段（建议）

```json
{
  "screenIndex": 18,
  "mountLevel": "L3",
  "mountReason": "moment_signature",
  "mountLocked": false
}
```

| 字段 | 类型 | 说明 |
|------|------|------|
| `mountLevel` | enum | `L0` \| `L1` \| `L2` \| `L3` \| `C` |
| `mountReason` | string | `sequence` / `default` / `chapter_object` / `peak` / `moment_signature` / `breath` / `user_override` |
| `mountLocked` | bool | Studio 手动锁定后，自动重排不覆盖 |

### 7.2 HTML 契约

```html
<div class="layout-screen ..."
     data-screen-index="18"
     data-role="moment"
     data-mount="L3"
     data-mount-reason="moment_signature">
```

- 读者 CSS 只消费 `data-mount`  
- 调试角标仅 `html[data-debug-mount="1"]` 或 Studio 预览开关时显示  

### 7.3 CSS 变量（建议）

```css
html {
  --mount-l0-gap: 6px;
  --mount-l1-gap: clamp(24px, 3.2vh, 36px);
  --mount-l2-air: clamp(48px, 7vh, 88px);
  --mount-l3-air: clamp(72px, 11vh, 128px);
  --mount-c-min: clamp(64px, 10vh, 120px);
}
html[data-export="wechat-longshot"] {
  --mount-l1-gap: clamp(28px, 3.8vh, 44px);
  --mount-l2-air: clamp(56px, 8vh, 104px);
}
```

---

## 8. 自动编排算法（V1）

### 8.1 流水线位置

```text
curate（含 moment/peak/plate）
  → screen plan
  → mount assign（本 PRD）
  → render HTML/CSS
```

### 8.2 赋值伪代码

```text
for each screen:
  if breath: mount = C
  else if role == moment: mount = L3
  else if role == peak: mount = L2
  else if is_plate: mount = L1
  else: mount = L1

# sequence pass：把「组图屏 + 后续同节拍单图」压成 L0
for each chapter:
  mark contiguous narrative runs (same day/scene/cluster, no role peak/moment)
  for screens in run except last: mount = L0  (keep last as L1 unless hero)

# chapter object pass：每章补 0–1 个 L2（若尚无 peak/L2）
for each chapter:
  if count(L2|L3 in chapter) == 0:
    pick best solo landscape/portrait by aesthetic score (not used as cover/closing)
    mount = L2, reason = chapter_object

# conflict pass
if L3 adjacent to L2: demote neighboring L2 → L1 or insert/keep C between
clamp L2 per chapter ≤ 2
```

### 8.3 选型启发式（chapter_object）

优先：单槽、高审美分、章中后段、与 plate/cover/closing 资产去重。  
回避：纯组图屏升 L2（组图更适合 L0 连作）。

---

## 9. 交互（分阶段）

### 9.1 V1（本 PRD 必达）

- 静态 `data-mount` 渲染节奏  
- Studio：屏卡片显示等级，支持 ±1 调整（受配额）  
- 预览开关：「显示装裱标注」  

### 9.2 V1.1（凝视模式 · 可选）

| 触发 | 行为 |
|------|------|
| 滚动停驻 ≥ 600ms 于 L2/L3 | 邻屏微降透明度，本品气口临时 +1 档 |
| 播放（present）进入该屏 | 等同凝视；snap 对齐 |
| 离开 | 恢复廊道态 |

V1.1 **不改变** HTML 结构，只叠加临时 class。

---

## 10. 场景分轨

| 场景 | 策略 |
|------|------|
| Web 长滚（默认） | 本文数值 |
| Present / snap | L1/L2 气口 ×1.1；snap 对齐 screen 顶 |
| 微信长图导出 | L1/L2 ×1.25；L3 暗场上下气口封顶 96px，避免长黑带 |
| 性能模式 | 取消 L2 提亮与 inset 描边，仅保留间距差 |

---

## 11. Studio 体验要求

| ID | 要求 |
|----|------|
| **UX-GNR-01** | 时间线/屏列表可看到 mount 色点（绿 L0 / 灰 L1 / 琥珀 L2 / 红 L3 / 蓝 C） |
| **UX-GNR-02** | 一键「重算装裱」；手动锁定屏不被覆盖 |
| **UX-GNR-03** | 超出配额时 toast：说明「本厅杰作已满，将降级另一屏」 |
| **UX-GNR-04** | 帮助文案：廊道=故事，展室=作品，勿每屏升 L2 |

---

## 12. 验收（Acceptance）

### 12.1 定量

| ID | 门禁 |
|----|------|
| **AC-GNR-01** | 任意 trip：L3 数量 ∈ {0,1}；若有 `momentAssetId` 则 =1 且同屏 |
| **AC-GNR-02** | 每章 L2+L3 ≤ 2 |
| **AC-GNR-03** | 全部 `breath-pause-screen` 计算样式高度 ≥ 64px |
| **AC-GNR-04** | L0 屏的实测 `margin-bottom` ≤ 10px |
| **AC-GNR-05** | L1 屏的实测 gap ∈ 20–40px（desktop 1440×900） |
| **AC-GNR-06** | L2 屏前后气口均 ≥ 40px |
| **AC-GNR-07** | 回归：封面/票根/封底行为不被破坏 |

### 12.2 定性（小样本盲测 · n≥6）

| ID | 门禁 |
|----|------|
| **AC-GNR-08** | 「哪几屏像被单独布展」指出的屏中，≥70% 落在真实 L2/L3 |
| **AC-GNR-09** | 「是否像连续游记」5 分制均分 ≥ 3.8（对比原版不下降） |
| **AC-GNR-10** | 「是否有 PPT/卡片网站感」负向提及 < 20% |

### 12.3 试验记录（已完成 · 2026-07-20）

在 `demo-65db8fd377` 上完成手工策展注入（不改生产代码）：

| mount | 数量 | 屏索引（摘要） |
|-------|------|----------------|
| L0 | 12 | 2,7,9,11,16,17,21,27,28,31,34,37 |
| L1 | 13 | 章门与常规换页 |
| L2 | 5 | **3, 8, 23, 29, 36** |
| L3 | 1 | **18**（既有 moment） |
| C | 7 | 全部 breath，抬升为真留白 |

复现方式（推荐，避免粘贴编码报错）：

1. 打开该 demo 页  
2. 用编辑器打开项目根目录 **`.tmp-gn-exp-loader.js`**（单行 ASCII，全选复制）  
3. 浏览器 DevTools → Console → 粘贴 → Enter  
4. 左下角切换「①原版 / ②装裱节奏 / ③节奏+标注」

备选：`.tmp-gn-exp-console.js` 为可读源码；若直接粘贴报 `Invalid or unexpected token`，改用 loader。

> 不要粘贴文件名。`Unexpected token '.'` = 粘贴了文件名；`Invalid or unexpected token` = 多半是中文源码粘贴时编码被破坏。

---

## 13. 实施分期

| 阶段 | 范围 | 出口 |
|------|------|------|
| **M0 · 试验** | 注入脚本 + 本文档 + 盲测 | 产品拍板 DS-GNR-* |
| **M1 · 渲染契约** | `data-mount` + CSS 变量 + breath 高度修复 | AC-GNR-03/04/05/06 |
| **M2 · 自动赋值** | mount assign 接入 curate→render | AC-GNR-01/02/07 |
| **M3 · Studio** | 显示 / 覆写 / 锁定 | UX-GNR-* |
| **M4 · 分轨** | 长图 / present 数值 | 导出目视验收 |
| **M5 · 凝视模式** | V1.1 可选 | 单独小 PRD |

---

## 14. 风险与缓解

| 风险 | 缓解 |
|------|------|
| L2 样式过「卡片」 | 禁止投影与大圆角；只用气口+微收宽+轻微纸色 |
| L3 暗场在亮色 folio 突兀 | 仅 moment；前后强制 L1/C 缓冲 |
| 自动选错杰作 | Studio 一键降级；锁定；配额提示 |
| 与现有 `--screen-rhythm-gap` 冲突 | M1 起由 `data-mount` 覆盖 margin，变量分层 |
| 长图导出变长过多 | 分轨系数封顶；L3 气口封顶 |

---

## 15. 开放问题

| ID | 问题 | 建议 |
|----|------|------|
| **OQ-1** | plate 是否允许升 L2？ | 默认否；作者可手动 |
| **OQ-2** | 无 moment 的小册是否强制制造 L3？ | 否；保持 0 |
| **OQ-3** | 凝视模式是否进 MVP？ | 否，进 V1.1 |
| **OQ-4** | 文案题签（作品名）是否绑 L2？ | 建议 L2/L3 可挂一行题签；另开文案小节 |

---

## 16. 附录 A · demo-65db8fd377 手工策展表

| 章 | 屏 | mount | 策展意图 |
|----|----|-------|----------|
| 01 | 1 | L1 | 章门 plate |
| 01 | 2 | L0 | 抵达连作（三叠） |
| 01 | 3 | L2 | **本厅杰作** |
| 01 | 4 | L1 | 双肖像收束 |
| 01 | 5 | C | 换气 |
| 02 | 6 | L1 | 章门 |
| 02 | 7 | L0 | 连作 |
| 02 | 8 | L2 | **本厅杰作** |
| 02 | 9 | L0 | 三叠连作 |
| 02 | 10 | C | 换气 |
| 02 | 11–13 | L0/L1 | 后段推进 |
| 03 | 14 | L1 | 章门 |
| 03 | 15 | C | 轻换气 |
| 03 | 16–17 | L0 | 连作导向高潮 |
| 03 | 18 | L3 | **全书签名黑匣**（moment） |
| 03 | 19 | L1 | 余波 |
| 03 | 20 | C | 换气 |
| 03 | 21–22 | L0/L1 | 推进 |
| 03 | 23 | L2 | 次高光 peak |
| 03 | 24–25 | L1/C | 厅末 |
| 04 | 26 | L1 | 章门 |
| 04 | 27–28 | L0 | 连作 |
| 04 | 29 | L2 | **本厅杰作** |
| 04 | 30–32 | C/L0/L1 | 收束 |
| 05 | 33 | L1 | 章门 |
| 05 | 34 | L0 | 三叠 |
| 05 | 35 | C | 换气 |
| 05 | 36 | L2 | **终章杰作** |
| 05 | 37–38 | L0/L1 | 告别 |

---

## 17. 附录 B · 一句话产品立场

**游记的连续感来自廊道；艺术感来自偶尔真正的展室。**  
装裱等级让系统在每一屏回答同一个问题：「这一步，是走路，还是看作品？」

---

## 18. 变更记录

| 版本 | 日期 | 说明 |
|------|------|------|
| v0.1.0-GNR | 2026-07-20 | 初稿；完成 demo 手工策展试验与注入脚本 |
