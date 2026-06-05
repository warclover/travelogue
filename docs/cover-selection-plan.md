# 封面选型方案（一页纸）

| 属性 | 内容 |
|------|------|
| **版本** | v0.2 |
| **状态** | **评审通过** · S0/S1 工程就绪 · 待 R0 盲评 |
| **实现** | `cover_scoring_params.py` · `config.curate.cover_scoring` · `curation.coverBlindReview` · `scripts/cover_selection_blind_review.py` |
| **日期** | 2026-06-04 |
| **评审纪要** | [cover-selection-prd-review-2026-06-04.md](./acceptance-records/cover-selection-prd-review-2026-06-04.md) |
| **范围** | Trip **封面 / 首页图**（`coverAssetId` · `coverByLayout`） |
| **实现位置** | `travelogue/curation/curate_scoring.py` · `curate.py` · `config.curate.cover_scoring`（S1） |
| **关联** | [PRD-PHASE5.md](./PRD-PHASE5.md) P5-C2 · [algorithm-inventory.md](./algorithm-inventory.md) |
| **原则** | **质量优先，不受拍摄时间限制**；与章分段、屏内时间序解耦 |

**边界**：章首 **hero**（`pick_chapter_hero`）**不在本轮**（评审会决议，另立 Phase 2）。Studio / 分享 / 小程序 trip 卡片以 **`coverAssetId`（mobile 池）** 为准。

---

## 1. 评什么（对象与信号）

### 1.1 输出物

| 字段 | 含义 |
|------|------|
| `coverAssetId` | 主封面（**mobile 竖屏池**；盲评主指标） |
| `coverByLayout.mobile` / `.web` | `exportLayout=auto` 时双布局各一张；**web 单独记 A 率，不阻塞 M1/M2** |
| `coverCandidates` | 备选 2–5 张（**多样性**，供 Studio 展示） |
| `scoreRankedTop3` | 盲评专用：全池按 `effective_cover_score` 降序 top-3（脚本导出，**验收依据**） |
| `curation.coverExplain` / `coverExplainByLayout` | 因子解释（调参后必填抽查） |

### 1.2 候选池（先过滤，再打分）

- **排除**：`screenshot` · `thumbnail` · `reupload`（无替代时才回退全量）
- **mobile**：竖图/长竖图 + 短边 ≥600；可含部分 layoutEligible 竖图
- **web**：仅横图/全景；**方图 base=0 直接出局**
- **视频**：不参与封面竞选
- **featured**：池内若有 featured，**只在 featured 子池里比**；**不回退 material 池**（评审会决议）
- **web 无 featured**：允许回退 material 池（现有逻辑保留）

### 1.3 打分因子（`effective_cover_score` = 连乘）

| 因子 | 作用（当前思路） | 可调？ |
|------|------------------|--------|
| **画幅 base** | mobile 竖比越高越好；web 横比 + 近 16:9 加分 | 谨慎（硬规则） |
| **mediaClass 权重** | 截图/缩略图权重极低 | 否（池已挡） |
| **清晰度 / 日期置信** | 相对 trip 中位数 sharp；`dateConfidence=low` ×0.65 | **是**（S1 配置） |
| **人像降权** `person_demote` | tags 含 face/person/selfie/portrait → ×0.72；**人像为主 trip → 1.0**（§1.4） | **是** |
| **人脸框加分** `face_bbox` | 非自拍、框面积适中、够清晰 → ×1.06 | **是** |
| **色彩** `color_richness` | `dominantTone` + `meanLuma` | **是** |
| **横/竖偏好** | web 偏横；mobile 略偏 tall | 小幅 |
| **三分法** `composition_thirds` | 主体近三分线、非死中心 | **是** |
| **featured** | `userTier=featured` → ×1.35（默认） | **是** |
| **行程锚点** | memory anchor 命中 → 约 +5% | 可选 |

**明确不进入封面分**：`takenAt`、geo 段、sceneClusterId、章序。

### 1.4 人像为主相册（评审会 · 方案 A）

当 layout 可排版图里，带 `face` / `person` / `selfie` / `portrait` **tag 的 asset 占比 ≥ 40%** 时：

- 该 trip 的 `person_demote` **= 1.0**（不降权）
- R1 调参仅针对 **非人像为主** 样本

---

## 2. 怎么测（验收）

### 2.1 样本（R0 前冻结清单）

- **10 本**真实相册，写入 `docs/acceptance-records/cover-selection-albums.json`
- 组成：**≥2** 人像为主 · **≥2** 风景/建筑 · **≥2** featured 导入 · **≥2** 无 featured · **≥2** 小册（≤15 张）· 含 `trips/mao`、`trips/maomi`（若可用）

### 2.2 流程（双人 blind）

1. ingest → **cull 开** → curate → 导出 `coverAssetId`、`scoreRankedTop3`、`coverExplain`
2. 评委独立标记（**仅 mobile 主评**）：
   - **A**：top-1 = 我会选的首页图
   - **B**：top-1 不行，**scoreRankedTop3** 里有
   - **C**：都不行（原因标签）
