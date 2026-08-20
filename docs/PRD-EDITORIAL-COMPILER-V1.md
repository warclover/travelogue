# Travelogue · 编辑编译器 V1 产品需求文档（PRD）

| 属性 | 内容 |
|------|------|
| **产品代号** | Travelogue Studio |
| **文档版本** | **v0.2.0** |
| **状态** | **Conditional Go · Must-Fix 已回写**（[七席](./acceptance-records/edc-editorial-compiler-v1-review-2026-08-13.md) · 2026-08-13）· W0 文档可 Kickoff · W1 合码挡 BLK-01/04（已回写为合同）· W3 挡 BLK-02/03/06（已回写） |
| **DOC-STATUS** | **active** |
| **主题代号** | 「编辑编译器」— **EDC**（Editorial Compiler） |
| **触发来源** | 2026-08-13 手工游记 40 页模板对照 · [智能模板建议0813.md](./智能模板建议0813.md) · 产品要求：管线升级须逼近人类手工排版 **80%** 审美与叙事 |
| **前置条件** | LTE YAML SSOT · MCS/MTSO GA · MEGC 默认 on · MSA **默认 off（盲评不通过，冻结）** · LVP M0–M2 结案 · `crop_solver` + `slots[].cropFocal` 已存在 · SCR / P23 peak / FRP / CAL 现行 · NAS 默认关闸 |
| **关联文档** | [CHARTER.md](./CHARTER.md) · [AGENT-ARCHITECTURE.md](./AGENT-ARCHITECTURE.md) · [PRD-PHASE16-layout-template-engine.md](./PRD-PHASE16-layout-template-engine.md) · [PRD-PHASE17-layout-strategy-engine.md](./PRD-PHASE17-layout-strategy-engine.md) · [MTSO](./PRD-MOSAIC-TEMPLATE-SELECTION-OPTIMIZATION-V1.md) · [MSA](./PRD-MOSAIC-SLOT-ADAPTATION-V1.md) · [LVP](./PRD-LAYOUT-VIBE-PICKER-V1.md) · [SCR](./PRD-SCREEN-COPY-REGION-V1.md) · [P23](./PRD-PHASE23-peak-moment.md) · [FRP](./PRD-FOOD-ROLE-POLICY-V1.md) · [TSL](./PRD-TEMPLATE-SEMANTIC-LAYER.md)（Draft，不阻塞） · [CAL](./PRD-COVER-CALLIGRAPHY-TITLE-V1.md) · [ACP](./PRD-AI-CAPABILITY-PLATFORM-V1.md) · [NAS](./PRD-NO-AI-SURFACE-V1.md) · [ALG-V3](./PRD-ALGORITHM-OPTIMIZATION-V3.md) · [zine 调研](./RESEARCH-PHOTO-ZINE-SKILLS-2026-08.md) · [AEL](./PRD-ALBUM-EDITORIAL-LAB-V1.md)（画册试验床 · 验证本主题 W1+W2 内核） |
| **评审纪要** | [edc-editorial-compiler-v1-review-2026-08-13.md](./acceptance-records/edc-editorial-compiler-v1-review-2026-08-13.md)（结案 · 7/7 Conditional Go · BLK-EDC-01～06） |
| **验收** | Kickoff 后拆 [ACCEPTANCE-EDITORIAL-COMPILER-V1.md](./ACCEPTANCE-EDITORIAL-COMPILER-V1.md)；本文 **§12 为源** |
| **实施** | Kickoff 后拆 [IMPLEMENTATION-EDITORIAL-COMPILER-V1.md](./IMPLEMENTATION-EDITORIAL-COMPILER-V1.md) |
| **更新日期** | 2026-08-13 |

> **v0.2.0 相对 v0.1.0（七席回写 · 2026-08-13）**
>
> 1. **Conditional Go**：主线冻结；W0 文档可 Kickoff。  
> 2. **BLK-EDC-01～06 关闭为合同**：现网人像 crop 保持默认可达；`program`↔`narrativeRole` 映射；W3 接管密插 breath；W1 失败链不含换 pattern；LVP GA 改写显式；opener 与章分隔让路。  
> 3. **OQ-EDC-01～05 关闭**。  
> 4. D-EDC-03 / D-EDC-12 / D-EDC-14 按会中改写；新增 D-EDC-21～25。
>
> **定位**
>
> 现网已经能「把合格照片装进合格拼图」。缺的不是更多模板，而是**主编**：这一页为什么存在、谁上这页、裁到哪才得体。  
> EDC 在策展与 MCS 之间插入一层 **页纲领编译**，把手工画册里必须由人完成的两步（选图填槽、裁进槽位）收成确定性管线。模板继续封闭；Agent 不直出 HTML。
>
> **一句话目标**：默认零步仍出册；成册从「照片墙」升到「有节奏的杂志」——在可测尺度上达到人类手工排版 **约 80%** 的审美与叙事语法，而不是复制那本 40 页参考书的像素。
>
> **产品铁律**
>
> 1. **编辑器，不是模板工厂** — 运行时禁止生成新 pattern / HTML。离线提案另立（W5，非用户功能）。  
> 2. **几何裁切是权威** — 视觉模型只评论合法窗；不得推翻人脸/保护框硬闸。  
> 3. **宁留白，不毁构图** — 保主体失败则换槽 → 换同纲领模板 → contain；禁止硬 cover 砍头切脚。  
> 4. **不绑 MSA** — 不改槽轨道、不改舞台 AR；MSA 保持默认 off。  
> 5. **默认可达不外呼** — W1–W3 本地确定性；AI critic/judge 仍受 NAS / MayCall。  
> 6. **零步不增加** — 用户路径仍是选相册 → 出游记 → 分享；气质入口沿用 LVP，不新开向导。  
> 7. **一份合同管整条线** — 复杂子系统达标才拆子 PRD（§8）；禁止平行 Kickoff 五个算法专题。  
> 8. **80% 是语法覆盖，不是神作克隆** — 见 §2.3；达不到的 20% 写进非目标，避免验收时无限加码。

