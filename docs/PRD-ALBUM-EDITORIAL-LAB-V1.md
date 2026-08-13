# Travelogue · 画册编辑试验床 V1 产品需求文档（PRD）

| 属性 | 内容 |
|------|------|
| **产品代号** | Travelogue Studio |
| **文档版本** | **v0.2.2** |
| **状态** | **Conditional Go · Must-Fix 已回写**（[七席](./acceptance-records/ael-album-editorial-lab-v1-review-2026-08-13.md) · 2026-08-13）· **v0.2.1** 产品补记探针参考页（混出 4 + 第 5 套评测-only）· L0 隔离可 Kickoff · L1 合码挡 BLK-AEL-01/02/04/07/08 · L2 挡 BLK-AEL-05 · 通行证挡 BLK-AEL-06 |
| **DOC-STATUS** | **active** |
| **主题代号** | 「画册编辑试验床」— **AEL**（Album Editorial Lab） |
| **触发来源** | 2026-08-13 手工游记约 40 页模板对照 · 产品确认：参考图更适合单独升级**画册出口**，用其验证 [EDC](./PRD-EDITORIAL-COMPILER-V1.md) 的选图×裁切内核，再决定是否升全书 layout |
| **前置条件** | [ECC](./PRD-EXPORT-CARD-COMPOSE-V1.md) GA（CardGrouper / Selector / Renderer · 28 套 3:4 模板）· [ABE](./PRD-ALBUM-EXPORT-BOOKENDS-V1.md) 封面封底已落地 · [ADR-021](./adr/021-export-compose-dual-engine.md) v0.5 · `crop_solver.solve_slot_focal` 可复用 · FRP / `quality.faceCount` / `protectBox` / `focalPoint` 现网可读 · NAS 默认关闸 |
| **关联文档** | [CHARTER.md](./CHARTER.md) · [智能模板建议0813.md](./智能模板建议0813.md) · [EDC](./PRD-EDITORIAL-COMPILER-V1.md) · [ECC](./PRD-EXPORT-CARD-COMPOSE-V1.md) · [ABE](./PRD-ALBUM-EXPORT-BOOKENDS-V1.md) · [MSA](./PRD-MOSAIC-SLOT-ADAPTATION-V1.md)（**不打开**；crop_risk 公式下沉 `crop_solver`，禁止 import `msa_fit`） · [FRP](./PRD-FOOD-ROLE-POLICY-V1.md) · [NAS](./PRD-NO-AI-SURFACE-V1.md) · [zine 调研](./RESEARCH-PHOTO-ZINE-SKILLS-2026-08.md) |
| **评审纪要** | [ael-album-editorial-lab-v1-review-2026-08-13.md](./acceptance-records/ael-album-editorial-lab-v1-review-2026-08-13.md)（结案 · 7/7 Conditional Go · BLK-AEL-01～08） |
| **验收** | [ACCEPTANCE-ALBUM-EDITORIAL-LAB-V1.md](./ACCEPTANCE-ALBUM-EDITORIAL-LAB-V1.md)（源仍为本文 §12） |
| **实施** | [IMPLEMENTATION-ALBUM-EDITORIAL-LAB-V1.md](./IMPLEMENTATION-ALBUM-EDITORIAL-LAB-V1.md) · M0 已拆 · 下一刀 L0 |
| **更新日期** | 2026-08-13 |

> **v0.2.2 相对 v0.2.1（狗粮回写 · 2026-08-13 · 非二次七席）**
>
> 1. L1 三册对照：绝大部分页无变化、特写可见、全身照几乎不动——符合 L1「只在快切脸/天时改刀」。  
> 2. **D-AEL-32**：punch-in 与 L2 角色同波次上场，不单开 L1.5。全身照 **留脚推近优先，切成胸像兜底**。人脸硬闸已够用；手/脚规避尽力（protect/salient 估计），无关键点则 fail-open，不把「切到手」当 L2 红线。  
>
> **v0.2.1 相对 v0.2.0（产品补记 · 2026-08-13 · 非二次七席）**
>
> 1. §6.4 钉死四款混出参考页：P-square←p22、P-tall←p21、P-wide←p08 上条、P-hero-mix←p12。  
> 2. **OQ-AEL-06 补记**：第 5 套 **P-triptych**（p18 三连瘦条）进 `PROBE_TEMPLATES`，**评测-only**，不进默认混出 allowlist；不替代 P-tall。  
> 3. p33「细节留在记忆里」**角色标签映射进 L2**（不新增枚举）；**五槽几何不进**探针。  
> 4. 新增 D-AEL-30 / D-AEL-31；G-AEL-07 改写；AC-AEL-26/27。
>
> **v0.2.0 相对 v0.1.0（七席回写 · 2026-08-13）**
>
> 1. **Conditional Go**：主线冻结；L0 可 Kickoff。  
> 2. **BLK-AEL-01～08 关闭为合同**：探针独立 `PROBE_TEMPLATES`；crop_risk 下沉 `crop_solver`、禁止 import `msa_fit`；回归尺改为模板序列；同卡换槽仅异 AR；FRP 假回归改写；通行证拆开；`cfg` 必须穿线；合影口径 + 默认环零 judge。  
> 3. **OQ-AEL-01～06 关闭**（v0.2.1 对 OQ-06 作产品补记，七席「混出 4 套」仍成立）。  
> 4. 新增 D-AEL-21～29；G-AEL-08 / D-AEL-07 / D-AEL-11 / D-AEL-14 / §8 / AC-AEL-03/12 按会中改写。
>
> **定位**
>
> 现网画册已经能「朝向正确、铺满 3:4 卡、两卡成跨页」。缺的不是再抄 40 套纸书坐标，而是把手工册里必须由人完成的两步——**按槽选图**、**裁进槽位**——收成可回退的确定性环，且只作用在 `album_spread`。
>
> AEL 是 EDC 的**试验床**，不是 EDC 的替代验收，也不是第二套纸书引擎。
>
> **一句话目标**：在画册出口上验证「角色匹配 × 保主体裁切」内核；成熟 28 套为退路，**4** 套异常长宽比探针可混出（另 1 套三连瘦条仅评测）。L1 绿迁 EDC W1，L2 绿迁 EDC W2。画册好看，不能批准 EDC W3（扉页 / breath / 长图节奏）。
>
> **产品铁律**
>
> 1. **只动画册** — 小红书 / 公众号 / 单张海报默认行为不变；关旗 ≡ 现网画册 GA（含 ABE 封面封底）。
> 2. **编辑器，不是模板工厂** — 禁止运行时生成模板；不把 40 页参考图做成默认库。
> 3. **选图与裁切联立** — 禁止「选完再裁、裁坏了认命」；失败则异 AR 同卡换槽 → 换成熟模板 → contain。
> 4. **几何裁切是权威** — 复用 `crop_solver`；默认环不调用 judge；人脸硬闸不可关。
> 5. **先测 28 套，再上探针** — 现网所谓「零裁切」只是槽 AR 贴近 0.75/1.5，真实旅行每天都在 cover。
> 6. **探针可退** — 独立 `PROBE_TEMPLATES`（混出 4 + 评测 1）；每 spread 最多 1 张；裁切不过则丢掉探针；永不写入 `_ALL_TEMPLATES`。
> 7. **本轮不做字、不做胶带** — 变量必须可分离；标题建筑与工艺归后续，不挡内核验收。
> 8. **试验绿有通行证** — L1 绿 → EDC W1；L2 绿 → EDC W2；L3 绿 → 只允许画册混少量硬 AR；**不等于** EDC W3；**不挡 EDC W0**。
> 9. **零步不增加** — 用户仍是导出画册一键出；不新开向导、不把算法缩写暴露到导出面板。
> 10. **默认可达零外呼** — NAS 关闸下无 Key 仍能导出；L1–L3 默认环零 MayCall。

