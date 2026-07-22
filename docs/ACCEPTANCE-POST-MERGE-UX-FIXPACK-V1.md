# ACCEPTANCE · 合入后 UX 修复包 V1（PMX）

| 属性 | 内容 |
|------|------|
| **DOC-STATUS** | **active** |
| **PRD** | [PRD-POST-MERGE-UX-FIXPACK-V1.md](./PRD-POST-MERGE-UX-FIXPACK-V1.md) §9 |
| **实施** | [IMPLEMENTATION-POST-MERGE-UX-FIXPACK-V1.md](./IMPLEMENTATION-POST-MERGE-UX-FIXPACK-V1.md) |
| **走查 / 冒烟** | [acceptance-records/post-merge-ux-trial-2026-07-22.md](./acceptance-records/post-merge-ux-trial-2026-07-22.md) §5 |
| **日期** | 2026-07-22 |
| **分支** | `fix/post-merge-ux-fixpack-v1` |

---

## 0. 范围钉定

| 项 | 结论 |
|----|------|
| 示例默认名 | **京都雨季漫游**（D-PMX-01） |
| AI 文案 | 导入 stub 与 UI readiness **两维分离**（D-PMX-02） |
| 封面 | 只绑 `displayTitle`（D-PMX-03） |
| 存量武大重渲 | **不进本包**（D-PMX-06 / D7） |
| 书架重名消歧 | **Park**（P-PMX-11） |
| 精修 × | Sheet 开时 Dock `pointer-events:none`，保留返回（D-PMX-05 冒烟加固） |

---

## 1. 产品 AC（AC-PMX-*）

| ID | 验收项 | 状态 | 证据 |
|----|--------|------|------|
| **AC-PMX-01** | 再做一遍后无「示例游记」（成功面 / 封面 / title / meta） | **Pass** | 冒烟 §5.1；`trips/demo-album/trip.json` |
| **AC-PMX-02** | 展示名「京都雨季漫游」 | **Pass** | FirstSuccess · `document.title` · meta |
| **AC-PMX-03** | L1：无「配置写作引擎后可升级」；有就绪 / 重新生成 | **Pass** | 成功面 + 精修「这本」 |
| **AC-PMX-04** | L0：本机文案 + 配置引导仍可用 | **Pass** | mock `llm/status=false` 实机 |
| **AC-PMX-05** | 武大封面「武大 米娜」，无 `--` | **Pass** | `demo-e863ec0da9` DOM |
| **AC-PMX-06** | 复用卡时 Wizard 不可见；单 dialog | **Pass** | `#v2-wizard-root[hidden]` |
| **AC-PMX-07** | 精修 × 中心可点；Esc 可关 | **Pass** | 命中 `preview-sheet__close`；Esc 关 sheet |
| **AC-PMX-08** | 大册可见「按章」语义 | **Pass** | 短标签「按章导出」 |
| **AC-PMX-09** | 章名无 `（N）` / 「续」 | **Pass** | `·晚上` / `·三` |
| **AC-PMX-10** | 新渲无误导绝对年；存量不挡门 | **Pass*** | 单测 + 新渲 demo；武大存量 D7 |
| **AC-PMX-11** | `HEAD /v2` = `GET /v2` = 302 `/` | **Pass** | HTTP |
| **AC-PMX-12** | 390 预览诚实门面 | **Pass** | `preview-narrow-gate` |
| **AC-PMX-13** | 导出成功面 · 意图卡 · 设置 AI · 首页窄屏 · 人话文件名不回退 | **Pass** | 见 §2 |
| **AC-PMX-14** | 朋友圈长图连读：Dock 短标签为「导出连读」（非裸「连读」） | **Pass** | `shortCtaLabelForPlatform` + JS 单测 |

---

## 2. AC-PMX-13 回归短冒烟

| 项 | 结果 | 摘要 |
|----|------|------|
| 设置 AI 摘要 | Pass | 「已就绪 · DeepSeek」 |
| 意图卡 | Pass | 武大：`选择分享` →「这趟精选了 23 张，你想怎么发？」 |
| 小册导出成功面 | Pass | Task Dock「长图已保存」 |
| 人话文件名 | Pass | `京都雨季漫游-长图.png`（无「示例游记」） |
| 首页窄屏 gate | Pass | 390px「请在电脑浏览器打开 Studio」 |

---

## 3. 工程门禁（单测）

```powershell
python -m pytest `
  tests/unit/domain/test_title_humanize.py `
  tests/unit/curation/test_curate_chapters.py `
  tests/unit/curation/test_chapter_titles_pmx.py `
  tests/unit/curation/test_sfi_demo_regression.py `
  tests/unit/render/test_moment_exif_pmx.py `
  tests/unit/web/test_studio_home_v2.py::test_studio_home_v2_head_redirects_to_root `
  tests/unit/web/test_ftue_telemetry.py -q
```

| 套件 | 状态 |
|------|------|
| 题名禁词 / 章名 ·二·三 / moment 硬闸 / HEAD /v2 / 遥测接线 | **Pass**（2026-07-22） |

> 仓库内尚未固化独立 Playwright e2e 套件；实机证据见走查底稿 §5。合入后可再抽 `tests/e2e` 门禁。

---

## 4. 遥测（PRD §8）

| 事件 | 状态 |
|------|------|
| `ftue_demo_album_success` + `displayTitle` | **已接线** |
| `first_success_copy_branch`（`l0_degraded` / `l1_ready` / `neutral`） | **已接线** |
| `refine_copy_branch`（状态变化时） | **已接线** |
| `refine_close_click_blocked` | 可选 · 未做（修后期望 0，不挡验收） |

---

## 5. 明确不验

- 武大等存量批量重渲后的图注年  
- 书架两本「武大 米娜」消歧  
- 成功面强推「立即重新生成」旧册文案  

---

## 6. 总评

| 门 | 结论 |
|----|------|
| M1 | **Go** |
| M2 | **Go** |
| M3 | **Go** |
| 全包 | **敢合**（Conditional Go 合同项已兑现） |
