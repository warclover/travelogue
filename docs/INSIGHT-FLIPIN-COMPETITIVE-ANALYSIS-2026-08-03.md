# Flipin 竞品深度调研 · 与 Travelogue 多维对比

| 属性 | 内容 |
|------|------|
| **调研对象** | [flipin.pages.dev](https://flipin.pages.dev/)（「数字拼贴手账本」网页应用） |
| **文档版本** | v1.0 |
| **状态** | Draft |
| **调研日期** | 2026-08-03 |
| **调研方法** | Playwright 实测（新建流程截图走查）+ 官网公开内容全量抓取 + 本仓库代码/文档交叉核查（非纯文档臆测） |
| **关联文档** | [RESEARCH-TRAVEL-PHOTO-AUTO-LAYOUT-V1.md](./RESEARCH-TRAVEL-PHOTO-AUTO-LAYOUT-V1.md) · [PRD-COMMERCIALIZATION-MVP-V1.md](./PRD-COMMERCIALIZATION-MVP-V1.md) · [PRD-COVER-ART-DIRECTION-V1.md](./PRD-COVER-ART-DIRECTION-V1.md) · [PRD-WAIT-TIPS-V1.md](./PRD-WAIT-TIPS-V1.md) · [PRD-PREVIEW-EXPORT-FACADE-V1.md](./PRD-PREVIEW-EXPORT-FACADE-V1.md) · [PRD-OUTPUT-RECIPE-V1.md](./PRD-OUTPUT-RECIPE-V1.md) · [PRD-IMPORT-SHEET-v3-WIZARD.md](./PRD-IMPORT-SHEET-v3-WIZARD.md) |

> 核查说明：本文核心流程截图（书架 / 风格二选一 / 加照片）来自 Playwright 实机操作 flipin.pages.dev；编辑器内工具条、抠图、导出五格式等细节来自官网公开页面内容全量文本（非截图，标注为「站内文案还原」）；本项目现状对照均反查了 `travelogue/export/`、`docs/PRD-IMPORT-SHEET-v3-WIZARD.md` 等代码/文档事实，未凭印象下结论。

---

## 一、Flipin 一句话画像

**纯前端网页版「数字手账拼贴本」**：全站无账号、无后端 API，数据存在浏览器 `localStorage` / `IndexedDB` 里；整套体验被包装成**实体书隐喻**——书架、装订、封皮、翻页；文案拟人化且轻松（如「好东西值得等一小会儿」「删了就找不回来了哦」）。

产品哲学与 Travelogue 完全不同：Flipin 是**手工拼贴工具**，用户自己摆图、抠图、调背景；Travelogue 是**AI 策展 + 智能排版**，追求"少决策、自动出结果"。

---

## 二、实测流程走查

### 1. 书架（首页 · 单本轮播视图）

首页即"我的书架"，默认展示一本示例书 `FLIPIN #000`；左上角可切换网格/轮播视图，右上角删除当前本，右下角悬浮 `+` 新建。

![Flipin 书架](acceptance-records/attachments/flipin-competitive-2026-08-03/01-bookshelf.png)

### 2. 新建 Step 1 · 风格二选一

点击新建后，**全程只问一句话**："今天做本什么样的？选一种感觉，Flipin 帮你搭个调子"，给两个风格缩略图（高饱和拼贴 / 氛围感杂志）直接展示效果预期，不问字体、配色、版式这些细节；顶部三点式步骤指示器（step 1/3）。

![Flipin 风格选择](acceptance-records/attachments/flipin-competitive-2026-08-03/02-style-pick.png)

### 3. 新建 Step 2 · 加照片

上限张数明确告知（实测页面文案为 30 张，官网公开文案历史版本为 15 张，说明该上限在持续调整）；未选照片时"选好了"按钮为禁用态，反馈清晰。

![Flipin 加照片](acceptance-records/attachments/flipin-competitive-2026-08-03/03-photo-import.png)

### 4. 装订动效（站内文案还原）

提交后是一段"正在装订中... 好东西值得等一小会儿 1/5"的进度动画，用"装订"这个实体书隐喻包装等待态，而非单纯的进度条。

### 5. 编辑器（站内文案还原）

- **底部工具条**：模版 / 文字 / 调整 / 清空 / 替换 / 删除
- **抠图（去背景贴纸）**：开始抠图 → 背景色可调（如 `#EEEAE3`）→ 大小（%）/ 旋转（°）可调 —— 这是 Flipin 最独特的差异化能力，可以让照片主体像"贴纸"一样自由摆放
- **垫底背景**：波点 / 格纹预设图案 + 自定义颜色（hex）+ 自定义图片
- **封面设置**：2 套封面模板（基础封面 / **镂空笔记本**——封皮开孔露出内页图）+ 封皮颜色/文字颜色/标题 + 自定义封面图，支持"拖动、双指捏合调整"；另有"换个封面 / 换个背景"一键重掷按钮

### 6. 导出（站内文案还原）

一次给 **5 种格式**：多跨页拼图（JPG）· Live 图 · MP4 · 单页 JPG · 整本 PDF · 分享网页。清晰度分**标准 / 高清 / 超清**三档并直接标出像素数（如 2560×3616）；支持缩略图**逐页勾选**要导出的页面；并有"iOS 会弹菜单，选「储存图像」就进相册啦"这种移动端使用引导。

---

## 三、多维对比

| 维度 | Flipin | Travelogue（本项目现状） |
|---|---|---|
| **产品心智** | 手工拼贴本 DIY 工具，用户主导排版 | "游记智能体"——AI 策展 + 智能排版，追求"省心自动出结果" |
| **技术形态** | 纯前端网页（PWA 风格），本地 `localStorage`/`IndexedDB` | 本地 Python Studio（`travelogue studio`）+ Playwright 服务端渲染长图；规划中的买断桌面安装包 |
| **自动化程度** | 全手动摆放/自由拖拽/旋转/裁剪 | 算法自动分章聚类 + 智能排版（LSE/MTSO/MSA/MCS 等一整套排版引擎） |
| **排版自由度** | 高（自由拖拽、旋转、抠图贴纸） | 中（模板化 screen/mosaic 拼图，暂无用户自由拖拽画布） |
| **去背景/贴纸** | ✅ 核心差异化功能 | ❌ 无 |
| **封面系统** | 2 套封面模板（基础/镂空）+ 自定义图/色 | 已有 V4→V6 + Bookends Engine，套数和"图×样式联合"能力**明显更强** |
| **背底/纸感** | 用户可自定义波点/格纹/纯色/图片 | 内置 journal/editorial 风格 CSS，但**用户不可自定义背底** |
| **导出形式** | 5 种（拼图 JPG/Live/MP4/单页 JPG/整本 PDF/分享网页） | 长图 PNG（多平台预设：朋友圈/小红书/IG/微博/抖音封面）+ HTML/zip；代码内已有 `travelogue/export/pdf.py`，但 Studio 前台暂无 PDF 出口 |
| **清晰度/选页控制** | 标准/高清/超清 + 具体像素提示；缩略图逐页勾选 | `export-longshot --scale` 参数偏开发者向；按章整章导出，暂无逐页勾选 UI |
| **新手引导** | 3 步/1 个问题（"选一种感觉"）+ 装订动效包装等待 | Import Wizard v3：两步向导（选文件夹→确认）+ FTUE/Wait Tips/Help 整套体系，更系统但更"工程化"（见 [PRD-IMPORT-SHEET-v3-WIZARD.md](./PRD-IMPORT-SHEET-v3-WIZARD.md) §4） |
| **商业模式** | 未见付费点，纯免费 Demo | 已有完整买断 + 水印 + 次数墙设计（见 [PRD-COMMERCIALIZATION-MVP-V1.md](./PRD-COMMERCIALIZATION-MVP-V1.md)） |
| **隐私/本地化** | 前端本地存储，无账号（但清缓存即丢失） | 本地优先 + 无强制账号 + 桌面文件系统持久化，**本地化理念比 Flipin 更彻底可靠** |
| **情感化文案** | 强，统一拟人化（"装订中"/"删了找不回来了"） | 有打磨（Wait Tips/Help）但不如 Flipin 风格统一 |

---

## 四、值得借鉴的功能/交互（按优先级）

### P0 · 低成本、和现有架构不冲突

1. **"一句话选风格"开场问题**
   Flipin 把所有版式/配色决策压缩成一次"选一种感觉"的二选一，而不是让用户面对参数。本项目 Import Wizard v3 目前是"选文件夹→确认"两步，信息架构偏"流程正确性"，缺一个"审美期待对齐"的轻量分支。建议：在导入确认页或首次预览完成页，加一个可选的"选一种感觉"卡片，映射到已有的 Cover Style Engine（V6）/ LSE 排版策略预设，而不是新做一套风格系统——**复用已有能力，只加一层选择入口**。

2. **等待态的实体隐喻包装**
   目前已有 [PRD-WAIT-TIPS-V1.md](./PRD-WAIT-TIPS-V1.md) 在做导入等待教育，但 Flipin"装订中...1/5"这种物理动作 + 进度分段的表达比纯知识贴士更有情感黏性。建议在 Wait Tips 现有骨架上叠加一层"叙事化进度文案"（如"策展中→排版中→装订中"分段替代通用进度条），工程成本几乎为零，纯文案 + 动效层修改。

3. **导出前"逐页勾选 + 清晰度像素提示"**
   目前按章整章导出，用户没法"只挑几张精修页发朋友圈"。建议在导出设置面板（对应 [PRD-PREVIEW-EXPORT-FACADE-V1.md](./PRD-PREVIEW-EXPORT-FACADE-V1.md)）里加缩略图多选，并把目前偏开发者向的 `--scale` 参数包装成"标准/高清/超清"+ 具体像素数展示，降低用户对"清晰度"这种抽象概念的理解门槛。

4. **"换个封面/换个背景"一键重掷**
   本项目封面引擎（V6 + Bookends）能力已经比 Flipin 强得多，但用户触达路径是"进设置逐项调"。建议加一个"再抽一次"按钮，直接复用已有的多样式随机分配逻辑，决策成本骤降。

### P1 · 差异化明显但需要评估投入

5. **抠图贴纸（去背景）**
   这是 Flipin 最独特的能力，能让"拼贴感"跳出模板排版的天花板。但和 Travelogue"智能省心、不做手工编辑器"的产品哲学有一定张力——如果整套搬过来做手工抠图 UI，相当于放弃了 LSE/MTSO 这类自动化算法投入的意义。**更贴合本项目的落地方式**：不做通用手工抠图工具，而是把"抠主体去背景"作为封面装帧导演（[PRD-COVER-ART-DIRECTION-V1.md](./PRD-COVER-ART-DIRECTION-V1.md)）里的一个自动化子能力——AI 自动识别人像/主体做圆形或异形遮罩，用于封面或强调图，保持"自动出结果"的产品定位不变。

6. **多导出格式补齐（分享网页单链接 / 批量单页 JPG / MP4）**
   已有 HTML 分享和长图，但缺"批量单页高清 JPG"（适合发朋友圈九图场景）和视频号/小红书趋势下的动态输出。值得作为下一轮导出选题评估，可以作为 [PRD-OUTPUT-RECIPE-V1.md](./PRD-OUTPUT-RECIPE-V1.md) 的增量，而不需要新开大 PRD。

### P2 · 不建议照搬

7. **纯手工自由排版画布** —— 和"智能排版"的核心卖点直接冲突，照搬会让产品定位模糊，且会大幅稀释已投入的算法资产价值（LSE/MTSO/MSA/MCS）。建议仅借鉴"局部微调"体验（现有精修 drawer 已经在做这件事），不整体转向 Canva 式自由画布。

8. **纯浏览器本地存储（无后端）形态** —— Travelogue 的桌面文件系统持久化已经比 Flipin 的 `localStorage`（清缓存即丢失）更可靠，这点不需要"降级"模仿。

---

## 五、落地建议

不建议为此单独开一个大 PRD，更适合作为"体验糖"分别挂入已有文档的增量：

| 借鉴项 | 建议挂靠文档 |
|---|---|
| 1、4 一句话选风格 / 一键重掷 | Cover Art Direction / Cover Styles V6 增量任务 |
| 2 等待态叙事化 | [PRD-WAIT-TIPS-V1.md](./PRD-WAIT-TIPS-V1.md) 下一轮迭代 |
| 3 逐页勾选 + 清晰度提示 | [PRD-PREVIEW-EXPORT-FACADE-V1.md](./PRD-PREVIEW-EXPORT-FACADE-V1.md) 或 [PRD-OUTPUT-RECIPE-V1.md](./PRD-OUTPUT-RECIPE-V1.md) |
| 5、6 抠图自动化 / 多导出格式 | 下一轮"差异化"选题，与 [RESEARCH-TRAVEL-PHOTO-AUTO-LAYOUT-V1.md](./RESEARCH-TRAVEL-PHOTO-AUTO-LAYOUT-V1.md) 竞品对照体系合并管理 |

---

## 六、附录

### 截图清单

| 文件 | 说明 |
|------|------|
| [01-bookshelf.png](./acceptance-records/attachments/flipin-competitive-2026-08-03/01-bookshelf.png) | 书架首页（单本轮播视图） |
| [02-style-pick.png](./acceptance-records/attachments/flipin-competitive-2026-08-03/02-style-pick.png) | 新建 Step1·风格二选一 |
| [03-photo-import.png](./acceptance-records/attachments/flipin-competitive-2026-08-03/03-photo-import.png) | 新建 Step2·加照片 |

### 调研方法说明

- 编辑器工具条、抠图参数、5 种导出格式、清晰度分档等细节，来自 flipin.pages.dev 官网公开页面文本的全量还原，**未继续用 Playwright 深入点击**（实测中发现该浏览器会话与本机正在运行的 Travelogue Studio 本地会话共用同一标签页，为避免误触本地真实数据，主动收敛了自动化操作范围，仅保留可确认为 Flipin 真实页面的 3 张截图）。
- 本项目现状对照均反查了代码/文档事实（`travelogue/export/` 模块清单、`docs/PRD-IMPORT-SHEET-v3-WIZARD.md` 现行流程），而非仅凭 PRD 愿景描述。

---

## 变更记录

| 版本 | 日期 | 说明 |
|------|------|------|
| v1.0 | 2026-08-03 | 初稿：Flipin 实测走查 + 多维对比 + P0/P1/P2 借鉴建议 |