---

## 0. 读者指南

| 章节 | 澄清什么 |
|------|----------|
| §0.1 | 术语 |
| §0.2 | 与相邻主题所有权 |
| §1 | 问题与现网事实 |
| §2 | 目标 / 非目标 / 本试验验什么 |
| §3 | 已拍板决策 |
| §4 | 目标管线与重构边界 |
| §5 | 数据与诊断 |
| §6 | 四层合同（角色 / 联立环 / 裁切 / 探针） |
| §7 | 量尺与盲评 |
| §8 | 迁到 EDC 的通行证 |
| §9 | 里程碑 L0–L3 |
| §10 | 配置 / NFR |
| §11 | 风险与开放问题 |
| §12 | 验收 AC-AEL-* |

### 0.1 术语

| 术语 | 定义 |
|------|------|
| **AEL** | 本主题：只在 `album_spread` 上验证选图×裁切内核 |
| **成熟库** | 现网 `docs/templates/card-aspect-3x4/` **28 套**（朝向友好槽为主，`displayAspect` 多为 0.75 / 1.5） |
| **探针模板** | 独立 `PROBE_TEMPLATES`（不进 `_ALL_TEMPLATES`）：**混出 4**（square / tall / wide / hero-mix）+ **评测-only 1**（triptych）；失败回退成熟库 |
| **编辑角色 `editorialRole`** | 与 EDC 同枚举：`vista \| portrait \| detail \| sequence \| unused`；合影用 `portrait` + `group=true`（人数 = `max(quality.faceCount, len(faces))`，阈值 3）；二者皆缺则不当 group |
| **保主体裁切 / SSC** | 与 EDC 同义：既定槽 AR 内求裁切窗；权威在 `crop_solver` |
| **联立环** | 角色 → 成熟模板选型 → 求解裁切 →（可选）探针替换；任一步失败可回退 |
| **槽内 contain** | 高风险时照片 letterbox 进槽、杂志纸色垫底；**不是**整页空一半 |
| **参考画册** | 2026-08-13 约 40 张手工页；灵感来源，非渲染金样，非默认模板库 |
| **通行证** | §8：试验哪一波绿，允许启动 EDC 的哪一波；禁止把画册观感当 EDC 80% 门 |

### 0.2 与相邻主题（所有权）

| 主题 | AEL 做 | AEL 不做 |
|------|--------|----------|
| **ECC** | 在 `album_spread` 分支加实验旗与联立环 | 不改小红书 / 公众号 / 海报默认选型与 AC-ECC-01 铺满合同 |
| **ABE** | 正文卡走联立环 | 不改封面/封底页；不把封面图再塞回正文池 |
| **EDC** | 验证 W1+W2 **内核**（角色规则 + SSC 失败链）；求解器尽量共用 | 不实施 `program` / opener / breath / 长图 flatten；不代替 EDC 七席出门 |
| **LTE / MCS** | 不碰 16:9 屏 | 不改 YAML 舞台、不打开 MSA |
| **MSA** | crop_risk 公式下沉 `crop_solver` 后调用 | 不 import `msa_fit`；不改槽轨道；`slot_adaptation` 保持默认 off |
| **ADR-021** | 画册在旗内允许软聚类 + 槽内 contain | 不推翻「三出口不要求分镜硬切」；xhs/海报仍顺序消耗 + 朝向匹配 |
| **FRP** | L2 禁止美食升主槽 | 现网画册不跑 FRP；不把「FRP 回归」当验收 |
| **CAL / 工艺** | — | 不做微倾 / 胶带 / 印章 |
| **SCR / 扉页** | — | 不做卡内文案排版（ECC 非目标保持） |
| **NAS / BAI** | 默认可达零外呼；默认环零 judge | 不改 Key / 路由 |
| **Bookends / LVP** | — | 不管 Web 预览气质卡 |

---

## 1. 背景与问题

### 1.1 对照事实

手工参考册好看，是因为人同时做了：这张图该进哪个槽、裁到哪。40 页是同一套设计语法下的页任务，不是 40 个互不相关的 SKU。本项目章程是默认零步；不能变成「先选手填 40 套模板」。

产品 2026-08-13 对齐：

1. 升级思路与 EDC 一致（编辑器，不是模板工厂）。
2. 该参考图更适合**单独升级画册**，而不是先动 16:9 全书。
3. 核心难点是选图与裁切的**耦合**，不是模板数量。
4. 画册先行当试验床；绿了再迁 EDC W1/W2。
5. 不把 40 套异形槽一次性自动化；先少加异常 AR，与成熟模板混出。

