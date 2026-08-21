# IMPLEMENTATION · 作品集成册双管线 PFM V1

| 属性 | 内容 |
|------|------|
| **PRD** | [PRD-PORTFOLIO-FOLIO-MODE-V1.md](./PRD-PORTFOLIO-FOLIO-MODE-V1.md) **v0.2.0** |
| **验收** | [ACCEPTANCE-PORTFOLIO-FOLIO-MODE-V1.md](./ACCEPTANCE-PORTFOLIO-FOLIO-MODE-V1.md) |
| **DOC-STATUS** | **active** |
| **分支** | `feat/pfm-portfolio-folio-mode-v1` |
| **状态** | **W0–W3 编码已清** · ISO-04/06 已关 · **AS-PFM-03 已升格 · 五档入库**（后继 [MSP](./acceptance-records/pfm-as-pfm-03-msp-promote-2026-08-21.md)）· W4 狗粮协议已锁、人评未开 · 首页次链仍关 |
| **更新日期** | 2026-08-21 |

---

## 0. 实施原则

1. **默认关旗 ≡ 现网 GA。** 导入两击、Dock「导出长图」、LVP 两卡零改。
2. **身份是 `trip.studio.edition`，不是第三引擎。** `layoutEngine` 仍只有 `legacy` / `screens`。禁止 `folio` / `surface` 作存储标识符。
3. **游记不写 `studio.edition`。** 缺省即 journal。
4. **无正式系列不得称作品集。** 空目录 → `E_PORTFOLIO_UNAVAILABLE`，禁止静默掉回 journal 却仍标作品集。
5. **引擎不读** `docs/templates/reserve/`。P0 `magazine-16-standard` 已入库。工坊脸经编译器写成 LTE `page-*.yaml`（运行时只读 `layout_templates/templates/`）。

---

## 1. 波次任务卡

### W0 · 命名 / schema / flag

| ID | 任务 | 状态 |
|----|------|------|
| BE-PFM-01 | 父开关 `studio.portfolio_pipeline` 默认全关 | **Done** |
| BE-PFM-02 | trip schema：`edition` / `portfolio` / `copyOrphans`；不动 `layoutEngine` | **Done** |
| BE-PFM-03 | import payload 接受 `edition`；关旗 409 | **Done** |
| FE-PFM-01 | Wizard Step 2 身份分段 DOM（默认 hidden） | **Done**（关旗不露） |
| FE-PFM-02 | 作品集卡置灰 + 知情继续（D-PFM-29）；导入不问页数 | **Done** |
| FE-PFM-03 | 首页次链 DOM（`homepage_entry=false` 不露） | **Done** |

**验证**

```powershell
python -m pytest tests/unit/config/test_edition.py tests/unit/web/test_portfolio_pipeline.py tests/unit/layout_engine/test_editorial_series.py tests/unit/web/test_import_wizard_payload_contract.py -q
node --test tests/js/import-wizard-logic.test.mjs
```

**回滚**：删 `travelogue/config/edition.py`、`editorial_series` 包、父开关字段；还原 import / curate / 首页 DOM。关旗路径与现网一致，无用户面回滚。

### W1 · 匹配器（P0 系列已入库 · 仍挡 AS-PFM-02 出门称作品集）

