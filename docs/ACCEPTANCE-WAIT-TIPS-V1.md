# 导入等待教育 Wait Tips V1 · 验收清单

| 属性 | 内容 |
|------|------|
| **对应 PRD** | [PRD-WAIT-TIPS-V1.md](./PRD-WAIT-TIPS-V1.md) **v0.2.0** |
| **评审纪要** | [跨职能](./acceptance-records/wait-tips-v1-review-2026-07-17.md) · Conditional Go |
| **实施清单** | [IMPLEMENTATION-WAIT-TIPS-V1.md](./IMPLEMENTATION-WAIT-TIPS-V1.md) |
| **手测狗粮** | [wait-tips-v1-dogfood-CHECKLIST.md](./acceptance-records/wait-tips-v1-dogfood-CHECKLIST.md) |
| **线框** | [wireframes/wait-tips-v1-wireframe.html](./wireframes/wait-tips-v1-wireframe.html) · F1–F5 |
| **状态** | **W0+W1 编码已合入 · 工程契约绿 · 产品手测待填** |
| **日期** | 2026-07-17 |

> **验收原则**
>
> 1. 环境：Windows · Studio · Chrome/Edge；建议示例相册导入。  
> 2. W0 / W1 分门；**W0 ≠ 主题完成**。  
> 3. Tips **不是** Help L1；关闭不写 Help seen。  
> 4. 进度主句 / FirstSuccess 合同以 First-Session Trust 为准；本主题不得破坏。  
> 5. 手测「产品」列须 **非实现者** 勾选。

---

## 1. 里程碑完成度

| 里程碑 | 文档 | 编码 | 说明 |
|--------|------|------|------|
| **评审 + 线框 + AC/IMPL + 相邻脚注** | ✅ | — | 2026-07-17 Conditional Go |
| **W0** | ✅ 合同 | ✅ 编码 | 嵌壳 · 6 卡 · 交互 · dismiss · 埋点核心 |
| **W1** | ✅ 合同 | ✅ 编码 | 短尾抑制 · reduced-motion |
| **W2（可选）** | ✅ 合同 | ✅ 编码 | 帮助抽屉重播 |

---

## 2. W0 · AC-WT

| ID | 标准 | 方法 | 工程 | 产品手测 |
|----|------|------|------|----------|
| **AC-WT-01** | Importing 且未 dismiss 时，进度主句下方出现 Tips；主句随 stage 变且不受 Tips 影响 | 手测 F1 + 代码审查 | ✅ 挂载锚点 | ⏳ |
| **AC-WT-02** | 默认约 10s 自动切；可 ‹ › / 圆点手动切 | 手测 F3 | ✅ | ⏳ |
| **AC-WT-03** | 悬停卡片区暂停自动播；移出后继续 | 手测 | ✅ | ⏳ |
| **AC-WT-04** | × 关闭后同会话及刷新后再导均不再出现（localStorage） | 手测 + 契约 | ✅ | ⏳ |
| **AC-WT-05** | Job succeeded → Tips 已卸载；FirstSuccess 无 Tips 残留 | 手测 / 建议 e2e | ✅ unmount | ⏳ |
| **AC-WT-06** | Importing 期间无 Help L1 / 导出脉冲 / 能力卡 | 手测 + 代码审查 | ✅ 不写 Help | ⏳ |
| **AC-WT-09** | 六张字面 = PRD §4；WT-02 标题非「照片留在本机」；无「主链」、无「为的是…不是…」 | **契约单测必锁** | ✅ | — |

### W0 非回归

| ID | 标准 | 方法 |
|----|------|------|
| **AC-WT-NR-01** | FST：阶段主句 / 慢安抚 / FirstSuccess ≤1s 不回归 | 手测对照 FST dogfood F1–F2 |
| **AC-WT-NR-02** | Tips JS 失败或已 dismiss 时，进度壳仍完整可用 | 手测 F5 降级面 |
| **AC-WT-NR-03** | 不新建全屏 Tour / 独立 Modal 教育栈 | 代码审查 |

---

## 3. W1 · AC-WT

| ID | 标准 | 方法 | 工程 | 产品手测 |
|----|------|------|------|----------|
| **AC-WT-07** | 文案不含微信操作步骤、精修、工程词、杂志级承诺；不含与 stage/estimate 同义过程复述 | 契约 + 手测 | ✅ | ⏳ |
| **AC-WT-08** | `prefers-reduced-motion: reduce` 时不自动轮播 | 手测 / 单测 | ✅ | ⏳ |
| **AC-WT-10** | render 末段或短尾启发式下不再 auto-advance（D-WT-07） | 手测 / 埋点 | ✅ | ⏳ |

---

## 4. 主题完成门（编码后）

| ID | 标准 |
|----|------|
| **AC-WT-11** | W0+W1 AC 产品手测勾选完成 |
| **AC-WT-12** | 关闭率 / 平均浏览张数有一周观测记录（阈值见 PRD §2.3；不挡工程合入） |

---

## 5. 签核

| 角色 | 签名 | 日期 |
|------|------|------|
| 产品 | | |
| 交互 | | |
| 开发 | | |
| QA / 手测人（非实现者） | | |
