# Travelogue · 备用库成册样例柜 V1（PRD）

| 属性 | 内容 |
|------|------|
| **产品代号** | Travelogue |
| **文档版本** | **v0.1.0** |
| **状态** | **W1 已落地**（2026-08-18 产品拍板 · 最小闭环已实现） |
| **DOC-STATUS** | **active** |
| **特性代号** | **RSC**（Reserve Series Cabinet） |
| **文档类型** | 备用库手编样例柜产品合同（设计工具，不是现网成册引擎） |
| **触发来源** | 2026-08-18 成册 tab 要排多本样例、不能覆盖 16 页金样；四条产品决定已拍板 |
| **前置** | 备用库 `gallery.html` 成册 tab + `series/folio-16-standard.yaml` 已能手编一本；真图试印「按系列」已能铺该本 |
| **工坊总合同** | [PRD-TEMPLATE-DESIGN-VERIFICATION-V1.md](./PRD-TEMPLATE-DESIGN-VERIFICATION-V1.md)（**TDV** · 设计工坊）。本文是成册柜细则，不废止。 |
| **正式成册合同** | [PRD-TEMPLATE-SYSTEM-UPGRADE-V1.md](./PRD-TEMPLATE-SYSTEM-UPGRADE-V1.md)（TSU · `/series-editor` · 引擎系列）。**本文不升格、不代替 TSU。** |
| **现场** | [templates/reserve/README.md](./templates/reserve/README.md) · [templates/reserve/临时模板库管线讨论备忘录.md](./templates/reserve/临时模板库管线讨论备忘录.md) |
| **线框对照** | TSU F4 编排器（左库存 / 中页轨 / 右检查器）。本波只在备用库成册 tab 扩「柜」，不新开 `/series-editor` |
| **不改** | 引擎、MCS、`layout_templates`、`trip.json`、封面封底砖、备用库脸几何、星级写入 |
| **更新日期** | 2026-08-18 |

> **一句话目标**：在备用库成册 tab 里，手编并保存**很多本**页序样例（任意页数、多轮试印），每本一份 YAML；16 页金样不被覆盖。引擎不读。
>
> **产品铁律**
>
> 1. **样例柜，不是第二本 SKU。** 页数任意，本数不封顶。禁止把「32 页」写成唯一第二档。  
> 2. **仓库 YAML 是本。** 浏览器只是按 id 分开的草稿。未写入的轨不算柜里的一本。  
> 3. **日常走本地静态服。** 不养多种子表。`file://` 只保证 16 页金样还能看见。  
> 4. **保存只覆盖当前 id。** 新建 / 另存必须新 id；禁止默认盖 `folio-16-standard.yaml`。  
> 5. **本波只做手编柜。** 不做自动填页、疏密矩阵、书衣、正式编排器、引擎消费。

---

## 0. 读者指南

| 章节 | 澄清什么 |
|------|----------|
| §1 | 问题与现网单例 |
| §2 | 目标 / 非目标 / 与 TSU 边界 |
| §3 | 已拍板决策 D-RSC-01～16 |
| §4 | 身份、目录、打开方式 |
| §5 | 数据模型（本 / 目录 / 草稿） |
| §6 | 成册 tab 与试印交互 |
| §7 | 校验与红灯 |
| §8 | 里程碑 |
| §9 | 验收 AC-RSC-* |
| §10 | 风险与开放问题 |
| 附录 A | 实施时会动的文件（对照，不是合同正文） |

实施清单不平行另开；Kickoff 后按 §8 / §9 改代码。

### 0.1 术语

| 术语 | 定义 |
|------|------|
| **本 / 样例** | 一份系列 YAML。身份是 `id`。柜里的一本书。 |
| **样例柜** | 备用库 `series/*.yaml` 的集合 + 成册 tab 的切换 / 新建 / 保存 + 试印选本 |
| **金样** | `folio-16-standard`。第一本 16 页正。只读身份：新建 / 另存不得占用此 id |
| **开口径** | 新建时写下的目标 `pageCount`（与密度）。页数是意图，不是「轨上现有几页」 |
| **软目标** | 允许 `sequence.length ≠ pageCount` 时仍保存为 `sketch`。顶栏写「目标 N / 现 M」 |
| **目录** | 静态服扫描 `series/*.yaml` 派生的本列表。浏览器不维护第二份清单文件 |
| **草稿** | `localStorage` 里按 id 分格的未写入状态。不是本 |
| **种子** | 仅 `series-folio-16.js` 这一份，给 `file://` 应急看金样。新本不进种子 |