| ID | 任务 | 状态 |
|----|------|------|
| BE-PFM-04 | `run_curate` 身份分叉；游记 `compose_trip` 签名零改 | **Done** |
| BE-PFM-05/10 | `editorial_series` 包 + 正式目录加载器（跳过 `folio-*`） | **Done** |
| BE-PFM-08 | 无系列 → `E_PORTFOLIO_UNAVAILABLE` | **Done**（空目录 / 空资产仍硬失败） |
| BE-PFM-09 | import-linter：mosaic / layout_templates 不得反向依赖 | **Done** |
| BE-PFM-06 | 组→页：一组一页/连续多页；禁止跨组 | **Done** |
| BE-PFM-07 | 写出 `screens[]`（`patternId` 为占位 `page-*`，无几何） | **Done** |
| BE-PFM-21 | 溢出：升档 ≤32 → 收录上限 + `overflow` | **Done**（夹具） |
| BE-PFM-22 | `items[]` 从实收 `screens` 派生（schema 8 块 stub 上限内全等） | **Done**（夹具） |
| BE-PFM-19 | 单测：跨组硬拼、`photo_span`、升档、密页跳过 burst | **Done** |
| AS-PFM-01 | P0 `magazine-16-standard` 入 `editorial_series/series/`（手编 16 页升格，`status: official`，`photo_span: [48, 80]`） | **Done** |
| AS-PFM-04 | CHARTER 补第二形态一行 | **Done** |
| AC-PFM-03 | ISO-01 游记指纹不含 `studio.edition` | **Done** |

夹具在 `tests/unit/layout_engine/fixtures/editorial_series/`，短 `photo_span` 只测升档，**不是**现网金样。生产路径不传 `series` / `series_dir`，走官方 `magazine-16-standard`。空 `series=[]` 或空目录仍硬失败。Wizard 置灰阈值现网派生为 **48**（系列 `photo_span` 下界）。C 端首页主 CTA 仍不得称作品集（D-PFM-26 · `homepage_entry` 仍关）。

**不得**：运行时扫 `docs/templates/reserve/`；把 `folio-*` 原样丢进 `series/`；打开 `homepage_entry`。

**验证**

```powershell
python -m pytest tests/unit/layout_engine/test_editorial_series.py tests/unit/web/test_portfolio_pipeline.py -q
```

### W2 / W3 / W4

**AS-PFM-02（本波）**：工坊 `faces.js` + `packet.yaml` 编译进 `travelogue/layout_templates/templates/page-*.yaml`，再 `export --sync-journal`。P0 金样本 11 张全收；其余能过 LTE schema（≤9 槽）的一并收，共 **75** 张。`page-10-grid-port` 因槽数 10 未收。

- 状态 `experimental`（不写 `rollout.percent: 0`，避免踏 E1 复审钟）；`list_active` **跳过** `page-*`，游记 MCS 配额与候选不变。
- 运行时 **不扫** `docs/templates/reserve/`。重编译：`python -m travelogue.layout_templates.cli promote-pages` 然后 `export --sync-journal`。

W2 其余：Wizard 置灰已做。W4 狗粮盲评后才考虑 `homepage_entry`。游记 Dock 零改。

| ID | 任务 | 状态 |
|----|------|------|
| FE-PFM-04 | 作品集 Dock 主钮「导出作品集」→ `portfolio_pages` | **Done** |
| FE-PFM-10 | 成功面「打开这一本」+ 发送压缩包 / 打开文件夹；不自动 8s 隐藏 | **Done** |
| FE-PFM-16 | 溢出角标「本册收录 N / M 张」+「改用游记（全收）」 | **Done** |
| FE-PFM-05 | ▾ 换种分享默认折叠 + 印刷副文 | **Done** |
| BE-PFM-15 | `POST …/edition`：只从 curate 装配段重入；`confirmed: true`；关旗拒作品集 | **Done** |
| FE-PFM-07/08 | 精修「成册类型」两卡 + 确认模态；作品集卸载 LVP | **Done** |
| FE-PFM-11 | 书架「作品集 · N 页」弱标 + 菜单「改为游记重排」 | **Done** |
| FE-PFM-09 | 精修页数芯片（自动 / 8–32）；非 4 倍数靠档 | **Done** |
| BE-PFM-25 | 切身份 / 钉页数后回填手改文案；落 `copyOrphans`；解 structure + copy 锁 | **Done** |
| FE-PFM-02 | Wizard 作品集卡置灰 + 知情继续；导入不问页数 | **Done** |
| BE-PFM-17 | `curate`/`run --edition`；作品集 `export-longshot` 缺 `--platform` 硬报错 | **Done** |
| FE-PFM-13 | 作品集等待态「正在按杂志页编排」；禁「文案 / 正在写」；游记 Wait Tips 六张字面不动 | **Done** |
| FE-PFM-14 | 关旗隐藏 B/C；打开存量作品集横幅 +「改为游记重排」 | **Done** |
| FE-PFM-12 | 窄屏 gate：作品集精修/导出仍电脑；游记字面不动 | **Done** |
| FE-PFM-15 | 身份 radiogroup 键盘可切；确认走 studioModal 焦点陷阱 | **Done** |

