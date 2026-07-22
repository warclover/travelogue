# 完工表面积收敛（CSC）多方评审纪要 · 2026-07-22

| 属性 | 内容 |
|------|------|
| **对象** | [PRD-COMPLETION-SURFACE-CONVERGENCE-V1.md](../PRD-COMPLETION-SURFACE-CONVERGENCE-V1.md) v0.1.0-CSC |
| **形式** | 九席只读评审（对照产线代码 / 相邻 PRD / 配置与命中基线） |
| **结论** | **Conditional Go** · 战略方向锁定；W0 基线方法论与 Profile/配置口径合入 PRD 后方可 Kickoff W1 |
| **PRD 回写** | **v0.2.0-CSC**（同日）：OQ 全关 · BLK 合入 · 波次修订 · WIP 门禁 |
| **关联** | [FTT](../PRD-FINISH-THIS-TRIP-V1.md) · [ARCH-OPT](../PRD-ARCH-OPTIMIZATION.md) · [AAD](../PRD-ARCH-ALGO-DEEPENING-V1.md) · [CHARTER](../CHARTER.md) |

---

## 参评席位

| 席位 | 角色 | 结论 | 一句话 |
|------|------|------|--------|
| **ARCH** | 资深架构师 | Conditional Go | 诊断准；禁止再发明第三套 Profile 名；ceiling 要可计量且防刷分 |
| **BE** | 后端开发 | Conditional Go | 承接 `StudioProfile.studio_default`；W2b 让位 AAD；pipeline 用棘轮别大拆 |
| **FE** | 前端开发 | Conditional Go | 表面积一半在设置/帮助/admin 入口；W1 必须含 UI 库存 |
| **PM** | 产品 | Conditional Go | 与 FTT 同向；对外只讲「默认更短」，不讲边数 |
| **UI** | UI/UX | Conditional Go | Advanced 隔离要有视觉合同，不能只靠「URL 不链首页」 |
| **UX** | 用户体验 / 流程 | Conditional Go | 用户痛在决策面，不在 facade；先砍可见旋钮与话术 |
| **QA** | 资深测试 | Conditional Go | AC 多处不可执行；W0 脚本与 DIFF/等价口径必须先钉 |
| **USER** | 典型用户代表（截取型 · 搁置型 · 成册者） | Conditional Go | 同意变简单；怕「收敛」变成又一次大改、设置搬家找不到 |
| **EVAL** | 应用测评专家 | Conditional Go | 用「解释默认路径时长 / 导出前设置点击」做务实测评，勿空谈平台化 |

**汇总**：**Conditional Go**。方向与否决闸成立；下列 BLK 合入 v0.2 后，允许 **W0 Kickoff**；**W1 编码**另需 W0 基线文件入库。

---

## 1. 全场高度共识（直接采纳）

1. **战略正确**：问题是「默认表面积」，不是「缺排版能力」；与 CHARTER / FTT「成册完工」同向。  
2. **减法优先、禁止大爆炸**：CSC 成功故事 ≠ 新功能面；分波 + 可回滚。  
3. **两本账必须坚持**：对外 = 完工/敢发/可解释；对内 = 配置根、facade、legacy ceiling、文档状态。  
4. **不重开** ARCH-OPT P0（写锁等）、不重写 AAD Utility/beam、不重写 FTT 完成状态机。  
5. **保护条款有效**：`trip.json` SSOT、模板优先、单进程 Studio、golden 文化不得借收敛破坏。  
6. **admin / LSE flags 不得进首趟主 CTA**（CSC-PR-08）全席同意。  
7. **算法可深，默认要窄**：新能力默认 flag 关；进 Happy Path 要过闸——但闸门须分层，避免把存量能力一刀切重审（见 BLK-04）。

---

## 2. 产线证据快照（评审当日）

| 项 | 数值 / 事实 | 含义 |
|----|-------------|------|
| `config.yaml.example` 顶层键 | **23** | D-CSC-04 压力真实 |
| `StudioProfile` | 已有 `cli_default` / `studio_default` | **勿再造**平行 `finish_this_trip` 类型 |
| `curate.py` / `studio_pipeline.py` | **~1938** / **~1127** 行 | 巨石仍在；大拆有 WIP 风险 |
| `layout_engine.__all__` | `[]` | facade 缺口成立 |
| curation→layout_engine import | **20**（其中 adapter **17**） | 已大体经 adapter；内部深 import 少但须锁死 |
| `\blegacy\b` / `\bshim\b`（travelogue/**/*.py） | **236** / **25**（82 文件含 legacy） | 原始 rg **不可**直接当 ceiling（注释/叙事噪声大） |

---

## 3. 阻塞项（BLK · 必合入 v0.2）

