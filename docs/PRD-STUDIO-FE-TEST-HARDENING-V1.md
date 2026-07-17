# Travelogue · Studio 前端测试硬化 V1（工程还债 PRD）

| 属性 | 内容 |
|------|------|
| **产品代号** | Travelogue Studio（`templates/studio/` 原生 ESM） |
| **文档版本** | **v1.1.0-SFH** |
| **状态** | **Done（本机）** · [结案](./acceptance-records/studio-fe-test-hardening-v1-closeout-2026-07-17.md) · [评审纪要](./acceptance-records/studio-fe-test-hardening-v1-review-2026-07-17.md) · [IMPLEMENTATION](./IMPLEMENTATION-STUDIO-FE-TEST-HARDENING-V1.md) |
| **特性代号** | **SFH**（Studio Frontend Hardening） |
| **性质** | **工程还债 PRD**：前端可测边界 + Node 单测金字塔 + 测试入口；**零 intentional 用户功能** |
| **触发来源** | 2026-07-17 前端测试弱项专项分析；五席 Conditional Go → 本版消化 BLK-01..08 |
| **关联文档** | [TESTING.md](./TESTING.md) · [PRD-ASSERTION-HARDENING-V1.md](./PRD-ASSERTION-HARDENING-V1.md) · [DEFINITION-OF-DONE.md](./DEFINITION-OF-DONE.md) · [QUALITY-GATE.md](./QUALITY-GATE.md) · [PRD-OUTPUT-RECIPE-V1.md](./PRD-OUTPUT-RECIPE-V1.md) · [PRD-SHARE-READY-OPTIMIZATION-V1.md](./PRD-SHARE-READY-OPTIMIZATION-V1.md) · [PRD-IMPORT-SHEET-v3-WIZARD.md](./PRD-IMPORT-SHEET-v3-WIZARD.md) · [PRD-PREVIEW-EXPORT-FACADE-V1.md](./PRD-PREVIEW-EXPORT-FACADE-V1.md) |
| **评审纪要** | [studio-fe-test-hardening-v1-review-2026-07-17.md](./acceptance-records/studio-fe-test-hardening-v1-review-2026-07-17.md) |
| **验收配套** | 本文 §9；结案后补 `docs/acceptance-records/studio-fe-test-hardening-v1-closeout-YYYY-MM-DD.md` |
| **实施清单** | [IMPLEMENTATION-STUDIO-FE-TEST-HARDENING-V1.md](./IMPLEMENTATION-STUDIO-FE-TEST-HARDENING-V1.md) |
| **更新日期** | 2026-07-17 |

> **一句话目标**
>
> 把 Studio 前端从「主要靠 Playwright + Python 源码字符串护栏」调整为  
> **纯逻辑 Node 单测（秒级）→ Python/API 合同（字段级）→ Playwright 关键路径（跨层）**，  
> 且**不引入** Jest/Vitest/RTL 新测试栈。
>
> **完成定义**
>
> | 门 | 含义 | 不等于 |
> |----|------|--------|
> | **W0a Go** | JS 入口可信：**本机**全量 `tests/js` 必绿；workflow 补丁已落库（Actions 恢复后生效） | Recipe 抽离未做 |
> | **W0b Go** | Output Recipe 决策有 Node 单测 + Band 双端契约；行为等价对照表齐 | 导入/长图全覆盖 |
> | **W1 Go** | 导入运行态与长图 stale 可秒级回归；热点源码合同降噪（有旧→新对照） | 向导 DOM 全单测 |
> | **W2 Go** | `TESTING.md` / DoD 固化；wizard 薄逻辑；机会主义还债约定生效 | 覆盖率 KPI |
>
> **Actions 额度约束（2026-07-17 起生效）**
>
> GitHub Actions **额度已用尽**：本主题 **不以 Actions 跑通作为任何波次 Go 的前置证据**。  
> - **验收 SSOT = 本机命令输出**（§9.5）。  
> - **仍须**把 `test-pr` 的 Node/`test:js` 改动写入 `.github/workflows/ci.yml`（合同落库），待额度恢复后自然生效。  
> - **禁止**为「验证 CI」反复触发 workflow / 空 commit 刷 Actions。

---

## 0. 文档说明

### 0.1 定位

本 PRD 解决的是 **「前端关键决策测得慢、测得脆、测不到分支」**，不是产品功能缺口。

三类债：

1. **反馈周期债**：Band / 意图卡 / 导入状态机 / 长图 stale 等决策，多数只能靠 Playwright 或浏览器手测。
2. **定位能力债**：失败落在 e2e 或「源码里必须包含某字符串」，难以指向具体函数分支。
3. **契约耦合债**（与 ASH-P-03 同族）：Python 扫 JS/HTML 字面量过多 → 改文案即碎，且给假安全感。

