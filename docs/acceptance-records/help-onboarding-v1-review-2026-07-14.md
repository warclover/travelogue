# 帮助与情境引导系统 V1 · 跨职能评审会结论

| 属性 | 内容 |
|------|------|
| **会议日期** | 2026-07-14 |
| **材料** | [PRD-HELP-ONBOARDING-V1.md](../PRD-HELP-ONBOARDING-V1.md) **v1.1.0 → 已回写 v1.1.1** |
| **形式** | 跨职能评审（产品 · UI/UX · 用户体验 · 架构 · 开发 · 典型用户代表） |
| **结论状态** | **有条件通过（Conditional Go）** · **Must-Fix 已回写 PRD v1.1.1 · 可开 W0** |
| **记录人** | 产品 / UX / 工程联合纪要 |
| **前置** | 精修 V1 + 精修可用性 V1.1 Conditional Go；导出门面 V1 合同有效 |

---

## 1. 与会角色

| 角色 | 关注点 |
|------|--------|
| **产品（拍板）** | 北极星、主链是否被 FirstSuccess「保存长图」分流、W0/W1 切拍、与精修/Facade 边界 |
| **UI / UX（交互）** | 「?」入口、脉冲 tip 可见性、帮助↔精修冲突、FirstSuccess 副文案、线框 |
| **用户体验** | UX-HELP-01 可测性、认知负荷、80% 分享者不被精修/帮助打断 |
| **架构** | seen 权威、忙碌态门禁、sheet 仲裁、与现网键/CTA 冲突 |
| **开发** | 增量落点、迁移成本、W1 不含 Drawer 是否可验收 |
| **典型用户 · 分享者** | 会不会又多一层提示；发群能不能看懂 |
| **典型用户 · 编辑者** | 「完成≠更新版面」会不会再被帮助说乱 |

---

## 2. 总评（一句话）

> **方向正确、克制得当（无 tour、案 A、对齐 V1.1）；阻塞不在愿景，而在三处「合同与现网打架」：① FirstSuccess 主 CTA 现为「保存长图」可跳过验货；② 案 A tip 若仅写 aria 则明眼用户看不见；③ `exportPulseSeen` 仍有 per-trip 门禁且缺 busy 门禁 / 默认群聊 `publishGuide` 字段为空。**

**表决**：七席一致 **Conditional Go** · 附 §5 Must-Fix；**W0 完成回写后方可开 W1 编码**。

| 角色 | 表决 | 备注 |
|------|------|------|
| 产品 | Conditional Go | 必须先拍死 FirstSuccess 主链（OQ-HELP-01） |
| UI / UX | Conditional Go | 补 tip 可见性 +「?」权重 + 冲突帧线框 |
| 用户体验 | Conditional Go | W1 主门禁坚持 UX-HELP-01；反对双打扰 |
| 架构 | Conditional Go | seen 迁移与忙碌态须 W0 冻结 |
| 开发 | Conditional Go | W1 可增量；Drawer 正确在 W2 |
| 用户 · 分享者 | Conditional Go | 支持「只教长图」；怕再弹一堆 |
| 用户 · 编辑者 | Conditional Go | 支持教「完成≠更新版面」；怕和 Dock 说法不一致 |

---

## 3. 分角色意见摘要

### 3.1 产品

