# 敢发净化 V1 · 验收清单

| 属性 | 内容 |
|------|------|
| **对应 PRD** | [PRD-SHARE-FACE-PURITY-V1.md](./PRD-SHARE-FACE-PURITY-V1.md) **v0.1.1** |
| **评审纪要** | [acceptance-records/share-face-purity-v1-review-2026-07-24.md](./acceptance-records/share-face-purity-v1-review-2026-07-24.md) · Conditional Go |
| **实施清单** | [IMPLEMENTATION-SHARE-FACE-PURITY-V1.md](./IMPLEMENTATION-SHARE-FACE-PURITY-V1.md) |
| **手测狗粮** | [share-face-purity-v1-dogfood-CHECKLIST.md](./acceptance-records/share-face-purity-v1-dogfood-CHECKLIST.md) |
| **线框** | [wireframes/share-face-purity-v1-wireframe.html](./wireframes/share-face-purity-v1-wireframe.html) · F1–F5 |
| **试用底稿** | [persona-feedback-trial-2026-07-24.md](./acceptance-records/persona-feedback-trial-2026-07-24.md) |
| **状态** | **W0–W2 工程已合入** · W3 真人门待签 |
| **日期** | 2026-07-24 |

> **验收原则**
>
> 1. 环境：Windows · Studio · Chrome/Edge。  
> 2. W0 / W1 / W2 分门挡；**W0 ≠ 主题完成**。  
> 3. **不**验收 AI 文案 / Key（NAS）。  
> 4. 手测「产品」列须非实现者勾选。  
> 5. 完成宣布前：真人 N≥5（建议含 U1 / U4 / U7）。

---

## 1. 里程碑完成度

| 里程碑 | 文档 | 编码 | 说明 |
|--------|------|------|------|
| **PRD + 线框 F1–F3** | ✅ | — | 2026-07-24 签核 |
| **W0** | ✅ | ✅ | 章名/题名/图注/互斥/migrate/校验 |
| **W1** | ✅ | ✅ | 章序 SSOT · 「可重排」 |
| **W2** | ✅ | ✅ | 小红书文案包入口 · fixture/狗粮 |
| **W3** | ✅ 清单 | ⏳ | Persona 复测 + 真人 N≥5 |

---

## 2. W0 · AC-SFP

| ID | 标准 | 方法 | 工程 | 产品手测 |
|----|------|------|------|----------|
| **AC-SFP-01** | 读者面章名不匹配序号腔 | 单测 + 刷新/重导 | ✅ | ⏳ |
| **AC-SFP-02** | 脏日期 displayTitle → 体面名 | 单测 + 打开预览 migrate | ✅ | ⏳ |
| **AC-SFP-03** | 回声 caption 读者面/长图为空 | 单测 share_face_copy | ✅ | ⏳ |
| **AC-SFP-06** | 开分章 → 点 × 不被导出 caret 挡 | 源码契约 + 手测 | ✅ | ⏳ |
| **USR-SFP-04** | 手改章名/题名不被 migrate 覆盖 | 负例单测 | ✅ | ⏳ |

---

## 3. W1 · AC-SFP

| ID | 标准 | 方法 | 工程 | 产品手测 |
|----|------|------|------|----------|
| **AC-SFP-04** | 跨年/乱序 segment → 章序时间单调 | `sort_chapters_by_temporal_key` 单测 | ✅ | ⏳ |
| **AC-SFP-05** | 用户面无「可更新」主词；算法态「可重排」+ tooltip | shelf/bento/help 契约 | ✅ | ⏳ |

---

## 4. W2 · AC-SFP

| ID | 标准 | 方法 | 工程 | 产品手测 |
|----|------|------|------|----------|
| **AC-SFP-07** | 小红书：设置内或成功面可复制文案包；无 AI 时 topics 非空 | export panel + task-dock | ✅ | ⏳ |
| **AC-SFP-08** | NAS：默认面无 AI 文案配置入口 | 既有 NAS 回归 | ✅ | ⏳ |

---

## 5. 主题完成门（W3）

| ID | 标准 | 状态 |
|----|------|------|
| **AC-SFP-W3-01** | 存量书架抽检章名零「·二/·三」 | ⏳ |
| **AC-SFP-W3-02** | Persona Agent 复测 E2–E8（除 AI）关闭或降 P2 | ⏳ |
| **AC-SFP-W3-03** | 真人 N≥5 签核 | ⏳ |
