# IMPLEMENTATION · 当前版无 AI 面与主线打磨 V1（NAS）

| 属性 | 内容 |
|------|------|
| **文档版本** | **v0.2.1** |
| **对应 PRD** | [PRD-NO-AI-SURFACE-V1.md](./PRD-NO-AI-SURFACE-V1.md) **v0.2.1** |
| **评审** | [acceptance-records/no-ai-surface-v1-review-2026-07-22.md](./acceptance-records/no-ai-surface-v1-review-2026-07-22.md) · **Conditional Go** · MF 已回写 PRD |
| **验收** | [ACCEPTANCE-NO-AI-SURFACE-V1.md](./ACCEPTANCE-NO-AI-SURFACE-V1.md) **v0.1.1** |
| **DOC-STATUS** | **active** |
| **范围本版** | 前端门控/入口/文案 + **BE P0**（`aiSurfaceEnabled` · narrate / settings 写 / **ping** 硬拒绝）+ 禁词审计 |
| **编码启动** | **可开 W1**（先 PR-A 门控底座，见 §3） |
| **非范围** | 不删除 `travelogue/llm/**`；不改 stub/decorLine 算法；不改长图截图链路；不解开 `scope=frame` |
| **更新日期** | 2026-07-22 |

> **v0.2.1** = 编码前代码勘察回写（S1–S10）+ **ping 硬拒决议**。未改业务代码。

---

## 0. 切拍总览

| 波次 | 范围 | Go / No-Go | 状态 |
|------|------|------------|------|
| **W0** | PRD 评审 · MF 回写 · ACCEPTANCE · 本 IMPLEMENTATION v0.2.1 | Conditional Go | ✅ |
| **W1** | **PR-A** 门控底座 + **PR-B** 首页面（M3–M10）+ 翻转单测第一批 + W1 禁词 | AC-NAS-01～04 · 08a · 13 · 15～17a | ✅ e2e/unit |
| **W2** | **PR-C** Sheet/Dock/抽屉 + 全量禁词 + 长图狗粮 + shareCopyPack 抽检 | AC-NAS-05～07 · 11 · 14 · 08b | ✅ 自动化；07/11 手测 ☑ |
| **W3** | **PR-D** dark 恢复冒烟 · 文档指针 | AC-NAS-09～10 · 12 · 17b | ☑ DOC ✅ · dark 手测开 |

**铁律（实施时）**

1. 所有入口读同一 `isAiSurfaceEnabled()`（同步默认 `false`；**仅**读 bootstrap/`config.aiSurfaceEnabled`）。  
2. Hide, don't delete：模块与 dark 路径可留；**禁止**为过禁词审计删除 `llm-settings.js` / WEA 源（D-NAS-21）。  
3. **藏 UI ≠ 断触发**：Sheet 隐藏后仍须处理 **M1 drawers** 与 **M11 Dock→startLlmNarrate**。  
4. **三层防御**：L1 UI 门控 · L2 函数门闩（`openLlmSettings` / `startLlmNarrate` / `maybeShow*`）· L3 服务端 403。  
5. **`llmAvailable` ≠ 可展示 AI**：默认面禁止用 `llmAvailable` 决定任何用户可见文案/按钮（S2 / AC-NAS-10）。  
6. **分期不混 KPI**：本期只考 OUT-01～05；不解 `scope=frame`（D-NAS-22 · PRD §14）。

---

## 0.1 编码前补充（S1–S10）· 现网勘察决议

> 来源：2026-07-22 开发负责人对照现网代码的 Kickoff 反馈。实施以本表为准；与 PRD 冲突处见 **Ping 决议** 注记。