| 态度 | 要点 |
|------|------|
| ✅ 赞成 | 六条铁律完整；帮助=纪律不是新功能面；与精修 V1.1 / Facade 边界清楚 |
| ✅ 赞成 | W1 不强制 Coach、W2 再上「?」——切拍合理，避免大爆炸 |
| 📌 **须拍板 · FirstSuccess** | 现网 `quick_share` 主 CTA=「保存长图」（可跳过预览验货），与 PRD 主链「先验货再长图」**冲突**。二选一： |
| | **方案 A（推荐）**：主 CTA 改回「打开卷轴预览」+ T-SUCCESS-NEXT 副文案；「保存长图」降为次按钮 |
| | **方案 B**：承认跳过验货为合法主链，改写 PRD §3.2，删除倒计时接力依赖 |
| 📌 **须拍板 · 默认群聊发群句** | backend `wechat_chat` 常空 `publishGuide`；冻结客户端最低三要素兜底（已保存 / 按序发 / 打开文件夹） |
| ⚠️ 边界 | 勿借本主题做桌面安装 tour 或小程序 onboarding |
| 📌 切拍 | **W0 无新 UI 面**（合同+迁移+FirstSuccess 决策+发群句）；W1 主链触点；W2 Drawer |

### 3.2 UI / UX（交互 · 视觉）

| 态度 | 要点 |
|------|------|
| ✅ 赞成 | 案 A、忙碌态零 L1、帮助不挡 Dock「长图」命中区 |
| 🔴 **MF** | 案 A「aria **及/或** tip」含糊 → **冻结：W1 首访必须有一次性可见 tip**；aria 并行；禁止「仅 aria」过 AC-HELP-05 |
| 🔴 **MF** | FirstSuccess 副文案须与主 CTA **同卡可视区**；字重不能当脚注灰字 |
| 🔴 **MF** | 开帮助关精修面板后：chip「精修中」+ Dock「完成」须保留；**不**因开帮助清 pending |
| 🔴 **MF** | 「?」：首页+预览同源幽灵图标；**不进** Task Dock；不与金色「长图」并排抢主 |
| 🔴 **MF** | 重播文案只提长图，但会清 `refineSaveSeen` → 须改成覆盖「长图 + 精修保存说明」 |
| 🔧 SF | 窄窗帮助改底部 Sheet；pending 时 tip 避让「更新版面」；H2 标题缩短扫读 |
| 🖼 | **当前无 help 线框** → W1 前至少补 F1–F7（见 §6） |

### 3.3 用户体验

| 态度 | 要点 |
|------|------|
| ✅ 赞成 | 终点=会发微信；UX-HELP-01 作 W1 主门禁（比 70% 埋点更真） |
| ✅ 赞成 | 同时只亮一个 L1；反对脉冲+coach 双打扰 |
| ⚠️ | 自动跳转/快路径若跳过验货，分享者可能「做成了但不会验货」——与产品 FirstSuccess 拍板绑定 |
| ⚠️ | 重播若静默重置多种 tip，用户会觉得「怎么又出来了」——文案预期管理是体验债 |
| 📌 | S1 类门禁：W1 建议 N≥5；不过不标主题 Go |

### 3.4 架构

| 态度 | 要点 |
|------|------|
| ✅ 赞成 | 复用脉冲 / Task Dock / FirstSuccess / Wizard details；不引入 tour 库 |
| 🔴 **MF** | 现网 `exportPulseSeen` **含 per-trip 后缀**；与 D-HELP-07 全局技能冲突 → W0 写迁移：读兼容、写双键、**门禁只用全局** |
| 🔴 **MF** | 脉冲在 `init-v3` 一次性判定，**无 busy 门禁、无 idle 补发** → 定义 `isHelpL1Blocked()` |
| 🔴 **MF** | 默认微信群 `publishGuide=""`；Task Dock 硬编码兜底 ≠ 合同字段 → 冻结兜底 COPY |
| ⚠️ | 帮助↔精修冲突需要轻量 orchestrator（W2）；AC-15 可先写清归属 |
| 🔧 | COPY 常量集中；整理 `refineStarTipSeen` / `bookTabMigrateTipSeen` / legacy coach 键，避免第三次分裂 |

### 3.5 开发