---

## 0. 读者指南

| 章节 | 澄清什么 |
|------|----------|
| §0.1 | 术语 |
| §0.2 | 与相邻主题所有权 |
| §1 | 问题与现网零件 |
| §2 | 目标 / 非目标 / **80% 操作化** |
| §3 | 已拍板决策（含三个分叉） |
| §4 | 目标管线与重构边界 |
| §5 | 数据模型 |
| §6 | 五层合同（角色 / 纲领 / 裁切 / 工艺 / 离线扩库） |
| §7 | 80% 量尺与盲评 |
| §8 | 子 PRD 拆出规则 |
| §9 | 里程碑 W0–W5 |
| §10 | 配置 / NFR |
| §11 | 风险与开放问题 |
| §12 | 验收 AC-EDC-* |

### 0.1 术语

| 术语 | 定义 |
|------|------|
| **编辑编译器 / EDC** | 本主题：把「页纲领 + 角色匹配 + 保主体裁切」编进默认可达 layout 管线 |
| **页纲领 `program`** | 这一屏的编辑任务：`opener` / `hero` / `mosaic` / `grid` / `breath` / `journal` / `peak` |
| **编辑角色 `editorialRole`** | 照片在册中的叙事角色：`vista` / `portrait` / `detail` / `sequence` / `unused` |
| **保主体裁切 / SSC** | Subject-Safe Crop：在既定槽 AR 内求裁切窗，保人脸/保护框/高风险风景 |
| **工艺层 / Craft** | 微倾、胶带、印章等确定性装饰；不改拓扑 |
| **手工 80%** | §2.3 五维量尺均值 ≥4.0/5，且相对现网 GA 盲评不败；**不是**与参考纸书像素一致 |
| **参考画册** | 2026-08-13 约 40 张手工页模板（选图+手裁）；灵感来源，非渲染金样 |

### 0.2 与相邻主题（所有权）

| 主题 | EDC 做 | EDC 不做 |
|------|--------|----------|
| **LTE / TPC** | 扉页 3～5 个新 YAML 准入；消费既有 registry | 不重写几何引擎；不运行时发明模板 |
| **MCS / MTSO** | 在 `program` 约束内选型；角色匹配进打分软项 | 不重写漏斗；不放宽 P21 dense 上限 |
| **MSA** | **不打开、不复用其调轨** | 不把 crop_risk 反馈进窗口尺寸（避免 pacing 副作用，见 [MSA 盲评](./acceptance-records/msa-blind-review-2026-08-03.md)） |
| **MEGC / EGA** | 等权网格仍归 `grid` 纲领 | 不改等权几何合同 |
| **LSE / Editorial hints** | 不把 CAP-14 hint 当插入权威 | hint 默认 false 且不改 screens；W3 挂钩是 `insert_breath_screens_in_chapters` + 节奏 post-check |
| **ADR-020 `narrativeRole`** | `program` **映射**其上（D-EDC-22） | 不平行再造一套互不翻译的枚举 |
| **chapter-separator** | 有 opener 则章名让路（D-EDC-25） | 不叠两层巨字 |
| **LVP** | 盲评通过后，推荐气质吸收 SSC；W4 工艺不新增第三卡 | 不改两卡 IA；不把 MSA 绑进推荐 |
| **SCR** | 扉页主标题走屏级文案区；空则仍像干净章首 | 不强迫每屏必有字；不改 AIR Prompt |
| **P23 peak** | `peak` 纲领挂现有 moment/peak 屏 | 不重写 peak 打分 |
| **FRP** | 美食角色仍归 FRP；`editorialRole` 不替代 `subjectClass=food` | 不把菜当 vista/hero |
| **TSL** | 角色匹配是 TSL-P-01 的**可交付切片**；硬约束仍几何 | 不实现完整语义词表 / admin |
| **CAL / CAD** | 内页工艺学「实拍权威 + 派生装饰」 | 不管封面选片与书法贴纸 |
| **ACP / layout_critic / mosaic_judge** | 顾问可读 `program`；建议仍白名单 patternId | 不新开 Agent；不让 critic 改默认可达胜出 |
| **NAS / BAI** | 默认可达零外呼 | 不改 Key / 路由 / Sheet IA |
| **Bookends** | 正文屏；封面封底仍归 Bookends | 不把 Opening 改成章扉页 |
| **AEL** | 收画册 L1+L2 通行证后再 Kickoff W1/W2；求解器与角色枚举共用 | **不**在本主题实施 `album_spread`；画册选图×裁切试验归 [AEL](./PRD-ALBUM-EDITORIAL-LAB-V1.md)。画册绿 **不等于** 本主题 W3 / 80% 门 |