### 0.2 范围承诺

| 承诺 | 说明 |
|------|------|
| **零 intentional 用户功能** | 不改 Studio IA、文案语义、导出产物、recipe 业务规则；允许为可测性做**行为等价**的函数抽离 |
| **复用既有模式** | 沿用 `*-logic.js` + `tests/js/*.test.mjs` + `node --test` |
| **渐进还债** | 不要求 `templates/studio/**` 全覆盖；按故障成本排波次 |
| **行为等价优先** | 抽离不得改变用户可见行为；有意变更须另开产品 PRD |
| **证据驱动（本机优先）** | 每波：文件清单 + **本机** `npm run test:js` / pytest /（必要时）本机 Playwright + 回滚说明 |
| **约定写入 SSOT** | W0a 写入 `TESTING.md` 最短入口；W2 写全金字塔；DoD 引用 |
| **不烧 Actions** | 额度恢复前不把「看一眼 GitHub Checks」当门禁 |

### 0.3 非目标

| # | 排除项 | 理由 |
|---|--------|------|
| OUT-01 | 引入 Jest / Vitest / Mocha / Cypress / Testing Library | 与现栈分裂 |
| OUT-02 | 引入 jsdom / happy-dom 做大规模 DOM 单测 | DOM 编排继续交给 Playwright |
| OUT-03 | 全量重写 Python 源码字符串合同 | 只降噪热点，且须有替代护栏 |
| OUT-04 | Percy / 像素视觉 CI | 归属视觉回归路线 |
| OUT-05 | 为「好测」而改用户文案或 IA | 测试迁就产品真相 |
| OUT-06 | 覆盖率数字 KPI | 与「关键路径必测」冲突 |
| OUT-07 | preview-toolbar 全量逻辑单测 | W2 仅约定 |
| OUT-08 | 把全部 Playwright 下沉为 Node 单测 | 跨层合同必须保留 e2e |
| OUT-09 | 以消耗 Actions 额度验证本主题 | 额度用尽；本机验收 |

### 0.4 术语

| 术语 | 含义 |
|------|------|
| **`*-logic.js`** | 无 DOM / 无 `fetch` / 无 `window` 副作用的纯决策模块 |
| **Node 单测** | `tests/js/*.test.mjs`，由 `node --test` 执行 |
| **聚合入口** | `test_v2_js_logic_node_units`（目录扫描） |
| **`test:js` 唯一入口** | `npm run test:js` → 跨平台稳定命令（见 D-SFH-11） |
| **源码字符串合同** | Python 读源码断言子串；须标 `# ASH-CONTRACT` |
| **跨层 e2e** | Playwright：服务端 + DOM + 用户可观察结果 |
| **行为等价抽离** | 原样挪逻辑；调用方改 import；语义不变 |
| **本机 Go 证据** | 开发者机器上命令退出码 0 + 粘贴关键输出到结案/PR 描述 |

### 0.5 读者指南

| 章节 | 需要冻结的决策 |
|------|----------------|
| §0.6 / §3 | 评审决议 R-SFH-*、设计决策 D-SFH-* |
| §1 | 现状证据 |
| §2 | 成功度量 |
| §4–§5 | 金字塔与优先级 |
| §6–§8 | W0a / W0b / W1 / W2 施工 |
| §9 | 验收（含本机优先与 Actions 休眠） |
| §10 | 风险与已关闭 OQ |

### 0.6 评审决议（R-SFH-* · v1.1 真相源）

> 来源：[评审纪要](./acceptance-records/studio-fe-test-hardening-v1-review-2026-07-17.md) BLK-01..08 + OQ 拍板。  
> 本表覆盖并关闭 v1.0 §10.3 开放问题。