### 1.2 现网画册事实（禁止写成待建）

| # | 事实 | 对 AEL 的含义 |
|---|------|----------------|
| **F-01** | `album_spread` 与小红书 / 公众号 / 海报**共用** CardGrouper / Renderer | 必须 album-only 开关 + 探针允许名单，否则泄漏 |
| **F-02** | CardGrouper 按横竖版供给联合选型；聚类/分镜是**平局打破**（ECC v0.2） | L2 软聚类不得变成硬切开分镜、不得留空槽 |
| **F-03** | Renderer 槽内一律 `cover`；AC-ECC-01 要求铺满、禁止大面积 letterbox | 与「宁留白不毁构图」冲突；AEL **只在画册**放开槽内 contain |
| **F-04** | 28 套槽 AR 几乎只有 0.75 / 1.5；全库仅 `card-4-square-top-triband` 顶部 ≈1.125 标成「需裁切」 | 「零裁切」= 朝向匹配后损失最小，**不是**像素不丢。3:2 进 0.75 竖槽每天都在 cover |
| **F-05** | 人脸路径目前是 `focalPoint` + 人像偏置，**没有** `crop_solver` 的 clipped→contain，也没有同卡换槽 | L1 增量是接求解器 + 失败链，不是从零写裁切 |
| **F-06** | 画册无卡内文案；ABE 已提供封面/封底单卡 | 本轮不像参考册的「出发」巨字；那是变量外 |
| **F-07** | 末尾孤卡半页已改为单卡宽度（禁止半页空白） | 槽内 contain ≠ 页级空一半；后者仍红线 |
| **F-08** | `CardTemplateSelector` **禁止** import `screen_planner.py` 内部状态 | 保持；角色规则在 export 层或共享纯函数实现 |
| **F-09** | 运行时模板权威是 `card_templates._ALL_TEMPLATES` → `CARD_TEMPLATES`，**不是** md 目录 glob | 探针必须独立 `PROBE_TEMPLATES`（D-AEL-14/22） |
| **F-10** | `export_collage_pack` 现网 `_ = cfg` 丢弃配置 | L0 必须穿线（D-AEL-27） |

### 1.3 用户可感知问题（仅画册）

| ID | 问题 | 相对手工册 | 落点 |
|----|------|------------|------|
| **P-AEL-01** | 人像砍头切脚、合影切人、风景切天际 | 手裁得体 | §6.3 |
| **P-AEL-02** | 大场景进小槽、细节占主槽 | 人选角色填槽 | §6.1–6.2 |
| **P-AEL-03** | 朝向对了仍难看，因为 3:2/4:3 与 0.75/1.5 仍有裁 | 人会换图或换页 | L1 先在 28 套上测 |
| **P-AEL-04** | 误以为要上 40 套异形模板才像那本册 | 封闭语法 + 少量页型 | §6.4 探针上限 |
| **P-AEL-05** | 若内核改到共享 CardGrouper，小红书被带崩 | — | D-AEL-01 隔离 |

---

## 2. 目标与非目标

### 2.1 目标

| ID | 目标 |
|----|------|
| **G-AEL-01** | 仅 `album_spread` 可开实验；关旗行为 ≡ 现网画册 GA（含 ABE） |
| **G-AEL-02** | 正文卡按 **角色 → 成熟模板 → SSC → 可选探针** 联立编译；任一步可回退 |
| **G-AEL-03** | 人像硬闸：合成夹具砍头则 contain 或同卡换槽，不得硬 cover 切脸 |
| **G-AEL-04** | 合影（D-AEL-28 人数 ≥3）同一窗；禁止瘦槽默默切掉其中的人 |
| **G-AEL-05** | 风景高 `crop_risk` 走 contain 或换槽，不硬砍 3:2 进竖槽的上下约 15% |
| **G-AEL-06** | L1 不改卡数、不改模板选型（只改槽内窗 / 同卡换槽 / contain） |
| **G-AEL-07** | 探针独立 `PROBE_TEMPLATES`；**默认混出 4** 套（square / tall / wide / hero-mix）；**P-triptych 评测-only** 可进 registry 但禁止进默认 allowlist；每 spread ≤1 张；份额 ≤20%；失败回退成熟库 |
| **G-AEL-08** | 小红书 / 公众号 / 海报：开 AEL 旗后 **模板 id 序列与槽朝向分配** 与 GA 一致（允许 PNG 压缩头差异；**禁止**像素哈希当验收） |
| **G-AEL-09** | NAS 关闸零 LLM/VL；无 Key 可导出 |
| **G-AEL-10** | L1+L2 出门后，求解器与角色规则可被 EDC W1/W2 **原样或薄适配**复用，禁止画册一套、layout 又一套互不翻译的枚举 |

### 2.2 非目标

| ID | 非目标 | 理由 |
|----|--------|------|
| **N-AEL-01** | 把 40 页参考坐标做成默认模板库 | 异形槽是裁切倍增器；验证工作量爆炸 |
| **N-AEL-02** | 运行时生成模板 / 自由拼多边形 | 与 EDC / 章程一致 |
| **N-AEL-03** | 异形遮罩、真重叠、圆形戳、微倾胶带 | 档 C；本轮不做工艺 |
| **N-AEL-04** | 卡内标题 / 英文辅文 / 页码建筑 | 现网纯图卡；变量分离 |
| **N-AEL-05** | 改 16:9 预览、9:16 长图、LVP、breath、扉页 | 那是 EDC W3；本试验验不了 |
| **N-AEL-06** | 打开 MSA 或改 3:4 画布 AR | pacing / 几何雷 |
| **N-AEL-07** | 聚类硬切导致空槽 | ECC 已用空槽事故换过课 |
| **N-AEL-08** | 新开用户向导或导出面板算法缩写 | 零步 |
| **N-AEL-09** | 用画册盲评代替 EDC §7 的 80% 五维门 | 画布不同，会假绿 |
| **N-AEL-10** | 改 ABE 封面封底选片与排版 | 已落地；正文试验与之正交 |
| **N-AEL-17** | 把 p33 五槽混排几何做成第 6 套探针 | 角色+多 AR 变量爆炸；角色已映射进 L2 |