---

## 1. 背景与问题

### 1.1 对照事实

手工参考册好看，是因为人做了两件事：挑哪张进哪页、裁到哪个不规则槽。本项目立志省掉这两步。现网零件已经很多（约 47 套槽位模板、MCS/MTSO、`crop_solver`、节奏禁令、`screen-breath-pause`、editorial hints、峰时刻、封面工艺），但**没有主编层**：先定拓扑再塞图，裁切被动，页与页缺少「故意少图」。

战略上也不再平行 Kickoff MSA/MEGC/SSG 这类悬空专题（见 [战略优先级复盘](./INSIGHT-STRATEGIC-PRIORITY-REVIEW-2026-08-03.md)）。EDC 是**收口与升维**，不是第五个算法开关。

### 1.2 用户可感知问题

| ID | 问题 | 相对手工册 | 落点 |
|----|------|------------|------|
| **P-EDC-01** | 人像砍头切脚、风景切地平线 | 手裁「得体」 | §6.3 SSC |
| **P-EDC-02** | 大场景进小槽、细节占满幅 | 人选角色填槽 | §6.1 角色 |
| **P-EDC-03** | 连续同构网格，没有扉页/呼吸 | 成册节奏 | §6.2 纲领 |
| **P-EDC-04** | 内页字只是图说，不是建筑 | 「出发」巨字扉页 | W3 扉页 SKU |
| **P-EDC-05** | 整齐但不「手作」 | 微倾/胶带/印章 | W4 工艺（可选） |
| **P-EDC-06** | 误以为要 AI 现场生模板 | 封闭设计系统 | D-EDC-02 |

### 1.3 现网可复用（禁止重写）

| 零件 | 用途 |
|------|------|
| `assets[].focalPoint` / `protectBox` | SSC 输入 |
| `slots[].cropFocal` / `cropContain` / `cropSafety` | **已在默认路径写入**（cover 槽）；W1 **扩展条件**，不另起字段名 |
| `apply_slot_crop_focals` | As-Is：人脸 clipped → contain；无人脸 → cover（不看 crop_risk） |
| `slots[].role`（portrait/landscape/main/food） | 槽侧角色；照片侧补 `editorialRole` |
| `layout_contract.rhythm` 连续禁令 | 升为 `program` 连续封顶 |
| `insert_breath_screens_in_chapters`（interval 默认 4） | **现网密插**；W3 **接管**为每章 ≤1，不是从零插入 |
| ADR-020 `narrativeRole` | `program` 的推导底（D-EDC-22） |
| `chapter-separator` | 章名条；与 opener 互斥标题（D-EDC-25） |
| P23 `data-role="peak"` / `moment` | `program=peak` |
| FRP `subjectClass=food` | 与角色正交，美食 demote 继续有效 |
| `layout_critic` 白名单建议 | 开闸加分，不改默认可达 |

---

## 2. 目标与非目标

### 2.1 目标

| ID | 目标 |
|----|------|
| **G-EDC-01** | 默认可达管线按 **角色 → 纲领 → 模板 → 保主体裁切** 编译；无 Key 成片不退化 |
| **G-EDC-02** | 主体完整性显著优于现网 GA（人像硬闸；风景高 crop_risk 合法留白或换槽） |
| **G-EDC-03** | 每合格章可见扉页或等价章首；禁止连续三屏同一 `program` |
| **G-EDC-04** | V1 新模板 **仅** 3～5 个扉页 YAML；不扩拼图 SKU |
| **G-EDC-05** | 预览与导出共用持久化裁切窗 |
| **G-EDC-06** | 父开关可回滚到关闭**增量** ≡ 现网 GA（含人像 crop 与密插 breath） |
| **G-EDC-07** | **80% 门**：§7 量尺在约定语料上达标 |

### 2.2 非目标

| ID | 非目标 | 理由 |
|----|--------|------|
| **N-EDC-01** | 运行时生成模板 / 自由 HTML | 章程；回归；品牌 |
| **N-EDC-02** | 打开 MSA 或改 16:9 / 9:16 舞台 | pacing 雷；交付契约 |
| **N-EDC-03** | 人手选图、手裁主路径 | 另一个产品 |
| **N-EDC-04** | 纸书对页引擎 / 第二套画布 | 新产品，非本升级 |
| **N-EDC-05** | 默认异形槽、任意多边形遮罩 | 裁切倍增器；W4 仅矩形+CSS 变换 |
| **N-EDC-06** | 默认路径外呼 VL / 生图 | NAS；L0 永不因缺 Key 失败 |
| **N-EDC-07** | 完整 TSL 词表与模板后台语义编辑 | Draft 不阻塞；本主题只交付角色切片 |
| **N-EDC-08** | 文学正文达到人类游记作者 80% | 叙事 80% 指**页序与章法**，不是文笔（文笔归 AIR） |
| **N-EDC-09** | 与参考 40 页册版式坐标一致 | 画布不同；借语法不借网格 |
| **N-EDC-10** | LVP 第三卡 | V1 工艺走 EDC 实验旗；不破坏两卡 IA |

### 2.3 「人类手工排版 80%」操作化（北极星）