### 0.2 与相邻主题（所有权）

| 主题 | RSC 做 | RSC 不做 |
|------|--------|----------|
| **TSU** | 沿用角色 / 纲领 / 邻页软规则 / 书衣沿用现网；线框对标 F4 | 不写引擎系列、不建 `/series-editor`、不完成 B7 七本正式 SKU |
| **EDC** | 页上可标 `program`（人标） | 不编译、不匹配角色 |
| **AEL / ECC** | 无 | 不把 `page-*` 接到画册跨页 |
| **备用库微缩 / 星级** | 成册库存继续读本库脸与星级排序 | 不改 `stars.yaml` 写入、不改脸几何 |
| **真图试印** | 「按系列」改为按柜选本 | 不改「按星级」铺脸；不做填图器 |

---

## 1. 问题与现网

### 1.1 要解决的问题

作品集管线要靠**多本手编页序**试节奏（16 / 24 / 32 / 任意页、多轮改），不是先定一个正式 32 页 SKU。

现网成册整条链是**单例**：

| 层 | 现状（2026-08-18） |
|----|-------------------|
| 身份 | `id` / `pageCount` / `photo_span` / 保存文件名写死 `folio-16-standard` |
| 草稿 | 一个 `localStorage` 键，后开的盖先开的 |
| 落盘 | 「写入系列」永远建议覆盖同一份 YAML |
| `file://` | 只认一份 `series-folio-16.js` |
| 试印 | hash 能写 `series=`，正文仍当 16 页正 |
| 红灯 | closer 中段按 `1–14 / 16` 写死 |

只加「新建」按钮、保存仍走旧路径，**必然会覆盖金样**。这不是手误，是产品没做柜。

### 1.2 现网仍保留

- 成册仍在 `gallery.html` 第二 tab，不新开页面。  
- 拖脸、换同族、朝向拒收、检查器改纲领 / 弹性位，本波不改手感。  
- 「写入系列」「复制 YAML」「按本序试印」仍在。  
- 金样文件 `series/folio-16-standard.yaml` **继续存在**，内容本波不改（除非人主动打开该本并写入）。  
- 引擎、CI、MCS **继续不读** `docs/templates/reserve/`。

---

## 2. 目标与非目标

### 2.1 目标（本波出门）

做成**手编样例柜**：

1. 能**列出**已落盘的本，成册与试印共用同一目录。  
2. 能**新建**一本：任意正整数页数 + 新 id + 默认空轨，可选从已有本复制。  
3. 能**切换**当前本；未保存草稿按 id 分格；切本时脏草稿要拦。  
4. 能**按当前 id 写入** `series/<id>.yaml`，不默认覆盖金样。  
5. 试印 `#series=<id>` 铺该本页序；标题、建议张数跟本走。  
6. 日常用本夹静态服打开；种子表不扩张。

### 2.2 非目标（本波明确不做）

| 不做 | 说明 |
|------|------|
| 正式 SKU 量产 | 不要求 8/16/20×疏正密七本齐；不升附录 A |
| 疏 / 密当同一本开关 | 疏密以后**另开一本**，`density` 本波默认 `standard` |
| 自动填页 / 匹配器 | 人拖脸；不调用 MCS |
| 书衣砖 | 封面 `veil-footer`、封底现网收束；不编封面封底页 |
| 引擎消费 | 不进 `layout_templates`、不写现网系列目录、不改 `trip.json` |
| `/series-editor` | 不迁 Studio 后台 |
| 并排对照台 | 两本可先后试印，不做双栏 |
| UI 删本 / 重命名 | 手删 YAML 后刷新目录即可 |
| 把脸画软 | 朝向硬门、组先于脸，沿用备忘录 |
| 多种子双写 | 新本只写 YAML |

### 2.3 与 TSU 档位的关系

TSU D-U-07：正式先做 8/16×疏正密，金样 20 页正；档位表有 4…32。禁止小本×2 当正式 SKU。

RSC：**测试样例不受该表限制。** 新建可给 18、22、32。建议芯片用 TSU 档位，**不挡**保存。从 16 页复制再加页，是派生样例，id 必须是新的，不得把金样拉长冒充正式 32 页档。

---

## 3. 冻结决策