| 态度 | 要点 |
|------|------|
| ✅ 赞成 | W1 落点清晰：`first-success.js`、`init-v3.js`/`longshot.js`、`preview-toolbar-v3-task-dock.js`、`studio-home-v2` Wizard |
| ✅ 赞成 | W2 再做 Drawer；可参考 `maybeShowRefineStarTip` 模式做 tip |
| ⚠️ | Wizard 已有「文件夹怎么选？」折叠，但四点与 AC-HELP-01 不全匹配 → W1 扩写非 greenfield |
| ⚠️ | 倒计时现网**已禁用** → PRD §3.2「≥2s」目前不可验；随 FirstSuccess 方案 A/B 改写 |
| ⏱ | W0 ~0.5–1 人日；W1 ~2–4 人日（视 FirstSuccess 改动）；W2 ~2–3 人日 |

### 3.6 典型用户

| 代表 | 态度 | 原话摘要 |
|------|------|----------|
| 分享者 | 支持 | 「只要别逼我进精修，教我点长图、告诉我怎么发群就行。」 |
| 编辑者 | 支持但紧张 | 「千万别又把『完成』说成更新版面。帮助和 Dock 必须同一套词。」 |

---

## 4. 与现网对齐的关键发现（工程核查）

| 触点 | 现网 | 对 PRD 的影响 |
|------|------|----------------|
| `exportPulseSeen` | 全局 + **per-trip** OR | 违反 D-HELP-07；W0 必须迁 |
| 脉冲时机 | init 一次性加 class | 缺 AC-HELP-13 忙碌态 |
| FirstSuccess | `quick_share`→「保存长图」；倒计时关闭 | 与 §3.2 主链/接力冲突 |
| Task Dock 发群 | 有硬编码句；`publishGuide` 常空 | AC-HELP-06 须承认客户端兜底 |
| 首页「?」 | **未实现** | 正确属 W2；勿写入 W1 Go |
| Import 文件夹支架 | Wizard 有部分 details | W1 扩写即可 |

---

## 5. Must-Fix / Should-Fix / Park（合并拍板清单）

### Must-Fix（**已回写 PRD v1.1.1** · 可开 W0）

| ID | 项 | 结论（已写入 PRD） |
|----|-----|-------------------|
| **MF-HELP-01** | FirstSuccess 主链 | **方案 A**：主 CTA=打开预览 + 副文案；次按钮「保存长图」· **D-HELP-10** |
| **MF-HELP-02** | 案 A tip 可见性 | 首访**必须**可见 tip（非仅 aria）· **D-HELP-03′** |
| **MF-HELP-03** | seen 迁移 | 全局门禁 + 双写；per-trip 只读兼容 · **D-HELP-07′** |
| **MF-HELP-04** | 默认群聊发群句 | 客户端三要素兜底 · **D-HELP-09** |
| **MF-HELP-05** | 忙碌态门禁 | `isHelpL1Blocked`；idle 可补评估 · **D-HELP-08′** |
| **MF-HELP-06** | 帮助开时精修态 | 关面板保模式；chip/完成保留；不清 pending · §5.3 |
| **MF-HELP-07** | 重播文案 | 明示重置长图引导 **与** 精修保存 hint · §5.1 |
| **MF-HELP-08** | W1 前线框 | 至少 F1–F3/F7；无线框不挡 W0，挡 W1 UI 合入 |

### Should-Fix

| ID | 项 |
|----|-----|
| **SF-HELP-01** | 窄窗帮助改底部 Sheet |
| **SF-HELP-02** | pending 与长图 tip 避让 |
| **SF-HELP-03** | COPY 常量单文件 |
| **SF-HELP-04** | H2 标题缩短；reduced-motion 静态描边规格 |
| **SF-HELP-05** | AC 增补：迁移零重复脉冲、reveal_folder 可选、默认群聊兜底句 |

### Park

| ID | 项 |
|----|-----|
| **PK-HELP-01** | Coachmark / 箭头（W2+） |
| **PK-HELP-02** | 帮助 GIF |
| **PK-HELP-03** | 「永不显示提示」总开关 |
| **PK-HELP-04** | FirstSuccess 主 CTA 改「保存长图」为唯一主路径（若未选方案 B） |
| **PK-HELP-05** | 小程序 / 安装器平行 tour |