手工册最后 20% 不可自动化：某一张「就是这一章的灵魂」、半像素的情绪裁切、对页文学节奏、即兴手帐。EDC **不承诺**这 20%。

承诺的 80% 是**可识别的编辑语法覆盖**：

| 维 | 手工在做什么 | EDC 做到什么算 80% | 明确不做的 20% |
|----|--------------|-------------------|----------------|
| **A 得体** | 裁到脸/地平线完整 | 人像零砍头切脚红线；风景高风险不硬砍 | 为「更好看」做艺术性二次构图 |
| **B 节奏** | 扉页→英雄→密网→留白 | 每章有章法；连续同构下降 | 像设计师一样每页独一无二 |
| **C 匹配** | 大场景进大槽、脸进竖槽 | 角色→槽位可解释命中 | 美食/建筑/情绪的细分类审美 |
| **D 叙事** | 「出发」起、高光落 | 章首 + 峰/签名仍在；页序可读 | 人类作者级文案与隐喻 |
| **E 纸面** | 留白、字当建筑、偶发手作 | 扉页巨字 + 合法留白；工艺可选 | 默认满页胶带拼贴 |

达标公式见 §7。产品话术对外可说「接近手工画册的气质」，对内验收只认量尺，不认「我觉得还差一口气」的无限加码。

---

## 3. 已拍板决策（产品总监 · v0.1.0）

三个原讨论分叉于此锁定。

| ID | 决策 |
|----|------|
| **D-EDC-01** | **一份总 PRD 管整条线**。子 PRD 仅当 §8 拆出条件满足。Kickoff 后先拆 ACCEPTANCE / IMPLEMENTATION，不拆五个主题 PRD。 |
| **D-EDC-02** | 禁止运行时生成 pattern / HTML。离线 YAML 提案 = W5 内部工具。 |
| **D-EDC-03** | **现网人像求解保持默认可达**（不关 `crop_solver`）。「先盲评再默认开」只适用于 W1 **增量**（风景 crop_risk contain、同屏换槽）。增量过门后吸收进 LVP `magazine_default`（D-EDC-24）。 |
| **D-EDC-04** | **W3 改页数：默认每章最多 +1 扉页**；breath **有条件、每章最多 +1**。`program.enabled` 时 **禁用**现网 interval=4 密插（D-EDC-23）。手帐页只进 W4 实验气质。插入可一键回滚。 |
| **D-EDC-05** | 80% = §7 五维量尺，不是参考书像素克隆。 |
| **D-EDC-06** | 裁切权威 = 几何求解；AI 只在合法候选上评论。 |
| **D-EDC-07** | **不打开 MSA**。SSC 只改槽内裁切，不改轨道、不把 crop 分反馈进 MCS 窗口尺寸。 |
| **D-EDC-08** | 不改 Web 16:9 / 竖屏 9:16 / 长图契约。 |
| **D-EDC-09** | W1–W3 默认可达零外呼；critic/judge 仍 MayCall。 |
| **D-EDC-10** | `layout_critic` 继续只写建议、不改 `chapters[]`。 |
| **D-EDC-11** | V1 新增模板上限：**3～5 个 `program=opener` YAML**。 |
| **D-EDC-12** | **W1 失败链**：同屏换槽 → `fit=contain`。**禁止** W1 换 pattern（避免改窗宽/页数，对齐 AC-EDC-05）。换同 `photoCount` 的 pattern 最早 **W2**，且须单测内容屏张数不变。人脸硬闸不可关闭。 |
| **D-EDC-13** | 照片角色枚举：`vista \| portrait \| detail \| sequence \| unused`。美食继续走 FRP，不新增 `food` 到此枚举。 |
| **D-EDC-14** | 纲领枚举：`opener \| hero \| mosaic \| grid \| breath \| journal \| peak`。`journal` V1 可映射现有 editorial/文案屏，不新造长文引擎。**须映射 ADR-020 `narrativeRole`**（D-EDC-22）。 |
| **D-EDC-15** | 裁切持久化扩展现有 `cropFocal` / `cropContain` / `cropSafety`；预览/导出/重渲染共用。 |
| **D-EDC-16** | 连续同一 `program` 硬顶 **2**（对齐 ALG-V3 VC-04 连续同 pattern 精神，主尺改为 program）。 |
| **D-EDC-17** | 重构范围 = layout **编排层**。不推倒 LTE/MCS/visual-journal。 |
| **D-EDC-18** | 默认路径零新增用户步骤。 |
| **D-EDC-19** | W4 工艺默认 off；不新增 LVP 第三卡。 |
| **D-EDC-20** | 父开关 `editorial_compiler.enabled=false` 时行为 ≡ 关闭**增量**前的 GA（**含**现网人像 crop_solver；**含** interval=4 breath 密插）。 |
| **D-EDC-21** | （BLK-01）W1 配置键只控增量；禁止「父关则不写 cropFocal」。 |
| **D-EDC-22** | （BLK-02）`program` 可空；缺失时由 `narrativeRole` + `patternId` 推导。映射见 §6.2.1。旧 trip 无 `program` 可渲染。 |
| **D-EDC-23** | （BLK-03）`program.enabled=true` 时 web `insert_breath_screens_in_chapters` 与长图 `interleave_breath_items` 均改走章配额，禁止 interval=4。 |
| **D-EDC-24** | （BLK-05）W1 增量默认 on 出门日：修订 LVP `magazine_default` 剖面与推荐卡后果文案；AC-LVP-01 另条增补，禁止静默改 GA。 |
| **D-EDC-25** | （BLK-06）章内存在非空标题的 `program=opener` 屏 → 该章 `chapter-separator` 不上章名（可保留线）；长图同样。 |

