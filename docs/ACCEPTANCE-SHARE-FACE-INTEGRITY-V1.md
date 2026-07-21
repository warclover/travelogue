# 敢发面一致性 V1 · 验收清单

| 属性 | 内容 |
|------|------|
| **对应 PRD** | [PRD-SHARE-FACE-INTEGRITY-V1.md](./PRD-SHARE-FACE-INTEGRITY-V1.md) **v0.2.0** |
| **评审纪要** | [跨职能](./acceptance-records/share-face-integrity-v1-review-2026-07-21.md) · Conditional Go · BLK-SFI-01～10 |
| **实施清单** | [IMPLEMENTATION-SHARE-FACE-INTEGRITY-V1.md](./IMPLEMENTATION-SHARE-FACE-INTEGRITY-V1.md) |
| **手测狗粮** | [share-face-integrity-v1-dogfood-CHECKLIST.md](./acceptance-records/share-face-integrity-v1-dogfood-CHECKLIST.md) |
| **线框** | [wireframes/share-face-integrity-v1-wireframe.html](./wireframes/share-face-integrity-v1-wireframe.html) · F0–F5 |
| **试用底稿** | [persona-blogger-trial-2026-07-21.md](./acceptance-records/persona-blogger-trial-2026-07-21.md) · [persona-deep-trial-2026-07-21.md](./acceptance-records/persona-deep-trial-2026-07-21.md) |
| **状态** | **合同已定 · 工程未开工**（文档波次） |
| **日期** | 2026-07-21 |

> **验收原则**
>
> 1. 环境：Windows · Studio · Chrome/Edge；脏名 / 离群用例建议独立 `--trips-dir` 或固定样本册。  
> 2. W0 / W1 / W2 分门挡；**W0 ≠ 主题完成**。  
> 3. 本主题硬化 SFC/FST 执行层与存量兑现；**不**重验 Recipe / 意图卡全案（见非回归）。  
> 4. 手测「产品」列须 **非实现者** 勾选。  
> 5. 对外宣布完成前：真人 N≥5（AC-SFI-15 · 观察法协议）。  
> 6. AC-SFI-11：先**前置核验** FST W0 忙碌态是否已落地；未落地则标跨主题阻塞，禁止空转打勾。

---

## 1. 里程碑完成度

| 里程碑 | 文档 | 编码 | 说明 |
|--------|------|------|------|
| **PRD + AC + IMPL + 线框** | ✅ 2026-07-21 | — | Doc 包 |
| **跨职能评审 + BLK 回写** | ✅ 2026-07-21 | — | Conditional Go · PRD v0.2.0 |
| **W0** | ✅ 合同 | ⏳ | 过滤 · 重渲 · 命名 · 调试串 |
| **W1** | ✅ 合同 | ⏳ | 刷新 · 离群 · 分章行内改名 |
| **W2** | ✅ 合同 | ⏳ | 可砍 · 须真实册归因 |
| **完成宣布** | ✅ 合同 | ⏳ | AC-SFI-15 |

---

## 2. W0 · AC-SFI（不出糗）

| ID | 标准 | 方法 | 工程 | 产品手测 |
|----|------|------|------|----------|
| **AC-SFI-01** | 样本 13 册重渲后读者面禁入句命中 = 0（含 decorLine：「白天，傍晚」「示例游记」） | 自动抽检脚本 + 手测 F0/F-share | ⏳ | ⏳ |
| **AC-SFI-02** | 武大用例：封面 / 书架 / FirstSuccess / 导出文件名四处一致且无裸 `--`；zip 文件名无 `trip-{id}` | 重渲后对照 + 导出落盘核验 | ⏳ | ⏳ |
| **AC-SFI-03** | 精修态无 `Plate` / `screen-*`（非 `?debug=1`） | 手测 F0 | ⏳ | ⏳ |
| **AC-SFI-04** | 题名复读图注抑制后空渐变条不渲染；导出/截图态零 inline-edit 占位 | DOM/长图抽检 + 手测 | ⏳ | ⏳ |
| **AC-SFI-10** | 回归：SFC AC-SFC-01/03/07；stale 主词仅「分享图需更新」；C7 → AC-SFC-11（无 Key 无「杂志文案已完成」） | 既有 SFC 契约 + 手测 | ⏳ | ⏳ |
| **AC-SFI-11** | 导入忙碌态：前置核验 FST W0；若未落地 → 跨主题阻塞（不可空转 ✅） | 打开 FST AC 状态表 + 手测导入 | ⏳ | ⏳ |

### W0 非回归

| ID | 标准 | 方法 | 工程 |
|----|------|------|------|
| **AC-SFI-NR-01** | Ambiguous 意图卡三选一仍可用 | 手测中册 | ⏳ |
| **AC-SFI-NR-02** | Narrative「按章导出」CTA 仍可用 | 手测大册 | ⏳ |
| **AC-SFI-NR-03** | 不新建第四套进度/成功面栈 | 代码审查：复用 Dock | ⏳ |
| **AC-SFI-NR-04** | 分支 D（九宫格/海报）无文案过滤器误伤 | 导出九宫格/海报冒烟 | ⏳ |