| ID | 决策 |
|----|------|
| **D-RSC-01** | 柜里一本 = 一个 `id` = 一份 `docs/templates/reserve/series/<id>.yaml`。 |
| **D-RSC-02** | `id` 匹配 `^[a-z][a-z0-9-]{1,47}$`。新建时人可改建议名。与已有本或金样撞车则拒。 |
| **D-RSC-03** | 建议名 `folio-{pageCount}-{density}`；同口径多轮加后缀（`folio-24-standard-r2`、`folio-18-standard-river`）。 |
| **D-RSC-04** | `pageCount` 为任意 ≥1 整数。开口径。软目标：轨上页数可以不等于它。 |
| **D-RSC-05** | 本波 `density` 默认 `standard`。界面不提供疏/密切换；字段写入 YAML 以便以后另开本。 |
| **D-RSC-06** | `folio-16-standard` 是金样。新建 / 另存 / 复制为本 **禁止**使用此 id。打开该本后「写入系列」仍可更新它（金样迭代）。 |
| **D-RSC-07** | 手编样例 `status: sketch`，`kind: series`，`stage: "16:9"`。书衣字段沿用 `coverHint: veil-footer`、`backHint: closing-default`，本波不编砖。 |
| **D-RSC-08** | 新建默认**空轨**。可选「从柜里已有本复制」（第一轮复制源含金样）。复制 = 新 id + 拷 `sequence`，可另写目标 `pageCount`。 |
| **D-RSC-09** | **仓库 YAML 是本。** 试印目录与「按系列」默认只列已落盘文件。未保存本若要预览，必须标明「未保存的 &lt;id&gt;」。 |
| **D-RSC-10** | 草稿按 id 分格。禁止再用单键盖掉另一本未保存改动。切本、新建前若当前本脏，先选留下（写入）或丢掉草稿。 |
| **D-RSC-11** | 「写入系列」建议文件名 = `<id>.yaml`，目标目录 = `series/`。校验：文件内 `id` 与当前本一致，且 `kind: series`。 |
| **D-RSC-12** | **日常打开 = 本夹静态服。** 目录由服务端扫描 `series/*.yaml` 派生。浏览器不写第二份 catalog 文件。 |
| **D-RSC-13** | `series-folio-16.js` **只**服务金样的 `file://` 应急。新本不进种子、不双写。`file://` 下列不出新本，须提示去开静态服。 |
| **D-RSC-14** | `photo_span` 跟该本走，不沿用金样 48–80（除非该本就是 16 页正且空轨，见 §5.3）。试印「建议张数」= 当前本 `photo_span[0]`。 |
| **D-RSC-15** | 红灯跟当前 `pageCount` 与邻页走，不写死 16。见 §7。 |
| **D-RSC-16** | 引擎 / MCS / CI / 现网系列目录 **不读**本柜。本波零 Python 业务包、零 pytest 业务断言（静态服脚本除外）。 |

看见「32 页」只是样例之一，不是本合同的默认第二本。

---

## 4. 身份、目录、打开方式

### 4.1 文件布局

```
docs/templates/reserve/
  gallery.html          # 微缩 + 成册
  preview.html          # 按星级 / 按系列
  bind.js               # 成册：柜 + 轨
  series-folio-16.js    # 仅金样 file:// 种子
  serve.py              # 本波新增：静态服 + 目录 API
  serve.cmd             # 本波新增：Windows 一键打开
  series/
    folio-16-standard.yaml
    <id>.yaml           # 以后每一本
```

禁止把新本 YAML 写到 `series/` 以外。禁止把页序写进 `stars.yaml` / `catalog.yaml`（页型总表）/ `trip.json`。

### 4.2 目录 API（静态服派生）

`GET /series/index.json`（仅静态服提供）：

```json
{
  "books": [
    {
      "id": "folio-16-standard",
      "pageCount": 16,
      "density": "standard",
      "status": "sketch",
      "pages": 16,
      "slots": 53,
      "photoSpan": [48, 80]
    }
  ]
}
```

扫描规则：`series/*.yaml`，文件内须有 `kind: series` 与 `id:`。`id` 与文件名（去 `.yaml`）不一致则**不入目录**，成册打开该文件时红灯（防写错文件）。忽略 `series/` 下非 yaml。

`pages` = `sequence` 行数。`slots` = 各行 `faceHint` 在本库脸表上的槽数合计（未知脸计 0）。

`file://` 无此 API：目录 = 金样一种子，可加本机草稿 id（标未保存）。新 YAML 不可见。

### 4.3 打开方式

