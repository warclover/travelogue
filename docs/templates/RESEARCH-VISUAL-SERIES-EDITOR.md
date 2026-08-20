# 调研备忘 · 模板成册编排可视化引擎

| 属性 | 内容 |
|------|------|
| **日期** | 2026-08-15 |
| **类型** | 产品/工程调研（非正式 PRD） |
| **范围** | 同类商业产品与开源项目：版式图标、页序拖拽、成册序列 |
| **关联** | [PRD-TEMPLATE-SYSTEM-UPGRADE-V1.md](../PRD-TEMPLATE-SYSTEM-UPGRADE-V1.md) · [TEMPLATE-SYSTEM-UPGRADE.md](./TEMPLATE-SYSTEM-UPGRADE.md) §6 |
| **结论一句话** | 「用版式缩略图拖页序」是成熟交互；缺的是开源成品同时做「角色序列 + 槽账生成图标 + YAML 唯一真相」。借零件，不借整机。 |

---

## 0. 调研要回答什么

升级方案提出内部 **成册编排器**（图标 + 拖拉拽 + 系列 YAML）。拍板前需要知道：

1. 市场上是否已有同构产品或开源项目  
2. 哪些交互、数据模型值得抄  
3. 哪些会打穿本项目的封闭脸库 / 一屏一页 / 不管印刷  

---

## 1. 市场上其实有四层，别混成一个产品

| 层 | 在干什么 | 典型产品 | 和本项目的关系 |
|----|----------|----------|----------------|
| **填图编辑器** | 人选图拖进槽 | Mixbook、Canva 画册、Lumora | C 端路径；默认零步，内部编排器不要做成这个 |
| **换脸选择器** | 按「一页几张图」挑版式 | Lightroom Book、Mixbook Layouts、BookWright Layout Strip | **图标字典的直接对标** |
| **页序 / 全书视图** | 缩略图条上拖页 | Canva Page Manager、InDesign 页面面板、Mixbook All Pages | **页轨的直接对标** |
| **序列 / 母版编译** | 先定这一页干什么，再填 | InDesign 主页、Lightroom Auto Layout、Catalay YAML、sequences | **系列 YAML + 拖角色的对标** |

本项目要做的是后三层的**内部工具**，不是再做一个 Mixbook。

---

## 2. 案例

### 2.1 Lightroom Classic · Book 模块（图标语言的标准答案）