**BE-PFM-11 persist（本波）**：`layoutScreen.patternId` 用 `anyOf`（封闭 `screen-*` 枚举 ∪ `page-*` 前缀），H8 / Layout Critic 白名单仍只读枚举、不含 `page-*`。装配写出带 `screenId` + `slot`/`fit` 的屏；游记 trip 写 `page-*` 语义失败；未入库脸（如 `page-10-grid-port`）失败。

**BE-PFM-12 / 24（本波）**：作品集 web/share 阅读档默认 `magazine`。`edition=portfolio` 不进 Ambiguous 意图卡（`source=portfolio_bypass`）；显式六平台仍可解析。`portfolio_pages` 已登记到已知平台，**不进** PHASE_A 平铺、**不进**批量多选。群长图默认路径对作品集 trip 返回 `E_PORTFOLIO_PACK_REQUIRED`。

**BE-PFM-13 / 23（本波）**：`export/portfolio_pages.py` 按 `screens[]` 逐屏截预览同源 `index.html`（Playwright；禁止 CardGrouper 顶岗），Pillow 只做 1920×1080 letterbox。单页失败跳过、成功页紧凑编号。`platform=portfolio_pages` 一次动作并行尝试分享包 zip（`packager.export_trip`）+ 页图，任一失败不阻断另一件。Studio / CLI 对 `portfolio_pages` 跳过 Output Recipe（该 id 不在 `PLATFORM_TO_INTENT`）。

**FE-PFM-04 / 10 / 16（本波）**：作品集预览 Dock 主钮「导出作品集」，点击走 `portfolio_pages`（不弹 OR 意图卡、不把页图包写进六平台 prefs）。成功面主按钮「打开这一本」，次要发送压缩包 / 打开文件夹；有溢出时角标「本册收录 N / M 张」。游记 `init-v3.js` 默认串仍是「导出长图」。

**FE-PFM-05（本波）**：作品集导出 ▾ 主区「这一本 / 页图序列」；六平台收进默认折叠的「用同一批照片出社交图」。`album_spread` 仅在此面板改称「印刷跨页（现网画册）」并带副文「给印刷公司的 3:4 跨页，不是这一本」。游记弹层仍是「画册印刷」。

**BE-PFM-15 / FE-PFM-07/08/11（本波）**：精修「画册」新增「成册类型」（游记 / 作品集），确认必含「你手动改过的文字可能无法全部保留。」；作品集选中时 DOM 不渲染 LVP「成册风格」。`POST /__travelogue/trips/{id}/edition` 只 `run_curate(refresh_algorithms=False)`，改回游记清 `studio.edition`、保留 `studio.portfolio`。书架作品集票面弱标「作品集 · N 页」，⋯ 菜单「改为游记重排」。

**FE-PFM-09（本波）**：作品集精修出页数芯片（自动 / 8–32），导入仍不问。钉档走同一 `POST …/edition`（`pageCount`，无需二次确认）。非 4 倍数或目录无该档 → 靠档并提示「非标准页数 · 按 N 页靠档」。溢出角标现可点「改用游记（全收）」。

