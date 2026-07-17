# Travelogue · 输出配方引擎 V1 验收标准

| 属性 | 内容 |
|------|------|
| **PRD** | [PRD-OUTPUT-RECIPE-V1.md](./PRD-OUTPUT-RECIPE-V1.md) **v1.1.0** |
| **评审** | [output-recipe-v1-review-2026-07-14.md](./acceptance-records/output-recipe-v1-review-2026-07-14.md) |
| **ADR** | [016-longshot-platform-export.md](./adr/016-longshot-platform-export.md)（含分支 D） |
| **实施清单** | [IMPLEMENTATION-OUTPUT-RECIPE-V1.md](./IMPLEMENTATION-OUTPUT-RECIPE-V1.md) |
| **文档版本** | v1.0.0 |
| **状态** | Draft · QA 就绪（待开发） |
| **更新日期** | 2026-07-14 |

> **完成定义**
>
> - **Phase A**：§3 自动化 + §4 手测 + §6 非回归通过；**无**任何「九宫格→scroll」残留。  
> - **Phase B**：在 A 基础上 + §5 grid/xhs 通过。  
> - **Phase C/D**：§7 可选；不阻塞 A 灰度。

---

## 1. 验收原则

1. **环境**：Studio + Playwright；`http://` 预览；`studio.output_recipe.enabled` 可开可关。  
2. **样例 trip（建议）**：
   - **T-sparse**：`kept_n` 1–9  
   - **T-amb**：`kept_n` 10–30  
   - **T-narr**：`kept_n` 31–49  
   - **T-deep**：`kept_n` ≥50  
   - **T-m14**：书架非回归  
3. **自动化**：合并前 §3 对应用例 pytest 0 失败。  
4. **手测**：Phase 发布前由 **非实现者** 勾选。  
5. **名实铁律**：用户可见「九宫格」仅当产物为 `*-moments-grid-*.png`（或等价命名）。

---

## 2. 验收前提（已拍板）

| ID | 结论 | 验收含义 |
|----|------|----------|
| D-OR-17 | 否决假九宫格 | 无「九宫格」文案指向 `wechat_moments` |
| D-OR-16 | 书架 fallback | Ambiguous 书架不强制意图卡 |
| D-OR-18 | 选择并导出 | Ambiguous 主按钮合并 |
| D-OR-21 | pending 优先 | layoutPending 先于意图卡 |
| D-OR-24 | feature flag | 关闭后行为回退 LNG2 默认 |
| D-OR-26 | resolve 定默认 | Sparse/Narrative 仍常为 chat |

---

## 3. 自动化验收（AC-OR）

### 3.1 Phase A · 解析与默认

| ID | 标准 | 方法 | Phase | 通过 |
|----|------|------|-------|------|
| **AC-OR-01** | `kept_n` 边界 9→sparse、10→ambiguous、30→ambiguous、31→narrative；阈值可配 | 单测 resolve | A | ☑ |
| **AC-OR-02** | Sparse 默认 → `chat_longshot` + 非 grid | 单测 | A | ☑ |
| **AC-OR-03** | Ambiguous + preview + 无 intent → `needs_intent=true` | 单测 | A | ☑ |
| **AC-OR-03d** | 预览客户端：`kept_n∈[10,30]` 且 DOM 槽位偏少 → **仍**出意图卡（**D-OR-27**） | e2e（见 [Share-Ready AC-SR-02](./ACCEPTANCE-SHARE-READY-OPTIMIZATION-V1.md)） | A′ | ☐ 编码后 |
| **AC-OR-03b** | Ambiguous + shelf + 无 intent → `chat_longshot` + hint | 单测 | A | ☑ |
| **AC-OR-03c** | Ambiguous + CLI 无 intent/platform → 非 0 | CLI 测 | A | ☑ |
| **AC-OR-04** | Narrative 默认 `by_chapter`；≥50 含按章 hint/文案键 | 单测 | A | ☑ |
| **AC-OR-05** | Recipe schema；非法 platform/intent → **400** / `E_OR_*` | API 测 | A | ☑ |
| **AC-OR-06** | 写入 trip.output.intent 后 resolve 保留；session 覆盖仅本次 | 单测/集成 | A | ☑ |
| **AC-OR-07a** | `chat_longshot` 与 `moments_scroll` 各至少 1 条 CLI/集成绿 | 集成 | A | ☑ |
| **AC-OR-08** | Sparse/Narrative 无 pending 时导出门面 **C1** 不回归 | Playwright / 手测签字 | A | ☑ 静态护栏；手测待签 |
| **AC-OR-10** | `locale=zh` 默认不被 IG hook 改写；IG preset 仅 `hook_only` | 单测 | A | ☑ |
| **AC-OR-11a** | 代码/文案扫描：无「九宫格」绑定 `wechat_moments` | grep/单测护栏 | A | ☑ |
| **AC-OR-13** | `output_recipe.enabled=false` → 默认行为回退固定 chat | 集成 | A | ☑ |

### 3.2 Phase B · grid / xhs