### 3.1 分叉理由（备查）

1. **裁切增量先盲评再默认开**：现网人像求解已在默认可达。MSA AC-09 在三册上 2/3 倾向 off，且 on 会改变页数。W1 若把「风景 contain / 换槽」一上来默认 on，无法与现网人脸路径拆开评。人脸路径保持开；增量先实验，过门再进推荐气质。  
2. **扉页 +1、breath 有条件，且须先关掉密插**：现网每 4 屏插 ··· 已能把册插肿。W3 在密插之上再加扉页会让长图更劝退。配额成立的前提是 D-EDC-23 接管插入政策。  
3. **一份总 PRD**：避免再出现五个 Conditional Go 悬空；复杂处用 §8 门槛拆，而不是预先拆。

---

## 4. 目标管线与重构边界

### 4.1 As-Is（简化）

```
照片 → 筛选/聚类/分章 → 开窗 → MCS 选模板 → 绑图 → CSS cover（偶发 crop_solver）→ 渲染
                              ↑ 节奏禁令（偏惩罚，少插入）
```

### 4.2 To-Be

```
照片 → 筛选/聚类/分章
    → 角色标注（确定性；VL 仅 MayCall 校准）
    → 页纲领序列（每章剧本 + 配额）
    → 在纲领内 MCS/MTSO 选已有模板
    → 保主体裁切（写入 cropFocal；失败走 D-EDC-12）
    → 可选工艺层（W4）
    → 渲染（web / 长图读同一 slot 契约）
```

### 4.3 重构允许 / 禁止

| 允许 | 禁止 |
|------|------|
| curate→layout 抽出 PageProgram 编排 | 重写 MCS 打分器核心 |
| 扩展 crop 求解**条件**（风景 crop_risk / 同屏换槽） | 改舞台 AR；打开 MSA；W1 换 pattern |
| `assets[].editorialRole` 入 schema | Agent 直出 HTML |
| 接管 breath 插入政策 + peak 映射 | 第二套纸书引擎；把 CAP-14 hint 当插入权威 |
| 扉页 3～5 YAML + CSS | 运行时组合爆炸出新拓扑 |

挂点建议（实施时可微调，须在 IMPLEMENTATION 钉死）：角色在 bind 窗口之前；纲领在 MCS 候选过滤之前；SSC **增量**在现有 `apply_slot_crop_focals` 之后或之内扩展，不得拆掉现网人脸路径。**禁止**把 SSC 的 contain 分写回 MCS 窗口宽度（D-EDC-07）。**禁止** W1 换 pattern。

---

## 5. 数据模型（W0 钉死，W1 起写入）

字段名为草案，W0 与 `trip.schema.json` 对齐后冻结。原则：能扩展现有键就不造平行键。

### 5.1 照片

```json
"editorialRole": "vista|portrait|detail|sequence|unused",
"editorialRoleSource": "rules|manual",
"editorialRoleConfidence": 0.0
```

- 仅 `rules` 进入默认可达。`manual` 预留给精修（V1 可不做 UI）。  
- 与 `subjectClass` / FRP 共存：`food` 仍可标 `detail` 或 `unused`，但封面/peak demote 继续由 FRP 执行。

### 5.2 屏

```json
"program": "opener|hero|mosaic|grid|breath|journal|peak",
"programReason": "chapter-opener-quota"
```

- `patternId` 仍是渲染权威。  
- `program` 是选型约束与节奏主尺；**可空**，缺省由 `narrativeRole` + `patternId` 推导（D-EDC-22）。  
- 现有 `data-role="peak"|"moment"` 必须能映射到 `program=peak`（可派生，不必双写冲突）。  
- schema `additionalProperties: false`：W0 必须把 `program` / `programReason` / `editorialRole*` 写入 `trip.schema.json`。

### 5.3 槽（扩展，不改名）

| 字段 | V1 用法 |
|------|---------|
| `cropFocal` | 全槽求解结果（不限人像） |
| `cropContain` | 失败链走到 contain |
| `cropSafety` | 遥测：人脸是否完整、crop_risk、失败原因 |
| `fit` | 仍只 `cover` \| `contain` |

渲染只执行固化值（继承 LTE fit 三层模型）。

### 5.4 回滚

`editorial_compiler.enabled=false`：关闭**增量**（风景 contain / 换槽 / 角色 / 纲领插入）。现网人像 `cropFocal` 与 interval=4 breath **仍按 GA 运行**。旧 trip 无新字段可渲染。

---

## 6. 五层合同

### 6.1 角色标注（W2）· 替代「人选哪张进哪槽」

**默认可达 = 规则**，不绑视觉模型。

| 信号（示意，W0 钉阈值） | 倾向角色 |
|--------------------------|----------|
| 人脸或 protectBox 有效 + 竖/近方 | `portrait` |
| 无人脸 + 宽幅 + 质量高 | `vista` |
| 近重复簇非主图、局部、低场景分 | `detail` |
| 同场景短时密序列（可复用 SSG scene，不依赖 SSG look） | `sequence` |
| 质量闸淘汰 / 明确不用 | `unused` |

