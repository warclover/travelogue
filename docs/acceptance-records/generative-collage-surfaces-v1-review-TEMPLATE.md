# PRD-GENERATIVE-COLLAGE-SURFACES-V1 · 跨职能评审纪要（模板）

| 属性 | 内容 |
|------|------|
| **文档** | [PRD-GENERATIVE-COLLAGE-SURFACES-V1.md](../PRD-GENERATIVE-COLLAGE-SURFACES-V1.md) |
| **承接** | [PRD-PHASE17-research-stub.md](../PRD-PHASE17-research-stub.md)（P17-B 生成式 composite） |
| **相邻挡门** | [PRD-MCS-GEOMETRIC-QUALITY-V1.md](../PRD-MCS-GEOMETRIC-QUALITY-V1.md)（D-MGQ-02）· [PRD-PHASE16-layout-template-engine.md](../PRD-PHASE16-layout-template-engine.md) · [LTE-ADMISSION-LAYOUT-TEMPLATES.md](../LTE-ADMISSION-LAYOUT-TEMPLATES.md) · [PRD-OUTPUT-RECIPE-V1.md](../PRD-OUTPUT-RECIPE-V1.md) · [PRD-PREVIEW-EXPORT-FACADE-V1.md](../PRD-PREVIEW-EXPORT-FACADE-V1.md) |
| **对标** | [stefanwayon/collage](https://github.com/stefanwayon/collage)（BRIC · MIT） |
| **验收 / 实施** | 评审后拆否：□ 是 → `ACCEPTANCE-…` / `IMPLEMENTATION-…`　□ 否 · 暂用 PRD §9–§10 |
| **评审版本** | **v0.1.0 Draft** → Must-Fix 回写后升 **v0.x.x**（填） |
| **日期** | YYYY-MM-DD（填） |
| **结论** | □ Go　□ **Conditional Go**　□ No-Go　（勾选） |
| **编码** | □ 本轮仅文档/设计　□ 可 Kickoff W0　（勾选） |
| **参评角色** | 产品 · 算法 · 架构 · 开发 · 测试/QA · 交互/UI（导出门面）· 典型用户（分享者 · Sparse 轻量册） |
| **评审方式** | 分席只读（PRD §0.1 D/OQ · §2 目标/非目标 · §4 双轨 · §5 轨 A · §6 轨 B · OUT-01～10） |
| **记录人** | （填） |
| **本纪要状态** | **模板 · 备查**（正式结案见 [generative-collage-surfaces-v1-review-2026-07-18.md](./generative-collage-surfaces-v1-review-2026-07-18.md)） |

> **使用说明**  
> 1. 会前：参评人只读 PRD 定位块 + §0.1 + §2.2 非目标 + §4.2 禁止挂点；对照 MGQ「禁 runtime 改 rect」。  
> 2. 会中：§2 分席表决 → §4 收 Must-Fix → §6 拍板 D-GCS / OQ-GCS（**OQ-01 / OQ-03 本场必关**）。  
> 3. 会后：另存 `generative-collage-surfaces-v1-review-YYYY-MM-DD.md`，删「模板」字样；Must-Fix 回写 PRD 后再改结论行与 README 状态。

---

## 0. 会前宣读（主持人 · 3 分钟）

1. **切口**：BRIC 有价值，但落点是 **旁路**——轨 A 离线扩 LTE SKU；轨 B 海报导出 Writer。  
2. **已定案精神（勿当银弹重开）**：**禁止** MCS `used_legacy` 默认调 BRIC；**禁止** runtime 改 `slots[].rect`（对齐 D-MGQ-02）。  
3. **裁切**：海报面 = 统一 contain 系；**禁止**再套杂志 slot `cover`+focal。  
4. **术语**：用户 `mediaClass=collage` ≠ GCS 生成拼贴；海报 ≠ `moments_grid` 九宫格。  
5. **本场必拍**：D-GCS-01～10；**关闭** OQ-GCS-01（入口层级）与 OQ-GCS-03（拓扑规范化）。  
6. **本轮默认不动代码**（除非结论勾选可 Kickoff W0）。

---

## 1. 总评（一句话）

> （会后填写：双轨是否成立？禁区是否写死？最大阻塞是轨 A 投影、轨 B 入口，还是依赖/许可？W0 能否只做文档+工厂 spike？）

---

## 2. 分席表决

| 席位 | 表决 | 一句话 |
|------|------|--------|
| **产品** | □ Go / □ CG / □ No | |
| **算法** | □ Go / □ CG / □ No | |
| **架构** | □ Go / □ CG / □ No | |
| **开发** | □ Go / □ CG / □ No | |
| **测试 / QA** | □ Go / □ CG / □ No | |
| **交互 / UI（导出门面）** | □ Go / □ CG / □ No | |
| **用户 · 分享者** | □ Go / □ CG / □ No | |
| **用户 · Sparse 轻量册** | □ Go / □ CG / □ No | |

**汇总**：_/_ 席 · 结论 ______ · 未回写 Must-Fix 前 □ 不批无条件 Go

---

## 3. 全场共识（预填 · 会中可改）

1. **BRIC ≠ 杂志主链救场**：作 SKU 工厂 + 海报导出器，不作 runtime mosaic solver。  
2. **遵守 MGQ / P16 几何铁律**：固定 SKU + solidify；GCS 不进 `MosaicConfig` 评分路径。  
3. **轨 A KPI** = `used_legacy` / pattern-miss ↓，不是工厂产出 YAML 张数。  
4. **轨 B** 不抢 Sparse 默认 `chat_longshot`（除非本场推翻 OQ-01 倾向）。  
5. **名实一致**：用户可见「单屏海报」必须对应真 Writer；禁止长图 scroll 顶替。  
6. **W0 ≠ 主题完成**：W0=合同冻结 +（可选）枚举 spike；W1=工厂接线 + Writer；W2=入口/入库；W3=盲评/报表。  
7. **本轮默认只做评审/文档回写**。

**会中新增共识**：

- …

---

## 4. Must-Fix（阻塞 Kickoff · 候选清单 · 会中增删）

| ID | 议题 | 来源席位 | 要求 | 状态 |
|----|------|----------|------|------|
| **BLK-01** | 禁区一字面回写 | 架构 / 算法 | OUT-01/02 与 D-GCS-01/02 在 PRD §0 标「已冻结」；明确 MCS 失败口仍走 legacy | □ |
| **BLK-02** | P17-B stub 所有权 | 产品 / 文档 | stub 标明 GCS 拥有轨 A 排期；LSE 主线不吞并 | □ |
| **BLK-03** | OQ-GCS-01 入口冻结 | 产品 / 交互 | 主 CTA vs ▾ 写入已关闭一字面；同步 Output Recipe / 导出门面脚注 | □ |
| **BLK-04** | OQ-GCS-03 规范化策略 | 算法 / 架构 | 「投影轨道模型」或「直接 rect」二选一冻结；不合格拓扑丢弃规则可测 | □ |
| **BLK-05** | 依赖与许可 | 开发 / 架构 | MIT vendoring 或钉 commit；GPL（PhotoCollage）禁止进主包；AC-GCS-09 | □ |
| **BLK-06** | trip.json 边界 | 架构 | 轨 B 禁止伪 `patternId` 进 `screens[]`；落点 `exportArtifacts`/job 字段写清 | □ |
| **BLK-07** | 裁切合同可测 | 算法 / QA | 轨 B 无 per-slot cover；AC-GCS-05 含 AR/gutter fixture | □ |
| **BLK-08** | AC / IMPL 拆文节奏 | 开发 / QA | 拍板：W0 用 PRD §9–§10 挡门，或本轮即拆 ACCEPTANCE + IMPLEMENTATION | □ |
| **BLK-09** | （会中新增） | | | □ |

---

## 5. Should-Fix（不单独挡 Kickoff）

1. OQ-GCS-02（event-recap 绑海报）可保持「可选意图」，不挡 W0。  
2. OQ-GCS-04（face-aware letterbox）可进 V1.1；V1 统一 contain 即可。  
3. 轨 B 用户文案词表（「单屏海报」vs「精选拼贴」）进 Output Recipe 词表附录指针。  
4. 埋点 `gcs_*` 清单进 IMPLEMENTATION（评审后）。  
5. 代表 corpus 与 MGQ/BQP 盲评 trip 集是否共用——W3 前定即可。  
6. （会中新增）…

---

## 6. D-GCS / OQ 拍板表

### 6.1 决策（D-GCS）

| 决策 | PRD 草案 | 本场决议 | 写入 |
|------|----------|----------|------|
| **D-GCS-01** | 双轨；禁挂 MCS `used_legacy` | □ 采纳 □ 修订：____ | §0.1 |
| **D-GCS-02** | 遵守 MGQ；不进 MosaicConfig | □ 采纳 □ 修订：____ | §0.1 / §3 |
| **D-GCS-03** | MIT / vendoring；禁热路径漂移 | □ 采纳 □ 修订：____ | §7 |
| **D-GCS-04** | PhotoCollage 只读；禁 GPL 依赖 | □ 采纳 □ 修订：____ | §7 |
| **D-GCS-05** | 海报统一 contain 系 | □ 采纳 □ 修订：____ | §6 |
| **D-GCS-06** | 轨 B：3–6 推荐，硬上限 9 | □ 采纳 □ 修订：____ | §6 |
| **D-GCS-07** | 轨 B 不进 `screens[]` 伪 pattern | □ 采纳 □ 修订：____ | §6 / §7 |
| **D-GCS-08** | 轨 A 经 validator + admission | □ 采纳 □ 修订：____ | §5 |
| **D-GCS-09** | 确定性；禁生产 shuffle | □ 采纳 □ 修订：____ | §7 |
| **D-GCS-10** | 轨 B 默认露出绑盲评；轨 A KPI=miss↓ | □ 采纳 □ 修订：____ | §2 / §10 |

### 6.2 开放问题（OQ-GCS）

| OQ | PRD 倾向 | 本场决议（必填） | 写入 |
|----|----------|------------------|------|
| **OQ-GCS-01** | 默认 ▾，不抢 `chat_longshot` | （填）**本场必关** | §6 / Output Recipe 脚注 |
| **OQ-GCS-02** | event-recap 可选意图，不改叙事主链 | （填） | §6 |
| **OQ-GCS-03** | 投影到 stage cols/rows 轨道模型 | （填）**本场必关** | §5.2 |
| **OQ-GCS-04** | V1 统一 contain；face pad → V1.1 | （填） | §6.5 |
| **OQ-GCS-?** | （会中新增） | | |

---

## 7. 双轨范围签核

| 轨 | 范围陈述 | 产品签 | 算法签 | 架构签 | 备注 |
|----|----------|--------|--------|--------|------|
| **A · 离线 SKU 工厂** | 枚举 → validator → admission → YAML；不 runtime | □ | □ | □ | |
| **B · `poster_bric` Writer** | export surface；contain；≤9 | □ | □ | □ | |
| **禁区 · MCS runtime BRIC** | V1 不交付；另开 PRD 才可议 | □ | □ | □ | **关键** |
| **禁区 · 伪 patternId** | 不进杂志 `screens[]` | □ | □ | □ | |

---

## 8. 与相邻主题挡门关系（会中确认）

| 主题 | 关系 | 确认 |
|------|------|------|
| **MGQ** | 遵守 D-MGQ-02；GCS 不抢 MosaicConfig | □ |
| **LTE / Admission** | 轨 A 唯一入轨；复用 validator | □ |
| **P17-B stub** | 轨 A 升格归 GCS；匈牙利等仍归 LSE | □ |
| **URO** | 新 SKU 须可带 usage/eligibility；不另起引擎 | □ |
| **Output Recipe** | 增 preset/intent；不 fork 策展 | □ |
| **导出门面** | 不弱化 80% 主 CTA（随 OQ-01） | □ |
| **collage_routing** | 术语/telemetry 隔离 | □ |
| **moments_grid** | 分名；海报 ≠ 九宫格 | □ |

---

## 9. 代码 / 现网对齐摘要（架构 · 开发 · 会前可预填）

| 断言 | 现网观察（预填） | 会中确认 |
|------|------------------|----------|
| MCS 失败口 = legacy 规则屏，无 BRIC | 属实（无 `bric`/`fit_pictures` 实现） | □ 属实 □ 已变 |
| `mediaClass=collage` → full-frame contain | 属实（`collage_routing`） | □ |
| Output Recipe 有 `chat_longshot` / `moments_grid` 分流 | 属实 | □ |
| P17-B 仅 stub，无工厂脚本主交付 | 属实 | □ |
| MGQ 禁止 runtime 改 rect | 已冻结 D-MGQ-02 | □ |

**人日粗估（开发填）**：

| 波次 | 估时 | 备注 |
|------|------|------|
| W0（合同 + 可选 spike） | ____ 人日 | |
| W1（工厂 CLI + Writer） | ____ 人日 | |
| W2（入口 + admission 入库） | ____ 人日 | |
| W3（盲评 + miss 报表） | ____ 人日 | |

---

## 10. 验收挡门（会中勾选拆文策略）

| 项 | 决议 |
|----|------|
| W0 是否可用 PRD §9–§10 暂充验收 | □ 是　□ 否（本轮拆 ACCEPTANCE） |
| Kickoff 前是否必须有 IMPLEMENTATION | □ W0 可无　□ Kickoff 前必有 |
| 轨 B 默认露出是否绑 AC-GCS-BLIND ≥55% | □ 采纳　□ 修订阈值：____ |
| 杂志 golden / LRG 无回归是否 W1 硬门 | □ 是　□ 否 |

---

## 11. 下一步（勾选）

- [ ] Must-Fix 回写 PRD → 版本 ____  
- [ ] 另存正式纪要 `generative-collage-surfaces-v1-review-YYYY-MM-DD.md`  
- [ ] 更新 [docs/README.md](../README.md) GCS 状态行（Draft → Conditional Go / …）  
- [ ] 回写 [PRD-PHASE17-research-stub.md](../PRD-PHASE17-research-stub.md) 评审结论指针  
- [ ] 拆 `ACCEPTANCE-GENERATIVE-COLLAGE-SURFACES-V1.md` / `IMPLEMENTATION-…`  
- [ ] Output Recipe / 导出门面脚注（OQ-01）  
- [ ] Kickoff W0 排期：____  
- [ ] 狗粮：Sparse 3–6 张海报导出 N≥____；SKU 工厂至少 ____ 条 experimental

---

## 附录 · 会前材料包

| 材料 | 路径 | 必读 |
|------|------|------|
| 本 PRD | [PRD-GENERATIVE-COLLAGE-SURFACES-V1.md](../PRD-GENERATIVE-COLLAGE-SURFACES-V1.md) | §0.1 · §2 · §4–§6 |
| MGQ 禁区 | [PRD-MCS-GEOMETRIC-QUALITY-V1.md](../PRD-MCS-GEOMETRIC-QUALITY-V1.md) §0 D-MGQ-02 | ✓ |
| P17-B stub | [PRD-PHASE17-research-stub.md](../PRD-PHASE17-research-stub.md) | ✓ |
| LTE admission | [LTE-ADMISSION-LAYOUT-TEMPLATES.md](../LTE-ADMISSION-LAYOUT-TEMPLATES.md) | 轨 A 席必读 |
| Output Recipe | [PRD-OUTPUT-RECIPE-V1.md](../PRD-OUTPUT-RECIPE-V1.md) §7 意图矩阵 | 产品/交互必读 |
| 本模板 | 本文 | 记录人 |

---

## 附录 · 表决用词

| 符号 | 含义 |
|------|------|
| **Go** | 无条件通过；可按结论行 Kickoff |
| **CG**（Conditional Go） | 有条件通过；Must-Fix 回写前不批无条件 Go |
| **No** | No-Go；需重开范围或重大改写 |
