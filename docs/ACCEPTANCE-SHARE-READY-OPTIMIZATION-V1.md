# 敢发闭环优化 V1 · 验收清单

| 属性 | 内容 |
|------|------|
| **对应 PRD** | [PRD-SHARE-READY-OPTIMIZATION-V1.md](./PRD-SHARE-READY-OPTIMIZATION-V1.md) **v1.0.2** |
| **评审纪要** | [跨职能](./acceptance-records/share-ready-optimization-v1-review-2026-07-17.md) · [用户联席](./acceptance-records/share-ready-optimization-v1-user-panel-2026-07-17.md) · Conditional Go |
| **实施清单** | [IMPLEMENTATION-SHARE-READY-OPTIMIZATION-V1.md](./IMPLEMENTATION-SHARE-READY-OPTIMIZATION-V1.md) |
| **线框** | [wireframes/share-ready-optimization-v1-wireframe.html](./wireframes/share-ready-optimization-v1-wireframe.html) · F1–F6（v1.0.2 USR 增补） |
| **状态** | Draft · W0–W2 工程已落地（`feat/share-ready-optimization-v1-w0`）；产品手测待签 |
| **日期** | 2026-07-17 |

> **验收原则**
>
> 1. 环境：Windows · Studio · `studio.output_recipe.enabled: true`（测 Ambiguous 时）。  
> 2. W0 / W1 / W2 分门挡；**W0 ≠ 主题完成**。  
> 3. 成功面 AC 与 FTUE W1 **联合签字**（合同所有者 = FTUE + Help）。  
> 4. 手测「产品」列须 **非实现者** 勾选（对齐 Output Recipe 先例）。

---

## 1. 里程碑完成度

| 里程碑 | 文档 | 编码 | 说明 |
|--------|------|------|------|
| **评审 + 线框 + AC/IMPL** | ✅ | — | 2026-07-17 |
| **W0** | ✅ 合同 | ✅ 工程 | showcase · kept_n 同源 · 泄漏 · e2e；**产品手测待签** |
| **W1** | ✅ 合同 | ✅ 工程 | CTA · 进度 · 成功面联合挡门；**产品手测待签** |
| **W2** | ✅ 合同 | ✅ 工程 | stub 敢发门槛 · 书架降噪；**产品手测待签** |

---

## 2. W0 · AC-SR（自动化 + 手测）

| ID | 标准 | 方法 | 工程 | 产品手测 |
|----|------|------|------|----------|
| **AC-SR-01** | 首页 carousel/phone 关键帧 `naturalWidth≥200`；默认路径无黑 PLACEHOLDER | DOM/手测 F1 | ✅ e2e | ⏳ |
| **AC-SR-01b** | 样品区有持久可见「示例」徽标/标签（USR-04） | 手测 F1 | ✅ e2e | ⏳ |
| **AC-SR-02** | `kept_n∈[10,30]` 且 DOM 槽位人为偏少 → 仍出意图卡；hint 数字=服务端（文案无 kept_n） | **e2e 必锁** + 手测 F2 | ✅ | ⏳ |
| **AC-SR-03** | Ambiguous · 无 session intent · 三选一；**微信群长图**为 primary；取消不导出 | Playwright / 手测 | ✅ persona | ⏳ |
| **AC-SR-04** | UI Band/`needs_intent` 与 `GET /__travelogue/output-recipe` 一致 | 集成/手测 | ✅ FE 接线 | ⏳ |
| **AC-SR-05** | stale 且无 intent ·「重新导出」仍出意图或「换种分享」 | 手测 F3 | ✅ 同门 | ⏳ |
| **AC-SR-06** | 版心无 §4.4 工程/省略/说明书禁止项 | DOM 扫描 + 手测 F6 | ✅ CSS/JS | ⏳ |
| **AC-SR-07** | `?share=1` 无精修工程 tip、无 §4.4 泄漏 | 手测 | ✅ CSS | ⏳ |
| **AC-SR-15** | 首页/预览/意图卡/进度可见文本无 §4.6 工程词（USR-01） | 禁词扫描 + 手测 | ✅ 意图卡 | ⏳ |

### W0 非回归

| ID | 标准 | 方法 | 工程 |
|----|------|------|------|
| **AC-SR-NR-01** | Output Recipe persona e2e 8/8 | pytest | ⏳ |
| **AC-SR-NR-02** | 可见「九宫格」⇒ grid 产物（名实） | 既有护栏 | ⏳ |
| **AC-SR-NR-03** | 零精修可导出（UX-P5-80-01） | 回归 | ⏳ |

---

## 3. W1 · AC-SR

