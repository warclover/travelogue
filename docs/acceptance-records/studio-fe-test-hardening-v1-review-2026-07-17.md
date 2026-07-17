# PRD-STUDIO-FE-TEST-HARDENING-V1 · 跨职能评审纪要

| 属性 | 内容 |
|------|------|
| **文档** | [PRD-STUDIO-FE-TEST-HARDENING-V1.md](../PRD-STUDIO-FE-TEST-HARDENING-V1.md) |
| **评审版本** | **v1.0.0-SFH Draft** |
| **日期** | 2026-07-17 |
| **结论** | **有条件通过（Conditional Go）** → **Must-Fix 已回写** [PRD v1.1.0-SFH](../PRD-STUDIO-FE-TEST-HARDENING-V1.md) · **Ready for Kickoff（本机优先）** |
| **参评角色** | 产品 · 开发 · 架构 · 算法/策展规则 · 交互/UI-UX |
| **评审方式** | 分席只读评审（对照 PRD + CI 事实 + Output Recipe / Share-Ready / ASH 相邻合同） |
| **记录人** | 工程联合纪要（分席意见汇总） |
| **跟进** | PRD v1.1 已合入 BLK-01..08 + Actions 额度用尽约束（R-SFH-01）；编码从 **W0a** 开工；可选一页 IMPLEMENTATION |
| **运营约束** | GitHub Actions **额度已用尽**：Go 证据改为本机命令；`ci.yml` 仍落库、禁止刷 Actions 验证 |

---

## 1. 总评（一句话）

> **方向正确、栈选择克制（继续 `*-logic.js` + `node --test`），W0 切口也对；阻塞不在愿景，而在四处合同未钉死：① PR `test-pr` 未装 Node → JS 单测可静默 skip（假绿）；② Recipe「服务端裁决 vs 客户端本地 classify」边界与双端契约未写清；③ 与 Share-Ready 同改 `output-recipe.js` 缺串行/联合挡门；④ 合同降噪与体验回归缺「旧护栏→新护栏」硬对照。Must-Fix 回写后可 Kickoff。**

---

## 2. 分席表决

| 席位 | 表决 | 一句话 |
|------|------|--------|
| **产品** | Conditional Go | 零功能边界清楚；须写清与 Share-Ready/FTUE/Import 联合挡门，且 CI 真执行才算 W0 Go |
| **开发** | Conditional Go | 模式可落地；CI Node、Windows 入口、Share-Ready 并行冲突须先冻结 |
| **架构** | Conditional Go | 金字塔对；须防「双实现各测绿」≠「一致」；Node 不可静默跳过 |
| **算法** | Conditional Go | Band 适合 Node 测；必须补双端契约与阈值合法性，否则固化漂移 |
| **交互 / UI-UX** | Conditional Go | 无需线框；须冻结体验旅程映射与文案降噪红线 |

**汇总**：**五席一致 Conditional Go**。未回写 Must-Fix 前 **不批无条件 Go / Kickoff**。

---

## 3. 全场共识

1. **不做新测试栈**：继承 ASH OUT-03；继续 `*-logic.js` + `node --test`。  
2. **分层对**：Node=纯决策；Python=API/schema/服务端 resolve；Playwright=跨层用户结果；DOM/焦点不进 Node。  
3. **W0 应拆**：先 **W0a（CI 真跑 JS）**，再 **W0b（Recipe 抽离）**——后者让位于 Share-Ready 产品语义稳定后再做。  
4. **不替代产品 AC**：Share-Ready `AC-SR-02`、Import 下游合同、FTUE 成功面仍由原主题拥有。  
5. **不需要线框**：工程债；若实施中改 CTA/层级/成功面流程 → 停手另开产品 PRD。  
6. **不拆独立 ACCEPTANCE**：PRD §9 + 结案记录即可；建议补一页 IMPLEMENTATION。

---

## 4. Must-Fix（阻塞 Kickoff · 建议合入 PRD v1.1）