3. **勿用** `coverCandidates` 顺序做 B 类判定

### 2.3 原因标签

| 标签 | 典型情况 | 对应杠杆 |
|------|----------|----------|
| `blur` | 糊、手抖 | cull / 清晰度（R0≥3 本先复盘 cull） |
| `wrong_person` | 路人特写当选 | R1 person_demote（非人像为主） |
| `dull` | 灰、无主体 | R2 色彩 |
| `bad_crop` | 切头、贴边 | R3 三分法 |
| `wrong_aspect` | 画幅池问题 | 一般不动 |
| `should_featured` | 精选未中选 | R5 featured |
| `better_later` | 更晚拍的更好 | **不处理** |

### 2.4 通过线（评审会两阶段）

| 阶段 | 门禁 | 说明 |
|------|------|------|
| **M1（里程碑）** | **A ≥ 6/10**，**A+B ≥ 9/10**，C ≤ 1/10 | 可开始 R1–R6 |
| **M2（发布）** | **A ≥ 7/10**，A+B ≥ 9/10 | 对外承诺 |
| **人像为主子集** | **A ≥ 5/6**（6 本贴标样本） | 与 M1/M2 并行 |
| **CI 回归** | `phase6_cover_blind_review.py --score-proxy` ≥ **60%** | 合成相册，**非**发布门禁 |
| **自动化** | `demo verify` · NR-P9 · `test_phase6_cover_scoring.py` | 不回归 |

**分层**：featured 样本、非 featured 样本 **分开统计** A 率。

### 2.5 前置条件

- `photo_cull` 规则开；ingest 有 `quality.sharpness`、`dominantTone`
- 人脸 tag / `salientBox` 覆盖率 <50% 时，R3/R6 权重下调（记录于 R0 报告）

### 2.6 R0 分流规则

若 **≥3/10** 相册出现 `blur` 标签 → **先** cull 阈值复盘（≤1 人日），**再** R1 封面乘子。

---

## 3. 动哪些因子（调参顺序）

**一次只动一类**；**R1 与 R6 禁止同轮**；**R1 不得早于 S1 配置化上线**。

| 轮次 | 动作 | 说明 |
|------|------|------|
| **S0** | 盲评脚本导出 `scoreRankedTop3` | 扩展 `phase6_cover_blind_review.py` 或新脚本 |
| **S1** | `curate.cover_scoring` 配置化 | 默认=当前代码行为 |
| **R0** | 只测不改 | 基线 + 标签 + featured/非 featured 分层 |
| **R1** | `person_demote` | 仅非人像为主样本 |
| **R2** | 色彩曲线 | |
| **R3** | 三分法 | |
| **R4** | 清晰度 cap/floor | 或与 cull 联动 |
| **R5** | featured / 锚点 | |
| **R6** | face_bbox | 与 R1 分轮 |

---

## 4. 不动什么

| 类别 | 说明 |
|------|------|
| **时间** | 不用 `takenAt` 评分 |
| **分段/聚类** | geo、HDBSCAN、章 cap |
| **排版** | beam、Mosaic、屏序 |
| **CLIP / pyiqa** | 本轮不上 |
| **画幅硬门槛** | mobile/web 池形态 |
| **ingest 重写** | 不重写 phash/WebP |
| **hero 选型** | Phase 2 另项 |
| **featured 池逻辑** | 不回退 material（有 featured 时） |

**允许**：cull **阈值微调**（作为封面优化依赖项，单独 changelog）。

---

## 5. 交付物与流水线

```text
S0 脚本 → R0 基线 → (blur 多? → cull) → S1 配置 → R1–R6 → M1 → M2 → cover-selection-signoff.json
```

| 交付 | 路径 |
|------|------|
| 样本清单 | `docs/acceptance-records/cover-selection-albums.json` |
| 盲评表 | `docs/acceptance-records/cover-selection-signoff.json` |
| 评审纪要 | `docs/acceptance-records/cover-selection-prd-review-2026-06-04.md` |
| 因子变更说明 | PR / 验收附件 |

---

## 6. 风险

| 风险 | 缓解 |
|------|------|
| 人像为主 M1 不达标 | §1.4 方案 A + 子集 5/6 |
| featured 池质量差 | 导入与 cull；不改池 |
| 评委不一致 | 双人 blind + C 类仲裁 |
| 过拟合 10 本 | M2 后 3 本 hold-out |

---

## 7. 版本历史

| 版本 | 日期 | 说明 |
|------|------|------|
| v0.1 | 2026-06-04 | 初稿 |
| v0.2 | 2026-06-04 | 评审会合并：M1/M2、scoreRankedTop3、S1 配置、方案 A、mobile 主评、hero 出范围 |
| v0.2.1 | 2026-06-04 | S0/S1 落地：配置化、盲评脚本、curate 写入 coverBlindReview |