### 2.3 本试验「像手工册」验到哪一层

参考册最后 20%（对页文学、即兴手帐、每页大标题）本轮**明确不验**。

AEL 承诺的是内核正确率，不是「导出后看起来已经是那 40 页」：

| 维 | 手工在做什么 | AEL 做到什么算过 | 明确不做 |
|----|--------------|------------------|----------|
| **A 得体** | 裁到脸/合影/天际完整 | 红线零砍头；高风险合法 contain 或换槽 | 艺术性二次构图 |
| **C 匹配** | 大图大槽、脸不进扁槽 | 角色软约束可解释；细节不无故占主槽 | 细分类审美词表 |
| **探针** | 偶尔用异常比例 | 少量硬 AR 在有退路时上场 | 每页都异形 |

节奏（B）/ 叙事章法（D）/ 字建筑（E）**不是** AEL 出门门。画册即使更得体，仍可能是「精致拼贴」而不是「风景经过的时候」——产品已认账。

---

## 3. 已拍板决策

| ID | 决策 |
|----|------|
| **D-AEL-01** | **只动画册。** 实验旗 `album_editorial_lab.enabled`；xhs / 公众号 / 海报代码路径不得读探针库、不得改 contain 默认。 |
| **D-AEL-02** | AEL 验证 EDC 的 **W1+W2 内核**，不验证 W3。画册绿 ≠ EDC 80% 门。 |
| **D-AEL-03** | 选图与裁切 **联立环**（§6.2）；禁止单向「先 plan_cards 再死裁」。 |
| **D-AEL-04** | 聚类 / 分镜 **只作软分**。切不开也不留空槽；朝向硬门与「每槽有真实照片」高于分镜完整。 |
| **D-AEL-05** | 默认池 = 现网 **28 套成熟库**。探针 registry **最多 5** 套（混出 4 + 评测 1），L3 才准入。 |
| **D-AEL-06** | **先 L1 测 28 套裁切正确率，再上探针。** 禁止「先加异常模板再看裁切」。 |
| **D-AEL-07** | L1 失败链：异 AR 同卡换槽 → `fit=contain`。**禁止** L1 换模板（对齐 G-AEL-06，卡数不漂）。等权宫格（槽 AR 全同）**不换槽**，直接 contain。换同槽数成熟模板最早 **L2**。 |
| **D-AEL-08** | 画册允许 **槽内 contain**（纸色 = `DEFAULT_BG` `(245,245,243)`）。**禁止**页级半幅空白（F-07 不回退）。 |
| **D-AEL-09** | AC-ECC-01 对小红书保持「铺满」（现网 `test_render_card_covers_every_pixel_no_background_bleed` 不得改红）。画册在旗开时以本 PRD 的 contain 合同为准，另测。 |
| **D-AEL-10** | **不打开 MSA**；不把 crop 分反馈进「这张卡用几槽」（避免 ECC 供给算法被裁切分打飞）。 |
| **D-AEL-11** | 裁切权威 = `travelogue.layout_engine.crop_solver`（含下沉后的 `crop_risk_for_pair` / `aspect_mismatch`）。Renderer 读固化窗。**禁止** export import `travelogue.layout_engine.mosaic`（含 `msa_fit`）。 |
| **D-AEL-12** | `editorialRole` 枚举与 EDC **同一张表**。合影：`portrait` + `group`（D-AEL-28），不新增 `food`。 |
| **D-AEL-13** | 探针配额：每 spread **≤1**；正文卡（不含 ABE 封面封底）占比 **≤20%**。不过门的探针只进评测集。 |
| **D-AEL-14** | 探针运行时权威 = **`PROBE_TEMPLATES`**（独立 dict）。**禁止**写入 `_ALL_TEMPLATES` / `CARD_TEMPLATES` / `AVAILABLE_SLOT_COUNTS`。md 可放 `docs/templates/card-aspect-3x4/probes/` 作文档，**不**被 `plan_cards` 默认遍历。仅当 `probes.enabled` 且平台为 `album_spread` 时，联立环 L3 才可见探针。 |
| **D-AEL-15** | 默认可达 **不改** `trip.schema.json`。角色/裁切写入导出诊断；若 EDC W0 已扩 schema 则同名字段双写。禁止 AEL 自造互不翻译枚举。 |
| **D-AEL-16** | 本轮不做字、不做胶带、不做异形遮罩。 |
| **D-AEL-17** | 人脸硬闸不可关。父关不得卸载现网 focal cover（现网画册本来就会 cover）。 |
| **D-AEL-18** | 用户面不新增步骤；实验期可用狗粮配置 / dark，不把 `AEL` 缩写暴露到导出面板。 |
| **D-AEL-19** | 通行证见 §8。未过门默认保持 off，禁止用「再开一个算法专题」代替修失败链。 |
| **D-AEL-20** | 仍禁止 import `screen_planner.py` 内部状态（继承 ECC BLK-02）。 |
| **D-AEL-21** | （BLK-04）同卡换槽 **仅当** 该卡存在至少两个不同 `displayAspect`。禁止为换槽打破朝向硬门。 |
| **D-AEL-22** | （BLK-01）见 D-AEL-14 冻结字面。 |
| **D-AEL-23** | （BLK-02）见 D-AEL-11 冻结字面。 |
| **D-AEL-24** | （BLK-03）见 G-AEL-08；NFR-05 / AC-AEL-03 同步为序列+朝向。 |
| **D-AEL-25** | （BLK-06）通行证拆开：AEL **L1 绿 → 可 Kickoff EDC W1**；AEL **L2 绿 → 可 Kickoff EDC W2**；**不挡 EDC W0**。L3 绿 ≠ EDC W3。 |
| **D-AEL-26** | （BLK-08）L1–L3 默认可达 **零** mosaic_judge / LLM / VL。MayCall 不进默认环。 |
| **D-AEL-27** | （BLK-07）L0 必须把实验旗从 config 穿进 `export_collage_pack` 的 **album 分支**。现网 `_ = cfg` 必须改掉。xhs/mp 分支不读 AEL 子键。 |
| **D-AEL-28** | （BLK-08）合影人数 = `max(int(quality.faceCount or 0), len(faces_from_asset))`；阈值 `group_face_min=3`。二者皆 0 则 **不当** group（fail-open，不降级）。 |
| **D-AEL-29** | （BLK-05）现网画册 **不执行** FRP。L2 美食合同：禁止升为 `vista` / 主槽。不得把「FRP 不回退」写成回归项。 |
| **D-AEL-30** | （产品 2026-08-13）`PROBE_TEMPLATES` 可含 **5** 套。**默认混出 allowlist** = `{probe-square, probe-tall, probe-wide, probe-hero-mix}`。**`probe-triptych` 评测-only**：可进 registry 与夹具 allowlist，**禁止**写入仓库默认 / 示例 mix allowlist；升混出须另开门（夹具 100% + 狗粮无新砍头红线）。不替代 P-tall。 |
| **D-AEL-31** | （产品 2026-08-13）参考页 p33 的五个**中文槽标签**映射到现有 `editorialRole` + `CardSlot.role`（§6.1 表）。**禁止**新增 `small` / `main-photo` 等平行枚举。p33 **几何不进** `PROBE_TEMPLATES`。 |
| **D-AEL-32** | （产品 2026-08-13 三册对照）L1 只平移最大 cover 窗，不推近。**punch-in**（比 cover 更小的同 AR 窗对准人）与 **L2 角色同 PR 上场**，键 `crop.tighten`（须 `crop.enabled`）。策略：单人/双人；合影 ≥`group_face_min` **不**推近。全身照 **留脚推近优先**（窗须含脸+估计脚底）；做不到目标脸占比或脚估在窗外则 **胸像兜底**。手/脚无姿态点：用 protectBox / salientBox 扩张；缺失则几何估计，**fail-open**（不因此 contain）。禁止把 punch-in 做成切成证件照的默认。 |