**BE-PFM-25（本波）**：`POST …/edition` 在 `run_curate` 前 `collect_user_copy`，装配后按 assetId → 章序回填。作品集 V1 正文纯图：导语 / 图注 / 屏内 kicker+body 进 `studio.copyOrphans`（`reason: portfolio_body`），章 title 两边都回填。回填不上的 `reason: no_slot`。确认模态已问过，不再问：先 `unlock_structure_for_replan`，迁移后 `revert_copy_lock_for_edit` + 清 leftover copy 锁。本波不做 orphans 浏览 UI。不开 `homepage_entry`。

**FE-PFM-02（本波）**：低于 GET `/config` 投影的 `minKept`（现网系列库下界 **48**）时，Wizard 作品集卡 `is-dim`、副文改「照片较少」。点击弹 `studioModal`（「照片较少，作品集更适合 30 张以上。确认后仍可继续。」），确认后才选中，不硬拒。首页次链预选 / 草稿恢复不弹。导入仍无页数控件。

```powershell
python -m pytest tests/unit/web/test_portfolio_pipeline.py -q
node --test tests/js/import-wizard-logic.test.mjs
```

**BE-PFM-17（本波）**：作品集 trip 跑 `export-longshot` 未传 `--platform` → `E_PORTFOLIO_PLATFORM_REQUIRED`，文案列出 `portfolio_pages` / `wechat_chat`。游记仍默认 `wechat_chat`。`curate` / `run` 接受 `--edition portfolio|journal`（关旗时改成作品集失败）。

```powershell
python -m pytest tests/unit/cli/test_portfolio_cli.py tests/unit/config/test_edition.py -q
```

**FE-PFM-13（本波）**：作品集导入壳标题「正在按杂志页编排…」，副文去掉「配文」。`narrate` 或主句含「文案 / 正在写」时盖成编排句。Wait Tips 作品集只改 WT-03 为「分章排版，交给它」（无「杂志」）。游记 `STAGE_LABELS.narrate` 与六张卡字面不动。成功面 `portfolioSuccessCopy` 不含禁词。

```powershell
node --test tests/js/import-run-logic.test.mjs tests/js/portfolio-export-logic.test.mjs
python -m pytest tests/unit/web/test_wait_tips_v1_contracts.py tests/unit/web/test_portfolio_pipeline.py -q
```

**FE-PFM-14（本波）**：B/C 仍要求 `enabled`（`homepageEntry` 单独打开不够）。关旗后打开存量作品集：GET entry 投影 `portfolioPipelineEnabled`；预览横幅「作品集编排暂时关闭 · 这一本仍可翻阅」+「改为游记重排」（复用精修确认）。游记关旗不露成册类型。

```powershell
node --test tests/js/portfolio-edition-logic.test.mjs tests/js/import-wizard-logic.test.mjs
python -m pytest tests/unit/web/test_studio_entry.py tests/unit/web/test_portfolio_pipeline.py -q
```

**FE-PFM-12（本波）**：预览窄屏 gate 按身份选文案。游记手机句仍是「手机可阅读分享页；精修与导出请在电脑浏览器打开本地址。」作品集改为「手机可翻阅这一本；精修与导出请在电脑浏览器打开本地址。」旋转/窄窗若未提精修导出则补一句。`applyTripEdition` 后 `refreshPreviewNarrowGate`。Share 只读仍不拦截。

```powershell
node --test tests/js/narrow-gate-logic.test.mjs
python -m pytest tests/unit/web/test_snr_w3_contracts.py tests/unit/web/test_portfolio_pipeline.py -q
```

**FE-PFM-15（本波）**：Wizard 身份分段方向键 / Home / End 可切到作品集（默认仍游记）。精修「成册类型」改为 radiogroup + radio + roving tabindex。确认仍走 `studioModal`（Tab 陷阱、Esc、归还焦点）。低照片知情继续同一套模态。

```powershell
node --test tests/js/portfolio-edition-logic.test.mjs
python -m pytest tests/unit/web/test_portfolio_pipeline.py -q
```