| ID | 议题 | 来源席位 | 要求 |
|----|------|----------|------|
| **BLK-01** | **PR CI Node 假绿** | 开发 / 架构 / 产品 / 算法 | 事实：`setup-node` 仅在 `lint` job；`test-pr` **未装 Node**，聚合用例无 node 则 `skip`。W0 必须：`test-pr` 安装固定 Node + 显式跑 `npm run test:js`（或等价）；CI 上 Node 缺失/收集为空/`# fail≠0` → **fail**。本地无 Node 可保留 skip。 |
| **BLK-02** | **跨平台 `test:js` 入口定稿** | 开发 / 架构 | 禁止以未验证的 `tests/js/*.test.mjs` npm 通配作为验收前提。冻结唯一入口：`node --test tests/js` 或 `scripts/run-js-tests.mjs`（fs 扫描排序）。CI 与本地同一命令。 |
| **BLK-03** | **Recipe 服务端权威边界** | 架构 / 算法 / 产品 | 正文写死：成功取得 `/output-recipe` 后，`kept_n` / `band` / `needs_intent` / `intent` **采信服务端**；本地 `classifyBand` / `resolveClientRecipe` **仅**用于明示降级/离线路径，不得在成功响应后重裁决。交叉引用 D-OR-27 / Share-Ready。 |
| **BLK-04** | **Band 双端契约 + 阈值护栏** | 算法 / 架构 | W0b 验收增加：共享规则向量（默认+非默认阈值）同时跑 JS Node 与 Python resolve；覆盖边界值与 `enabled`/入口。阈值合法性（如 `sparseMax < ambiguousMax`）及非法/`0`/NaN 处理策略两端一致；logic 接受**显式 config 参数**。 |
| **BLK-05** | **与 Share-Ready 串行 / 联合挡门** | 产品 / 开发 | W0 拆 **W0a（CI/DX）** 与 **W0b（Recipe 抽离）**。W0b：Share-Ready 产品语义先合，或同 owner 单 PR；SFH 不拥有 AC-SR-*；触达 `output-recipe.js` 时 W0b Go **依赖**相关 Playwright 绿。 |
| **BLK-06** | **行为等价可验收** | 产品 / UX / 开发 | 每个抽离 PR 附「旧入口 I/O 或用户结果 → 新入口」对照表；fail-open/no-op 冻结具体输入输出，禁止口头「跟现实现」。 |
| **BLK-07** | **合同降噪对照表** | 架构 / 产品 / UX | G-SFH-06「撤两簇」改为：每簇必填 `旧断言 → 风险 → 新主护栏 → 删留理由`。禁止为凑数删仍有效的 `# ASH-CONTRACT`。 |
| **BLK-08** | **体验旅程强制映射** | UI-UX / 产品 | PR checklist 增加模块→必跑旅程：Recipe（意图卡可见/可选）、Import（取消/恢复/失败重试）、Longshot（成功面/stale 恢复）。仅「相关 e2e 未红」不够；映射旅程须显式执行。 |

---

## 5. Should-Fix（建议 v1.1 合入，不单独挡 Kickoff）

1. **估时修正**：W0（含 W0a+W0b）→ **2–3 人日**；W1 → **3–5 人日**；W2 → 1–2 人日仍可信。  
2. **TESTING.md 最小约定前移到 W0a**（命令 + CI 必跑 + 分层一句）；完整金字塔可仍在 W2。  
3. **一页 IMPLEMENTATION**：函数签名、调用迁移表、CI 命令、波次 owner；不强制独立 ACCEPTANCE。  
4. **`kept_n=0` 语义单列**：空内容降级 vs Sparse 普通边界，避免 Node 测固化未定义行为。  
5. **W2「≥8 用例」改为风险矩阵覆盖**（脏关闭 / next-back 合法性）；8 仅作最低参考。  
6. **意图卡 a11y**：焦点进入/归还仍由 Playwright 锁（Node 不测 DOM 不等于无测）。  
7. **Import 联合门**：W1 触达 import-run 时复跑 `AC-IW-DS-*` 相关回归，不只 payload contract。  
8. **成功度量补产品表述**：「选分享 / 导入恢复 / 长图过期」三条主链规则变更有秒级护栏，且用户路径 e2e 不回归。

---

## 6. OQ 拍板汇总（五席收敛）