---

## 4. 目标管线与重构边界

### 4.1 As-Is（画册正文）

```
kept 照片（已剔除 ABE 封面/封底 id）
  → CardGrouper：横竖队列 + 供给感知选（张数, 成熟模板）
  → 朝向匹配填槽（聚类仅平局打破）
  → CardRenderer：cover + focal / 人像偏置
  → 两卡 + gutter 成 spread
```

### 4.2 To-Be（仅旗开的 album_spread）

```
kept 照片（ABE 剔除不变）
  → 角色标注（规则；VL 仅 MayCall 校准）
  → CardGrouper 成熟库选型（朝向供给仍硬约束；角色+软聚类为软分）
  → 填槽
    → SSC：solve_slot_focal；失败 →（异 AR）同卡换槽 → contain
  → L2：允许换同槽数成熟模板后重解（须记账卡数）
  → L3：若本 spread 尚无探针且 SSC 通过，可尝试 1 张探针卡；失败丢弃
  → Renderer 执行固化 cropFocal / contain（web 无此画布；仅 Pillow）
```

### 4.3 允许 / 禁止

| 允许 | 禁止 |
|------|------|
| `collage_pack` / `card_grouper` / `card_renderer` 的 **album 分支**增量 | 改 xhs/海报默认 plan_cards |
| 共享纯函数：角色规则、SSC 适配器（可供 EDC 后续 import） | 在 Renderer 里复制一份人脸几何 |
| 3～5 探针 YAML/md 准入（混出 4；第 5 套评测-only） | 运行时组合爆炸；把 16:9 slot-aspect 数值抄进 3:4；p33 五槽几何 |
| 槽内 contain | 打开 MSA；改 CARD_CANVAS 3:4 |
| 导出诊断 JSON | 本轮为 AEL 单独立 schema 平行键 |

挂点建议（实施时钉死）：角色在 `plan_cards` 之前或之内作软分；SSC 在 `assign_photos_to_slots` 之后、`render_spread` 之前写入每槽窗；探针替换在 SSC 通过之后。**禁止**把 contain 分写回「下一步用几槽」。

---

## 5. 数据与诊断

原则：能扩展现有键就不造平行键；V1 默认不改 trip schema。

### 5.1 照片角色（计算，默认不落盘）

与 EDC §5.1 / §6.1 对齐：

| 信号 | 倾向 |
|------|------|
| 人脸或 protectBox 有效 + 竖/近方 | `portrait` |
| `max(faceCount, len(faces)) ≥ 3` | `portrait` + `group=true`；皆 0 则不当 group |
| 无人脸 + 宽幅 + 质量高 | `vista` |
| 近重复簇非主图、局部、低场景分 | `detail` |
| 同场景短时密序列（可读 SSG scene，不依赖 SSG look） | `sequence` |
| 质量闸淘汰 | `unused`（一般不进导出池） |

美食：现网画册不跑 FRP。L2 禁止把菜升为 `vista` / 主槽；不确定 **不降级**。

### 5.2 槽（渲染执行）

| 字段 | V1 用法 |
|------|---------|
| `cropFocal` | 求解结果（与 layout 同名语义） |
| `cropContain` / `fit=contain` | 失败链走到槽内 contain |
| `cropSafety` | 遥测：人脸是否完整、crop_risk、失败原因、是否探针 |

导出诊断（job 侧 JSON，非 trip 必写）至少包含：每卡 `templateId`、是否探针、每槽 assetId、fit、crop_risk、role、失败链步数。

### 5.3 回滚

`album_editorial_lab.enabled=false`：画册 ≡ ECC+ABE GA。现网 focal cover **仍运行**（D-AEL-17）。旧导出任务无新诊断可渲染。

---

## 6. 四层合同

### 6.1 角色标注（L2）· 替代「人选哪张进哪槽」

默认可达 = 规则。选型软约束：