选型约束（软，可打分；硬的只保留朝向门）：

- `vista` 优先 `hero` 主槽或宽槽  
- `portrait` 优先竖槽；禁止无门放进超宽扁槽  
- `detail` 禁止独占 `hero`/`opener` 满幅（除非章内没有 vista/portrait）  
- `sequence` 优先 `grid`  
- 美食：FRP 优先于本表

验收看命中率与反例（菜单进封面、脸进扁槽），不看 CLIP 新模型。

### 6.2 页纲领（W3）· 替代「每页都拼满」

每合格章默认剧本（不足素材则降级，不造空页）：

1. `opener`（每章最多 1）  
2. `hero` 或 `peak`（有池则峰仍按 P23）  
3. `mosaic` 或 `grid`  
4. 条件 `breath`（密度高 / 连续 mosaic≥2 之后）  
5. `journal` 仅当该屏已有 SCR 文案或 editorial 模板命中

硬配额：

| 规则 | 值 |
|------|-----|
| 每章 `opener` | ≤1 |
| 每章插入型 `breath` | ≤1，且须触发条件 |
| 连续同一 `program` | ≤2（D-EDC-16） |
| 因 EDC 导致的章内屏数净增 | ≤2（扉页+breath）；**相对「无密插、无扉页」的内容屏**，不是叠在 interval=4 之上再 +2 |

**Breath 治理（D-EDC-23 · BLK-03）**：`program.enabled=true` 时禁用 `insert_breath_screens_in_chapters` / `interleave_breath_items` 的 interval=4 密插，改为上表配额。父关回 GA 密插。`screen-breath-pause` 仍无 LTE YAML，保持特殊 pattern。

**与 `narrativeRole` 映射（D-EDC-22 · W0 冻结，可微调）**

| `program` | 典型 `narrativeRole` / pattern |
|-----------|--------------------------------|
| `opener` | 新 pattern 族；**无**现成 narrativeRole → W0 增 `opener` 或暂用 `plate` + pattern 前缀 |
| `hero` | `hero_single` |
| `mosaic` | `mosaic_hero` / `mosaic_flat` |
| `grid` | `stack` / `pair`（等权宫） |
| `breath` | `breath` |
| `journal` | `plate` + 有 SCR/editorial |
| `peak` | 现有 `data-role=peak\|moment`（与 narrativeRole 并存，语义分离已在 ADR-020） |

扉页 SKU（D-EDC-11）：

- 3～5 个固定 YAML，大中文标题（章名/地名）当建筑，0～1 张图。  
- 文案空则隐藏（SCR 空隐纪律）；标题优先级见 OQ-02 结案。  
- 必须进长图 flatten（学 SCR L1：禁止展平丢章首）。  
- **D-EDC-25**：该章 opener 标题非空 → `chapter-separator` 不上章名。

`journal` V1 **不**新写长文排版引擎，只标签化现有图文屏。完整手帐长文若需要，走 §8 拆出。

### 6.3 保主体裁切（W1）· 增量主战场

**As-Is（不可卸载）**：`apply_slot_crop_focals` 已对 cover 槽写 `cropFocal`；人脸 clipped 才 contain；无人脸走 focal cover。

**To-Be 增量（开关可控、默认 off 至盲评过门）**：

1. **感知**：沿用 face / protectBox / focalPoint；风景用 crop_risk + AR 错配，**不上**地平线模型（OQ-03）。  
2. **几何**：扩展 contain 条件（高 crop_risk 且非 bleed 名单）；**同屏换槽**（匈牙利/既有 rebind）。结果仍写 `cropFocal`。  
3. **评论（MayCall）**：mosaic_judge 可打分，不可改硬闸。  
4. **W1 不做**：换 pattern、改窗口张数、打开 MSA。

人像：脸硬约束；群像同一窗；protectBox 过大不得为保框破坏满幅合同（bleed 名单）。  
风景：高 crop_risk → contain 或同屏换槽，不硬砍 3:2 进扁槽的上下约 15%。contain 底色对齐杂志纸色（SHD-EDC-02）。

不规则槽分档：V1 只做 **档 A 矩形**。档 B（微倾）= 先裁正再 CSS，W4。档 C 异形 = 非目标。

### 6.4 工艺层（W4）· 手工感

确定性 CSS：微倾角度白名单、胶带色、角章。实拍像素不被重绘。默认 off。不进 LVP 第三卡。盲评单独做，失败则长期 dark。

### 6.5 离线模板语法（W5）· 内部

设计师助手：语法 → YAML 提案 → 几何审计 → 探针图 → 人工准入。无 Studio 入口。可无限期延期。

---

## 7. 80% 量尺与盲评

### 7.1 五维量表（每维 1–5）

| 维 | 1 | 3（现网常见） | 5（手工语法） |
|----|---|---------------|---------------|
| **A 得体** | 多处砍头/切地平线 | 偶发受伤 | 主体完整，留白可解释 |
| **B 节奏** | 连续同构墙 | 偶有变化 | 章内能指认扉页/英雄/密网/呼吸 |
| **C 匹配** | 角色明显错位 | 大体过得去 | 大图大槽、脸在竖槽、细节不占满幅 |
| **D 叙事** | 无章法 | 有分章无章首 | 起（扉页）承（英雄/网格）转（呼吸）合（峰/章末）可读 |
| **E 纸面** | 满铺廉价 | 整齐杂志 | 留白+字有建筑感（工艺加分不倒扣） |