| ID | 议题 | 谁强调 | 务实决议 |
|----|------|--------|----------|
| **BLK-CSC-01** | 再发明 Profile 名会分叉 | ARCH · BE · PM | **Happy Path 运行时 = 强化并冻结的 `StudioProfile.studio_default()`**；产品叙事可称「这一趟做完默认路径 / FTT 默认底座」，**不新增**第三套 dataclass 名 |
| **BLK-CSC-02** | legacy 原始命中不可运营 | ARCH · QA | ceiling 用 **结构化债务清单**（模块路径 allowlist + 再导出 shim 文件表），W0 冻结；**禁止**以全文 `\blegacy\` 降 30% 为 KPI |
| **BLK-CSC-03** | 「≤10 根」含 ops 键会假失败 | PM · BE · EVAL | 拆 **L0 运维根**（`trips_dir`/`llm`/`ffmpeg`/`geocode`…）与 **L1 结果旋钮**；**≤10 只约束 L1**；L0 另设「不进设置 UI」纪律 |
| **BLK-CSC-04** | §8 全量盲测过重 | 算法席并入 EVAL/PM | **分层闸门**：① 存量默认能力 → W0 **盘点祖父条款**；② **新增/扩大**默认集合 → 完整 G-CSC-MIN；③ research 永不进 L1 |
| **BLK-CSC-05** | 与 FTT/AAD 抢带宽 | ARCH · PM · BE | 写入 **G-CSC-WIP**：体验债/FTT 挡门优先；**W2b 默认「验收对齐 AAD」**，AAD 未动则只做薄 coordinator 切片，禁止并行大拆 `curate.py` |
| **BLK-CSC-06** | 前端表面积未入波次 | FE · UI · UX | W1 增加 **Settings / Help / Advanced 入口库存** + 隔离线框或对照表；否则 CSC 会变成纯后端自嗨 |
| **BLK-CSC-07** | AC 不可执行 | QA | W0 必须交付：基线 JSON/脚本、Profile 启用集合快照测、facade lint 规则草案、配置 L0/L1 键表 |
| **BLK-CSC-08** | pipeline「变薄」易变大重构 | BE · ARCH | W2c 改为 **行数/职责棘轮 + 禁止新增业务进巨石**；允许机会主义抽取，**不设**「一次拆到只剩编排」的大爆炸 DoD |

---

## 4. OQ 关闭（投票定案）

| ID | 议题 | 定案 |
|----|------|------|
| **OQ-CSC-01** | Profile 命名 | **关闭**：运行时身份 = `StudioProfile.studio_default`；文档名「Happy Path / 这一趟默认路径」；不与 FTT 特性代号抢代码符号 |
| **OQ-CSC-02** | legacy 计量 | **关闭**：绝对 ceiling + 只降不升；对象 = W0 结构化债务表，非原始 rg |
| **OQ-CSC-03** | `compose_trip` | **关闭**：经 `layout_engine` facade **再导出**；实现保留 `mosaic`；禁止 web/services 直 import mosaic 内部 |
| **OQ-CSC-04** | ≤10 是否含 llm 等 | **关闭**：不含 L0 运维根；L1≤10 |
| **OQ-CSC-05** | vs AAD 排期 | **关闭**：AAD 优先动 `curate`；CSC W2b=对齐/薄切片；facade（W2a）可与 AAD 并行 |

---

## 5. 分席深度意见（务实要点）

### 5.1 资深架构师（ARCH）

- 最大风险是 CSC 变成「ARCH-OPT 第三季」叙事膨胀。  
- **务实顺序**：W0 计量 → W1 默认冻结与可见面 → W2a facade 锁进口 → 清退。  
- `curation→adapter` 已是主边；CSC 价值是 **禁止回潮 + 公开符号表**，不是再迁一次包。

### 5.2 后端（BE）

- `studio_default` 已开 clustering / editorial / export auto——W1 重点是 **冻结快照 + 文档化默认启用/不启用**，不是新类。  
- `curate.py` 1938 行：联手 AAD 或只抽「阶段函数边界」，禁止 CSC 单独开「神级重构」。  
- `studio_pipeline` 1127 行：棘轮（例如新增净业务行 ≤0）比目标行数更可执行。

### 5.3 前端（FE）

- 用户感知表面积在：设置面板、帮助抽屉、LSE/模板 admin 链、高级选项折叠。  
- 建议 W1 交付物：`settings-surface-inventory.md`（或 PRD 附录）列出可见控件 → L0/L1/L3 映射；能藏则藏，能进 Advanced 则进。

### 5.4 产品（PM）

- CSC 是 FTT 的工程底座，**不另设漏斗指标**。  
- 对外三句话：① 默认更短；② 高级仍在但不挡路；③ 不是新功能版本。  
- 否决「借收敛上新默认能力」。

### 5.5 UI/UX（UI）

- 「入口隔离」须可视：主 CTA 区无 admin；设置分「常用 / 高级」；高级需二次展开。  
- 线框可轻：F-CSC-1 设置分层、F-CSC-2 高级警示，不必重做整站。

### 5.6 用户体验（UX）

- 截取型用户：零系统感；任何「Profile」「LSE」字样进主路径都是回归。  
- 搁置型：怕设置项搬家后找不到「上次那一项」——L3 迁移要有「仍可在高级找到」的说明。  
- 成册者：保留轻控制出口（对齐 FTT），但不是排版工作台。

### 5.7 资深测试（QA）

- AC-CSC-04/01/02 在 v0.1 不可测 → 必须先有键表与 lint。  
- W2 等价：复用 AAD/ARCH-OPT **replay/golden 思想**，禁止「自反全绿=行为不变」。  
- 建议独立 `ACCEPTANCE-COMPLETION-SURFACE-CONVERGENCE-V1.md`（W0 后拆）。

### 5.8 典型用户代表（USER）

| 画像 | 态度 | 底线 |
|------|------|------|
| 截取型 P | 支持「少让我选」 | 不要教我配置；不要研究开关 |
| 意向搁置型 | 支持，但怕大改 | 主按钮别换语义；失败能续 |
| 认真成册者 | 支持藏高级 | 高级里仍要能改标题/排除单张/导出确认 |

### 5.9 应用测评专家（EVAL）

建议 CSC 狗粮/测评只盯三件事（写入 AC）：

| 测项 | 通过口径（草案） |
|------|------------------|
| **解释默认路径** | 未读内部文档的测评员，凭 README Happy Path 短文，≤3 分钟复述「选相册→出游记→分享」且不提 LSE/MCS |
| **导出前设置点击** | 首趟狗粮：进入设置的次数与点击的 L1 控件数有上限（W0 钉数字，建议点击 L1≤2） |
| **Advanced 污染** | 首趟路径 HAR/路由：不出现 templates-admin / lse-flags-admin |

不验：算法分、文档总行数、legacy 字符串数。

---

## 6. 波次修订（相对 v0.1）

| Wave | v0.1 | 评审后 |
|------|------|--------|
| **W0** | 基线表 | **加强为 Kickoff 硬挡门**：结构化债务表、L0/L1 键表、Profile 启用快照、设置库存、DIFF 空表、测评三题数字 |
| **W1** | 新 Profile 代码 | **改为**：冻结/宣告 `studio_default` = Happy Path + 用户短文 + **设置/Advanced UI 隔离**（最高用户 ROI） |
| **W2a** | facade | **维持**；可与 AAD 并行；compose 再导出定案 |
| **W2b** | 拆 curate | **降级为对齐 AAD / 薄切片**；大拆不进 CSC 独有 DoD |
| **W2c** | pipeline 变薄 | **改为棘轮 + 禁堆料**；机会主义抽取 |
| **W3a** | legacy −30% | **改为**按 W0 债务表删除批次 + ceiling |
| **W3b** | example≤10 | **L1≤10**；L0 分离；research example 可选第二文件 |
| **W3c** | 文档归档 | **先状态机 + README 入口**；首批只标 5+ 篇示范，不搞全库搬家 |

---

## 7. 最务实解决办法（评审合成）

> 按杠杆排序——建议作为实施优先级。

| 优先级 | 动作 | 为何务实 |
|--------|------|----------|
| **P0** | W0 把「表面积」变成可 CI 的数 | 没有数，收敛是口号 |
| **P0** | W1 冻结 `studio_default` + 砍/藏设置可见面 | 用户一周内可感知；改动面可控 |
| **P1** | W2a `layout_engine/api.py` + 禁深 import | 锁结构回潮；与现有 adapter 现状匹配 |
| **P1** | 文档入口五件套状态标注 | 低代码、高降噪 |
| **P2** | 债务表驱动删 shim；pipeline 棘轮 | 持续降熵，避免运动式重构 |
| **P2** | curate 大拆交给 AAD，CSC 只验收 | 避免双 PRD 抢同一巨石 |

**明确不优先**：为 CSC 新建 Profile 框架、全文 legacy 降幅竞赛、一次拆完 `studio_pipeline`、对存量默认能力全面盲测重审。

---

## 8. WIP / 容量门禁（G-CSC-WIP）

| 规则 | 说明 |
|------|------|
| 与 FTT / 体验挡门冲突 | **FTT/体验优先** |
| 与 AAD 同改 `curate.py` | **AAD 优先**；CSC 改文档/验收/薄边界 |
| 单迭代建议 | W0 可独立；W1 可独立；W2a 可独立；勿 W2b+W2c+W3 同开 |
| 宣布 | W1 Done 前不对外说「表面积收敛完成」 |

---

## 9. Kickoff 清单（勾选后方可 W1 编码）

- [ ] PRD 升至 **v0.2.0-CSC** 且 BLK/OQ 已写入正文  
- [ ] W0 基线产物路径约定（建议 `docs/acceptance-records/csc-w0-baseline-*.json` + 键表 md）  
- [ ] Happy Path 用户短文草案（无黑话）经 PM 点头  
- [ ] 设置面库存负责人指定（FE）  
- [ ] facade 公开符号表草案经 ARCH 点头（含 `compose_trip` 再导出）  
- [ ] G-CSC-WIP 写入实施看板  

---

## 10. 修订记录

| 版本 | 日期 | 说明 |
|------|------|------|
| v1 | 2026-07-22 | 九席 Conditional Go；BLK-01～08；OQ 全关；波次与务实优先级合成 |