| ID | 主题 | 决议 / 动作 | 落入任务 |
|----|------|-------------|----------|
| **S1** | HTML 字面量是禁词主战场 | `#v2-settings-zone-ai` 现网已含「AI 文案 / 配置写作引擎…」且非 hidden。默认面：zone **`hidden` + `aria-hidden`**；摘要/CTA 改中性或空，**dark ON 再填写作引擎 CTA**。失败钮可保留 id，文案改 COPY，默认永不 `hidden=false`。**禁止**只靠 CSS `display:none` | FE-NAS-03 · 06 · 14 |
| **S2** | `llmAvailable` ≠ 可展示 AI | 有 Key 时 status/config 仍可能 `llmAvailable:true`。默认面**禁止**用其驱动 FS / stub / Sheet / Dock / settings badge | 全 FE；注释写死 |
| **S3** | 停间接点灯 | 默认面**停调** `GET /llm/status`（`first-success` / `home-stub-banner` / `settings-panel` / `init-v3` / `llm-readiness`）；避免 `travelogue:llm-status` 唤醒 tip | FE-NAS-02 · 05 · 09 |
| **S4** | 三路 narrate 同 PR | Sheet · Dock · 抽屉 → 皆通 `startLlmNarrate`；底闸 + UI 切断同 PR | FE-NAS-09+10 |
| **S5** | 错误文案三份镜像 | `errors.js` · `constants.js` · `studio_errors.py` 同步中性；`E_AI_SURFACE_DISABLED` 进 py + ERROR-CODES | FE-NAS-07 · BE-NAS-02 |
| **S6** | shareCopyPack 抽检 | `_share_copy_pack_entry` 在 `llmAvailable` 时塞 body；W2 有 Key/无 Key 各导出一次，确认无禁词（OUT-04）；有问题再补卡 | PR-C 冒烟 |
| **S7** | **Ping 决议（严于 PRD D-NAS-17）** | 门控 off：`POST /llm/ping` → **403** + `E_AI_SURFACE_DISABLED`（与「配不了」一致；现网 ping 可回写 `last_ping_ok`）。**`GET /llm/status` 仍可保留**（dark/curl）；默认面 FE 不请求。dark ON 恢复 ping（AC-NAS-09） | **BE-NAS-03** |
| **S8** | 源码禁词 / `nas-allow` | 默认可达面改中性；dark 专用串集中并标 `nas-allow`，分 job；**禁止**删整文件过 AC-08 | FE-NAS-01 · 14 · D-NAS-21 |
| **S9** | 单测翻转 Day-0 | W1 第一天同步拆 `*_nas_default` / `*_ai_surface_dark`（DLLM W2 · L0G FE · UX Trust 优先）；e2e 注入能力卡 fixture 不进默认禁词 job | FE-NAS-14 · PR-A/B |
| **S10** | 文档指针 | 实施/验收对齐 PRD **v0.2.1**（§5.5 冻结 · §14 解冻 · OUT-01～05） | 本文 · ACCEPTANCE · DOC-STATUS |

### Ping / status 对照（实施合同）

| API | 门控 off | 默认面 FE | dark ON |
|-----|----------|-----------|---------|
| `GET /llm/status` | **200 可保留**（不强制 403） | **不请求** | 可请求 |
| `POST /llm/settings`（写/删） | **403** | 无 UI | 可写 |
| `POST /llm/ping` | **403**（本决议） | 无 UI | 可 ping |
| `POST /narrate` | **403**（先于 Key） | 无入口 | 可 narrate |

> PRD D-NAS-17 原文写「status/ping 可保留」。**实施采纳更严：ping 硬拒**；status 仍可保留。若产品事后要放宽 ping，须改本表 + ACCEPTANCE，不得静默放行。

---

## 1. 前端任务卡索引

| 卡号 | 标题 | 波次 | PRD 触点 | 优先级 |
|------|------|------|----------|--------|
| **FE-NAS-00** | AI 面门控 helper | W1 · PR-A | D-NAS-02/03/14 · §5.2 | P0 |
| **FE-NAS-01** | 能力卡关闭 + body 禁词（M4） | W1 · PR-B | T-NAS-01 · T-NAS-30 · S8 | P0 |
| **FE-NAS-02** | stub banner / stub tip 关闭 + 停 status | W1 · PR-B | T-NAS-04/11 · S3 | P0 |
| **FE-NAS-03** | 设置去 AI zone + 总述（M5/M6 · S1） | W1 · PR-B | T-NAS-02/03/14 · T-NAS-31/32 | P0 |
| **FE-NAS-04** | 帮助去 H7 + H0/重播（M9） | W1 · PR-B | T-NAS-05/12/13 · T-NAS-35 | P0 |
| **FE-NAS-05** | FirstSuccess 仅中性句 + 停 readiness | W1 · PR-B | T-NAS-10 · S3 | P0 |
| **FE-NAS-06** | 失败面去配置出口（M7/M8 · S1） | W1 · PR-B | T-NAS-09 · T-NAS-33/34 | P0 |
| **FE-NAS-07** | 错误句三镜像中性化（M3 · S5） | W1 · PR-B | T-NAS-16/29 | P0 |
| **FE-NAS-08** | Sheet 去 llm 行 | W2 · PR-C | T-NAS-06/07 | P0 |
| **FE-NAS-09** | init 去 llm 状态机 + Dock 切断（M11） | W2 · PR-C | T-NAS-08/37 · S3/S4 | P0 |
| **FE-NAS-10** | **抽屉「按新感觉重写」+ toast（M1/M2）** | W2 · PR-C | T-NAS-27/28 · S4 | P0 |
| **FE-NAS-11** | **`openLlmSettings` 总门闩**（含 deeplink M10） | **W1 · PR-A** | T-NAS-36 · S 多源 | **P0** |
| **FE-NAS-12** | G1 副文案软改（M12） | W2 · PR-C | T-NAS-38 | P2 |
| **FE-NAS-13** | dark switch 恢复包（含 ping；**不**恢复能力卡） | W3 · PR-D | F-NAS-07 · D-NAS-20 | P1 |
| **FE-NAS-14** | 静态禁词门禁 + 翻转清单（S8/S9） | W1–W2 | F-NAS-08 · 附录 C | P0 |

