# PRD-GENERATIVE-COLLAGE-SURFACES-V1 · 跨职能评审纪要

| 属性 | 内容 |
|------|------|
| **文档** | [PRD-GENERATIVE-COLLAGE-SURFACES-V1.md](../PRD-GENERATIVE-COLLAGE-SURFACES-V1.md) |
| **模板** | [generative-collage-surfaces-v1-review-TEMPLATE.md](./generative-collage-surfaces-v1-review-TEMPLATE.md) |
| **承接** | [PRD-PHASE17-research-stub.md](../PRD-PHASE17-research-stub.md)（P17-B） |
| **相邻挡门** | [MGQ](../PRD-MCS-GEOMETRIC-QUALITY-V1.md) · [LTE P16](../PRD-PHASE16-layout-template-engine.md) · [LTE Admission](../LTE-ADMISSION-LAYOUT-TEMPLATES.md) · [Output Recipe](../PRD-OUTPUT-RECIPE-V1.md) · [导出门面](../PRD-PREVIEW-EXPORT-FACADE-V1.md) |
| **评审版本** | **v0.1.0 Draft** → Must-Fix 已回写 **[PRD v0.2.0](../PRD-GENERATIVE-COLLAGE-SURFACES-V1.md)** |
| **日期** | 2026-07-18 |
| **结论** | **有条件通过（Conditional Go）** · **可 Kickoff W0**（合同冻结 · 拆文 · 可选 spike；本轮不编码） |
| **编码** | **本轮明确不动代码**；Kickoff 以 IMPLEMENTATION W0 任务卡另排期 |
| **参评角色** | 产品 · 算法 · 架构 · 开发 · 测试/QA · 交互/UI（导出门面）· 用户体验 · 典型用户（分享者 · Sparse 轻量册） |
| **评审方式** | 分席只读（PRD §0.1·§2·§4–§6 + 现网对照：MCS legacy / collage_routing / Output Recipe / validator） |
| **记录人** | 产品 / 算法 / 架构 / 工程联合纪要（跨职能模拟联评） |
| **本纪要状态** | **已结案** · BLK-01～08 成立并回写 PRD v0.2.0 |

---

## 0. 会前宣读（主持人 · 3 分钟）

1. **切口**：BRIC 有价值，落点是旁路——轨 A 离线扩 LTE SKU；轨 B 海报导出 Writer。  
2. **勿当银弹**：禁止 MCS `used_legacy` 默认调 BRIC；禁止 runtime 改 `rect`（D-MGQ-02）。  
3. **本场必拍**：D-GCS-01～10；**关闭** OQ-GCS-01 / OQ-GCS-03。  
4. **本轮不动代码**。

---

## 1. 总评（一句话）

> **双轨旁路与 MGQ/LTE 禁区对齐正确，值得做；阻塞在轨 A「轨道原生枚举 vs BRIC→YAML」混写、OQ-01/03 未冻、trip.json/Output Recipe 落点未钉、AC 未可测化。BLK-01～08 回写 v0.2.0 后可 Kickoff W0；实现建议先 B 后 A 串行，本轮不编码。**

---

## 2. 分席表决

| 席位 | 表决 | 一句话 |
|------|------|--------|
| **产品** | Conditional Go | P-01/P-03 真实；双轨保留但串行，先海报价值后 SKU 工厂 |
| **算法** | Conditional Go | 旁路对；轨 A 须轨道原生枚举，禁 BRIC 连续 rect 硬塞 YAML |
| **架构** | Conditional Go | 禁挂点清楚；须钉 job sidecar 与 Recipe engine/intent 合同 |
| **开发** | Conditional Go | 可 Kickoff；vendoring/flag/拆文未钉则不批无条件 Go |
| **测试 / QA** | Conditional Go | AC 方向对；须输入→期望→命令 + LRG 硬门 + 独立盲评码 |
| **交互 / UI（导出门面）** | Conditional Go | ▾「单屏海报」；禁与九宫格/拼贴串词 |
| **用户体验** | Conditional Go | 不抢 Sparse 80% 长图主路径；失败勿静默顶替 |
| **用户 · 分享者** | Conditional Go | 聚会要一张能发的图，别叫九宫格 |
| **用户 · Sparse 轻量册** | Conditional Go | 默认仍要群长图；海报放次要入口即可 |

**汇总**：**九席一致 Conditional Go**。MF 已回写 v0.2.0 → **可 Kickoff W0（文档/设计 + 可选 spike）**；未回写前不批无条件 Go。

---

## 3. 全场共识

1. **BRIC ≠ 杂志主链救场**：SKU 工厂 + 海报导出器；不作 runtime mosaic solver。  
2. **遵守 D-MGQ-02**：不进 `MosaicConfig`；不 runtime 改 `rect`。  
3. **轨 A**：在 `stage.cols/rows` 上 **原生** guillotine/treemap；**禁止** BRIC 像素 rect 硬转 YAML；不合格丢弃。  
4. **轨 B**：vendored MIT `bric_compose`；统一 contain；产物走 export job，不进 `screens[]`。  
5. **OQ-01**：仅 ▾「单屏海报」，不抢 `chat_longshot`。  
6. **实现顺序**：**先 B 后 A**（串行）；双轨不砍。  
7. **轨 A KPI** = corpus 上 `used_legacy`/pattern-miss 相对 baseline ↓，非 YAML 产量。  
8. **本轮只做评审/文档回写**。