| ID | 决议 | 说明 |
|----|------|------|
| **R-SFH-01** | **本机优先验收；Actions 改动落库但不作为 Go 证据** | 额度用尽期间：W0a/W0b/W1/W2 Go **只认本机命令**。仍须修改 `ci.yml` 的 `test-pr`（setup-node + `npm run test:js`），待额度恢复自动生效。禁止刷 Actions 验证。 |
| **R-SFH-02** | **W0 拆为 W0a + W0b** | W0a=入口/DX/文档最小集 + workflow 补丁；W0b=Recipe 抽离 + 双端契约。W0a 可独立 Kickoff。 |
| **R-SFH-03** | **新建 `output-recipe-logic.js`** | 显式 thresholds/config 参数；壳层负责 fetch/DOM/storage。非第二份完整服务端 resolver。 |
| **R-SFH-04** | **服务端 recipe 成功后客户端不得重裁决** | 成功 `/output-recipe` 后：`kept_n` / `band` / `needs_intent` / `intent` **采信服务端**；本地 classify/resolve **仅**明示降级/离线路径（对齐 D-OR-27 / Share-Ready）。 |
| **R-SFH-05** | **Band 双端契约 + 阈值护栏** | 共享规则向量（默认+非默认）同时跑 Node 与 Python；非法/`0`/NaN 策略两端一致。 |
| **R-SFH-06** | **与 Share-Ready 串行** | W0b 在 Share-Ready 产品语义稳定后，或同 owner 单 PR；SFH **不拥有** AC-SR-*；触达时依赖本机复跑相关 Playwright。 |
| **R-SFH-07** | **行为等价须对照表** | 每个抽离 PR 附旧→新 I/O 或用户结果对照；fail-open/no-op 冻结具体输入输出。 |
| **R-SFH-08** | **合同降噪须旧→新护栏映射** | 「撤两簇」以对照表为验收物，禁止为凑数删除有效 `# ASH-CONTRACT`。 |
| **R-SFH-09** | **模块→用户旅程强制映射** | PR checklist 显式列出必跑本机旅程（§9.3）。 |
| **R-SFH-10** | **不拆独立 ACCEPTANCE** | 本文 §9 + 结案记录；建议一页 IMPLEMENTATION。 |
| **R-SFH-11** | **W1 不测轮询假时钟** | 只测状态转移/谓词；时序归 Playwright。 |
| **R-SFH-12** | **无需线框** | 若实施中改 CTA/层级/成功面流程 → 停手另开产品 PRD。 |

---

## 1. 背景与扫描证据

### 1.1 架构事实（2026-07-17）

| 项 | 事实 |
|----|------|
| 前端形态 | `templates/studio/` 原生 ESM；无 React/Vite 应用壳 |
| Node 单测 | **9** 文件；聚合入口手写 **8** 个——**漏** `bucket.test.mjs` |
| `package.json` | 仅 `tsc:preview-toolbar`；无 `test:js` |
| PR CI | `lint` job 有 `setup-node`；**`test-pr` 未装 Node** → 聚合用例可 `skip` **假绿** |
| Actions | **额度已用尽**（运营约束；见 R-SFH-01） |

### 1.2 缺口地图（按模块）

| 模块 | Node 单测 | 主要护栏 | 风险 |
|------|-----------|----------|------|
| `*-logic.js`（carousel 等） | ✅ | Node + e2e | 低 |
| `title-humanize.js` | ✅ | Node + Python | 低 |
| holdback `bucket` | ⚠️ 有文件、聚合漏 | 部分 e2e | 中 |
| `output-recipe.js` | ❌ | Playwright + guards | **P0** |
| `import-run.js` | ❌ | Playwright + payload 合同 | **P0** |
| `import-wizard.js` | ❌ | Playwright + 源码串 | **P1** |
| `longshot.js` | ❌ | e2e + 静态 export | **P1** |
| `dom.js` / toolbar 其余 | ❌ | 间接 | **P2** |

### 1.3 好模式

| 模式 | 锚点 |
|------|------|
| 纯逻辑 + `node --test` | `carousel-logic.js` ↔ `tests/js/*.test.mjs` |
| JS/Python 双实现对齐 | `title-humanize`（Band 契约升级为共享向量，见 §6.3） |
| ASH 行为断言优先 | `TESTING.md` §9 |

### 1.4 与相邻主题边界

| 主题 | 关系 |
|------|------|
| **ASH** | 继承 OUT-03（不引入 vitest）；本 PRD 承接「测不够」 |
| **Share-Ready / Output Recipe** | 产品 AC 仍归产品 PRD；SFH 只加可测边界。AC-SR-02 **继续 Playwright** |
| **Import / FTUE** | SFH 不改成功面/引导文案；W1 触达 import-run 时复跑下游 AC |

### 1.5 问题总览

| ID | 问题 | 严重度 |
|----|------|--------|
| **SFH-P-01** | 聚合手写列表漏测 + `test-pr` 无 Node 假绿 | **P0** |
| **SFH-P-02** | `output-recipe` 无 Node 单测；双端阈值可能漂移 | **P0** |
| **SFH-P-03** | `import-run` 状态机无 Node 单测 | **P0** |
| **SFH-P-04** | `longshot` stale 无 Node 单测 | **P1** |
| **SFH-P-05** | 热点源码字符串合同过多 | **P1** |
| **SFH-P-06** | `TESTING.md` 缺 Studio FE 分层 | **P1** |
| **SFH-P-07** | 无跨平台 `test:js` | **P2** |
| **SFH-P-08** | Actions 额度用尽 → 远程 CI 不可用 | **运营约束** |

---

## 2. 目标与成功度量

### 2.1 目标