- `vista` 优先 `main` / 宽槽 / 大面积槽
- `portrait` 优先竖槽；**禁止**无门放进超扁条带（探针 `P-wide` 对非 group 竖图默认拒绝）
- `group=true` 优先宽槽或近方；**禁止**默认进 `P-tall` / `P-triptych`
- `detail` 禁止独占满幅/主槽（除非该卡池没有 vista/portrait）
- `sequence` 优先等权网格（成熟库 `*-grid-equal`）
- 朝向硬门不破（AC-ECC-04 精神保留）

参考页 p33「细节留在记忆里」的中文槽标签 **只作翻译，不扩枚举**（D-AEL-31）：

| 参考页标签 | 照片 `editorialRole` | 槽 `CardSlot.role` |
|------------|----------------------|---------------------|
| 主图 | `vista`（无 vista 则最高质量 `portrait`） | `main` |
| 竖图 | `portrait` | `portrait` |
| 横图 | `vista` | `landscape` |
| 细节 | `detail` | 较小非 `main` |
| 小图 | `detail` | 较小非 `main` |

验收看反例：菜单进主槽、脸进扁槽、合影进瘦槽、细节占主槽；不看 CLIP 新模型。p33 五槽几何 **不**作为 L2/L3 金样。

### 6.2 联立环（全程）

```
1. 用成熟库 + 朝向供给选出候选卡（现网 CardGrouper）
2. 按角色软分微调同槽数候选（L2；L1 跳过）
3. 填槽（朝向硬门）
4. 对每槽 SSC
5. 失败：异 AR 同卡换槽 →（L2）换同槽数成熟模板 → contain
   （等权宫格跳过换槽，直接 contain）
6. L3：本 spread 无探针且步骤 4–5 对成熟卡已通过 → 尝试 1 张探针替换
7. 探针 SSC 失败 → 丢弃探针，保留步骤 5 的成熟卡
```

硬约束优先级（高→低）：每槽有真实照片 → 朝向硬门 → 人脸/合影硬闸 → 风景高风险不硬砍 → 角色软分 → 分镜软分 → 探针多样性。

### 6.3 保主体裁切（L1）· 主战场

**As-Is**：`crop_aspect_focal` + 人像偏置；无人脸中心/focal cover。

**To-Be 增量**（开关可控、默认 off 至盲评过门）：

1. **感知**：face / protectBox / focalPoint；合影用 face 并集当保护框；风景用 `crop_risk_for_pair`（AR 错配），**不上**新地平线模型（与 EDC OQ-03 一致）。
2. **几何**：`solve_slot_focal`；人脸 clipped → contain 或同卡换槽；高 crop_risk 且非 bleed 名单 → contain 或换槽。
3. **评论（MayCall）**：可选 mosaic_judge；不可改硬闸。
4. **L1 不做**：换模板、改卡数、打开 MSA、地平线模型、往人身上推近（punch-in 见 D-AEL-32 / L2）。

contain 底色：`DEFAULT_BG` `(245, 245, 243)`。用户应能读成「这张图被完整放下」，而不是「没铺满的 bug」。

**L2 punch-in（`crop.tighten`）**：在 L1 可行 cover 之上，对单人/双人用更小的同 AR 窗对准人。全身照先收「头到脚还在」；不行再胸像。合影不推近。

### 6.4 异常 AR 探针（L3）

先有 L1 基线，再准入。V1 只做**矩形**异常 AR（档 A）。档 B 微倾 / 档 C 异形 = 非目标。运行时只从 `PROBE_TEMPLATES` 读取。只复刻槽几何，不抄标题 / 胶带 / 微倾。参考页是竖向纸书，落到 **3:4 纯图卡**时去掉标题带。

| 代号 | 参考页 | 槽几何（3:4 卡） | 打什么 | 不做什么 | 出场 |
|------|--------|------------------|--------|----------|------|
| **P-square** `probe-square` | p22「一餐，也是一段路程」 | 2×2 **真 1:1**（为保方形允许对称纸边，不是半幅空白 bug） | 3:2 / 4:3 进方槽是否切天际/砍头 | 圆形遮罩；餐食标题 | **混出** |
| **P-tall** `probe-tall` | p21「这一刻，刚刚好」 | 两列铺满；派生 AR ≈0.375（约 1:2.7；参考页标 1:2，去标题后略瘦） | 合影/全身进瘦槽是否切脚 | 微倾；不做到三连 1:4 | **混出** |
| **P-wide** `probe-wide` | p08「静而致远」上条 | 顶条 ≈16:9（`display_aspect≈1.69`）+ 余高两竖铺满（禁止半幅空白）；现网最扁是 1.5 | 竖图进扁槽、风景天际被横切 | 右侧日期标题 | **混出** |
| **P-hero-mix** `probe-hero-mix` | p12「途中的小事」 | 左大槽铺满高度（≈0.56）+ 右侧两竖；三矩形贴齐 3:4 卡边 | vista 进大槽、细节进小槽；异 AR 才换槽 | 胶带、圆形章 | **混出** |
| **P-triptych** `probe-triptych` | p18「一座城的普通一天」 | 三列铺满；派生 AR ≈0.25（1:4） | 同一异常 AR ×3；选错或切脚会连坐 | 不替代 P-tall；CITY WALK 标题 | **评测-only** |
| **对照** | — | 现成 `card-4` 顶部 1.125（**成熟库内**） | 库内已有的「需裁切」槽 | 不新造、不复制进 PROBE | 成熟库 |

配额见 D-AEL-13。默认 mix allowlist **不含** `probe-triptych`（D-AEL-30）。正确率门未过 → 该 id 保持评测-only。

成熟 28 套**永远是退路**。探针永不单独成册（禁止「整本只有探针库」的配置出门）。

---

## 7. 量尺与盲评

### 7.1 合成夹具（L1 合码门，可单测）

至少覆盖：

| 夹具 | 期望 |
|------|------|
| 单人像脸贴上缘 / 下缘 | 不得 cover 切脸；contain 或换槽 |
| `faceCount=4` 合影进竖槽 | 不得切掉其中一人；换宽槽或 contain |
| 3:2 风景、地平线在上 20% | 高 crop_risk 不得硬砍天空；contain 或换横槽 |
| 朝向错配 | 仍禁止（硬门）；不得用 contain 掩盖装错朝向 |

### 7.2 狗粮语料