---

## 2. 后续编码清单（相对 PRD §12 · 2026-08-20）

W0–W3 主路径与 §2 编码项均已落。运营对账、狗粮盲评、开 `homepage_entry` 仍不在本表。

### 2.1 W3 收口

| 序 | ID | 状态 | 出口 AC |
|----|----|------|---------|
| 1 | **FE-PFM-06** | **Done** · `journalExportPanelSnapshot` 开旗前后零 diff | AC-PFM-02 · D-PFM-11 |
| 2 | **BE-PFM-16** | **Done** · `edition_chrome` 列表/预览同一份 CTA / 溢出 / LVP | AC-PFM-06 · 16 · 30 |
| 3 | **BE-PFM-20** | **Done** · telemetry 仅作品集写 edition / series / overflow | AC-PFM-21 |

### 2.2 隔离回归

| 序 | ID | 状态 | 出口 AC |
|----|----|------|---------|
| 5 | **BE-PFM-18** | **Done** · 指纹字段级 + xhs/album 卡序 + 仓库扫描 | AC-PFM-03 · **04** · 27 |
| 6 | **BE-PFM-14 补证** | **Done** · 作品集 trip 导出 xhs，plan 不读 patternId | AC-PFM-18 |

### 2.3 证据补洞

| 序 | ID | 状态 |
|----|----|------|
| 7 | **AC-PFM-10** | **Done** · `test_ac_pfm_10_dense_page_degrades_when_group_too_small` |
| 8 | **AC-PFM-32** | **Done** · 作品集正文纯图；封面封底书名地点仍在 |
| 9 | **AC-PFM-14** | **Done** · `wizardHitsToStart(quick, portfolio) === 2` |
| 10 | **AC-PFM-23** | **Done** · C 端可见串扫描（注释 / 测试 id 不扫） |

### 2.4 明确不做（本列车）

| 项 | 原因 |
|----|------|
| `copyOrphans` 浏览 UI | BE-PFM-25 已写明本波不做 |
| 打开 `homepage_entry` / 改首页主 CTA | W4 狗粮盲评后产品拍；D-PFM-06 |
| `page-10-grid-port` 入库 | 槽数 10 超 LTE schema；等 TSU |
| AS-PFM-03 工坊升格入库 | **五档已入**（8/12/16/20/28）；24/32/36 见 MSP ASK |
| AC-PFM-25 盲评「像一本」 | W4 人评，不是编码刀 |
| 游记 Dock / LVP / Wait Tips 六张字面 | 零改 |

### 2.5 W4 准备（2026-08-21）

| 项 | 状态 | 落点 |
|----|------|------|
| **ISO-04** | **Done** · 作品集 × 显式 `wechat_chat` 走 kept 竖条 | `portfolio_wechat.py` · `test_iso04_*` |
| **ISO-06** | **Done** · 作品集拒 LVP；切身份不改 `layoutVibe` | `test_iso06_lvp_rejects_portfolio_trip` |
| **AS-PFM-03** | **已升格 · 五档入库** · 对账原文不改 | [对账](./acceptance-records/pfm-as-pfm-03-atelier-reconcile-2026-08-21.md) · [MSP 后继](./acceptance-records/pfm-as-pfm-03-msp-promote-2026-08-21.md) |
| **W4 协议** | **已锁** · 人评未开 · 勿开 `homepage_entry` | [GUIDE](./acceptance-records/pfm-local-dogfood-GUIDE.md) · [盲评模板](./acceptance-records/pfm-blind-review-TEMPLATE.md) · [配置](./config-pfm-dogfood.example.yaml) |

**W0–W3 编码清单已清。** 下一刀是人评三册；过门前不开首页次链。

### P2-PFM-LSE

`curate` → `editorial_series` 是身份分叉的故意 +1 跨包边。待装配入口收到不计入 LSE 的 domain facade 后再收回。