**会中新增共识**：

- 轨 A / 轨 B **API 分家**：A=photo-agnostic mix 枚举；B 才吃具体 `sizes`。  
- `exportArtifacts` **非**现网 trip.json schema → 改 **export job sidecar** + telemetry。  
- Output Recipe 须登记独立 `intent` / `engine` / `platform`（禁冒充 `moments_grid`）。  
- 轨 A V1 **关闭**「可选 hero 面积带」伪 hero，避免撞 `mainSlotPolicy`。

---

## 4. Must-Fix（已成立 · 已回写 PRD v0.2.0）

| ID | 议题 | 来源席位 | 要求（冻结一字面） | 成立 |
|----|------|----------|-------------------|------|
| **BLK-01** | 禁区与落点写死 | 架构 / 算法 | OUT-01/02、D-GCS-01/02 标「已冻结」；MCS 失败口仍走 legacy；AC-GCS-01 可检无 BRIC 调用 | ✅ |
| **BLK-02** | 轨 A 搜索空间 | 算法 / 架构 | 轨道原生 guillotine/treemap；**禁止**「BRIC 连续 rect → YAML」主路径；投影/枚举失败一律丢弃 + discard 报表 | ✅ |
| **BLK-03** | OQ-01 入口 | 产品 / 交互 / UX | **仅 ▾「单屏海报」**；不进主 CTA；不抢 `chat_longshot`；脚注 Output Recipe / 导出门面 | ✅ |
| **BLK-04** | OQ-03 规范化 | 算法 / 架构 | **冻结投影/原生轨道模型**；不合格拓扑丢弃规则可测 | ✅ |
| **BLK-05** | 依赖与许可 | 开发 / 架构 | V1 **强制** vendor MIT（钉 commit/拷贝）；热路径零新 pip；禁 GPL；AC-GCS-09 | ✅ |
| **BLK-06** | trip.json / Recipe 边界 | 架构 | 轨 B → **export job sidecar**（默认禁未 schema 化根字段）；独立 `intent=poster_bric` + `engine` + `platform`；禁伪 `patternId` 进 `screens[]` | ✅ |
| **BLK-07** | AC 可测 + 主链门 | 测试 / 开发 | AC-02/03/05/06 写「输入→期望→命令」；AC-GCS-08 golden/LRG=W1 硬门；AC-GCS-BLIND 独立码绑默认露出 | ✅ |
| **BLK-08** | 拆文 + 交付序 | 开发 / 产品 | W0 可用 PRD §9–§10；**W1 merge 前**拆 ACCEPTANCE+IMPLEMENTATION；实现 **先 B 后 A** | ✅ |

---

## 5. Should-Fix（不单独挡 Kickoff）

1. OQ-GCS-02：event-recap **不默认绑**海报；可选意图即可。  
2. OQ-GCS-04：V1 统一 contain；face pad → V1.1。  
3. 轨 B letterbox fill：W0/IMPL 冻 solid 底色 vs blur 默认二选一。  
4. 轨 A V1 关闭可选 hero 面积带。  
5. W0 钉 corpus + baseline 口径（主指标 `used_legacy` vs pattern-miss）。  
6. 用户文案：「单屏海报 · 发群」；禁「九宫格 / 拼贴」串词（AC-GCS-10）。  
7. 埋点 `gcs_*` 进 IMPLEMENTATION。

---

## 6. D-GCS / OQ 拍板汇总

### 6.1 决策

| 决策 | 本场决议 |
|------|----------|
| **D-GCS-01** | **采纳** — 双轨；禁挂 MCS `used_legacy` |
| **D-GCS-02** | **采纳** — 遵守 MGQ；不进 MosaicConfig |
| **D-GCS-03** | **修订采纳** — 轨 B：vendored MIT BRIC；轨 A：轨道原生枚举，禁 BRIC→YAML 主路径；热路径零新 pip |
| **D-GCS-04** | **采纳** — PhotoCollage/GPL 禁进主包 |
| **D-GCS-05** | **采纳** — 海报统一 contain 系 |
| **D-GCS-06** | **采纳** — 3–6 推荐 / 硬上限 9 |
| **D-GCS-07** | **修订采纳** — 轨 B 落 export job sidecar；禁 `screens[]` 伪 pattern；默认禁未 schema 化 `exportArtifacts` 根写入 |
| **D-GCS-08** | **修订采纳** — validator + admission + 盲评；YAML 含 `generator` + `enum_params` |
| **D-GCS-09** | **修订采纳** — 轨 B：sizes+参数→positions；轨 A：mix+stage+enum_params→有序拓扑序列；禁 shuffle/dict 序 |
| **D-GCS-10** | **修订采纳** — 轨 B 默认露出绑 BLIND≥55%；轨 A 以 corpus 相对 baseline 的 legacy/miss ↓ 为准 |