| ID | 目标 | 验收口径 | 阶段 |
|----|------|----------|------|
| **G-SFH-01** | 全量 `tests/js` 可被唯一入口执行；聚合改目录扫描 | 本机 `npm run test:js` 绿；空目录 fail | **W0a** |
| **G-SFH-02** | `package.json` 有 `test:js`；`TESTING.md` 最短入口；`ci.yml` `test-pr` 补 Node+script（落库） | 文件 diff；**不要求** Actions 跑通 | **W0a** |
| **G-SFH-03** | Output Recipe Node 单测 + 双端契约向量 | §6.2–§6.3；本机绿 | **W0b** |
| **G-SFH-04** | Import-run 纯逻辑 Node 单测 | §7.1 | **W1** |
| **G-SFH-05** | Longshot stale 等 Node 单测 | §7.2 | **W1** |
| **G-SFH-06** | ≥2 簇合同降噪，每簇有旧→新对照表 | §7.3 | **W1** |
| **G-SFH-07** | `TESTING.md` 全金字塔 + DoD 勾选 | 文档合入 | **W2** |
| **G-SFH-08** | Wizard 风险矩阵纯逻辑（脏关闭 / next-back 等） | §8.1；用例数 ≥8 仅作下限 | **W2** |

### 2.2 产品可理解成功表述

> 三条发布关键路径——**选分享方式、导入恢复、长图过期提示**——的规则变更，在合并前均有**本机秒级**确定性护栏；原有用户路径 Playwright（本机复跑）不回归。

### 2.3 非成功指标

- 行覆盖率阈值；全量 Playwright Node 化；每个 UI 文件配测。  
- **GitHub Actions 绿勾**（额度恢复前明确不追）。

### 2.4 用户可感知差异

| # | 差异 |
|---|------|
| DIFF-SFH-01 | **无** intentional 用户可见差异 |
| DIFF-SFH-02 | 抽离误伤 → 当缺陷修，不记产品 DIFF |

---

## 3. 设计决策

