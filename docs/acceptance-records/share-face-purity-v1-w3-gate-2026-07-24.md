# Share-Face Purity V1 · W3 完成门底稿

| 属性 | 内容 |
|------|------|
| **对应** | [ACCEPTANCE-SHARE-FACE-PURITY-V1.md](../ACCEPTANCE-SHARE-FACE-PURITY-V1.md) §5 |
| **日期** | 2026-07-24 |
| **状态** | 🟡 工程侧完成 · 真人 N≥5 待签 |
| **Studio** | `http://127.0.0.1:8766`（W3 抽检前已重启加载 `1f0b60c` 代码） |
| **对照试用** | [persona-feedback-trial-2026-07-24.md](./persona-feedback-trial-2026-07-24.md) · 契约 [stable-qh-persona-trial-2026-07-15.md](./stable-qh-persona-trial-2026-07-15.md) |

## 1. 存量书架抽检 · AC-SFP-W3-01

| 步骤 | 结果 |
|------|------|
| 书架册数 | **15** 本（`trip.json` 可扫）· 章 **40** |
| 打开前磁盘 | 序号腔 **8/40**（如 `5月27日 · 三`）；脏 displayTitle **0** |
| 打开路径 | 逐册 `GET /__travelogue/trips/{id}/entry`（静默 migrate + 落盘） |
| **打开后磁盘** | 序号腔 **0** · 脏 displayTitle **0** |
| 样例 | `demo-album` ch-03：`5月27日 · 三` → `5月27日`（与 ch-01 同名日期，靠章号区分） |

- [x] 打开本机书架 ≥10 本；刷新/打开预览后章名零「·二/·三」
- [x] 抽检封面题名无 `旅行 · 24 1 20` 类数字日期链

> **注**：旧 Studio 进程未加载 SFP 代码时 entry 不会清洗；W3 以重启后进程为准。

## 2. Persona Agent 复测 · AC-SFP-W3-02

复用 `scripts/stable_qh_persona_trial.py`（**5/5 PASS**，约 3.1 分钟）+ 打开后书架/entry 抽检：

| 试用 | 预期 | 结果 | 证据 |
|------|------|------|------|
| E2 序号腔章名 | 关闭 | ✅ 关闭 | 打开后 0/40；单测 `test_share_face_purity` |
| E3 脏 displayTitle | 关闭 | ✅ 关闭 | 磁盘脏 display **0**；年度册无 `旅行 · 24 1…` |
| E4 图注回声 | 关闭 | ✅ 关闭 | `demo-album` entry 章内 caption **0** 非空回声；`test_share_face_copy` |
| E5 章序穿越 | 关闭或解释 | ✅ 关闭 | `demo-3ee2727aea` 时间键 2024-01→…→2024-08→**2025-01**（跨年单调正确；非乱序） |
| E6 可更新词表 | 关闭（现「可重排」） | ✅ 关闭 | P5 `bad_vocab=0`；FE 契约无「可更新」主词 |
| E7 分章 × 被挡 | 关闭 | ✅ 关闭 | `test_sfp_chapter_panel_playwright` AC-SFP-06 PASS |
| E8 小红书文案包 | 关闭（设置内可达） | ✅ 关闭 | 导出设置 `copy-xhs-pack`；entry `shareCopyPack` 含 title/topics |
| E1/E9 AI | **排除**（NAS） | — | 不验收 |

契约复跑明细（本轮）：

| 画像 | 结果 |
|------|------|
| P1–P5 | ✅ 全 PASS · trip 例 `qhtrial-p1-da01fa` · shelf≈17 · `bad_vocab=0` |

单测补签：`test_share_face_purity` + `test_share_face_copy` + `test_sfp_w0_contracts` + AC-SFP-06 · **19 passed**。

## 3. 真人 N≥5 · AC-SFP-W3-03

> Agent 不能代签。请产品约真人按狗粮 [share-face-purity-v1-dogfood-CHECKLIST.md](./share-face-purity-v1-dogfood-CHECKLIST.md) 走 F1–F5 + 互斥。

| 席 | 角色 | 主路径（建议） | 签核 |
|----|------|----------------|------|
| **U1** | 首次导出用户 | 京都册 → 发微信群 → 看章名是否敢原样发 | ⏳ |
| **U4** | 回访 / stale 词表 | 书架徽标：「可重排」≠「可更新」；与「分享图需更新」互斥 | ⏳ |
| **U7** | 体面题名敏感 | 打开年度混拍册封面/书架题名是否体面 | ⏳ |
| **U5** | 轻度编辑 | 分章改名后刷新仍保留；× 不被导出 caret 挡 | ⏳ |
| **B1** | 小红书图文 | 导出设置内「复制文案包」· 无 AI 时标题+话题可用 | ⏳ |

**邀请句（可复制）**

> 麻烦花 8–10 分钟帮敢发净化收口签一眼：打开 Studio → 任抽 2 本旧册看章名有没有「·二/·三」、封面是不是奇怪数字日期；再走一遍导出设置里的小红书「复制文案包」。通过/踩坑回一句即可。

## 4. 门结论

| ID | 标准 | 状态 |
|----|------|------|
| **AC-SFP-W3-01** | 存量书架抽检 | ✅ 工程完成（打开后 0 序号 / 0 脏题名） |
| **AC-SFP-W3-02** | Persona E2–E8 | ✅ 关闭 |
| **AC-SFP-W3-03** | 真人 N≥5 | ⏳ 邀请表已备 · 待签 |

**主题完成宣布**：须等 §3 至少 5 席勾选后，方可把 ACCEPTANCE 主题状态改为完成。