---

## 3. W1 · AC-SFI（兑现承诺）

| ID | 标准 | 方法 | 工程 | 产品手测 |
|----|------|------|------|----------|
| **AC-SFI-05** | Key 就绪 + stub 命中：dock 提示条符合纪律（非模态、不遮 CTA、导出/成功面不出、册级 dismiss）；刷新后禁入句 = 0；`origin=user` 不变；章名非 LLM invent；无并列第二刷新按钮 | 手测 F1·F2 + 单测 | 🔧 | ⏳ |
| **AC-SFI-06** | 仙本那：离群段不被小桶合并回灌；章名无「2018–2020」；附录/降权规则生效 | fixture 重 curate + 手测 F3 | ✅ QA-SFI-04 | ⏳ |
| **AC-SFI-07** | 武大：`dateConfidence=low` 读者面无绝对年份「2015」；决定性瞬间不选离群 | 重渲/重 curate + 手测 | ✅ QA-SFI-04 | ⏳ |
| **AC-SFI-08** | 分章行内改名可用；按钮为「重新分章」；解释句含日期重叠说明；无跳转闪跳 | 手测 F3 | 🔧 FE 已接 | ⏳ |
| **AC-SFI-09** | 附录知情：章头「往年 · 旧照 · N 张」· 分章列出原因 · 可移回 · 导出未含时显性提示可勾 | 手测 F3 · 导出设置 | 🔧 FE/BE 已接 | ⏳ |

---

## 4. W2 · AC-SFI（可砍）

| ID | 标准 | 方法 | 工程 | 产品手测 |
|----|------|------|------|----------|
| **AC-SFI-12** | 紧凑档前置：真实照片册归因表已签；非照片纵向像素占比较默认下降 ≥40%（脚本）∧ 5 席盲评敢发偏好 ≥3/5 | 归因附件 + 脚本 + 盲评表 | ⏳ | ⏳ |
| **AC-SFI-13** | 署名三态同时驱动辑封与长图尾；清晰度参数与产物一致；小红书文案包可复制（无 Key = 标题+话题） | 手测 F4·F5 | ⏳ | ⏳ |

---

## 5. 主题完成门

| ID | 标准 | 方法 | 通过 |
|----|------|------|------|
| **AC-SFI-15** | 真人 N≥5；真实输入；样本达 Completed；配比 ≥2×U1 · ≥1×U5 · ≥1×F1/F2；有 Key ≥2 · 无 Key ≥1；观察法「修破绽型」手改事件为零 ≥3/5 ∧ 「敢原样发」肯定 ≥3/5 | [狗粮 CHECKLIST](./acceptance-records/share-face-integrity-v1-dogfood-CHECKLIST.md) 非实现者签字 | ⏳ |

---

## 6. Fixture（必锁）

| Fixture ID | 输入 / 场景 | 期望 |
|------------|-------------|------|
| **FX-SFI-01** | 武大册 `demo-e863ec0da9`（脏名 + 弱枚举 decorLine + low 置信日期） | 重渲后封面无 `--`；无「白天，傍晚」；无「2015」绝对年份 |
| **FX-SFI-02** | 京都示例 `demo-album` 章名含「示例游记」 | 读者面无「示例游记」；编辑面可标「不成片」或已清洗 |
| **FX-SFI-03** | 仙本那 `demo-1d4f92d534`（seg 含 2020-11-30 单张） | 章名无「2018–2020」；离群不并回 |
| **FX-SFI-04** | 导出长图 / zip | 文件名 = 展示名规则；无 `demo-*-longshot` / `trip-{id}.zip` |
| **FX-SFI-05** | 用户手改杂志名后刷新文案 | 杂志名不变；stub 字段被替换 |
| **FX-SFI-06** | 注入 2 张 > 核心跨度阈值的离群照 | ≥2 → 附录「往年 · 旧照 · N」；知情面齐全 |
| **FX-SFI-07** | `segments≥2` 年度精选型 | 不自动误隔离（豁免或确认） |

---

## 7. 手测入口

| 波次 | 线框 | 狗粮 |
|------|------|------|
| W0 | F0 | CHECKLIST §W0 |
| W1 | F1–F3 | CHECKLIST §W1 |
| W2 | F4–F5 | CHECKLIST §W2 |
| 完成门 | — | CHECKLIST §完成门 |

---

## 8. 版本记录

| 版本 | 日期 | 变更 |
|------|------|------|
| v0.1.0 | 2026-07-21 | 首版 · 对齐 PRD v0.2.0 AC-SFI-01～13·15 |
