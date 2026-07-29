# 照片质量 / 选片 / 主图调研纪要（2026-07-28）

| 属性 | 内容 |
|------|------|
| **日期** | 2026-07-28 |
| **来源** | 产品/算法讨论会话整理 |
| **关联** | [PRD-HERO-INTEREST-TASTE-V1.md](./PRD-HERO-INTEREST-TASTE-V1.md)（HIT）· [PRD-PHASE23-peak-moment.md](./PRD-PHASE23-peak-moment.md) · [DESIGN-PHOTO-AESTHETIC-EVALUATION.md](./DESIGN-PHOTO-AESTHETIC-EVALUATION.md) |
| **范围** | Travelogue 现网主图/高光诊断 · 产品策略 · 开源算法 · 竞品/工具调研 |

> 本文汇总当次对话中的**调研与判断**；HIT 完整产品合同以独立 PRD 为准。

---

## 目录

1. [拼图主图筛选（现网）](#1-拼图主图筛选现网)
2. [审美 + 趣味主图策略（HIT 建议）](#2-审美--趣味主图策略hit-建议)
3. [产品图 / 相册品类 / 策略包](#3-产品图--相册品类--策略包)
4. [高光池与决定性瞬间（Phase 23）](#4-高光池与决定性瞬间phase-23)
5. [「相对高质量」难题](#5-相对高质量难题)
6. [开源审美与趣味算法](#6-开源审美与趣味算法)
7. [GIQA（ECCV 2020）](#7-giqaeccv-2020)
8. [雪艺 photo-quality-annotator](#8-雪艺-photo-quality-annotator)
9. [Aftershoot](#9-aftershoot)
10. [Lisa（Instagram 选图）](#10-lisainstagram-选图)
11. [digiKam](#11-digikam)
12. [对照总表与结论](#12-对照总表与结论)

---

## 1. 拼图主图筛选（现网）

### 1.1 结论

有主图槽的拼图：**几何硬门禁先于品味**。不合格不进主槽；合格集内再排序。不是「整库挑最好看的一张硬塞」。

### 1.2 两条路径

| 路径 | 条件 | 行为 |
|------|------|------|
| 默认 / AR guard 关 | `pick_main_for_pattern` → `_pick_main_landscape_id` | landscape 中按 `effective_hero_score`，sharpness tiebreak |
| 现网主路径 | `main_ar_guard=true` | `pick_best_main_eligible`：硬准入后再 `hero × AR boost` |

核心代码：

- `travelogue/layout_engine/mosaic/hero.py`
- `travelogue/layout_engine/mosaic/main_eligibility.py`
- `travelogue/layout_engine/planner/screen_planner.py`（`_pick_main_landscape_id`）
- `travelogue/curation/curate_scoring.py`（`hero_score` / `effective_hero_score`）

### 1.3 硬门禁（`asset_eligible_for_main_slot`）

由模板 `constraints.eligibility`（或旧 `mainSlotPolicy`）驱动，典型横主：

- 允许：`landscape`
- 禁止：`panorama` / `tall` / `portrait` / `square`
- 超宽、偏离 AR 梯子 → 拒

竖主家族可声明 `eligibleAspectKinds: [portrait]`，走竖图池。

### 1.4 合格集内排序（现网问题）

```text
sort_key ≈ effective_hero_score × ar_preference_boost
hero_score 含 w/h 底座 × media × [purpose_overall(hero) 或 sharpness]
```

**诊断**：几何已筛过一轮，AR boost 与宽高比底座仍二次偏置「贴梯子」，稀释美感 → 观感像「技术合格但不跳」。

另：`main_eligible_hero_score_gap`（URO）用于「无明确主次则不用 hero 页」；★ `featured` 仅软乘（约 1.35）。

### 1.5 与审美的关系（判断）

- **不完全是「没法用审美」**：门槛内有 `purpose_overall("hero")` 等。
- **准确说法**：几何管资格；审美不能推翻几何；现网品味分仍被几何代理稀释。

---

## 2. 审美 + 趣味主图策略（HIT 建议）

完整合同见：**[PRD-HERO-INTEREST-TASTE-V1.md](./PRD-HERO-INTEREST-TASTE-V1.md)**（特性代号 HIT）。

### 2.1 建议推进序

1. 改合格集内排序键（`purpose_overall(hero)` 为主；AR boost 降为微 tiebreak）
2. 唯美与有趣拆开（窗内 uniqueness，先 ΔE）
3. 用 HIT 分上的 gap 决定是否强主图页
4. ★ 合格精选硬优先
5. 盲评闭环；MLLM 后置

### 2.2 近似公式

```text
Eligible = main-eligible(window, pattern)
beauty   = purpose_overall(hero)
interest = (1-λ) + λ × uniqueness_window(ΔE)   # 建议 λ=0.4
hit_score = beauty × interest × featured? × anchor?
main = argmax(FeaturedEligible) if ★合格非空 else argmax(Eligible)
admit_hero_page = gap ≥ threshold
```

### 2.3 缩水方案（曾讨论、暂未拍板）

放弃趣味，改 **LAION Aesthetic V2.5 + 有人脸时笑脸软优先**：

- **可行**，工期更短
- 笑脸必须是**条件软 boost**，禁止全局硬规则（否则风景册误伤）
- 建议保留 gap + ★；用盲评门禁后再默认开

---

## 3. 产品图 / 相册品类 / 策略包

### 3.1 产品图拼长图

**不能零改直接用 Travelogue。**

- 可复用：导出长图截取/切段壳
- 不可直接用：时间章、burst、16:9 landscape 主槽、旅行 hero/moment 美学、人像/食物策略

最小可行：固定顺序 + 简单网格 + 长图导出；智能拼合需产品向模板与评分。

### 3.2 创建游记时是否强制选品类

- **有价值**：写真 / 旅行 / 风景 / 宠物 等主轴可驱动模板池与权重。
- **不宜**：开局强制单选才能继续（伤 FTUE；混合相册难选）。
- **更好**：导入后**推断 + 轻确认/可改**；2～4 个主轴；混合为安全默认。
- 现网已有：`meta.genre` 预留、`stratumPreference`、`infer_purpose_profile_kind`。

### 3.3 是否一类一条管线

**否。** 推荐：**共享主链 + 每类一份 Profile（策略包）**。

差异面：模板白名单、主槽 eligibility、评分权重、叙事规则、usage_rules。  
仅当模式结构不同（如电商固定 SKU 页）才分叉整条管线。

---

## 4. 高光池与决定性瞬间（Phase 23）

实现：`travelogue/curation/moment_scoring.py` · 配置：`travelogue/config/moment.py` · PRD：`PRD-PHASE23-peak-moment.md`。

### 4.1 双层模型

| 概念 | 字段 / 展示 | 含义 |
|------|-------------|------|
| 高光池 | `momentPoolIds`（约 5%，clamp 1–5） | 名场面候选小集合 |
| 决定性瞬间 / 签名 | `momentAssetId` · `data-role="moment"` · 角标 | 全册唯一；池内 top-1 |
| 次要高光 | `momentSecondaryIds` · `role=peak` | 池内其余；默认 solo + EXIF |

### 4.2 `peak_moment_score` 默认权重

| 因子 | 权重 | 说明 |
|------|------|------|
| arc_peak | 0.30 | peak 章或 highlight_windows |
| anchor | 0.25 | 记忆锚点 |
| aesthetic | 0.20 | `purpose_overall("moment")` |
| on_screen | 0.15 | 已上正文屏 |
| featured | 0.10 | ★ |

另：章 hero ×0.85；小册 ≤15 可整段关闭。

### 4.3 用户反馈诊断（会话结论）

**记忆锚点几乎不用 → anchor 25% 恒 0；arc_peak / on_screen 大面积同分 → 决胜塌成弱美学 + tiebreak → 观感像随机。**

不是 RNG，是**有效特征破产**。「决定性瞬间」文案过重于算法能力。

建议方向：空转权重重归一；有脸用睁眼/清晰；无人脸抬相对美学 + uniqueness；弱化或诚实降级文案。

---

## 5. 「相对高质量」难题

### 5.1 问题重定义

受制于拍摄水平，全册可能都「不高」——正确目标不是绝对杂志级，而是：

> **在本册天花板内，稳定挑出相对更好、且适合对应图位的照片。**

### 5.2 建议框架

1. **册内相对质量底座**：百分位 / z-score（`album_relative` 升为高价值图位默认）
2. **两段式**：技术及格 → 存活集相对排序 → 图位适配
3. **低天花板诚实**：少造神、少强 hero 拼、弱化重文案
4. **零意图可用信号**：清晰/曝光、相对美学、睁眼、去重；锚点有则加分、无则权重归零
5. **评测**：盲评 / 相对 SRCC，而非绝对美学阈值

---

## 6. 开源审美与趣味算法

### 6.1 审美（Aesthetic）

| 流派 | 代表 | 口碑口径 |
|------|------|----------|
| AVA 经典 | NIMA | 工程基线；Travelogue 已用（pyiqa） |
| 多尺度 | MUSIQ | 学术强 |
| 工具箱 | **pyiqa**（~3k★） | 工程集成最省事 |
| CLIP+MLP | **LAION / improved-aesthetic-predictor**（~1.3k★） | **工业落地最广** |
| 后继 | Aesthetic Predictor V2.5 / AestheticSigLIP | 社区新宠 |
| 学术 SOTA | VILA-R 等 | AVA 榜高；普及度不如 LAION |

「最受好评」需分口径：**落地最广 ≈ LAION 系；工程入口 ≈ pyiqa；论文榜 ≈ VILA 系。**

### 6.2 趣味（Interestingness）

| 代理 | 代表 | 说明 |
|------|------|------|
| 记忆度 | LaMem / MemNet / **PerceptCLIP Memorability** | 开源最像样；≠旅行叙事趣味 |
| 提示词排序 | CLIP × “interesting photograph” | 灵活、方差大 |
| 相对独特 | 窗内 ΔE / 嵌入距离 | **产品最稳、贴拼图主图** |

趣味领域**没有**像 LAION 审美那样的全民默认冠军。

### 6.3 对 HIT / Travelogue

- 唯美：NIMA 或 A/B **LAION-V2.5**
- 有趣：窗内 uniqueness（HIT V1）；记忆度仅可选探针
- 勿用 GIQA 直接当旅行择优（见下）

---

## 7. GIQA（ECCV 2020）

| 项 | 内容 |
|----|------|
| 论文 | [arXiv:2003.08932](https://arxiv.org/abs/2003.08932) |
| 代码 | [cientgu/GIQA](https://github.com/cientgu/GIQA) |
| 全称 | Generated Image Quality Assessment |
| 目标 | 给**单张 GAN 生成图**打分（非 FID/IS 的模型级指标） |

三种方法：

1. **MBC-GIQA**：迭代伪标签 + 多二分类器回归  
2. **GMM-GIQA**（推荐）：Inception 特征 + 真图分布 GMM，密度=质量  
3. **KNN-GIQA**：特征空间 K 近邻距离  

**与旅行择优**：测的是「像不像真图分布」，不是册内相对更好；若用本册建 GMM，可能抬「平庸常见」、压「独特瞬间」。

---

## 8. 雪艺 photo-quality-annotator

| 项 | 内容 |
|----|------|
| 仓库 | [Astrosnowsoftware/Skill](https://github.com/Astrosnowsoftware/Skill) |
| 路径 | [`photo-quality-annotator`](https://github.com/Astrosnowsoftware/Skill/tree/main/photo-quality-annotator) |
| 形态 | **Agent Skill（SKILL.md）**，不是传统装机 CV 软件 |

### 8.1 流程

盘点文件夹 → 内容标签 → **硬门槛** → 通过后打分 → 重复组只留最佳 PASS → 复制精选 + CSV/JSON。

### 8.2 硬门槛（人像/活动正式精选）

正对镜头、睁眼、无多余手势/动作、姿态干净、无遮挡、裁切自然、清晰、曝光、背景干净。  
原则：**宁可平淡达标，不要有趣但不达标。**

### 8.3 通过后加权（100 分）

技术 40 · 表情准备 30 · 构图 20 · 入选价值 10。

### 8.4 启示

规程化视觉 LLM 选片；可借鉴「硬门槛与软分拆开」；不宜整份当旅行主图算法。

---

## 9. Aftershoot

| 项 | 内容 |
|----|------|
| 官网 | [aftershoot.com](https://aftershoot.com/) |
| 评测 | [Unite.AI Aftershoot Review](https://www.unite.ai/aftershoot-review/) |
| 定位 | 职业摄影师本机 AI：**Cull + Edit + Retouch + Galleries** |

### 9.1 选片（公开）

- 号称 **30+ 因子** → **1–100 分**
- 相似/连拍分组（区分真重复 vs 创意变体）
- 桶：Selected / Highlights / Closed Eyes / Blurry / Duplicates / Warnings
- Automated vs Assisted 两种模式；可学习用户选片偏好
- 离线、不按张计费、非破坏（多写 XMP）

### 9.2 定价（官网口径，会变）

完整约 $45/月（年付）；仅 Cull 约 $10/月；30 天试用可不绑卡。

### 9.3 启示

相对分 + 缺陷硬标 + 组内留胜者 + 人可改选 + 反馈学习 —— 对 Travelogue「相对择优层」最有产品参考价值（模型闭源不可抄）。

---

## 10. Lisa（Instagram 选图）

| 项 | 内容 |
|----|------|
| 中文介绍 | [小众软件 · Lisa](https://www.appinn.com/lisa-photo-assistant-for-instagram/) |
| 公司 | Otto Labs（伊斯坦布尔，约 2017）· Tracxn 记为 IG 推荐 App |
| 定位 | 消费级：「哪张发 Instagram 更可能火」+ 自动 Hashtags |

### 10.1 功能

多图对比（早期约 2–5 张）· engagement 预测 · Hashtag · 灵感参考 · 可分享 IG · Plus 订阅。

### 10.2 技术

闭源 ML；优化 **社媒互动/网感**，非摄影技术分、非相册书叙事。  
与 Travelogue「相对高质量 / 决定性瞬间」**目标函数不同**；若借鉴，仅限海外分享包的社媒封面/标签切片。

---

## 11. digiKam

| 项 | 内容 |
|----|------|
| 官网 | [digikam.org](https://www.digikam.org/) |
| 文档 | [Image Quality Scanner](https://docs.digikam.org/en/maintenance_tools/maintenance_quality.html) |
| 定位 | 开源本地 **DAM + 编辑**（Win/macOS/Linux）；约 9.1.0（2026-06） |

### 11.1 相关 AI（OpenCV DNN，本机、按需下载模型）

- 人脸检测/识别（8.6+ 流水线增强、FIQA）
- Auto-Tags
- **Aesthetic Detection / Image Quality Scanner** → Pick Labels  
  - Basic：模糊/噪声/曝光/压缩  
  - DL：端到端美学分
- 相似指纹去重、自动旋转、红眼等

### 11.2 启示

开源「质量标签 + 相似去重 + 人脸」组合可对照；是整理检索工具，不是婚礼式一键精选或游记叙事选型。可作 ingest 旁路预标参考，不替代 MCS/moment。

---

## 12. 对照总表与结论

### 12.1 总表

| 对象 | 类型 | 优化目标 | 对 Travelogue |
|------|------|----------|----------------|
| 现网主图 | 自有 | 几何合格 + hero 分 | 需去几何稀释、加强品味 |
| HIT PRD | 自有规划 | 合格集内唯美+趣味 | 正式合同文档 |
| Phase 23 moment | 自有 | 全书签名/高光池 | 锚点空转需修 |
| LAION / NIMA / VILA | 开源审美 | 人类「好看」 | 可作 beauty 后端 |
| 记忆度 / ΔE unique | 开源/工程 | 难忘或相对独特 | uniqueness 用 ΔE 更稳 |
| GIQA | 论文+代码 | 生成图像真 | **不宜**直接当旅行择优 |
| 雪艺 Skill | Agent 规程 | 正式人像硬门槛 | 借鉴硬/软分层 |
| Aftershoot | 商业 App | 职业交付选片 | 借鉴相对分+分组+学习 |
| Lisa | 消费 App | IG 互动 | 目标不同；最多社媒切片 |
| digiKam | 开源 DAM | 整理+质量标签 | 对照开源质量管道 |

### 12.2 会话级结论（浓缩）

1. **主图**：几何至上没错；合格后应把排序还给品味（HIT），勿再被 AR 主轴稀释。  
2. **高光/决定性瞬间**：锚点缺位时像随机是预期；先修有效特征与文案承诺。  
3. **全差相册**：做册内相对择优 + 诚实降级，不做绝对高质量幻觉。  
4. **竞品/开源**：Aftershoot/digiKam/雪艺可借鉴**工作流合同**；Lisa/GIQA 目标错位勿硬套；审美升级可试点 LAION-V2.5。  
5. **产品图与品类**：长图壳可复用；品类用 Profile 而非复制管线；创建流程用推断确认而非强制单选。

---

## 附录 · 关键链接

- HIT PRD：`docs/PRD-HERO-INTEREST-TASTE-V1.md`
- Phase 23：`docs/PRD-PHASE23-peak-moment.md`
- PA 设计：`docs/DESIGN-PHOTO-AESTHETIC-EVALUATION.md`
- GIQA：https://arxiv.org/abs/2003.08932 · https://github.com/cientgu/GIQA
- 雪艺 Skill：https://github.com/Astrosnowsoftware/Skill
- Aftershoot：https://aftershoot.com/ · https://www.unite.ai/aftershoot-review/
- Lisa 介绍：https://www.appinn.com/lisa-photo-assistant-for-instagram/
- digiKam：https://www.digikam.org/ · https://docs.digikam.org/en/maintenance_tools/maintenance_quality.html
- LAION aesthetic：https://github.com/christophschuhmann/improved-aesthetic-predictor
- pyiqa：https://github.com/chaofengc/IQA-PyTorch

---

## 版本记录

| 版本 | 日期 | 说明 |
|------|------|------|
| v0.1 | 2026-07-28 | 初稿：汇总当次对话全部调研与判断 |