---

## 2. 任务卡正文

### FE-NAS-00 · AI 面门控 helper

| 项 | 内容 |
|----|------|
| **目标** | FE 单一真相源：`isAiSurfaceEnabled()` ← **仅** bootstrap/`config.aiSurfaceEnabled` |
| **建议路径** | 新建 `templates/studio/js/ai-surface.js` |
| **行为** | 默认同步 `false`；读取服务端下发字段；**禁止**假装读进程 env / localStorage 当正式开关；异步刷新不得闪出入口 |
| **导出** | `isAiSurfaceEnabled()`；可选 `whenAiSurface(fn)`；可选 `setAiSurfaceEnabledFromConfig(cfg)` |
| **验收** | 与 BE-NAS-01 联调；AC-NAS-15 |
| **依赖** | BE-NAS-01（同 PR-A） |
| **状态** | ⏳ |

---

### FE-NAS-01 · 能力卡关闭 + body 禁词（含 M4 · S8）

| 项 | 内容 |
|----|------|
| **目标** | 默认永不展示能力卡；卡内升级话术不进默认面字符串面 |
| **路径** | `templates/studio/js/capability-card.js` · `capability-card.css` · `homepage-v2/bootstrap.js` |
| **动作** | `maybeShowCapabilityCard` / `showCapabilityCard` 首行门控早退；升级链不绑定；**改写/移除**默认可达禁词（「更好的文案可稍后自行升级」「以后再升级 AI 文案」）；dark 专用串标 `nas-allow` 或迁出默认扫描面 |
| **COPY** | COPY-NAS-CAP-NONE（不展示） |
| **验收** | AC-NAS-01；静态扫描无上述禁词 |
| **状态** | ⏳ |

---

### FE-NAS-02 · stub banner / stub tip 关闭（含 S3）

| 项 | 内容 |
|----|------|
| **目标** | 首页「本机文案 / 升级 AI」条与预览 stub tip 默认关闭；**不**再 `GET /llm/status` |
| **路径** | `js/home-stub-banner.js` · `help-onboarding.js` `maybeShowStubNarrateTip` · 调用方 `import-run.js` / `first-success.js` / `init-v3.js` |
| **动作** | `sync*` / `maybeShow*` 门控早退；默认面跳过 status fetch |
| **验收** | 首访与首次预览无 stub 升级 tip |
| **状态** | ⏳ |

---

### FE-NAS-03 · 设置去 AI zone + 总述（含 M5/M6 · S1）

| 项 | 内容 |
|----|------|
| **目标** | 设置无「AI 文案」分组与写作引擎 CTA；总述去「AI 可选」 |
| **路径** | `studio-home-v2.html`（`#v2-settings-zone-ai` · `#v2-settings-desc`）· `settings-panel.js` · `bootstrap.js` `initLlmSettingsEntry` · `llm-settings.js` |
| **动作** | zone 默认 **`hidden` + `aria-hidden`**；摘要/CTA 中性或空（**dark ON 再填**）；`initLlmSettingsEntry` 门控；`refreshAiStatus` / badge sync **短路**（M6）；`focusZoneControl("ai")` 默认 no-op；bootstrap 接线门控（M5） |
| **COPY** | COPY-NAS-SET-DESC |
| **验收** | AC-NAS-02；HTML 静态禁词不因 zone 字面量失败 |
| **状态** | ⏳ |