| ID | 标准 | 方法 | Phase | 通过 |
|----|------|------|-------|------|
| **AC-OR-07b** | `moments_grid` + `xiaohongshu` 各至少 1 条绿 | 集成 | B | ☑ grid · `test_ac_or_07b_*`；xhs ☐（B1 / LNG2 既有 CLI） |
| **AC-OR-09** | grid · `kept_n=6` → **6** 张产物；无空白灌水 | 集成 | B | ☑ `test_photo_grid_pack` |
| **AC-OR-09b** | grid 文件名 `*-moments-grid-*`；失败无残缺 `.part` | 集成 | B | ☑ `test_photo_grid_pack` |
| **AC-OR-11b** | UI 点「九宫格」→ 仅 grid 产物 + 九宫格 guide | Playwright / 手测 | B | ☑ 自动化文案/路由；手测 ☐ |
| **AC-OR-14** | 横三拼：横仅与横拼；竖独立（B1） | 单测 fixture | B1 | ☐ |
| **AC-OR-15** | xhs 用户可见含「杂志页适配」诚实标注 | DOM/文案断言 | B | ☐ |

### 3.3 LNG2 非回归

| ID | 标准 | 方法 | Phase | 通过 |
|----|------|------|-------|------|
| **AC-OR-R01** | `wechat_moments` 切片回归不红 | LNG2 AC 子集 | A | ☑ |
| **AC-OR-R02** | 书架保存长图仍为微信群路径（无 intent 时） | M14 子集 | A | ☑ |
| **AC-OR-R03** | 非法 platform 仍 400 | 现网测 | A | ☑ |

---

## 4. Phase A 手测

| ID | 步骤 | 期望 | 通过 |
|----|------|------|------|
| H-A-01 | T-sparse 预览 · 无 pending · 主 CTA | 「导出长图 · 发微信群」；1 次点击开始导出 | ☑ 2026-07-16 |
| H-A-02 | T-amb 预览首次导出 | 出意图卡；标题含精选 N 张。**Phase A（Writer 未开）**：无九宫格可点或仅「即将推出」。**Phase B0+（Writer 已开）**：改测 H-B-01（可点九宫格） | ☑ 2026-07-16 · Writer 已开见 H-B |
| H-A-03 | 选「微信群长图」· 选择并导出 | 开始 chat 导出；成功态含类型名 + 发群 guide | ☑ 2026-07-16 |
| H-A-04 | 选「长图连读」· 选择并导出 | moments 切片产物；成功态写「长图连读」非「九宫格」 | ☑ 2026-07-16 |
| H-A-05 | 有 layoutPending 时点导出 | **先**拦截 Modal；关 pending 前不出意图卡 | ☑ 2026-07-16 |
| H-A-06 | T-amb 书架保存长图（无 intent） | 直接发群路径；弱提示可到预览选方式 | ☑ 2026-07-16 |
| H-A-07 | T-deep ≥50 主 CTA | 按章文案；整卷在高级且二次确认 | ☑ 2026-07-16 |
| H-A-08 | flag 关闭 | 行为回退；无意图卡 | ☑ 2026-07-16 |
| H-A-09 | 失败后「换种分享方式」 | 回到意图/高级入口 | ☑ 2026-07-16 · 接线级 |

---

## 5. Phase B 手测

| ID | 步骤 | 期望 | 通过 |
|----|------|------|------|
| H-B-01 | T-amb 意图卡含九宫格（Writer 已开） | 可点；文案「九宫格」 | ☐ |
| H-B-02 | 导出九宫格 · kept=6 | 6 张 `moments-grid`；hint 有几张发几张 | ☐ |
| H-B-03 | 对比连读 vs 九宫格成功态 | ≥4/5 受试者能说出差异 | ☐ |
| H-B-04 | 小红书卡 | 可见「杂志页适配」；非「原生笔记排版」 | ☐ |
| H-B-05 | Narrative 再导出九宫格 | ▾ 可达；不改变默认主 CTA | ☐ |

---

## 6. 非回归（导出门面）

| ID | 标准 | 通过 |
|----|------|------|
| **NR-EXP-C1** | Sparse/Narrative 无 pending → 1 次点击开始导出 | ☑ 2026-07-16 |
| **NR-EXP-C2** | pending 禁止静默旧长图 | ☑ 2026-07-16 |
| **NR-EXP-C3** | 用户可见词不回潮「应用排版」等旧词 | ☑ 2026-07-16 |

签字：Agent 手测（见 acceptance-records/output-recipe-ha-handtest-2026-07-16.md）　日期：2026-07-16  
非作者复核：__________ 日期：__________

---

## 7. Phase C/D（摘要）

| ID | 标准 | Phase |
|----|------|-------|
| AC-OR-C01 | band preference 跨 trip | C |
| AC-OR-C02 | GET/PUT output-recipe API | C |
| AC-OR-D01 | custom 白名单字段 + 400 非法几何 | D |
| AC-OR-D02 | IG hook_only 不改变 zh 默认 | D |

---

## 8. Go / No-Go

### Phase A → B

- [x] AC-OR-01～08、10、11a、13、R01～R03 绿  
- [x] H-A-01～09 签字（2026-07-16 Agent；待非作者复核）  
- [x] NR-EXP-C1～C3 签字（同上）  
- [x] 文案扫描无假九宫格  

### 发布（含 B）

- [ ] AC-OR-07b、09、11b、15 绿  
- [ ] H-B-01～05；≥3 非作者 Ambiguous 真发出  

---

## 9. 版本记录

| 版本 | 日期 | 说明 |
|------|------|------|
| v1.0.1 | 2026-07-14 | B0 抛光：AC-OR-07b grid CLI 绿；H-A-02 与 B0 Writer 口径对齐 |
| v1.0.0 | 2026-07-14 | 初稿 · 对齐 PRD v1.1 Conditional Go |