- 说明：[Peachpit · Working in the Book module](https://www.peachpit.com/articles/article.aspx?p=2999387&seqNum=2)  
- 补充：[B&H · 180+ templates](https://www.bhphotovideo.com/explora/photography/tips-and-solutions/how-to-make-a-photo-book-with-the-adobe-lightroom-book-module)

版式选择器里：**灰块 + 十字准星 = 图槽，横线框 = 文案槽**。内页按 **每页照片张数** 分组（1 / 2 / 3 / 4 / 多图）。全书 180+ 套，人靠「几格」而不是靠名字找。

另有 **Auto Layout Preset**（如「左空白、右单图」）一键铺满全书——即「系列」，只是写成预设，不是可 CRUD 的 YAML。全书 Multi-Page 视图 + 缩略图滑条。

| 借 | 不借 |
|----|------|
| 账徽按张数分组；微缩画槽不画照片；文案槽另一种记号；全书配方与单页换脸分开 | 右键任意加槽、拖锚点改几何（打穿封闭脸库） |

### 2.2 Blurb BookWright · Layout Strip

- [BookWright](https://www.blurb.com/bookwright)  
- [指南 PDF](https://downloads.blurb.com/sites/default/files/BookWrightGuide.pdf)  
- [Save Layout](https://support.blurb.com/hc/en-us/articles/207792306-Design-features-of-BookWright-layouts-covers-text-containers-soft-proofing-and-more)

版式缩略图带拖到某一页即换布局；做好的页可 Save Layout 再拖到别页。

| 借 | 不借 |
|----|------|
| 「拖版式到已有页」= 换 `faceHint`；保存自定义版式 = 新脸进观察室 | 空白页上自由画容器 |

### 2.3 Mixbook Studio

- [Studio](https://www.mixbook.com/studio)  
- [All Pages / 按张数筛 Layouts](https://www.tomsguide.com/us/how-to-create-photo-book-mixbook,review-5340.html)

侧栏 Layouts 按照片数筛（点「4」只看四图页）；All Pages 里拖整页换序；可按照片推荐版式。

| 借 | 不借 |
|----|------|
| 侧栏用 `3P` / `1L` 过滤；全书缩略图看节奏；按供给荐脸留给编译器 | 默认以跨页为编辑原子；贴纸/主题皮肤当一等公民 |

### 2.4 Canva · Page Manager

- [Page Manager](https://graphicdesignresource.com/managing-pages-in-canva-with-page-manager/)  
- [Photo Books](https://www.canva.com/photo-books/)

底栏缩略图：拖换序、页间 `+` 插入、一页套模板或应用到全部。一套 Photo Book 模板本身是多页系列。

| 借 | 不借 |
|----|------|
| 页间插入槽；「套到这一页」vs「套整本」必须分开 | C 端改网格和装饰；主题皮肤覆盖几何 |

### 2.5 InDesign · 页面面板 + 主页

主页是版式定义，页面是实例。「将主页应用于页面」= 换角色/换脸；页序在另一条列表里拖。

| 借 | 不借 |
|----|------|
| **主页 ≠ 页面**。系列里的一页是实例，角色/脸是主页 | 骑缝对页当默认画布；印前出血/页码 |

### 2.6 sequences（开源，最接近「先编后填」）

- [longfin/sequences](https://github.com/longfin/sequences)（MIT）

本地网页，专门做选图排序；README 写明 InDesign 在这个阶段太重。竖向摊开、可留空页、全书 contact sheet、3D 翻页 dummy。

| 借 | 不借 |
|----|------|
| 编排和填槽分阶段；空页/呼吸是一等公民；全书总谱 | 拖的是照片不是版式；默认跨页；几乎没有多槽模板 |

### 2.7 Catalay（开源，最接近「YAML 是真相」）

- [indiscipline/catalay](https://github.com/indiscipline/catalay)

TOML/YAML 声明目录页 → HTML 预览 → 灌进 InDesign。人改配置，不改排版软件。

| 借 | 不借 |
|----|------|
| 声明文件权威；预览是投影；编译器只读 | 优化的是商品目录宫格，不是旅行杂志节奏 |

### 2.8 IMG.LY CE.SDK Photobook UI（可嵌入商业套件）

- [Demo](https://img.ly/demos/photobook-ui/web/)  
- [starterkit](https://github.com/imgly/starterkit-photobook-ui-react-web)

版式是资源 `{ id, thumbUri, uri: layout.scene }`；套新版式时内容按槽重绑。侧栏页缩略图 + 加页。

| 借 | 不借 |
|----|------|
| 脸 = `{id, glyph, 几何}`；换脸保图、重切槽 | V1 为画布绑一家商业 SDK；贴纸/主题色当主路径 |

### 2.9 其它开源（参考价值有限）

| 项目 | 做什么 | 对本项目 |
|------|--------|----------|
| [Lumora](https://github.com/pchrysostomou/lumora) | 旅行画册 C 端，1/2/3/4/6 槽一键换，图回流 | 换脸回流可看；整体是填图器 |
| [Photo-Book-Binder](https://github.com/Kubimeter/Photo-Book-Binder) | 折手、签名、骑缝拼版 | 已定左侧胶装、不管印刷，**不抄** |
| [immich-book](https://github.com/ch1bo/immich-book) | 两端对齐流式排版，拖的是图 | 流式宫格 ≠ 封闭模板 |
| [storybook-co-editor](https://github.com/glenzli/storybook-co-editor) | 绘本：左页序拖拽，`[封面][扉页]` 标签，空白页凑印张 | 角色标签、空白页可看；印前拼版不抄 |

国内印厂编辑器（印鸽、世纪开元、有福）和稿定/创客贴，交互基本是 Canva 页管理 + 填槽，公开资料里没有「角色序列编译器」。

---

## 3. 行业共识 vs 本项目差异

**成熟工具都同意：**

1. 版式用示意图，不用实拍当图标（Lightroom / BookWright / Mixbook）  
2. 库存按每页张数分组（LR / Mixbook）  
3. 全书要有 All Pages 缩略图轨（Canva / Mixbook / LR Multi-Page）  
4. 「换这一页的版式」和「排全书顺序」是两个动作  
5. 专业线把定义（主页/系列）和实例（这一本的页）分开（InDesign / Catalay）

**几乎没有开源项目同时做这三件：**

- 拖的是页任务/角色，不是照片、也不是锁死的模板 ID  
- 图标从槽账自动生成（横几竖几），不是手绘 180 张 thumb  
- 系列是 YAML 合同，画布只是编辑器  

交互抄 Lightroom + Canva + InDesign 主页；数据模型走 Catalay；不要去找一个可以 fork 的「Travelogue 编排器」。

---

## 4. 明确不该抄

- **自由画框**（BookWright / LR Add Cell）：和封闭脸库、可回归探针冲突  
- **跨页当默认单位**（Mixbook / sequences）：已定一屏一页；全书视图仍做成单页网格  
- **折手/出血/骑缝拼版**（Photo-Book-Binder、绘本印前）  
- **C 端主题皮肤 + 贴纸**（Mixbook / CE.SDK）：工艺层以后再说  
- **流式 justified 宫格**（immich-book）：吃掉朝向硬门  
- **商业 SDK 当 V1 底座**：除非单独采购评审；章程是模板 + manifest 出页，不是 scene 编辑器出 HTML  

---

## 5. 对落地方案 7 条拍板的含义

| # | 落地方案原建议 | 调研含义 |
|---|----------------|----------|
| 1 | 独立 `/series-editor` | 对。LR / InDesign / Canva 都把全书页序做成独立表面 |
| 2 | 主拖角色，脸只换 hint | 对，且是差异化。V1 可做成「拖角色（带默认微缩）」，看起来像拖版式，写入仍是 role |
| 3 | SVG 由数据包生成 | 行业多用静态 thumb。生成更适合本库（脸少、字段会变）。分组方式仍抄 LR：按张数/横竖 |
| 4 | YAML 是唯一真相 | 对。Catalay 已证明「声明 → 预览 → 编译」 |
| 5 | V0 只读 → V1 拖 → V2 预演 | 对。sequences 主张先序后填。V0 做成 LR Multi-Page 只读总谱即可验收图标 |
| 6 | 页轨用换行网格，不对页画布 | 对。仍建议学 Canva/LR 做缩略图缩放滑条。邻页只用密度条软规则 |
| 7 | 竖红横蓝 + 角标 | 对，比 LR 全灰十字多了朝向信息。文案可用细线框，默认仍可不画 |

调研额外建议（未写入原 7 条）：

**库存按槽数分组（1 / 2 / 3 / 4 / 6+），不要平铺 18 个图标。** Lightroom 与 Mixbook 都靠这个降低寻找成本。

---

## 6. 合成建议

没有现成开源引擎可以「装上就用」。有的是经过十年验证的 **页轨 + 版式示意图 + 主页/实例分离**。落地应是：

- 外观像 Lightroom 选版式 + Canva 拖页  
- 心智像 InDesign 主页  
- 存盘像 Catalay  

而不是再造一个用户向的 Mixbook。

---

## 7. 修订

| 版本 | 日期 | 说明 |
|------|------|------|
| 0.1.0 | 2026-08-15 | 初稿。对应升级方案 v2.1 图标章与可视化编排落地方案拍板前调研。 |
| 0.1.1 | 2026-08-15 | 交叉引用随升级方案 v2.2 改为 §6。 |
| 0.1.2 | 2026-08-15 | 关联升为 TSU 正式 PRD。 |