---

### FE-NAS-04 · 帮助去 H7 + H0/重播（含 M9）

| 项 | 内容 |
|----|------|
| **目标** | 帮助无 AI 配置条目；重播不再唤醒能力卡/stub tip |
| **路径** | `js/help-onboarding.js` |
| **动作** | 默认列表去掉 H7；H0 换 COPY-NAS-H0-*；replay toast → COPY-NAS-REPLAY；**默认面禁止** `clearCapabilityCardSeen` / `clearStubHintSeen` 作为重播副作用（M9） |
| **验收** | AC-NAS-03；重播后仍无能力卡（M9） |
| **状态** | ⏳ |

---

### FE-NAS-05 · FirstSuccess 仅中性句（含 S3）

| 项 | 内容 |
|----|------|
| **目标** | 成功面不按 llm readiness 分支 |
| **路径** | `homepage-v2/first-success.js` · `HELP_COPY.firstSuccessNext*` |
| **动作** | 固定 COPY-NAS-FS-01；**停调** `loadLlmReadiness`（不只忽略结果）；analytics 分支恒 `nas_hidden` 或停发 |
| **验收** | AC-NAS-04；无多余 `/llm/status` |
| **状态** | ⏳ |

---

### FE-NAS-06 · 失败面去配置出口（含 M7/M8 · S1）

| 项 | 内容 |
|----|------|
| **目标** | 失败面不引导写作引擎；焦点不落配置钮 |
| **路径** | `homepage-v2/import-failed.js` · `studio-home-v2.html`（`#v2-failure-open-settings` · `#v2-failure-continue-stub`） |
| **动作** | 隐藏配置钮且改写 HTML 字面量；改写「杂志感文案暂不可用」等；`focusId` 永不落到 settings（M7）；「继续生成本机游记」→ 隐藏或 COPY-NAS-FAIL-CONTINUE（M8）；`openSettingsFromFail` → `openLlmSettings` 被 FE-NAS-11 挡住 |
| **COPY** | COPY-NAS-FAIL-01 · COPY-NAS-FAIL-CONTINUE |
| **验收** | 失败狗粮无配置 CTA/焦点 |
| **状态** | ⏳ |

---

### FE-NAS-07 · 错误句三镜像中性化（M3 · S5）

| 项 | 内容 |
|----|------|
| **目标** | 用户可见 `E_LLM_*` 不再引导「设置 → AI 文案 / 写作引擎」 |
| **路径** | `templates/studio/js/errors.js` · `templates/studio/js/constants.js` · **`travelogue/web/studio_errors.py`** |
| **动作** | 三份同步中性（对齐 COPY-NAS-FAIL-01）；或确保默认路径永不展示；新码 `E_AI_SURFACE_DISABLED` → COPY-NAS-NARRATE-403 |
| **验收** | 静态禁词覆盖三文件；AC-NAS-08 |
| **状态** | ⏳ |

---

### FE-NAS-08 · Sheet 去 llm 行

| 项 | 内容 |
|----|------|
| **目标** | 精修「这本 / 整本信息」无「重新生成文案」与配置写作引擎 |
| **路径** | `preview-toolbar-v3-sheet.js`（`bookCopyRefreshHtml` 等） |
| **动作** | 默认不渲染 `data-tool="llm"` / `llm-setup` / `llm-expect` / unavailable hint |
| **验收** | AC-NAS-05 |
| **状态** | ⏳ |

---

### FE-NAS-09 · init 去 llm 状态机 + Dock 触发切断（M11 · S3/S4）

| 项 | 内容 |
|----|------|
| **目标** | 不轮询 llm status；Dock 就绪条不出现；**切断** copyRefresh → `startLlmNarrate` |
| **路径** | `preview-toolbar/init-v3.js` · `preview-toolbar-v3-task-dock.js` · `preview-toolbar/core.js` |
| **动作** | 跳过 `setLlmAvailable` / status fetch；`root._copyRefreshHint` 恒 false；移除/门控 Dock→narrate（M11）；Dock 不渲染「重新生成文案」；**`startLlmNarrate` 首行 `isAiSurfaceEnabled()` 早退**（D-NAS-19） |
| **验收** | AC-NAS-05/06/14；默认面 **0×** `/narrate` |
| **依赖** | FE-NAS-00；**与 FE-NAS-10 同 PR-C** |
| **状态** | ⏳ |