| ID | 标准 | 方法 | 工程 | 产品手测 |
|----|------|------|------|----------|
| **AC-SR-08** | Sparse Dock 可见文案含「微信」或完整 `cta_label`（缩短形允许「发微信群」） | 手测 F4 | ✅ | ⏳ |
| **AC-SR-09** | 导出成功 → 发群主句第一可读行；≥3s 或可找回 | 手测 F5 · **联合 FTUE** | ✅ 复用 Help | ⏳ |
| **AC-SR-09b** | 成功面动作区可点「换种分享方式」（USR-03） | 手测 F5 | ✅ | ⏳ |
| **AC-SR-10** | 「在文件夹中显示」可定位 PNG | 手测 | ✅ 既有 | ⏳ |
| **AC-SR-11** | 进度第一行匹配人话；无孤立「正在打开浏览器…」作唯一主句 | 手测 F5 | ✅ | ⏳ |
| **AC-SR-R01** | 文内「保存长图」无脉冲/无 tip | 手测 | ✅ tertiary | ⏳ |

**降级 COPY（BLK-05）**：recipe API 失败 toast 唯一句：

> 暂时按微信群长图导出，可稍后重试选分享方式。

| ID | 标准 | 方法 | 通过 |
|----|------|------|------|
| **AC-SR-11b** | 模拟 recipe 失败 → 出现上述 toast（或等价）且可继续/明确取消 | 手测/单测 | ✅ W0 接线 |

---

## 4. W2 · AC-SR

| ID | 标准 | 方法 | 工程 | 产品手测 |
|----|------|------|------|----------|
| **AC-SR-12** | L0 stub hook 不匹配「关于…的 N 天」「N 张照片汇成」；可空 | 单测 + 手测 | ✅ | ⏳ |
| **AC-SR-13** | 无地理信号不强行「旅途」支撑「1 个地方」仪式 | 手测 | ✅ | ⏳ |
| **AC-SR-14** | 书架主标题可读；「模板已锁定」不抢主行 | 手测 | ✅ | ⏳ |
| **AC-SR-NR-04** | 默认中文预览无海外 IG 主 CTA | 手测/DOM | ✅ 未改 IG | ⏳ |

---

## 5. 手测脚本（编码后）

### 5.1 环境

```powershell
cd C:\Users\xiafe\Projects\travelogue
# 确认 config.yaml: studio.output_recipe.enabled: true
python -m travelogue studio --port 8766
```

浏览器桌面视口 ≥1280×720；必要时清该 origin 的 session intent。

### 5.2 步骤

| 步 | 操作 | 期望 | 线框 |
|----|------|------|------|
| 1 | 打开 `/` | 样品非黑屏 | F1 |
| 2 | 打开 Ambiguous trip（如 `ha-amb-18`）点长图 | 意图卡 · N=服务端 | F2 |
| 3 | 取消意图卡 | 不导出 | F2 |
| 4 | stale 行程点重新导出 | 仍可问怎么发 | F3 |
| 5 | Sparse 看 Dock | 「发微信群」语义 | F4 |
| 6 | 导出至成功 | 进度人话 + 发群句 | F5 |
| 7 | 扫封面；开精修对比 | 版心无泄漏；精修内可有 tip | F6 |

---

## 6. Go / No-Go

| 门 | Go | No-Go |
|----|-----|-------|
| **W0** | AC-SR-01～07 · 01b · 15 + NR-01～03 绿；F1/F2/F3/F6 对照 | 意图卡仍被 DOM 跳过；首页仍黑 PLACEHOLDER；用户面见 kept_n |
| **W1** | AC-SR-08～11 · 09b / R01；FTUE 成功面同绿 | 成功面闪过无发群；无「换种分享」；CTA 仍只见「长图」 |
| **主题对外宣布完成** | W0+W1+W2 + **真人 N≥5**（U1/U2/U5 · USR-06） | Agent 联评不可替代；未做海外 IG **不**阻塞 |

---

## 7. 签字

| 项 | 负责人 | 日期 | 结论 |
|----|--------|------|------|
| 文档/AC 齐备 | Agent | 2026-07-17 | ✅ |
| W0 编码 | Agent | 2026-07-17 | ✅ `feat/share-ready-optimization-v1-w0` |
| W1 编码 | Agent | 2026-07-17 | ✅ 同上分支 |
| W2 编码 | Agent | 2026-07-17 | ✅ 同上分支 |
| W0 产品手测（非作者） | — | — | ⏳ |
| W1 联合 FTUE | — | — | ⏳ |
| W2 产品手测 | — | — | ⏳ |
| 主题对外宣布完成 | — | — | ⏳ 须真人 N≥5（§6） |