---

## 6. 线框补帧清单（UI）

> **已出稿**：[wireframes/help-onboarding-v1-wireframe.html](../wireframes/help-onboarding-v1-wireframe.html)（F1–F10 Tab）

| 帧 | 内容 | 挡 | 线框 |
|----|------|-----|------|
| **F1** | FirstSuccess：主/次 CTA + 副文案同屏 | W1 | ✅ |
| **F2** | 预览：长图脉冲 + 一次性 tip（无 coach） | W1 | ✅ |
| **F3** | success：Task Dock publishGuide / 兜底三要素 | W1 | ✅ |
| **F4** | 首页/预览「?」位置（W2 可先占位说明） | W2 | ✅ |
| **F5** | 帮助抽屉 H1–H5 + 重播说明 | W2 | ✅ |
| **F6** | 精修开 → 点? → 面板关+帮助开（chip/完成在） | W2 | ✅ |
| **F7** | 忙碌态：无脉冲/无 tip | W1 | ✅ |
| **F8** | T-REFINE-SAVE 两行 hint | W2 | ✅ |
| **F9** | 窄窗底 Sheet | W2 | ✅ |
| **F10** | pending 与 tip 避让 | W1 建议 | ✅ |

---

## 7. 推荐发布门禁

### W0 Go

| 门禁 | 标准 |
|------|------|
| **Go** | FirstSuccess 方案 A/B 已写入 PRD；seen 迁移方案已写；默认群聊发群句合同已写；文案抽检清单就绪 |
| **No-Go** | 仍同时存在「主链必须验货」与「主 CTA=保存长图跳过验货」且无显式选择 |

### W1 Go

| 门禁 | 标准 |
|------|------|
| **Go** | AC-HELP-01～06、11～13；可见 tip；UX-HELP-01 ≥4/5；无双打扰 |
| **No-Go** | 仅 aria 无 tip；忙碌态仍弹脉冲；成功态无发群句 |

### W2 Go

| 门禁 | 标准 |
|------|------|
| **Go** | AC-HELP-07/09/10/14/15；「?」+5 条目；冲突规则手测过 |

---

## 8. 会议结语

> 帮助系统 V1 **可以有条件通过**：它把「教什么」收成纪律，而不是再堆一层 Product Tour。  
> 但若不先解开 **FirstSuccess 主 CTA** 与 **seen/发群句/可见 tip** 四件现网债务，W1 会做出「文档正确、产品拧巴」的实现。  
> **下一步：PRD v1.1.1（Must-Fix）已回写 → 补 F1–F3/F7 线框 → W0 → W1。**

| 项 | 内容 |
|----|------|
| **建议结论** | ☑ **Conditional Go** |
| **下一步** | 工程按 v1.1.1 开 W0（seen 迁移 · FirstSuccess 方案 A · 发群兜底 COPY）；线框 F1–F10 [已出](../wireframes/help-onboarding-v1-wireframe.html) |
| **确认人 / 日期** | 产品 / 2026-07-14 · **MF 已回写 v1.1.1** |

---

## 附录 · 已冻结的决策句（v1.1.1 已写入 PRD）

1. **D-HELP-03′**：W1 首访长图 = 脉冲 + **可见 tip** + aria；禁止第二 coach 层。  
2. **D-HELP-07′**：L1 门禁仅全局键；per-trip 只读兼容。  
3. **D-HELP-09**：默认微信群成功态客户端兜底发群三要素。  
4. **D-HELP-10**：FirstSuccess = **方案 A**（主 CTA=打开卷轴预览；保存长图=次按钮）。  
5. **D-HELP-08′**：忙碌态零 L1（`isHelpL1Blocked`），且 idle 后可补评估。