---

### FE-NAS-10 · 抽屉「按新感觉重写」隐藏 + toast（M1/M2）★

| 项 | 内容 |
|----|------|
| **目标** | 堵住 Sheet 之外的 LLM 入口；去掉再生引导 toast |
| **路径** | `preview-toolbar/drawers.js` |
| **动作** | 默认不渲染「按新感觉重写这段」；不调用 `_startLlmNarrate`；保存 toast → COPY-NAS-DRAWER-SAVE |
| **验收** | 抽屉无该按钮；toast 无禁词；无法从抽屉打 narrate |
| **依赖** | FE-NAS-00；**与 FE-NAS-09 同 PR-C** |
| **状态** | ⏳ |
| **备注** | **W2 必做**；漏做则 NAS 名存实亡 |

---

### FE-NAS-11 · `openLlmSettings` 总门闩（含 deeplink M10）★ 升 P0 / W1

| 项 | 内容 |
|----|------|
| **目标** | 所有打开写作引擎 Modal 的路径在默认面失效（不止 deeplink） |
| **路径** | `js/llm-settings.js`：`openLlmSettings` · `initLlmSettingsEntry` · `?llmSetup=1` |
| **现网调用方（须一并挡住）** | capability-card · home-stub-banner · import-failed · settings CTA · preview narrate fail（`core.js` dynamic import）· deeplink |
| **动作** | `isAiSurfaceEnabled()===false` 时 **`openLlmSettings` 直接 return**；`init*` 不绑 entry；deeplink 忽略 |
| **验收** | AC-NAS-15；伪造 deeplink / fail CTA 不弹窗 |
| **波次** | **W1 · PR-A（与 FE-NAS-00 同 PR）** |
| **优先级** | **P0**（原 P1 升格） |
| **状态** | ⏳ |

---

### FE-NAS-12 · G1 副文案软改（M12）

| 项 | 内容 |
|----|------|
| **目标** | 降低「生成文案」被读成 AI 写稿的概率 |
| **路径** | `preview-toolbar-v3-task-dock.js`（G1 确认副文案）；可选设置 G1 hint（`studio-cfg-g1-hint`） |
| **动作** | → COPY-NAS-G1-NEXT（「将继续排版成册」） |
| **验收** | 文案替换；非阻断 |
| **优先级** | P2 |
| **状态** | ⏳ |

---

### FE-NAS-13 · dark switch 恢复包

| 项 | 内容 |
|----|------|
| **目标** | `aiSurfaceEnabled=true` 时恢复 DLLM 核心用户面，便于内部回归 |
| **恢复** | 设置 AI zone（填回写作引擎 CTA）+ Modal + **ping** + settings 写；Sheet llm 行；**抽屉「按新感觉重写」**；Dock copyRefresh（若产品仍要） |
| **默认不恢复** | 能力卡 / stub banner / H7 / FS 分支（D-NAS-20） |
| **验收** | AC-NAS-09；OFF 时有 Key 仍隐藏（AC-NAS-10） |
| **波次** | W3 · PR-D |
| **状态** | ⏳ |

---

### FE-NAS-14 · 前端静态禁词门禁（S8/S9）

| 项 | 内容 |
|----|------|
| **目标** | CI 防止禁词回流；Day-0 翻转清单 |
| **路径** | `scripts/studio_no_ai_surface_audit.py`；`test_no_ai_surface_*.py`；翻转清单见 ACCEPTANCE §5 |
| **扫描语义** | PRD 附录 C.1（默认可达面；W1 分区 / W2 全量；dark 分 job；`nas-allow`） |
| **Day-0 优先翻转** | `test_desktop_llm_setup_w2.py` · `test_l0_guidance_hardening_fe.py` · `test_ux_trust_v1.py` ·（W2）`test_preview_toolbar_v3.py` · `test_sfi_dock_arbitration.py` |
| **验收** | AC-NAS-08a/08b · AC-NAS-FLIP |
| **状态** | ⏳ |

---

## 3. 建议合入顺序（PR 切片）