### 7.2 通过线（G-EDC-07）

语料：至少 **3 本真实册**（建议复用 MSA 三册：混排 / 重混排 / 近全单反），整章对照，打乱 A/B。

| 门 | 标准 |
|----|------|
| **相对 GA** | 整章偏好 EDC-on **≥ GA**（胜+平 ≥70% 对，且无红线回退） |
| **绝对语法** | 五维均值 **≥ 4.0**；任一维平均 **≥ 3.5** |
| **红线** | 人像砍头切脚不可接受；朝向硬门不回退；舞台 AR 不变；**W3 页数净增不超过 §6.2 配额** |
| **零步** | 无 Key、NAS 关闸，成片可出 |

W1 盲评只评 **A + 红线 + 页数不因 SSC 漂移**（D-EDC-07）。  
W3 盲评评 **A–E 全量**，才算 80% 门。  
W4 不挡 80% 门。

未达标：默认保持 off，记原因，禁止用「再开一个算法专题」代替修配额/裁切。

### 7.3 与参考 40 页册的关系

参考册用于定义量表的「5 分长什么样」，**不**作为 A/B 对手。画布不同，像素对比无意义。

---

## 8. 子 PRD 拆出规则

总 PRD 已覆盖合同。仅当下列**触发**成立，才单独立项（新文件 + DOC-STATUS 行）。未触发则继续在 EDC 波次内实施。

| 子主题 | 代号 | 触发（满足其一） | 仍由 EDC 管的 |
|--------|------|------------------|---------------|
| 保主体裁切深化 | **SSC** | 需新地平线/显著物模型；或 crop 契约超出扩展 `cropFocal` | W1 人像硬闸 + crop_risk contain |
| 页纲领与长图 | **PPR** | 扉页 SKU>5 或 journal 要独立长文引擎；或长图 flatten 需独立七席 | 配额、program 枚举、+1/+1 |
| 内页工艺 | **CRF** | 需要 CAL 级风格注册表 / 多 Opening 适配 | W4 开关与「非默认」 |
| 离线扩库 | **OTG** | 真要做内部提案工具 | 「禁止运行时生成」 |
| 角色语义 | 并入 **TSL** | TSL 转正且要接管 editorialRole | W2 规则表 |

拆出后：子 PRD 不得修改 D-EDC-02/07/08/12/18；冲突以本文为准，直到七席改版。

---

## 9. 里程碑

编码 Kickoff 以 W0 评审 Go 为准。W1 合码不要求 80% 全量（全量在 W3）。

| 波次 | 内容 | 合码 / 出门门 | 默认 |
|------|------|----------------|------|
| **W0** | schema 扩字段 · `program`↔`narrativeRole` 映射表 · 3 册纸面模拟（密插 vs 配额）· 拆 AC/IMPL | 七席已 Go；本波文档 | — |
| **W1** | SSC **增量**（crop_risk contain + 同屏换槽）；人像路径保持；增量开关 | AC-EDC-01～08；**盲评 A 维 + 内容屏张数不漂移** | 增量 **off** → 过门后 on（D-EDC-24） |
| **W2** | editorialRole 规则 + 选型软约束；可选同 photoCount 换 pattern | AC-EDC-09～12 | 随父开关 |
| **W3** | program 编排 + 3～5 扉页 + **接管 breath** + 长图 flatten + 章分隔让路 | AC-EDC-13～18/21～23；**盲评 A–E（80% 门）** | 过门后 on；可单独关插入 |
| **W4** | 工艺 CSS 实验旗 | 单独盲评；失败则 dark | **off** |
| **W5** | 离线 YAML 助手 | 可无限延期 | 无用户面 |

W3 必须提供 **插入回滚**（只关 opener/breath，保留 W1/W2），避免 80% 门失败时连得体裁切一并关掉。

---

## 10. 配置与 NFR

### 10.1 配置（示意）

```yaml
editorial_compiler:
  enabled: false          # 父开关；false ≡ 关闭增量（人脸 crop / 密插 breath 仍按 GA）
  crop:
    enabled: false        # 只控 W1 增量（风景 contain / 同屏换槽）
    face_hard_gate: true  # 不可关；现网人脸求解不走此键关闭
  roles:
    enabled: false
  program:
    enabled: false        # true 时接管 breath 密插（D-EDC-23）
    max_opener_per_chapter: 1
    max_breath_per_chapter: 1
    max_consecutive_program: 2
    max_net_screens_added_per_chapter: 2
  craft:
    enabled: false
```

禁止把上述键暴露为用户可见的算法缩写。用户面最多沿用 LVP 两卡；实验裁切在通过前可走 dark / 狗粮配置。

### 10.2 NFR

| ID | 要求 |
|----|------|
| **NFR-01** | 同 trip + 同配置重跑 layout，`program`/`cropFocal` 稳定（允许浮点容差） |
| **NFR-02** | W1 对默认墙钟：大册（~200 图）裁切求解不得把 layout 做成不可用（W0 定预算；超则只对高风险槽求解） |
| **NFR-03** | 无新字段 trip 可渲染 |
| **NFR-04** | NAS 关闸零外呼 |