| 路径 | 行为 |
|------|------|
| **主路径** | 双击 `serve.cmd` 或在本夹运行 `python serve.py`。起在 `127.0.0.1` 固定端口 **18765**（避开现网 serve / golden 常用的 8765–8766），占用则试 18766–18774。自动打开 `gallery.html#tab=bind`。 |
| **试印** | 同一源打开 `preview.html`。跨源 `file://` ↔ `http://127.0.0.1` 的 localStorage **不共用**，故草稿不能当目录。 |
| **`file://` 应急** | 成册 / 试印仍能看到金样。顶栏常驻一句：新本请用 `serve.cmd`。 |
| **复制 YAML** | 保留。保存框选错目录时，把文本贴回 `series/<id>.yaml`。 |

静态服用标准库即可（`http.server` 子类）。不引入 npm、不进 Studio Hub。

### 4.4 种子收缩

| 文件 | 本波 |
|------|------|
| `series-folio-16.js` | 保留。内容继续与金样 YAML 同步。**只有改金样页序时才改它。** |
| 其它 `series-*.js` | **禁止新增** |

---

## 5. 数据模型

### 5.1 系列 YAML（一本）

字段与现网金样同构，仅身份与口径跟本走：

```yaml
id: folio-24-standard-r1
kind: series
status: sketch
stage: "16:9"
pageCount: 24
density: standard
photo_span: [72, 120]
coverHint: veil-footer
backHint: closing-default
sequence:
  - { i: 1, role: hero-land, program: hero, faceHint: page-1-hero-land-wide }
```

| 字段 | 规则 |
|------|------|
| `id` | 与文件名一致 |
| `pageCount` | 目标页数，整数 ≥1 |
| `density` | 本波写 `standard` |
| `photo_span` | `[lo, hi]`，`lo ≤ hi`，整数。算法见 §5.3 |
| `sequence[].i` | 写入时重排为 1…N（N = 轨上实际页数） |
| `sequence[].role` / `program` / `faceHint` | 与现网成册相同；看起来拖脸，落盘写这三项 |
| `sequence[].flex` | 可选。真则写出 `flex: true` |

序列行语法保持现网单行 `{ i, role, program, faceHint }`，便于现网 `bind.js` 解析器沿用。

### 5.2 草稿

新键：`reserve-series-drafts-v2`

```json
{
  "currentId": "folio-24-standard-r1",
  "drafts": {
    "folio-16-standard": { "series": {}, "file": {} },
    "folio-24-standard-r1": { "series": {}, "file": {} }
  }
}
```

迁移：若存在旧键 `reserve-series-draft-v1` 且其 `series.id` 为金样，则纳入 `drafts[folio-16-standard]`，然后不再读旧键（可读一次后丢掉，避免和柜抢权威）。

单本草稿体积应可接受；本波不做草稿 GC。实现时注意勿把整份脸库写进草稿。

### 5.3 `photo_span`

密度 `standard` 的 PPC 带 = **3–5**（与现网顶栏「正 · PPC 3–5」一致）。

| 轨状态 | 默认 `photo_span` |
|--------|-------------------|
| 空轨 | `[pageCount × 3, pageCount × 5]`。金样 16 → `[48, 80]`，与现网闭合。 |
| 有页 | 仍以**开口径**算默认带：`[pageCount × 3, pageCount × 5]`。槽合计只用于顶栏对照，不自动改带。 |

复制本：新本按**新** `pageCount` 重算带，不沿用源本的 48–80。

本波检查器不提供手改 `photo_span`。以后要疏/密本，另立 PPC 表。

试印文案：每个相册建议 ≥ `photo_span[0]` 张；少于则标「少」。密页组锁子夹名为 `01`…`NN`，`NN = max(pageCount, sequence.length)`，不再写死 `01`…`16`。

---

## 6. 界面

仍三栏：左库存、中页轨、右检查器。本波增量在**顶栏 + 新建对话框 + 试印选本**。

### 6.1 成册顶栏

从左到右：

1. 品牌「成册编排」  
2. **本切换**：下拉。已落盘本 + 仅存在于草稿的本（标「未保存」）。当前项显示 `id`。  
3. 页数芯片：`目标 {pageCount} / 现 {n}`。`n === pageCount` 或 `n === 0` 中性；否则琥珀。  
4. 密度芯片：`正 · PPC 3–5`（只读）  
5. 槽芯片：`当前 {slots} 槽 · 带 {lo}–{hi}`，低于 lo / 超过 hi 琥珀。  
6. 脏芯片：未保存 / 已与文件一致  
7. 「不写 trip.json」  
8. 右侧按钮：**新建** · **复制为本** · 按本序试印 · 复制 YAML · 写入系列  