```
PR-A（W1 底座）★ 最先
  BE-NAS-01/02/03 + FE-NAS-00 + FE-NAS-11
  + E_AI_SURFACE_DISABLED 登记
  + 翻转单测脚手架（可先拆 DLLM/UX Trust）

PR-B（W1 首页面）
  FE-NAS-01～07 + FE-NAS-14（W1 分区审计）
  → AC-01～04 · 08a · 16

PR-C（W2 预览面）★
  FE-NAS-08 + FE-NAS-09+10 同 PR + FE-NAS-12(P2)
  + FE-NAS-14 全量 + shareCopyPack 抽检（S6）+ 纯照片长图狗粮
  → AC-05～07 · 14 · 08b；0× /narrate

PR-D（W3）
  FE-NAS-13 dark（不恢复能力卡）+ DOC-NAS-02 + 月度冒烟钩子
  → AC-09/10 · 17b
```

**同 PR 强绑定**

- PR-A：`BE-NAS-*` + `FE-NAS-00` + `FE-NAS-11`  
- PR-C：`FE-NAS-09` + `FE-NAS-10`（切断全部 narrate UI 触发）

**不要**把 PR-A 与「只改帮助文案」拆成两周——中间态更脏。

---

## 4. 文件 ↔ 任务对照（速查）

| 文件 | 任务卡 |
|------|--------|
| `travelogue/web/ai_surface.py`（新） | BE-NAS-01 |
| `travelogue/web/studio_handlers/config_handlers.py` | BE-NAS-01 |
| `travelogue/web/studio_handlers/export_handlers.py` | BE-NAS-02 |
| `travelogue/web/studio_handlers/llm_settings_handlers.py` | BE-NAS-03 |
| `travelogue/web/studio_errors.py` · `docs/ERROR-CODES.md` | BE-NAS-02 · FE-NAS-07 |
| `js/ai-surface.js`（新） | FE-NAS-00 |
| `js/capability-card.js` | FE-NAS-01（M4） |
| `js/home-stub-banner.js` | FE-NAS-02 |
| `js/help-onboarding.js` | FE-NAS-02 · 04（M9）· 05 COPY |
| `js/llm-settings.js` | FE-NAS-03 · **11** · 13 |
| `js/llm-readiness.js` | FE-NAS-05（默认面停用） |
| `js/errors.js` · `js/constants.js` | FE-NAS-07（M3） |
| `js/analytics.js` | 随入口停发（可选，W3）；保留 `llm_*` schema |
| `studio-home-v2.html` | FE-NAS-03 · 06（**S1 HTML**） |
| `homepage-v2/bootstrap.js` | FE-NAS-00 接线 · 01 · 03（M5） |
| `homepage-v2/settings-panel.js` | FE-NAS-03（M6 · S3） |
| `homepage-v2/first-success.js` | FE-NAS-05 |
| `homepage-v2/import-failed.js` | FE-NAS-06（M7/M8） |
| `homepage-v2/import-run.js` | FE-NAS-02 调用点 |
| `preview-toolbar-v3-sheet.js` | FE-NAS-08 · 13 |
| `preview-toolbar/init-v3.js` | FE-NAS-09（M11）· 02 tip |
| `preview-toolbar/core.js` | FE-NAS-09 · 11（fail→openLlm）· 13 |
| `preview-toolbar-v3-task-dock.js` | FE-NAS-09 · 12（M12） |
| **`preview-toolbar/drawers.js`** | **FE-NAS-10（M1/M2）** ★ |
| `travelogue/web/studio_entry.py`（shareCopyPack） | S6 抽检（W2） |

---

## 5. 后端任务卡（P0）

### BE-NAS-01 · 下发只读 `aiSurfaceEnabled`

| 项 | 内容 |
|----|------|
| **建议路径** | 新建 `travelogue/web/ai_surface.py` → `resolve_ai_surface_enabled(cfg)`；仿 `studio_homepage_gate`：`TRAVELOGUE_AI_SURFACE` truthy **OR** `studio.ai_surface_enabled==true`；默认 **false** |
| **暴露** | `config_handlers.handle_config` **顶层** `aiSurfaceEnabled`（与 `llmAvailable` 同级）；**不进** `patch_config_file` / `allowed_studio` |
| **验收** | AC-NAS-13/15 联调；config 有字段；PATCH 无法自开 |
| **波次** | W1 · PR-A · P0 |
| **状态** | ⏳ |

### BE-NAS-02 · narrate 硬拒绝