---

## 11. 风险与开放问题

### 11.1 风险

| 风险 | 缓解 |
|------|------|
| 插入页让长图过长、pacing 变差（MSA 同类） | D-EDC-04 硬顶；W3 单独回滚；盲评查页数 |
| SSC 留白被看成「没铺满/廉价」 | 杂志纸色 contain（MSA BLK-06 可借鉴）；量表 E 维解释留白 |
| 角色规则把好图标成 detail | 保守：不确定 → 不降级；只在高置信约束 |
| 扉页无字变空洞 | SCR 空隐；无章名则降级跳过 opener |
| 80% 被理解成「再调一年」 | §2.3 / §7 锁门；未过则 off，不叠加专题 |
| 文档加法 | 子 PRD 有触发门槛 |

### 11.2 开放问题（七席已结案 · 2026-08-13）

| ID | 问题 | 结案 |
|----|------|------|
| **OQ-EDC-01** | 极小章是否强制 opener？ | ✅ **跳过**（layoutEligible &lt; 4） |
| **OQ-EDC-02** | 扉页标题章名还是地名？ | ✅ **章名 → 地名 → 皆空则跳过 opener** |
| **OQ-EDC-03** | W1 是否上地平线模型？ | ✅ **不上**；AR 错配 + crop_risk；系统性失败再拆 SSC |
| **OQ-EDC-04** | `journal` 是否进枚举？ | ✅ **保留枚举**；V1 映射现有屏 |
| **OQ-EDC-05** | 80% 评委人数 | ✅ 至少 **1 产品 + 1 非作者**；开发者须打乱 A/B |

---

## 12. 验收摘要（源）

Kickoff 后拆 ACCEPTANCE；下列为合同源。编号预留，实施时可补细项。

| ID | 摘要 | 波次 |
|----|------|------|
| **AC-EDC-01** | 父开关 false ≡ 关闭增量前 GA（pattern 序列主尺）；**不得**少写现网人脸 `cropFocal` | W1 |
| **AC-EDC-02** | 人像硬闸：合成 fixture 砍头则 contain 或**同屏**换槽，不得 cover 切脸 | W1 |
| **AC-EDC-03** | `cropFocal` 写入 slots；render 不重解（除非 layout 重跑） | W1 |
| **AC-EDC-04** | 预览与长图 object-position 同源 | W1 |
| **AC-EDC-05** | W1 增量 **不**改变窗口张数/章内**内容屏**张数（相对增量 off；breath 屏不计此条） | W1 |
| **AC-EDC-06** | 不打开 `slot_adaptation.enabled` | W1 |
| **AC-EDC-07** | NAS 关闸零 LLM/VL 调用 | W1 |
| **AC-EDC-08** | W1 盲评：A 维 on≥off；红线无回退；内容屏张数不漂移 | W1 出门 |
| **AC-EDC-09** | `editorialRole` 规则单测（竖脸→portrait，宽无人脸→vista） | W2 |
| **AC-EDC-10** | 无 vista/portrait 时 detail 允许满幅（降级合法） | W2 |
| **AC-EDC-11** | FRP 美食 demote 不回退 | W2 |
| **AC-EDC-12** | 角色约束不突破朝向硬门 | W2 |
| **AC-EDC-13** | 合格章 opener≤1；无素材或极小章则跳过 | W3 |
| **AC-EDC-14** | 连续 program≤2 | W3 |
| **AC-EDC-15** | 章内因 EDC 净增屏≤2（相对无密插基线） | W3 |
| **AC-EDC-16** | 扉页 3～5 YAML 在 registry；长图 flatten 含 opener | W3 |
| **AC-EDC-17** | 插入回滚后保留 W1/W2 | W3 |
| **AC-EDC-18** | W3 盲评：§7.2 80% 门 | W3 出门 |
| **AC-EDC-19** | 工艺默认 off；无 LVP 第三卡 | W4 |
| **AC-EDC-20** | 无运行时生成模板的代码路径（禁测：不存在 public API） | 全程 |
| **AC-EDC-21** | 缺 `program` 时可由 `narrativeRole`+pattern 推导；二者不矛盾 | W0/W3 |
| **AC-EDC-22** | `program.enabled` 时 web+长图均无 interval=4 密插；每章 breath≤1 | W3 |
| **AC-EDC-23** | opener 标题非空之章，chapter-separator 无章名 | W3 |

---

## 13. 变更记录

| 版本 | 日期 | 说明 |
|------|------|------|
| v0.2.0 | 2026-08-13 | 七席 Conditional Go 回写。BLK-EDC-01～06 → D-EDC-21～25；D-EDC-03/12/14 改写；OQ-01～05 结案；AC-21～23。纪要：[edc-editorial-compiler-v1-review-2026-08-13.md](./acceptance-records/edc-editorial-compiler-v1-review-2026-08-13.md)。 |
| v0.1.0 | 2026-08-13 | 初稿。产品总监拍板：总 PRD 管线、W1 裁切先盲评再默认开、W3 每章 +1 扉页 + 有条件 breath、80% 五维量尺。灵感来源 [智能模板建议0813.md](./智能模板建议0813.md)。 |