### 6.2 开放问题

| OQ | 决议 |
|----|------|
| **OQ-GCS-01** | **已关闭 · A** — 仅 ▾「单屏海报」；不进主 CTA；不抢 `chat_longshot`；`features.gcs_poster_bric` 默认 false 至盲评 |
| **OQ-GCS-02** | **已关闭 · A** — 不默认绑 event-recap；仅可选意图/CLI |
| **OQ-GCS-03** | **已关闭 · A** — 轨道模型原生枚举/投影；无法入轨则丢弃；禁 BRIC 绝对 rect 硬塞 |
| **OQ-GCS-04** | **已关闭 · A** — V1 统一 contain；face-aware → V1.1 |

---

## 7. 分席要点摘要

### 7.1 产品
- 保留双轨，串行交付；用户价值先落轨 B。  
- 海报文案用人话「单屏海报」，避免拼贴/九宫格。

### 7.2 算法
- 轨 A 最大风险是连续几何硬塞离散轨道 → 已用 BLK-02 挡住。  
- 新 SKU 必须带可被 URO/MCS 消费的 usage/eligibility，否则降不了 legacy。

### 7.3 架构
- 现网：MCS 失败=legacy；无 BRIC 实现；`exportArtifacts` 非现网字段。  
- Recipe 须扩 `EngineId`（现仅 `chapter_capture|platform_segment|photo_grid`）。

### 7.4 开发
- 先 B：Writer + flag=false 可狗粮、零 MCS 风险。  
- W1 merge 前必有 ACCEPTANCE/IMPLEMENTATION。

### 7.5 测试 / QA
- fixture：轨 B `n=3/6/9` + `n=2` 禁用 + collage 排除；轨 A 合法/非法各 1。  
- LRG/golden = W1 硬门；盲评 Gate 码独立。

### 7.6 交互 / UX / 用户
- Sparse 主路径长图不动。  
- 失败回退须明示「改导出长图」，禁止静默顶替海报文案。

---

## 8. 双轨范围签核

| 轨 | 范围陈述 | 签核 |
|----|----------|------|
| **A · 离线 SKU 工厂** | 轨道原生枚举 → validator → admission → YAML | ✅ 产品/算法/架构 |
| **B · `poster_bric` Writer** | export job；contain；≤9；▾ 入口 | ✅ 产品/架构/交互 |
| **禁区 · MCS runtime BRIC** | V1 不交付 | ✅ 全场 |
| **禁区 · 伪 patternId** | 不进杂志 `screens[]` | ✅ 全场 |

---

## 9. 与相邻主题挡门（已确认）

| 主题 | 确认 |
|------|------|
| MGQ | 遵守 D-MGQ-02；不抢 MosaicConfig | ✅ |
| LTE / Admission | 轨 A 唯一入轨 | ✅ |
| P17-B stub | 轨 A 升格归 GCS；匈牙利仍归 LSE | ✅ |
| Output Recipe / 导出门面 | ▾ 次入口；独立 intent/engine | ✅ |
| collage_routing / moments_grid | 术语与 Writer 隔离 | ✅ |

---

## 10. 人日粗估（合流）

| 波次 | 算法 | 架构/接线 | 开发（含实现） | 备注 |
|------|------|-----------|----------------|------|
| W0 | 1–2 | 1.5–2.5 | 1–2 | 合同 + 拆文 + 可选 spike |
| W1 | 6–8 | 4–6 | 6–8 | 先 B Writer + A CLI 骨架 |
| W2 | 3–5 | 2.5–4 | 4–6 | ≥3 experimental + ▾ 入口 |
| W3 | 2–4 | 1.5–2.5 | 3–5 | 盲评 + miss 报表 |
| **合计口径** | — | — | **约 14–21**（开发串行） | 盲评执行/SKU 设计评审另计 |

---

## 11. 下一步

- [x] Must-Fix 回写 PRD → **v0.2.0**  
- [x] 正式纪要本文  
- [x] 更新 [docs/README.md](../README.md) GCS 状态行  
- [ ] 拆 `ACCEPTANCE-GENERATIVE-COLLAGE-SURFACES-V1.md` / `IMPLEMENTATION-…`（W1 merge 前必有；W0 可先用 PRD §9–§10）  
- [ ] Output Recipe / 导出门面脚注（OQ-01）  
- [ ] Kickoff W0 排期：____  
- [ ] 狗粮：Sparse 3–6 张海报 N≥5；SKU 工厂 ≥3 experimental

---

## 附录 · 现网对齐断言

| 断言 | 结论 |
|------|------|
| MCS 失败口 = legacy，无 BRIC | **属实** |
| `mediaClass=collage` → full-frame | **属实** |
| Output Recipe 无 `poster_bric` | **属实** |
| LTE `validate_for_publish` / admission 可用 | **属实** |
| `exportArtifacts` 已是 trip.json 标准字段 | **不属实** → 改 job sidecar |
| D-MGQ-02 已冻结 | **属实** |
