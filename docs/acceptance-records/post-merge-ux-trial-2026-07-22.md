# 合入后完整 UX 走查 · 2026-07-22

| 属性 | 内容 |
|------|------|
| **Studio** | `http://127.0.0.1:8766` |
| **HEAD** | `master` @ `3efc0ed`（PR #16 CSC · PR #17 SFI） |
| **方式** | Playwright 实机 · 按真实用户高频路径 |
| **样片** | `demo-album` · `demo-e863ec0da9` · `demo-815dc906d3` · 书架 14 本 |
| **性质** | Agent 模拟联评 + 工程狗粮；不能替代真人 N≥5 |
| **修复合同** | [PRD-POST-MERGE-UX-FIXPACK-V1.md](../PRD-POST-MERGE-UX-FIXPACK-V1.md) |

---

## 1. 一句话结论

> **主链路敢用**（导入 → 预览 → 意图卡/发群 → 导出成功面 → 设置/窄屏 gate）在合入后实测成立；**敢发内容层与两处交互摩擦仍破**——示例重做写出「示例游记」、Key 就绪仍提示配置引擎、封面脏名半修好，以及 Wizard 叠层 / 精修 × 点不到。

---

## 2. 通过项（摘要）

| # | 项 | 结果 |
|---|----|------|
| 1 | 首页 v2 双预览 + 书架 | Pass |
| 2 | 导入忙碌壳阶段句 + Wait Tips | Pass |
| 3 | 小册「发微信群」真实导出 + 人话文件名 | Pass（`京都雨季漫游-长图.png`） |
| 4 | 中册「选择分享」意图卡 | Pass |
| 5 | 导出设置五目标 + 改选诚实 + 长图密度 | Pass |
| 6 | 窄屏首页 gate | Pass |
| 7 | 设置 AI「已就绪 · DeepSeek」 | Pass |
| 8 | 精修「照片类型」；无 Plate | Pass |
| 9 | `GET /` · `GET /v2`→302 · `GET /classic` | Pass |

---

## 3. 缺陷账本（→ PRD P-PMX）

| 走查 | PRD | 严重度 | 摘要 |
|------|-----|--------|------|
| T1 | P-PMX-01 | P0 | 示例再做一遍 →「示例游记」 |
| T2 | P-PMX-02 | P0 | Key 就绪仍「配置写作引擎」 |
| T3 | P-PMX-03 | P0 | 封面 `武大--米娜` / 书架 `武大 米娜` |
| T4 | P-PMX-04 | P1 | Wizard + 复用卡叠层 |
| T5 | P-PMX-05 | P1 | 精修 × 被工具栏拦截 |
| T6 | P-PMX-06 | P1 | 图注露出 2015 离群年 |
| T7 | P-PMX-07 | P1 | 章名 `5月27日（3）` |
| T8 | P-PMX-11 | P2 | 书架两本武大（Park） |
| T9 | P-PMX-09 | P2 | `HEAD /v2` 404 |
| T10 | P-PMX-08 | P2 | 大册 CTA 可见文案缺「按章」 |
| T11 | P-PMX-10 | P2 | 预览窄屏近黑屏 |

---

## 4. 环境注记

- 走查中曾重启 Studio 以加载最新路由；`GET /v2` 302 在现行代码成立。  
- 本地截图 `qa-full-*.png` 为走查产物，默认不入库。  
- AI：`llmAvailable=true` · provider DeepSeek · model `deepseek-chat`。

---

## 5. PMX 修复包实机冒烟 · 同日复测

| 属性 | 内容 |
|------|------|
| **分支** | `fix/post-merge-ux-fixpack-v1` |
| **Studio** | `http://127.0.0.1:8766`（干净重启后） |
| **方式** | Playwright 实机 |
| **截图** | `qa-pmx-first-success.png` · `qa-pmx-wuda-cover.png` · `qa-pmx-narrow-gate.png` · `qa-pmx-home-narrow.png` |

### 5.1 AC 结果

| AC | 结果 | 证据摘要 |
|----|------|----------|
| **AC-PMX-01/02** | **Pass** | FirstSuccess：`《京都雨季漫游》已生成 · 照片 6 张`；`trip.json` meta.title/displayTitle=`京都雨季漫游`；`document.title` 同 |
| **AC-PMX-03** | **Pass** | `llmAvailable=true`；成功面与精修「这本」均为「AI 文案已就绪…重新生成」；无「配置写作引擎」 |
| **AC-PMX-04** | **Pass** | mock `llmAvailable=false`：成功面「本机文案；配置写作引擎…」；精修「这本」同；无「AI 文案已就绪」 |
| **AC-PMX-05** | **Pass** | `demo-e863ec0da9` 封面/标题=`武大 米娜`；DOM 无 `武大--米娜`；`entry.displayTitle` 人话 |
| **AC-PMX-06** | **Pass** | 复用卡时 `#v2-wizard-root[hidden]`；仅 `studio__modal` 一个可见 dialog |
| **AC-PMX-07** | **Pass**（冒烟中加固） | Dock `pointer-events:none`（保留返回）后 × 可点；Esc 关 sheet |
| **AC-PMX-08** | **Pass** | 大册可见短标签「按章导出」；`aria-label`=`按章导出长图 · 发微信群` |
| **AC-PMX-09** | **Pass** | 章名：`5月27日` / `5月27日 · 晚上` / `5月27日 · 三`；无 `（N）`/「续」 |
| **AC-PMX-10** | **Pass*** | 新渲 `demo-album` HTML 无 `2015`；`demo-e863ec0da9` 存量仍可含 `2015`（**D7 接受**） |
| **AC-PMX-11** | **Pass** | `HEAD /v2` → 302 `Location: /`（与 GET 一致） |
| **AC-PMX-12** | **Pass** | 390×844 预览出现诚实门面（返回首页制作 / 复制地址） |
| **AC-PMX-13** | **Pass** | 设置「已就绪 · DeepSeek」；武大意图卡；小册「长图已保存」；文件 `京都雨季漫游-长图.png`；首页窄屏未回退 |

### 5.2 冒烟结论

> **敢合**：AC-PMX-01～13 实机成立（含 L0 mock 与回归短冒烟）。正式合同见 [ACCEPTANCE-POST-MERGE-UX-FIXPACK-V1.md](../ACCEPTANCE-POST-MERGE-UX-FIXPACK-V1.md)。