去掉写死的 `folio-16-standard.yaml` 单芯片，改由本切换承担。

### 6.2 新建

对话框（或顶栏展开条，二选一，须一次开口径）：

| 字段 | 规则 |
|------|------|
| 目标页数 | 数字。建议芯片：8 / 16 / 20 / 24 / 28 / 32。可键入任意 ≥1 |
| id | 默认 `folio-{pageCount}-standard`；若已占用则自动 `-r2`、`-r3`… |
| 起点 | **空轨**（默认） / 从某本复制 |
| 复制源 | 柜里已落盘的本（含金样）。无本时该项禁用 |

确定后：当前本切到新 id；`pageCount` / `photo_span` 按 §5.3；空轨则 `sequence: []`；复制则深拷源 `sequence`（可短于目标）。**不自动写入 YAML。** 顶栏标未保存。人点「写入系列」才落盘。

### 6.3 复制为本

等价于新建且起点预选当前本。必须改 id。不得把结果存回金样 id。

### 6.4 切换与脏拦截

切到另一本、新建、离开成册 tab **不**强制写入。若当前本 `serialize` ≠ 上次成功写入（或首次未写），弹出：

- 写入系列（走现网保存框）  
- 丢掉草稿并切换  
- 取消  

丢掉 = 删掉该 id 的草稿格；已落盘文件不动。

### 6.5 写入系列

与现网相同：优先 File System Access，`suggestedName = <id>.yaml`；`id` 目录建议独立（按本，不要所有本共用一个 file picker id 导致总盖同一文件）。失败则下载。成功后该本进入目录（刷新 `index.json`）。

写入**不得**改其它 YAML。实现时禁止把当前序列序列化成金样文件名，除非当前 id 就是金样。

### 6.6 页轨

沿用现网：拖入插入、同族换脸、朝向拒收、金色「再加一页」、检查器改纲领与 flex。  
空轨时中间是空壳 + 投放区，不预置 N 张空白页（避免假页）。目标页数只出现在顶栏。

### 6.7 试印（`preview.html`）

| 项 | 合同 |
|----|------|
| 模式 | 「按星级」不动。「按系列」读目录 + hash |
| 选本 | 下拉已落盘本。无目录（`file://`）则只有金样种子 |
| hash | `#series=<id>`；可与 `album=` 并存 |
| 缺本 | 「柜里没有 &lt;id&gt;。回成册新建并写入 series/&lt;id&gt;.yaml」 |
| 标题 | `{id} · 目标 {pageCount} 页 · 现 {n} 页`，禁止写死「16 页正」 |
| 入座 | 按朝向消耗，用过的不再给后面的页（现网按系列语义） |
| 未保存 | 默认不铺纯草稿。若实现选择铺当前草稿，必须在标题加「未保存」且 hash 带 `draft=1` |

成册「按本序试印」链到 `preview.html#series=<当前id>`。

### 6.8 文案

成册导语改为柜，不再写「只写入 folio-16-standard.yaml」。  
备用库 README 成册节改为指向本文 + `serve.cmd`。

---

## 7. 校验与红灯

### 7.1 保存前硬拒（不写文件）

- `id` 不合 D-RSC-02  
- 新建 / 另存 id 为 `folio-16-standard`  
- 序列化后 `id` 与当前本不一致  

软目标：**不**因页数未满而拒写。

### 7.2 顶栏 / 检查器红灯（可保存）

沿用并改写死 16 的部分：

| 灯 | 规则 |
|----|------|
| 相邻密页 | 连续两页槽数都 ≥5 |
| opener 连 opener | 邻页 `program` 皆为 `opener` |
| closer 在中段 | `program === closer` 且页码 ≤ `pageCount - 2`（16 页时即 ≤14，与现网同构） |
| 页数未对齐 | `n > 0` 且 `n ≠ pageCount`（琥珀，不是红） |
| 槽出带 | `slots < lo` 或 `slots > hi`（琥珀） |
| 文件名与 id | 目录扫描发现不一致（红，且不入柜） |

邻页双密页、opener 连 opener：有则红，仍允许写入（与现网一致：灯是编辑提示，不是门禁）。

### 7.3 拖入规则（不改）

朝向或家族不符：**拒收换脸**。插入走空隙或「再加一页」。不把脸画软。

---

## 8. 里程碑