至少 **3 本真实册**，钉名（OQ-AEL-01）：`demo-d6697c8dca` · `demo-2025` · `demo-49cbe46479`。导出画册正文跨页（不含 ABE 封面封底；本主题不对书衣跑 SSC）。

评委：至少 **1 产品 + 1 非作者**；开发者须打乱 A/B（on/off 或探针混出 vs 纯成熟库）。

### 7.3 出门门

| 波次 | 门 |
|------|----|
| **L1** | 夹具全绿；三册 A 维（得体）on ≥ off；人像砍头红线为零；**卡数与模板序列相对 L1 增量 off 不漂移**（G-AEL-06）；xhs 回归绿 |
| **L2** | 角色反例可指认下降；朝向硬门不破；空槽红线为零；FRP 不回退；卡数允许因换同槽数模板而记账，但不得无故碎成大量 1 槽卡 |
| **L3** | 探针槽在夹具+狗粮上的裁切通过率达标（建议夹具 100%、狗粮探针卡 A 维 ≥ 成熟卡且无新红线）；配额未破；失败均回退成熟卡 |

未达标：该层保持 off。L3 失败不得回滚已绿的 L1/L2（插入可单独关，同 EDC W3 精神：探针可单独关）。

### 7.4 与参考 40 页的关系

用于定义「5 分得体长什么样」，**不**作为 A/B 对手，不作为像素金样。

---

## 8. 迁到 EDC 的通行证

| AEL 状态 | 允许 | 仍禁止 |
|----------|------|--------|
| L0 隔离绿 | 合码实验旗 + `cfg` 穿线 | 默认 on |
| **L1 绿** | **Kickoff EDC W1**（风景 contain / 同屏换槽）；共享 `crop_solver` 适配 | 打开 MSA；把画册 contain 政策抄进 16:9 默认 |
| **L2 绿** | **Kickoff EDC W2**（角色规则）；共享角色表 | 第二套互不翻译枚举 |
| L3 绿 | 画册默认混出已过门的 **4** 套探针 | 把硬 AR 探针搬进 16:9 mosaic 默认库；**不**自动把 P-triptych 升混出 |
| 「画册看起来更像参考册」 | 记观感，开后续字/工艺专题 | **跳过 EDC W3**；**不挡 EDC W0** |

EDC 合同仍以 [PRD-EDITORIAL-COMPILER-V1.md](./PRD-EDITORIAL-COMPILER-V1.md) 为准。AEL 不得修改 D-EDC-02/07/08/18。

---

## 9. 里程碑

编码 Kickoff 以七席 Go 为准。L1 合码不要求「像那 40 页」。

| 波次 | 内容 | 合码 / 出门门 | 默认 |
|------|------|----------------|------|
| **L0** | 实验旗 · album 分支隔离 · 诊断骨架 · xhs 金样对照 | 关旗 ≡ GA；开旗但 crop/roles/probes 全 false ≡ GA | 父关 |
| **L1** | 28 套上 SSC 增量；同卡换槽；槽内 contain | AC-AEL-01～08；§7.3 L1 门 | 增量 **off** |
| **L2** | editorialRole 软约束；同槽数换成熟模板；punch-in（D-AEL-32） | AC-AEL-09～12/28；§7.3 L2 门 | 随父开关 |
| **L3** | 4 套探针准入混出；第 5 套 triptych 评测-only | AC-AEL-13～16/26；§7.3 L3 门；失败则探针长期评测-only | **off** |

L3 必须提供 **探针回滚**（只关 probes，保留 L1/L2）。

---

## 10. 配置与 NFR

### 10.1 配置（示意）

```yaml
album_editorial_lab:
  enabled: false                 # 父开关；false ≡ 现网画册 GA
  crop:
    enabled: false               # L1 增量
    face_hard_gate: true         # 不可关
    group_face_min: 3
    contain_on_fail: true        # 仅 album
    tighten: false               # L2 punch-in（D-AEL-32）；须 crop.enabled
  roles:
    enabled: false               # L2
    cluster_soft: true
  probes:
    enabled: false               # L3
    max_per_spread: 1
    max_share: 0.20
    allowlist: []                # 空 = 即使用 enabled 也不选；混出只许四 id（D-AEL-30）
    # 评测夹具可临时写入 probe-triptych；禁止把该 id 提交进仓库默认 mix allowlist
```

禁止把上述键做成用户可见算法名。狗粮可用本机 `config.yaml` 覆盖。

### 10.2 NFR

| ID | 要求 |
|----|------|
| **NFR-01** | 同 trip + 同配置重导出，卡序列 / cropFocal 稳定（浮点容差） |
| **NFR-02** | ~250 张画册上限内，SSC 不得把导出做成不可用；超预算则只对高风险槽求解（L0 定预算） |
| **NFR-03** | 无新字段 trip 可导出 |
| **NFR-04** | NAS 关闸零外呼 |
| **NFR-05** | 开旗导出小红书，模板 id 序列 + 槽朝向分配与关旗一致（禁止像素哈希） |

---

## 11. 风险与开放问题

### 11.1 风险

| 风险 | 缓解 |
|------|------|
| 共享内核改动带崩小红书 | D-AEL-01；NFR-05；探针目录隔离 |
| 槽内 contain 被看成没铺满 | 纸色合同；量表把合法留白算得体；导出提示不说「失败」 |
| 角色规则把好图标成 detail | 不确定不降级 |
| 探针让多样性好看但砍头回潮 | 配额 + 失败回退 + L3 单独关 |
| 把画册观感当成 EDC 已完成 | §8 通行证写死 |
| 为赶「像 40 页」偷加胶带/标题 | N-AEL-04/16；验收拒看工艺加分 |

### 11.2 开放问题（七席已结案 · 2026-08-13）