| 项 | 内容 |
|----|------|
| **行为** | 门控 off：`POST /narrate` → **403** + `E_AI_SURFACE_DISABLED` + COPY-NAS-NARRATE-403 |
| **检查顺序** | 解析 trip / pipeline 校验之后、**任何** `studio_llm_status` / Key / Job **之前**（现网在 Key 检查前插入） |
| **禁止** | 复用 `E_LLM_AUTH`（会点燃配置 CTA） |
| **路径** | `export_handlers.handle_narrate` · `studio_errors.USER_MESSAGES` · `docs/ERROR-CODES.md` |
| **验收** | AC-NAS-13；有 Key 仍 403 |
| **波次** | W1 · PR-A · P0 |
| **状态** | ⏳ |

### BE-NAS-03 · settings 写 + ping 硬拒绝（S7）

| 项 | 内容 |
|----|------|
| **行为** | 门控 off：`POST`/`DELETE` `/llm/settings` → **403**；**`POST /llm/ping` → 403**（同码；防 `last_ping_ok` 回写） |
| **保留** | `GET /llm/status` **不强制 403**（dark/curl）；默认面 FE 不调用（S3） |
| **路径** | `llm_settings_handlers.handle_llm_settings` · `handle_llm_ping` |
| **验收** | AC-NAS-17a；另补：off 时 ping → 403（写入 ACCEPTANCE 备注或 AC 扩展） |
| **波次** | W1 · PR-A · P0 |
| **状态** | ⏳ |
| **注记** | **严于 PRD D-NAS-17**（见 §0.1 Ping 对照）；dark ON 后 ping 须可用（AC-NAS-09） |

### 导入路径

- **不必**对导入 pipeline 加 NAS 403：`resolve_studio_narrate_provider` 已恒 stub。

---

## 6. 文档任务

| ID | 任务 | 波次 | 状态 |
|----|------|------|------|
| DOC-NAS-01 | ACCEPTANCE-NO-AI-SURFACE-V1 | W0 | ✅（v0.1.1 已指 PRD v0.2.1） |
| DOC-NAS-02 | ERROR-CODES / CSC / SFI / Help 指针；PRD D-NAS-17 与 ping 决议对齐注记 | W2–W3 | ✅ 2026-07-22（Help §12.4 · SFI FE-SFI-04 · CSC Happy Path · DLLM/WEA 文首；责任人：产品合同 / 工程门控） |
| DOC-NAS-03 | README · DOC-STATUS | W0 | ✅ / 随 v0.2.1 同步 |
| DOC-NAS-04 | 本 IMPLEMENTATION v0.2.1（S1–S10 · ping · PR 切片） | W0 | ✅ |

---

## 7. 风险（实施）

| 风险 | 缓解 |
|------|------|
| 只藏 Sheet、漏 drawers | **FE-NAS-09+10 同 PR-C**；AC-NAS-14 |
| 只藏 UI、Modal 仍可开 | **FE-NAS-11 进 PR-A**；多源调用方清单 |
| `llmAvailable` 间接点灯 | S2/S3；默认面停 status |
| HTML 字面量过不了禁词 | S1；zone hidden + 改串 |
| DLLM 静态单测红 | S9 Day-0 翻转；禁止只删断言 |
| 禁词误伤「杂志感」版式 hint | 附录 C.1/C.3 |
| dark 恢复能力卡 | D-NAS-20 / FE-NAS-13 |
| 复用 E_LLM_AUTH | BE-NAS-02 独立错误码 |
| narrate 先查 Key 再门控 | BE-NAS-02 顺序强制 |
| ping 回写 secrets | BE-NAS-03 ping 403 |
| PATCH 自开 dark | BE-NAS-01 永不进 allowlist |
| 拆底座过禁词 | D-NAS-21 · §5.5 冻结清单 |

---

## 修订记录

| 版本 | 日期 | 说明 |
|------|------|------|
| **v0.2.1** | 2026-07-22 | **编码前勘察回写**：S1–S10 · **ping 硬拒决议（严于 D-NAS-17）** · FE-NAS-11 升 W1/P0 · 错误三镜像 · PR-A/B/C/D 切片 · 对齐 PRD v0.2.1；未改业务代码 |
| v0.2.0 | 2026-07-22 | 对齐 PRD v0.2：BE-NAS-01～03 升 P0 任务卡；FE-00/09/14 补丁；编码可开 W1 |
| v0.1.0 | 2026-07-22 | 初稿：前端任务卡 FE-NAS-00～14（含 M1–M12 映射）；不动业务代码 |