| 波 | 做什么 | 完成标志 |
|----|--------|----------|
| **W0** | 本文 v0.1.0 合入索引 | 产品确认四条决定已写进 D-RSC；**本波已完成** |
| **W1** | 最小闭环：静态服 + 目录 + 新建/切换/按 id 保存 + 试印选本 + 草稿分格 + 金样保护 | §9 AC-RSC-01～12 绿。**不**覆盖金样页序（除非测试时显式打开金样） |
| **W2**（可选，另立） | 检查器改 `photo_span` / `density`；UI 删本；试印铺未保存草稿 | 不在 W1 出门 |

W1 一次做完。禁止先做新建按钮、保存仍写死金样文件名。

---

## 9. 验收

实现后在备用库用静态服手验。不进 CI。

| ID | 断言 |
|----|------|
| **AC-RSC-01** | `serve.cmd` / `python serve.py` 能打开成册 tab；`GET /series/index.json` 至少含 `folio-16-standard`。 |
| **AC-RSC-02** | 成册下拉能看到柜里每一本已落盘 YAML（id 与文件名一致者）。 |
| **AC-RSC-03** | 新建：页数 32、空轨、id `folio-32-standard`（若空闲）。轨为空；顶栏「目标 32 / 现 0」；未写入前试印目录**没有**这本。 |
| **AC-RSC-04** | 对该本「写入系列」，保存框建议 `folio-32-standard.yaml`。写入后刷新目录可见；`folio-16-standard.yaml` 内容不变。 |
| **AC-RSC-05** | 新建禁止把 id 设为 `folio-16-standard`（控件拒或确定时拒）。 |
| **AC-RSC-06** | 「从 folio-16-standard 复制」得到新 id，页序与金样相同，金样文件未被改。 |
| **AC-RSC-07** | 在 A 本改一页不保存，切到 B：出现拦截。丢掉后 A 的文件仍是旧内容；留下则走写入。 |
| **AC-RSC-08** | 两本各有未保存草稿时，切回 A 仍是 A 的轨，不是 B 的。 |
| **AC-RSC-09** | 试印选 `folio-32-standard`（或 hash `#series=folio-32-standard`）铺该本页数，标题不含写死的「16 页正」。 |
| **AC-RSC-10** | `file://` 打开 gallery / preview：仍能看见金样 16 页；新本不出现；有去静态服的提示。 |
| **AC-RSC-11** | 任意页数（例 18）可新建、可写入、可试印。`photo_span` 默认 `[54, 90]`。 |
| **AC-RSC-12** | 仓库内无新的 `series-*.js`（金样那一份除外）。引擎路径、MCS、`layout_templates` 无新增引用 `reserve/series`。 |

---

## 10. 风险与开放问题

| ID | 内容 | 默认 |
|----|------|------|
| **R-RSC-01** | File System Access 仍可能存到「下载」。复制 YAML 保留。 | 接受 |
| **R-RSC-02** | `http://127.0.0.1` 与 `file://` 草稿隔离。主路径只用静态服。 | 接受 |
| **R-RSC-03** | 金样页序若在 W1 被误写，用 git 还原该文件。 | 验收盯 AC-RSC-04/05 |
| **OQ-RSC-01** | 是否允许试印带 `draft=1` 铺未保存本。 | W1 **否**（D-RSC-09） |
| **OQ-RSC-02** | 空轨是否预置 N 张占位页。 | W1 **否**（§6.6） |
| **OQ-RSC-03** | 非 `standard` 的 PPC。 | 本波不做 |

---

## 附录 A · W1 将动的文件（对照）

合同以正文为准。实施时预期改动：

| 文件 | 动作 |
|------|------|
| `docs/templates/reserve/serve.py` | 新增 |
| `docs/templates/reserve/serve.cmd` | 新增 |
| `docs/templates/reserve/bind.js` | 去单例；柜 / 新建 / 草稿 v2 / 按 id 保存 |
| `docs/templates/reserve/gallery.html` | 导语、顶栏容器够用即可 |
| `docs/templates/reserve/preview.html` | 选本、标题、hash、密页 `01`…`NN` |
| `docs/templates/reserve/README.md` | 成册节改为柜 + 静态服 |
| `docs/templates/reserve/series-folio-16.js` | **不改**（除非金样 YAML 变） |
| `docs/templates/reserve/series/folio-16-standard.yaml` | **不改** |

不改：`faces.js`、`roles.js`、各 `page-*/packet.yaml`、引擎包。