| # | 决策 | 说明 |
|---|------|------|
| **D-SFH-01** | 不引入新前端测试框架 | Runner = `node --test` |
| **D-SFH-02** | 决策下沉，DOM 留 e2e | 输入→枚举/布尔/下一状态进 logic |
| **D-SFH-03** | 聚合扫目录，禁手写漏收 | `tests/js/*.test.mjs` 全收 |
| **D-SFH-04** | 抽离必须行为等价 | 先对照表，再搬；禁改 Band/文案/默认 intent |
| **D-SFH-05** | **一个行为一个主护栏** | Node=纯判定/映射；Python=handler/schema/**服务端** resolve；Playwright=跨层用户结果。Python **不对** JS export 做常规源码断言 |
| **D-SFH-06** | 源码合同只保留短 `# ASH-CONTRACT` | 降噪必须有替代（R-SFH-08） |
| **D-SFH-07** | storage/fetch 注入或隔离 | logic 显式参数；禁 Node 碰真浏览器 API |
| **D-SFH-08** | 与产品 PRD 冲突时产品赢 | |
| **D-SFH-09** | **CI 合同落库；Go 证据本机** | `test-pr` 必须含 setup-node + `npm run test:js`（额度恢复后生效）。**否决**「无 node 则 skip 仍算 CI 可信」。本地无 node：pytest 聚合可 skip；开发者做 FE 决策时须自备 node |
| **D-SFH-10** | 命名：`{domain}-logic.js` / `tests/js/{domain}-logic.test.mjs` | |
| **D-SFH-11** | **`test:js` 跨平台唯一入口** | **冻结**：`node --test tests/js`（目录模式），或 `node scripts/run-js-tests.mjs`（fs 扫描排序 spawn）。**禁止**依赖未验证的 npm shell 通配 `*.test.mjs` |
| **D-SFH-12** | Recipe：成功响应后不重裁决 | 见 R-SFH-04；logic 只承载 UI 映射 + 明示降级 |
| **D-SFH-13** | 不烧 Actions | 见 R-SFH-01 / OUT-09 |

### 3.1 架构不变式

1. **Recipe 裁决单一权威**：服务端成功响应存在时，客户端不得用 DOM / 本地阈值 / 本地 resolver 改写 `kept_n`、Band、`needs_intent`、intent。  
2. **一个行为一个主护栏**：禁止 Node 与 Python 各测一份互不知情的 Band 真相却都绿。  
3. **声明进快测的 JS 不可静默跳过（CI 语义）**：workflow 合同如此书写；额度恢复后必须 fail-closed。额度用尽期间用本机等价命令代替证据。

---

## 4. 目标金字塔（Studio FE）

```text
        ┌──────────────────────┐
        │ 人工 / 真机 AC       │
        ├──────────────────────┤
        │ Playwright 跨层 e2e  │  本机复跑（Actions 休眠）
        ├──────────────────────┤
        │ Python 合同 / 集成   │  API · schema · 服务端 resolve
        ├──────────────────────┤
        │ Node 纯逻辑单测      │  本机 npm run test:js（主反馈）
        └──────────────────────┘
```

| 层 | 允许 | 禁止 |
|----|------|------|
| Node | 返回值、状态转移、载荷→view-model 映射 | `document`、真 HTTP、像素 |
| Python | handler/schema、**服务端** recipe、短 ASH-CONTRACT | 大段文案、常规 JS export 扫串 |
| Playwright | 可见性、role、服务端注入后 UI | 无注释固定 sleep（ASH） |

---

## 5. 模块施工优先级与挡门

### 5.1 优先级

| 优先级 | 工作 | 波次 |
|--------|------|------|
| P0 | `test:js` + 聚合扫描 + `TESTING.md` 最短入口 + `ci.yml` 补丁落库 | **W0a** |
| P0 | `output-recipe-logic` + 双端契约（待 Share-Ready 空窗） | **W0b** |
| P0/P1 | `import-run-logic` | **W1** |
| P1 | `longshot-logic` + 合同降噪对照 | **W1** |
| P2 | wizard-logic + 文档全量 | **W2** |

### 5.2 相邻主题挡门（产品）

```text
SFH W0a ──可插空窗、独立 Kickoff──► 本机 test:js + workflow 落库
Share-Ready W0 ──优先于──► SFH W0b
SFH W0b ──依赖──► Share-Ready 相关 e2e 本机绿（SFH 不拥有 AC）
FTUE / Share-Ready W1 成功面 ──SFH 不拥有、不改──
SFH W1 import-run ──联合──► Import 下游 AC 本机回归
SFH W2 ──治理收尾──
```

**抢人优先级**：Share-Ready W0 → FTUE/成功面 → SFH W0a → SFH W0b/W1 → W2。

---

## 6. W0a · 入口可信（本机）+ workflow 落库

> **目标**：本机不再漏跑 JS 单测；CI 补丁已进仓库，Actions 恢复后无需再改语义。

### 6.1 施工清单

| ID | 任务 | 验收 |
|----|------|------|
| T-W0a-01 | `test_v2_js_logic_node_units` 改为扫描 `tests/js/*.test.mjs`（排序） | 含 `bucket.test.mjs`；0 文件 → fail |
| T-W0a-02 | 本地无 `node` → pytest **skip**（开发机约定）；**不要**把「CI 无 node skip」写成目标态 | 代码注释标明 R-SFH-01 |
| T-W0a-03 | `package.json`：`"test:js"` = D-SFH-11 唯一入口 | 本机 Windows/（若有）Linux 同命令绿 |
| T-W0a-04 | `.github/workflows/ci.yml`：`test-pr` 增加 `actions/setup-node`（与 lint 同主版本）+ `npm ci`（若需要）+ `npm run test:js` | **diff 合入即可**；**不要求** push 后 Checks 绿 |
| T-W0a-05 | `TESTING.md` 最短节：本机命令、分层一句、Actions 休眠说明 | 文档 diff |
| T-W0a-06 | （建议）一页 IMPLEMENTATION：入口命令、owner、W0a/W0b 切分 | 可选同 PR |

### 6.2 W0a 验收命令（本机 SSOT）

```powershell
npm run test:js
python -m pytest tests/unit/web/test_studio_home_v2.py -k v2_js_logic_node_units -q
# 人工：ci.yml test-pr 已含 setup-node 与 npm run test:js（读 diff，不触发 Actions）
```

### 6.3 W0a 回滚

还原聚合入口、`package.json`、`ci.yml`、`TESTING.md` 最短节。

---

## 6b. W0b · Output Recipe 可测 + 双端契约

> **前置**：Share-Ready 产品语义已稳定，或同 owner 单 PR 串行（R-SFH-06）。  
> **目标**：Recipe 决策秒级可回归；服务端权威边界不被「本地测绿」稀释。

### 6b.1 落盘

| 文件 | 职责 |
|------|------|
| `templates/studio/js/output-recipe-logic.js` | 纯函数：`classifyBand`、`needsFullExportConfirm`、意图映射、**降级路径** resolve、cache/session helpers（storage 注入）；**显式 bands/config 参数** |
| `templates/studio/js/output-recipe.js` | fetch / DOM 意图卡 / analytics；成功响应后**直接采用**服务端字段（R-SFH-04） |
| `tests/js/output-recipe-logic.test.mjs` | Node 单测 |
| 共享向量（建议） | `tests/fixtures/output_recipe_band_vectors.json`（或 yaml）供 Node + Python 同读 |

### 6b.2 行为等价对照（PR 必附）

至少列出：`classifyBand` / `needsFullExportConfirm` / 降级 `resolveClientRecipe`（若保留）/ session helpers 的代表输入→输出；并注明「成功服务端路径不再走本地重裁决」。

### 6b.3 Node 决策表（AC-SFH-OR）

| 用例 ID | 输入要点 | 期望 |
|---------|----------|------|
| OR-U-01 | `keptN`∈[0, sparseMax]（**0 是否空内容降级须在测试名写清现语义**） | `band=sparse` 或文档化降级 |
| OR-U-02 | `sparseMax+1..ambiguousMax` | `ambiguous` |
| OR-U-03 | `>ambiguousMax` | `narrative` |
| OR-U-04 | `enabled=false` | 与现实现一致的 no-op/fail-open（对照表冻结） |
| OR-U-05 | narrative + full + wechat_chat + `keptN≥hint` | `needsFullExportConfirm=true` |
| OR-U-06 | chapter 或非 chat | `false` |
| OR-U-07 | INTENT↔PLATFORM 关键键互逆 | 与现常量一致 |
| OR-U-08 | session helper + 假 storage | round-trip / clear |
| OR-U-09 | **仅降级路径**：ambiguous + 无 session → needs_intent | 不得宣称覆盖「成功服务端路径」 |
| OR-U-10 | sparse/narrative 默认不强迫意图卡 | 跟现语义 |

### 6b.4 双端契约（AC-SFH-OR-X · BLK-04）

| 用例 ID | 要求 |
|---------|------|
| OR-X-01 | 共享向量：默认阈值 `9/30/50` **与**至少一组非默认（如 `5/20/35`） |
| OR-X-02 | 边界：`0, sparseMax, +1, ambiguousMax, +1, hint-1, hint` |
| OR-X-03 | 同一向量：JS `classifyBand` 与 Python `classify_band`（或 resolve 结果中的 band）一致 |
| OR-X-04 | preview/shelf：`needs_intent` / 默认 intent（服务端 resolve）有 Python 测；客户端成功路径只断言**映射**不重算 |
| OR-X-05 | 非法阈值 / NaN / 类型错误：**冻结** FE `Number(x)\|\|default` 回退（不抛错）；Node 测锁定；Python `kept_n=0→sparse` 对照 |
| OR-X-06 | 阈值关系：`isBandThresholdOrderValid`；共享向量强制 sparse&lt;ambiguous；乱序 **不**自动改写（行为等价） |

> 跨层「DOM 少图仍出卡」**仍**由 Share-Ready Playwright 锁；本机复跑，不触发 Actions。

### 6b.5 不抽 / 不测（W0b）

- 意图卡 DOM/焦点（Playwright；含 a11y 焦点归还）。  
- 改默认阈值或产品文案。  
- 遥测全字段。

### 6b.6 W0b 验收命令（本机）

```powershell
npm run test:js
python -m pytest tests/unit/web/test_studio_home_v2.py -k v2_js_logic_node_units -q
# Band 双端：按 IMPLEMENTATION 指向的 pytest nodeid（含共享向量）
python -m pytest tests/e2e/test_share_ready_w0_playwright.py tests/e2e/test_output_recipe_persona_playwright.py -q
```

### 6b.7 W0b 回滚

删除 `output-recipe-logic*` 与向量夹具；还原 `output-recipe.js`；恢复被删合同。

---

## 7. W1 · Import-run + Longshot + 合同降噪

### 7.1 Import-run

| 文件 | 职责 |
|------|------|
| `import-run-logic.js` | payload 规范化；态转移；resume/retry 谓词 |
| `import-run.js` | HTTP/轮询/面板 |
| `tests/js/import-run-logic.test.mjs` | Node |

| 用例 ID | 场景 |
|---------|------|
| IR-U-01 | payload 字段与 Python contract 一致 |
| IR-U-02 | 空/非法 title·path：**冻结现用户可见结果**（对照表） |
| IR-U-03 | running→cancelling；terminal cancel no-op |
| IR-U-04 | resume 谓词 |
| IR-U-05 | retry 谓词（若有） |

不测：真 XHR、假时钟轮询（R-SFH-11）。  
联合门：本机复跑 Import 下游相关 AC / wizard e2e（§9.3）。

### 7.2 Longshot

| 文件 | 职责 |
|------|------|
| `longshot-logic.js` | stale；纯布尔；可选 `assessMagazineTitleRisk` |
| `tests/js/longshot-logic.test.mjs` | Node |

| 用例 ID | 场景 |
|---------|------|
| LS-U-01 | revision/token 不一致 → stale |
| LS-U-02 | 一致 → 非 stale |
| LS-U-03 | 缺字段 fail-open/closed（写进测试名） |
| LS-U-04 | title risk 边界（若纳入） |

跨层：成功面主/次 CTA、stale 恢复动作 → Playwright 映射旅程（§9.3），不仅「请求已发出」。

### 7.3 合同降噪（AC-SFH-CN）

≥2 簇；每簇 PR 附件表：

| 旧断言 | 保护的风险 | 新主护栏 | 删/留 |
|--------|------------|----------|-------|
| … | … | … | … |

**文案红线（禁止裸删，可迁 SSOT/Playwright）**：

- `HELP_COPY` 首成功 / 导入失败 / 长图成败过期 / 分享建议的**渲染消费点**  
- 禁词与误导 CTA；用户面不出现 `kept_n`  
- 意图卡标题数量语义、选项标签、主推荐、取消  
- 向导：智能挑选摘要、日期错误、导入中拦截、取消确认、失败重试  
- 成功面主/次 CTA  

「常量存在」≠「正确键被渲染」。

### 7.4 W1 验收命令（本机）

```powershell
npm run test:js
python -m pytest tests/unit/web/test_studio_home_v2.py -k v2_js_logic_node_units -q
python -m pytest tests/unit/web/test_import_wizard_payload_contract.py -q
python -m pytest tests/e2e/test_import_wizard_v3_playwright.py tests/e2e/test_preview_toolbar_arc14_playwright.py -q
# 若有更贴「成功面/stale 恢复」的用例，按 §9.3 映射表追加本机执行
```

---

## 8. W2 · 约定固化 + Wizard 薄抽离

### 8.1 Wizard logic

只抽 **1** 个风险矩阵（例如：脏表单关闭确认、next/back 合法性）。  
`import-wizard-logic.js` + `tests/js/import-wizard-logic.test.mjs`；用例 ≥8 为下限，**验收看矩阵覆盖**（G-SFH-08）。

### 8.2 文档

| ID | 任务 |
|----|------|
| T-W2-01 | `TESTING.md` 全金字塔（§4） |
| T-W2-02 | DoD：Studio FE 决策优先 logic + `tests/js`；跨层本机 Playwright |
| T-W2-03 | studio 文档指针 |
| T-W2-04 | （可选）ASH OUT 反向链接 |

### 8.3 机会主义

其后改 `dom.js` format helper、shelf/bento 新分支、toolbar 新纯函数时顺手抽测。

---

## 9. 验收门禁

### 9.1 波次门禁

| 门 | 必须满足 |
|----|----------|
| **W0a Go** | G-SFH-01..02；§6.2 本机命令绿；`ci.yml` diff 含 test-pr Node+`test:js`；**不要求** Actions |
| **W0b Go** | G-SFH-03；§6b.2 对照表；OR-U + OR-X 本机绿；§9.3 Recipe 旅程本机绿；Share-Ready 串行条件满足 |
| **W1 Go** | G-SFH-04..06；降噪对照表；§9.3 Import/Longshot 旅程本机绿 |
| **W2 Go** | G-SFH-07..08；文档合入 |

### 9.2 全局不变式

| ID | 不变式 |
|----|--------|
| INV-01 | 无 intentional 用户文案/IA/导出语义变更 |
| INV-02 | Node 测不依赖网络与真实 `trips/` |
| INV-03 | 不新增 Jest/Vitest |
| INV-04 | 新增长源码合同须 `# ASH-CONTRACT` 且短 |
| INV-05 | 抽离后映射旅程本机绿 |
| INV-06 | **不触发 Actions 仅为「看绿」**（额度用尽期间） |
| INV-07 | 成功服务端 recipe 响应后无客户端重裁决（R-SFH-04） |

### 9.3 模块→用户旅程映射（本机必跑）

| 模块 | 必跑旅程（本机 Playwright 或已有套件） |
|------|----------------------------------------|
| `output-recipe` | 服务端 `kept_n` Ambiguous → 意图卡可见可选；选后可继续导出；API 失败降级 toast（若已落地） |
| `import-run` / wizard | 导入中拦截、取消确认、刷新恢复、失败重试 |
| `longshot` | 导出成功面主/次 CTA；stale 后清晰恢复/再导出 |

### 9.4 PR Checklist

```markdown
## SFH checklist
- [ ] 行为等价对照表（或链到产品 PRD 的有意变更）
- [ ] 纯逻辑在 `*-logic.js`；显式 config（Recipe）
- [ ] 本机 `npm run test:js` 绿（粘贴摘要）
- [ ] 本机 `pytest … -k v2_js_logic_node_units` 绿
- [ ] §9.3 映射旅程已本机执行（列出 nodeid）
- [ ] 降噪：旧→新护栏表（若适用）
- [ ] 若改 ci.yml：仅落库，未为验证刷 Actions
- [ ] 成功 recipe 路径无本地重裁决（若触达）
```

### 9.5 本机证据模板（结案 / PR 描述）

```text
SFH evidence (local · Actions quota exhausted)
- node -v: …
- npm run test:js: exit 0 · (# pass / # fail)
- pytest v2_js_logic_node_units: …
- (W0b+) band vectors / e2e nodeids: …
- ci.yml: patched yes/no (not executed on Actions)
```

### 9.6 结案产物

- [x] 本文 → **Done（本机）** · 主施工 `a2d615f` · 结案补丁见 closeout  
- [x] closeout 记录（含 §9.5 证据）→ [studio-fe-test-hardening-v1-closeout-2026-07-17.md](./acceptance-records/studio-fe-test-hardening-v1-closeout-2026-07-17.md)  
- [x] `TESTING.md` / DoD 已按波次更新  
- [ ] Actions 额度恢复后：抽查一次 `test-pr` 确跑 `test:js`（记入 closeout 补记，非本波阻塞）

---

## 10. 里程碑、风险与已关闭问题

### 10.1 排期

| 波次 | 工期 | 依赖 |
|------|------|------|
| **W0a** | 0.5–1 日 | 无；可立刻 Kickoff |
| **W0b** | 1.5–2.5 日 | Share-Ready 空窗或同 owner；本机 Node+pytest+相关 e2e |
| **W1** | 3–5 日 | W0a 已稳 |
| **W2** | 1–2 日 | 文档 + 薄切片 |

### 10.2 风险

| ID | 风险 | 缓解 |
|----|------|------|
| R-01 | 抽离循环依赖 / 顶层 DOM | 先 `node --test` import 冒烟 |
| R-02 | Windows 入口不稳 | D-SFH-11 目录/wrapper |
| R-03 | Actions 长期不可用 | R-SFH-01 本机 SSOT；额度恢复后补记一次 |
| R-04 | Share-Ready 文件冲突 | W0a 先行；W0b 串行 |
| R-05 | 降噪过度 | R-SFH-08 对照表 |
| R-06 | 双实现各测绿不一致 | OR-X 共享向量 |
| R-07 | 误烧 Actions | OUT-09；PR checklist |

### 10.3 开放问题 → 已关闭

| # | 决议 |
|---|------|
| Q-01 | **新建** `output-recipe-logic.js`（R-SFH-03） |
| Q-02 | **CI 合同要装 Node + 跑 test:js**；Go 证据本机（R-SFH-01 / D-SFH-09）；可不新建独立 job |
| Q-03 | **不测**轮询假时钟（R-SFH-11） |
| Q-04 | **不拆** ACCEPTANCE；建议一页 IMPLEMENTATION（R-SFH-10） |

---

## 11. 附录

### 11.1 现有 Node 单测基线

`carousel` · `lightbox` · `viewport` · `layout-tier` · `shelf-actions` · `bento-preview-picker` · `manifest` · `bucket`（W0a 前未聚合）· `title-humanize`

### 11.2 目标新增文件

| 波次 | 路径 |
|------|------|
| W0a | （可选）`scripts/run-js-tests.mjs` |
| W0b | `output-recipe-logic.js` · `output-recipe-logic.test.mjs` · band 向量夹具 |
| W1 | `import-run-logic.*` · `longshot-logic.*` |
| W2 | `import-wizard-logic.*` |

### 11.3 e2e 分工

| 场景 | 护栏 |
|------|------|
| Ambiguous + 服务端 `kept_n` 出卡 | Playwright（Share-Ready）· 本机 |
| Band 阈值 / confirm / 双端向量 | Node + Python |
| 导入 cancel/resume 谓词 | Node；真恢复 Playwright |
| 长图成功面 / stale 恢复 | Playwright；stale 布尔 Node |

### 11.4 v1.0 → v1.1 变更摘要

| 来源 | 合入 |
|------|------|
| BLK-01/02 | W0a；`test:js` 唯一入口；`test-pr` 补丁落库 |
| **运营** | Actions 额度用尽 → 本机 Go；不刷 CI |
| BLK-03/04 | R-SFH-04/05；§6b 双端契约 |
| BLK-05 | W0a/W0b 拆分 + 挡门矩阵 |
| BLK-06/07/08 | 对照表、降噪映射、旅程映射 |
| OQ | 全部关闭见 §10.3 |
| 估时 | W0a 0.5–1d；W0b 1.5–2.5d；W1 3–5d |

### 11.5 版本历史

| 版本 | 日期 | 说明 |
|------|------|------|
| v1.1.0-SFH | 2026-07-17 | 评审 Must-Fix 回写；W0a–W2 施工 + 结案（closeout） |
| v1.0.0-SFH | 2026-07-17 | 初稿 |