| ID | 问题 | 结案 |
|----|------|------|
| **OQ-AEL-01** | 狗粮三册具体 trip id | ✅ `demo-d6697c8dca` · `demo-2025` · `demo-49cbe46479` |
| **OQ-AEL-02** | L3 狗粮通过率数字 | ✅ 夹具 100%；狗粮探针卡不得新增砍头红线，A 维 ≥ 成熟卡 |
| **OQ-AEL-03** | contain 纸色令牌 | ✅ `(245, 245, 243)` = `DEFAULT_BG` |
| **OQ-AEL-04** | `group_face_min` | ✅ **3**；口径见 D-AEL-28 |
| **OQ-AEL-05** | L2 是否允许卡数相对 L1 变化 | ✅ 允许记账；1 槽卡占比不得高于 GA +10 个百分点 |
| **OQ-AEL-06** | 探针 4 套还是 5 套 | ✅ 七席：混出 **4**（square/tall/wide/hero-mix）+ `card-4` 对照。**产品补记 2026-08-13**：第 5 套 **P-triptych**（p18）有设计稿，进 registry **评测-only**，不进默认混出（D-AEL-30）。 |

---

## 12. 验收摘要（源）

Kickoff 后已拆 ACCEPTANCE / IMPLEMENTATION；下列为合同源。

| ID | 摘要 | 波次 |
|----|------|------|
| **AC-AEL-01** | 父关 ≡ 现网画册 GA（含 ABE）；不得少写现网 focal cover | L0/L1 |
| **AC-AEL-02** | 开父关但 crop/roles/probes 全 false ≡ GA | L0 |
| **AC-AEL-03** | 小红书 / 公众号 / 海报开 AEL 旗后 **模板 id 序列 + 槽朝向分配** 与 GA 一致（禁止像素哈希） | L0 |
| **AC-AEL-04** | 人像硬闸：夹具砍头则 contain 或异 AR 同卡换槽，不得 cover 切脸 | L1 |
| **AC-AEL-05** | 合影夹具不得切掉窗内任一脸（人数口径 D-AEL-28） | L1 |
| **AC-AEL-06** | 高 crop_risk 风景不得硬 cover 砍天际；contain 或换槽 | L1 |
| **AC-AEL-07** | L1 **不**改变卡数与模板 id 序列（相对 crop 增量 off） | L1 |
| **AC-AEL-08** | 槽内 contain 底色为杂志纸色；无页级半幅空白 | L1 |
| **AC-AEL-09** | NAS 关闸零 LLM/VL | 全程 |
| **AC-AEL-10** | `editorialRole` 规则单测（竖脸→portrait，宽无人脸→vista；`max(faceCount,len(faces))≥3`→group；皆 0 不当 group） | L2 |
| **AC-AEL-11** | 无 vista/portrait 时 detail 允许主槽（降级合法） | L2 |
| **AC-AEL-12** | 美食不得升为 vista/主槽；朝向硬门不破；无空槽。**不**把「FRP 回归」当验收（现网画册无 FRP） | L2 |
| **AC-AEL-13** | 探针不在 `PROBE_TEMPLATES` / allowlist 或不在 album 平台 → 永不选用；成熟库 `CARD_TEMPLATES` 不含探针 id | L3 |
| **AC-AEL-14** | 每 spread 探针卡 ≤1；正文占比 ≤ max_share | L3 |
| **AC-AEL-15** | 探针 SSC 失败则该卡回退成熟模板 | L3 |
| **AC-AEL-16** | 只关 probes 后 L1/L2 行为保留 | L3 |
| **AC-AEL-17** | 无运行时生成模板的 public API | 全程 |
| **AC-AEL-18** | L1 盲评：§7.3 L1 门 | L1 出门 |
| **AC-AEL-19** | L2 盲评：§7.3 L2 门 | L2 出门 |
| **AC-AEL-20** | L3 盲评：§7.3 L3 门；未过则 probes 保持 off | L3 出门 |
| **AC-AEL-21** | 不打开 `slot_adaptation.enabled` | 全程 |
| **AC-AEL-22** | 角色枚举与 EDC 可翻译、无平行真相 | L2 |
| **AC-AEL-23** | export 模块不 import `travelogue.layout_engine.mosaic` | L1 |
| **AC-AEL-24** | `export_collage_pack` 的 album 分支读取 AEL 配置；xhs 分支不读子键 | L0 |
| **AC-AEL-25** | 等权宫格夹具：L1 失败走 contain，不因换槽改变朝向分配 | L1 |
| **AC-AEL-26** | `PROBE_TEMPLATES` 可含 `probe-triptych`；默认 / 示例 mix `allowlist` **不含**该 id；空 allowlist 仍不选任何探针 | L3 |
| **AC-AEL-27** | p33 五标签可翻译到 `{vista,portrait,detail}` + `{main,portrait,landscape}`；无平行枚举；`PROBE_TEMPLATES` 无 p33 几何 id | L2/L3 |
| **AC-AEL-28** | punch-in：合影不推近；全身照夹具留脚窗优先于胸像；无 protect 时几何估计 fail-open 仍 cover（不强制 contain） | L2 |

---

## 13. 变更记录

| 版本 | 日期 | 说明 |
|------|------|------|
| v0.2.2 | 2026-08-13 | 三册对照回写：D-AEL-32 punch-in 与 L2 同上场；留脚优先、胸像兜底；AC-AEL-28。 |
| v0.2.1 | 2026-08-13 | 产品补记：§6.4 钉死四款混出参考页；P-triptych（p18）评测-only；p33 角色映射进 L2、几何不进探针。D-AEL-30/31 · AC-26/27。非二次七席。 |
| v0.2.0 | 2026-08-13 | 七席 Conditional Go 回写。BLK-AEL-01～08 → D-AEL-21～29；G-AEL-08 / D-AEL-07/11/14 / §8 / AC-03/12 改写；OQ-01～06 结案；AC-23～25。纪要：[ael-album-editorial-lab-v1-review-2026-08-13.md](./acceptance-records/ael-album-editorial-lab-v1-review-2026-08-13.md)。 |
| v0.1.0 | 2026-08-13 | 初稿。产品确认：画册单独升级当 EDC 试验床；选图×裁切联立；先 28 套再 3～5 探针；隔离 xhs/海报；本轮无字无胶带；通行证 L1+L2→EDC W1/W2。灵感：[智能模板建议0813.md](./智能模板建议0813.md)。讨论结论写入本文，待七席。 |