| OQ | 决议 | 备注 |
|----|------|------|
| **Q-01** | **新建 `output-recipe-logic.js`** | 五席一致；须显式 thresholds；非第二份完整服务端 resolver |
| **Q-02** | **改：CI 必须有 Node 且真执行** | 可不新建独立 job，但必须进 `test-pr`（或等价 step）；**否决**「观察两周再加」 |
| **Q-03** | **W1 不测轮询假时钟** | 只测状态转移/谓词；时序归 Playwright |
| **Q-04** | **不拆独立 ACCEPTANCE** | §9 + 结案记录；建议补一页 IMPLEMENTATION |

---

## 7. 文案 / 合同降噪红线（UI-UX · W1 禁止裸删）

可从「扫源码字面量」迁到 `HELP_COPY` SSOT 或 Playwright 可见文本，但须保留等价护栏：

- `HELP_COPY` 首成功 / 导入失败 / 长图成功·失败·过期 / 分享建议的消费点  
- 禁词：用户面不出现 `kept_n` 等内部字段；误导 CTA / 废弃句  
- 意图卡：标题数量语义、选项可见标签、主推荐、取消路径  
- 向导：智能挑选摘要、日期错误、导入中拦截、取消确认、失败重试  
- 成功面：主/次 CTA 与下一步提示  

断言「常量存在」≠「正确键被渲染」。

---

## 8. 与相邻主题挡门关系（产品拍板）

```text
SFH W0a ──独立可插空窗──► CI Node + test:js 全收 + 最小文档
Share-Ready W0 ──优先于──► SFH W0b（output-recipe 抽离）
SFH W0b ──依赖──► Share-Ready AC-SR-02 等相关 e2e 绿
FTUE / Share-Ready W1 成功面 ──SFH 不拥有、不改──
SFH W1 import-run ──联合──► Import 下游 AC 回归
SFH W2 ──治理收尾──► TESTING.md / DoD / wizard 薄切片
```

**抢人优先级**：Share-Ready W0 → FTUE/Share-Ready W1 成功面 → SFH W0b/W1 → SFH W2。

---

## 9. 代码 / CI 对齐摘要（只读）

| 断言 | 现网 | 结论 |
|------|------|------|
| JS 聚合手写 8 文件、漏 `bucket.test.mjs` | `test_v2_js_logic_node_units` | **属实** |
| `package.json` 无 `test:js` | 仅 `tsc:preview-toolbar` | **属实** |
| PR `test-pr` 装 Node | 仅 `lint` job 有 `setup-node` | **属实 · BLK-01** |
| `output-recipe.js` 含 fetch/analytics/sessionStorage | 顶层 import 非纯 | **属实 · 宜新建 logic** |
| 客户端/服务端 Band 阈值来源可能分叉 | FE←`/config`；BE←yaml/resolve | **算法席风险成立 · BLK-04** |

---

## 10. 建议狗粮 / 证据（编码后 · 非本轮）

1. PR CI 日志可见 `npm run test:js` 且非 skip。  
2. 改一处 Band 边界 → Node 秒级红；改回绿。  
3. 非默认阈值向量 JS/Python 同绿。  
4. Share-Ready：DOM 少图 + `kept_n` Ambiguous 仍出意图卡。  
5. 抽离后：导入取消/恢复、长图成功面/stale 映射旅程显式绿。

---

## 11. 签字

| 项 | 负责人 | 日期 | 结论 |
|----|--------|------|------|
| 分席评审 | 五席联合 | 2026-07-17 | **Conditional Go** |
| Must-Fix 回写 PRD v1.1 | 产品/文档 | 2026-07-17 | ✅ [PRD v1.1.0-SFH](../PRD-STUDIO-FE-TEST-HARDENING-V1.md)（含 Actions 休眠 / 本机 Go） |
| W0a 入口 + workflow 落库 | 开发 | — | **可 Kickoff（本机验收；不跑 Actions）** |
| W0b Recipe 抽离 | 开发 | — | **待 Share-Ready 空窗 / 串行** |
| **编码 Kickoff** | — | — | **批准 W0a；W0b 按挡门矩阵** |
