# Travelogue · 预览中删除护栏 V1 产品需求文档（PRD）

| 属性 | 内容 |
|------|------|
| **产品代号** | Travelogue Studio |
| **文档版本** | **v0.2** |
| **状态** | **Implemented · dogfood**（M1–M3 主路径已落地 · 见 ACCEPTANCE） |
| **DOC-STATUS** | **active** |
| **主题代号** | 「预览中删除护栏 V1（Preview Delete Guard）」— **PDG** · 先断开预览 · 再删盘 · 不卡死 |
| **调研来源** | 2026-07-23 用户复现：「首页将游记设为预览默认 → 书架删除该游记 → 页面卡死/浏览器崩溃；硬刷新后回示例空态」+ 同日开发负责人代码探查 |
| **评审来源** | 2026-07-23 开发 + 测试联评（Must-Fix / AC 收紧 / 四条当场锁定决策） |
| **关联文档** | [Homepage v2 · D-14](./PRD-STUDIO-HOMEPAGE-v2.md#68-预览画册选择器d-14--v206-草案) · [DATA-CONTRACT](./studio-homepage-v2/DATA-CONTRACT.md) · [M14 书架长图](./PRD-M14-shelf-save-longshot.md) · [QFX](./PRD-QUALITY-FIXPACK-V1.md) · [PMX](./PRD-POST-MERGE-UX-FIXPACK-V1.md) |
| **验收** | [ACCEPTANCE-PREVIEW-DELETE-GUARD-V1.md](./ACCEPTANCE-PREVIEW-DELETE-GUARD-V1.md) · 本文 §9 |
| **实施清单** | [IMPLEMENTATION-PREVIEW-DELETE-GUARD-V1.md](./IMPLEMENTATION-PREVIEW-DELETE-GUARD-V1.md)（须遵守 §0.3 / §0.4 与实施层 I-PDG-*） |
| **更新日期** | 2026-07-23 |

> **定位**
>
> D-14 已规定：preference 指向已删 trip 时，**冷启动**清除 preference → 回示例 + toast（AC-D14-04）。  
> 但**热路径**——用户正在把某本画册当作首页 Bento 预览，同时又从书架删除同一本——**没有防护**：
>
> 1. 删除确认不区分「是否正在展示」；  
> 2. 前端不先断开预览引用，仍对即将消失的目录发大量静态图请求；  
> 3. 后端 `DELETE` 同步 `rmtree`，与静态资源服务 / 派生图后台线程无互斥。
>
> 本 PRD 是一次**窄修复包（Fixpack）**，不引入新功能面：补齐「预览中删除」的知情同意、状态事务与删除稳定性，使该路径**可预期、可取消、不卡死**。

> **v0.2 相对 v0.1（联评回写摘要 · 2026-07-23）**
>
> - **Conditional Go**：方向正确；v0.1 若干处把「期望能力」写成「已有能力」，已按 Must-Fix 改合同。  
> - **D-PDG-02**：拆成「清 preference + 换示例」与「媒体尽力释放」；**文件句柄安全归后端 deleting gate**，禁止宣称现有 setter 已 abort 图片请求。  
> - **D-PDG-04 锁定**：`begin_trip_delete` → stop/join on-demand → rename `_deleting-*` → 204 → 异步 rmtree + **启动续删**；放弃「仅同步 rmtree」作主路径。  
> - **D-PDG-03 / AC-05**：删除中态落在**卡片/菜单**（modal 确认后关闭），不扩展全局 `studioModal` loading API。  
> - **断开失败策略**：尽力清空后仍 DELETE；不把 localStorage 静默写失败当作可中止条件。  
> - **独立预览页同时打开**：升为 **M2 必验**（不 Park）。  
> - **AC 收紧**：锁定必含/禁含短语、DELETE 调用瞬间采样、有状态 fixture mock、409/500 分例。

> **一句话目标**：**删除正在首页展示的画册时，先明确告知并征得许可；获准后先切回示例，再删盘；全过程页面可交互，禁止卡死或崩溃。**

> **完成定义**
>
> | 门 | 含义 | 不等于 |
> |----|------|--------|
> | **M1 Go** | 预览中删除有强确认；确认后先清 preference 并回示例再 DELETE；卡片删除中防重入；AC-PDG-01～04/06 绿 | 改书架 IA；不宣称前端已释放全部文件句柄 |
> | **M2 Go** | deleting gate + on-demand stop + rename 异步清理；独立预览页同时打开不挂死；AC-PDG-05/07/08 绿 | 存储平台重构；服务端预览租约 |
> | **M3 Go** | 真测覆盖热路径；AC-D14-04 不回退；邻接合同回写；主题 Done | 全量书架操作审计 |

---

## 0. 读者指南与边界

### 0.1 与相邻主题

| 主题 | 关系 | 本主题做什么 |
|------|------|--------------|
| [Homepage v2 · D-14](./PRD-STUDIO-HOMEPAGE-v2.md#68-预览画册选择器d-14--v206-草案) | **硬化热路径** | 不重开 Combobox / preference 模型；**扩展**「删除正在预览的册」知情同意 + 先断开后删除；AC-D14-04 冷启动兜底**保留** |
| [DATA-CONTRACT](./studio-homepage-v2/DATA-CONTRACT.md) | **状态契约所有者** | 回写：删除热路径必须先清空 `bentoPreviewTripId`；禁止悬空引用；reroute 不得复活刚删 ID |
| [M14 书架长图](./PRD-M14-shelf-save-longshot.md) | **书架菜单邻居** | 不改长图入口；仅改「删除画册」分支文案与时序 |
| [QFX](./PRD-QUALITY-FIXPACK-V1.md) | **质量包邻居** | 不重开 NAS / keep-all / 导出 manifest；本包专攻删除×预览竞态 |
| 示例保护（`is_protected_demo_trip`） | **已有合同** | 示例册仍不可删；本包只管**用户册且为当前预览** |

### 0.2 探查结论摘要（2026-07-23）

| ID | 结论 |
|----|------|
| **R-PDG-01** | 删除确认**不检查** `tripId === V2.bentoPreviewTripId` |
| **R-PDG-02** | `onTripDeleted` **不清** `bentoPreviewTripId` / `userManifest` / localStorage；收敛依赖事后 `V2.reroute()` 或硬刷新 |
| **R-PDG-03** | `handle_delete_trip` 直接 `shutil.rmtree`；`is_trip_busy` **覆盖不到** `derivatives.materialize_on_demand` 后台线程；无 trip 写锁 |
| **R-PDG-04** | Bento carousel / phone-strip 在删除窗口仍绑定 `/{tripId}/assets/*`；Windows 上文件占用易使 `rmtree` 挂起或半删除 |
| **R-PDG-05** | AC-D14-04 仅覆盖「冷启动 ghost preference」，**未覆盖**「预览中当场删除」 |
| **R-PDG-06**（联评补） | 现有 `setBentoPreviewTripId(null)` **不会** abort 已发出的 img/`new Image()` 请求；dispose 仅清监听与 timer |
| **R-PDG-07**（联评补） | `materialize_on_demand` **无**公共 join/cancel API；`studioModal` **无** loading/controller API |
| **R-PDG-08**（联评补） | 独立预览页持续请求同一 trip 静态资源时，首页清 preference **无效**于句柄占用 |

### 0.3 已锁定决策（2026-07-23 Conditional Go）

| 决策 | 锁定结论 |
|------|----------|
| **D-PDG-01 强确认** | 当且仅当 `tripId === bentoPreviewTripId`（不论 manifest 是否已加载 / 是否「预览不可用」占位）时，删除弹层使用**强确认文案**（§5.1）。其余删除保持通用文案（§5.2）。 |
| **D-PDG-02 先断开后删除** | 用户确认后顺序冻结为：① **尽力**清 preference（memory + localStorage + session shim）并切示例 + 媒体尽力释放（§4 R1.2）；② 标记删除中；③ `DELETE`。禁止「盘已删、预览仍指旧 ID」。**不得**宣称步骤①已保证服务端文件句柄释放——句柄安全归 **D-PDG-04**。 |
| **D-PDG-03 进行中反馈** | Modal **确认后关闭**；删除中态落在**该书架卡片/菜单**（禁用删除项 +「删除中」或等价 `aria-busy`）。全局对同一 `tripId` 忽略第二次 DELETE。失败 toast + **保持示例态**（不把 preference 写回被删 ID）。**不**扩展共享 `studioModal` 的 loading API。 |
| **D-PDG-04 后端协调（选型锁定）** | 主路径：**原子 `begin_trip_delete` → stop/join on-demand（须新增公共 API）→ 同根 rename 至 `_deleting-{tripId}-{nonce}` → 响应 204（语义=逻辑已摘除，非物理已删完）→ 后台有限重试 rmtree + Studio 启动扫描续删墓碑**。静态服务对 deleting / 原 ID 已 rename 的请求 **≤1s 内** 404/410，**不得再 open 原路径文件**。deleting 集合扩在 `StudioJobStore`（独立集合，**禁止**伪造 StudioJob）；`is_trip_busy` 含 deleting。 |
| **D-PDG-05 半删除 / 失败面** | rename 失败：`E_TRIP_DELETE_FAILED` + 非空 `message`。墓碑以下划线前缀隐藏于 `GET /trips`。前端已执行 D-PDG-02 时：失败**不**回滚到「继续预览已损坏册」。 |
| **D-PDG-06 测试升档** | 新增热路径真测（§9）；AC-D14-04 冷启动回归保留。E2E 使用**有状态** DELETE/list mock；**禁止**依赖会重注入 preference 的 `?bentoPreviewTrip=` 做硬刷新断言。 |
| **D-PDG-07 断开失败策略** | **尽力清空后仍 DELETE**。localStorage 静默写失败**不**作为中止条件（现状 store 不可观测）。若 memory 已切示例则继续删；仅当无法切换到示例 UI（极端）时 toast「无法切换预览，删除已取消」并中止——IMPLEMENTATION 须给出可测判定（如 render 抛错），默认路径不依赖 storage reject。 |
| **D-PDG-08 独立预览页** | **M2 必验**：首页预览 A + 另开该 trip 预览页时删除 A，不得卡死；靠 deleting/static gate，不靠首页 dispose。 |

**挂钩**：本主题为「预览 × 删除」唯一合同；不拆平行「书架清理」大 PRD。

### 0.4 联评 Must-Fix 对照（已消化进合同）

| Must-Fix | v0.2 落点 |
|----------|-----------|
| 修正「setter = dispose 图片请求」 | D-PDG-02 · R1.2 · R-PDG-06 |
| 冻结后端选型，取消「锁或 rename」二选一 | D-PDG-04 |
| 补 on-demand 公共 stop/join | D-PDG-04 · R2.1 · §6 |
| 断开失败可观测 / 改策略 | D-PDG-07 |
| 独立预览页同时打开 | D-PDG-08 · AC-PDG-08b |
| AC 关键词 / 时序 / mock 合同 | §9 · §0.5 |

### 0.5 测试工程约束（联评锁定）

| 约束 | 要求 |
|------|------|
| Fixture | `studioFixture=multi` 等不可变列表**不能**直接当真删；须 **有状态 `page.route`**：记录 DELETE 次数，成功后后续 `GET /trips` 排除该册 |
| 设预览 | 热路径 e2e **通过 UI**（如 `_select_preview_trip`）或等价写入后**去掉**会在刷新时重灌的 URL 参数 |
| 时序（AC-03） | 延迟 DELETE mock；在浏览器包装 `fetch`，于 DELETE **调用瞬间**采样 localStorage / select / demo-flag——禁止只在响应后断言「先断开」 |
| Modal | 不测「确认钮长时间 loading」；测卡片/菜单删除中 + DELETE 次数=1 |
| 后端 AC-07/08 | 提供可控 test hook / barrier（避免靠真实图片处理碰运气）；断言改为状态与 HTTP，不直接断言「文件句柄」 |

---

## 1. 背景与证据

### 1.1 复现路径（用户报告 · 已与代码对齐）

1. 打开 Studio 首页 v2；书架有 ≥1 本用户画册。  
2. 书架「⋯ → 在上方预览」，Bento 切到该册（`bentoPreviewTripId` 持久化）。  
3. 同一本：书架「⋯ → 删除画册」→ 通用确认 → 确认删除。  
4. **观测**：页面卡死 / 浏览器未响应或崩溃。  
5. 硬刷新后：首页恢复；预览回**默认示例**；preference 已被冷启动兜底清除。

### 1.2 环境假设

| 项 | 内容 |
|----|------|
| OS | Windows（文件占用对 `rmtree`/rename 更敏感；实现须兼容 macOS/Linux） |
| Studio | homepage `data-homepage-variant=v2` · `ThreadingHTTPServer` |
| 样本 | 真实用户册（含多档 WebP / 可选 derivativesPreparing）；M2 另含「独立预览页同时打开」 |
| 对照 | 硬刷新恢复 ≡ AC-D14-04 冷启动路径生效，**不证明**热删除路径安全 |

### 1.3 根因分层

| 层 | 根因 | 表象 |
|----|------|------|
| **产品** | 无「正在展示」知情同意 | 用户不知情删掉首页主舞台 |
| **前端状态** | 删除成功不清 preference；依赖异步 reroute | 悬空 ID；删除窗口内仍渲染旧 manifest |
| **前端媒体** | dispose 不 abort 进行中请求；背景/bench probe 无 generation | 切示例后仍可能有旧 GET / 旧回调回写 |
| **并发** | 展示中的静态 GET（含独立预览页）与 `rmtree` / 派生写盘竞态 | Windows 挂起、半删除、500、卡死感 |
| **验收空洞** | 只测冷启动 ghost；harness 无有状态 DELETE | 热路径回归为零 |

### 1.4 联评结论（摘要）

- **开发**：M1 前端止血可行；M2 必须新增 on-demand stop/join + deleting gate；rename 须定义墓碑、列表隐藏、启动续删与 204 语义。  
- **测试**：M1 e2e 可快速补；AC-05 随卡片删除中合同；AC-07/08 选型锁定后方可自动化；禁止 `bentoPreviewTrip=` URL 测硬刷新。

---

## 2. 问题陈述（P-PDG-*）

| ID | 问题 | 严重度 | 证据 |
|----|------|--------|------|
| **P-PDG-01** | 删除正在首页预览的画册时，无专用提醒与许可 | **P0** | `shelf-menu.js` `confirmDelete` 仅通用文案；不读 `bentoPreviewTripId` |
| **P-PDG-02** | 删除热路径不先清空预览 preference / manifest | **P0** | `onTripDeleted` 无 clear；仅 `reroute` / 硬刷新收敛 |
| **P-PDG-03** | 预览中删除可导致页面卡死或浏览器崩溃 | **P0** | 用户复现；rmtree×静态资源×派生线程竞态；独立预览页加重 |
| **P-PDG-04** | 删除无进行中态，易重复点击放大故障 | **P1** | `confirmDelete` / `runDelete` 无 in-flight；modal 关闭后可再点 |
| **P-PDG-05** | 后端删除与 on-demand 派生 / 静态服务无互斥 | **P1** | `is_trip_busy` 仅 job store；无公共 on-demand stop |
| **P-PDG-06** | 「预览中当场删除」无自动化验收 | **P1** | 仅有 `test_ac_d14_04_deleted_trip_fallback`（冷启动） |
| **P-PDG-07** | 前端 dispose 被误认为句柄安全 | **P1** | 联评 R-PDG-06/08；v0.1 合同过承诺 |

---

## 3. 目标与非目标

### 3.1 产品目标

1. **知情同意**：删「当前首页展示画册」时，文案明确告知将切回示例，用户可取消。  
2. **状态事务**：确认删除 ⇒ 先示例、清 preference ⇒ 再删盘；全程无悬空 `bentoPreviewTripId`；reroute 不复活刚删 ID。  
3. **稳定可用**：该路径下页面保持可交互；禁止卡死/崩溃；失败有可读错误；**独立预览页同时打开**亦不挂死（M2）。  
4. **契约闭合**：热删除与冷启动兜底终态一致（示例 + preference 空）。

### 3.2 非目标

- 不改 D-14 Combobox / deep link / stale bar 主模型。  
- 不引入批量删除、回收站 UI、云同步删除。  
- 不重写 derivatives 算法或导入流水线（仅补删除协调 API）。  
- 不改变「示例画册不可删」既有保护。  
- 不要求删除非预览册时也走强确认。  
- 不做服务端「哪些浏览器 session 正在预览」的租约。  
- 不做手机完整制作台删除体验。  
- **不**扩展共享 `studioModal` 为通用异步 loading 对话框（本包用卡片删除中态）。

### 3.3 成功指标

| 指标 | 现状（2026-07-23） | 目标 |
|------|-------------------|------|
| 预览中删除有强确认 | 否 | **是** |
| DELETE 发出前 preference 已空（调用瞬间） | 否 | **是** |
| 预览中删除后页面可交互 | 否（复现） | **100%**（约定样本 + M2 预览页场景） |
| 终态 = 示例 + toast | 仅硬刷新可靠 | **热路径可靠** |
| 自动化覆盖热路径 | 0 | ≥1 条有状态 e2e（M1）+ M2 后端/集成 |

---

## 4. 需求详述

### WS1 · 知情同意与前端事务（P0）— M1

#### R1.1 预览中删除强确认（P-PDG-01 · D-PDG-01）

**Given** 用户打开书架菜单「删除画册」，且 `trip.tripId === V2.bentoPreviewTripId`。

**Then**

- 标题：`删除正在展示的画册？`（锁定）；  
- 正文**必须**同时包含锁定短语（见 §5.1 / AC-PDG-01）；  
- 主按钮危险「删除」；`focusCancel: true`；  
- 遥测：`shelf_delete_confirm` / `cancel` / `success` / `fail` 带 `was_previewing: true|false`。

**非预览册**：通用确认；正文**不得**出现「切回示例」（AC-PDG-02）。

#### R1.2 先断开预览，再发起删除（P-PDG-02 · D-PDG-02 · D-PDG-07）

用户确认「删除」后，顺序**冻结**：

| 步 | 动作 | 失败策略 |
|----|------|----------|
| 1a | 清 `V2.bentoPreviewTripId`、尽力写 localStorage/session；`userManifest`/`userPreviewTrip`→null；切 `demoManifest` 并 `renderBentoSurface` | 默认：**继续**（D-PDG-07）。仅极端无法切示例 UI 时中止 |
| 1b | **媒体尽力释放**（本包新增合同，见下）：dispose carousel/phone；清空可见旧 `img` 的 `src`/`srcset`；背景/bench probe 带 **render generation**，禁止旧回调回写 demo 之后的 DOM | 尽力而为；**不**作为 DELETE 前置硬失败；**不**声称已释放服务端句柄 |
| 2 | 卡片/菜单进入删除中；`deletingTripIds`（或等价）加入 tripId | — |
| 3 | `DELETE /__travelogue/trips/{tripId}` | 失败：toast；**保持示例**；preference 仍空；退出删除中；卡片保留 |
| 4 | 成功：摘卡 + toast（§5.3）；`reroute` 刷新列表 | `applyStoredBentoPreviewPreference` / D-13 迁移 **不得**把刚删 ID 写回；建议校验 `deletingTripIds` / 世代 |

**媒体尽力释放（合同，非现状能力）**

现有 `setBentoPreviewTripId(null)` **不足**。IMPLEMENTATION 须增加等价于 `disposeBentoMedia({ tripId, generation })` 的行为：

- carousel / phone-strip：dispose 监听与 timer **之外**，清空仍挂在 DOM 或即将卸载节点上的 `img.src` / `srcset`；  
- `bento.js` 背景与 bench `new Image()`：generation 校验，过期 onload **禁止**写 DOM；  
- **明确非保证**：已进入 `SimpleHTTPRequestHandler` 的响应、独立预览页请求、杀毒占用 —— 归 D-PDG-04。

**铁律**：禁止「DELETE 成功后再靠 `ensureTripInCatalog` 发现不存在才清 preference」作为热路径唯一手段。

#### R1.3 进行中态与防重入（P-PDG-04 · D-PDG-03）

- Modal 确认后**立即关闭**。  
- 该卡片菜单「删除画册」禁用；可选封面/卡片 `aria-busy=true` 或可见「删除中」。  
- 同一 `tripId` 未决期间再次触发删除 → **忽略**（网络层 DELETE 次数=1）。  
- 不阻塞整页滚动与示例预览浏览。

#### R1.4 成功/失败反馈

| 结果 | 反馈 |
|------|------|
| 成功且曾为预览 | toast：`已删除「{title}」，已切回示例` |
| 成功且非预览 | `已删除「{title}」` |
| DELETE 失败 | 服务端 `message` 优先；否则 `删除失败，请重试`；示例保持；卡片保留可再删 |
| 409 busy | 既有 busy 句；示例已切则不回滚预览 |

#### R1.5 边界（M1 Should · 部分升 M2）

| 边界 | 行为 |
|------|------|
| 最后一本用户册删除成功 | `IdleEmpty` + 示例 + picker 仅示例/禁用态与现网空态一致（Should；M1 冒烟） |
| 离线 | **草案**：删除入口可点则先切示例，DELETE 失败 toast（非回滚）；或 IMPLEMENTATION 选择禁用删除——须写死一种 |
| Fixture / harness | 有状态 mock（§0.5）；虚拟列表删除不得「复活」 |
| 多首页标签页 | Should：不要求实时同步；另一标签硬刷新走 AC-D14-04 |

### WS2 · 后端删除稳定性（P1）— M2

#### R2.1 删除事务（P-PDG-05 · D-PDG-04）

`handle_delete_trip` 顺序锁定：

1. 示例保护 → 403（既有）；  
2. 原子 `begin_trip_delete(trip_id)`：若已 busy（含 job / deleting）→ 409；否则标记 deleting；  
3. **新增** `stop_or_join_on_demand(trip_dir, timeout=…)`（`derivatives.py` 公共 API；禁止锁内长时间 join）；  
4. 静态 gate 已生效（原 ID → 404/410）；  
5. 同根原子 rename → `_deleting-{tripId}-{nonce}`（列表扫描已忽略 `_` 前缀目录——与现 `studio_trips` 约定对齐，IMPLEMENTATION 核实）；  
6. 响应 **204**（逻辑摘除完成）；  
7. 后台线程有限重试 `rmtree(tombstone)`；失败打日志，留墓碑；  
8. **Studio 启动**：扫描 `_deleting-*` 续删。

拿 trip 写锁的时机：rename 前与 `TripService` 写路径协调（避免与 `_persist_trip_json` 交叉）；细节见 IMPLEMENTATION。

#### R2.2 错误面（D-PDG-05）

| 失败点 | 响应 |
|--------|------|
| begin 时 busy | 409 · 既有 / 明确 busy message |
| rename 失败 | 500 · `E_TRIP_DELETE_FAILED` + 非空 message；**清除** deleting 标记（可重试）或保持 deleting 并文档化——IMPLEMENTATION 写死一种且可测 |
| 异步 rmtree 失败 | 不改已返回的 204；启动续删；监控日志 |

前端已先回示例：任意失败**不**恢复旧 preference。

#### R2.3 Windows 与时限

- 约定样本（≥20 张多档 WebP）+ 可选「独立预览页打开」：DELETE（至 204）P95 目标 **\< 5s**（rename 路径）。  
- rename 亦可能 WinError 32/5：有限重试（可参考 `TripService` replace 重试模式）。  
- 禁止依赖用户硬刷新收敛。

#### R2.4 独立预览页（D-PDG-08）

- 首页 Bento 预览 A 时，另开 `/{A}/…` 预览页，再从首页删除 A。  
- 期望：首页可交互、回示例；预览页可 404/诚实失败；**无**长时间未响应。  
- 验收靠 deleting/static gate，不靠首页 `disposeBentoMedia`。

### WS3 · 契约与验收（P1）— M3

#### R3.1 回写 D-14 / DATA-CONTRACT

| 场景 | 行为 |
|------|------|
| 用户删除**当前预览**画册 | 强确认 → 先清 preference 并回示例 → DELETE → 成功 toast；失败保持示例 + 错误 toast |
| preference 指向已删 trip（冷启动） | 保持 AC-D14-04 |
| reroute / D-13 迁移 | 不得复活 `deletingTripIds` 中或刚成功删除的 ID |

#### R3.2 自动化（D-PDG-06 · §0.5 · §9）

见 §9；M3 含邻接文档回写与 AC-D14-04 回归。

---

## 5. 交互与文案规格

### 5.1 强确认（预览中）— 锁定短语

| 元素 | 规格（锁定） |
|------|----------------|
| 标题 | `删除正在展示的画册？` |
| 正文 | `「{title}」是当前首页预览。删除后将切回示例作品，并移除其排版与预览记录。你电脑上的原始照片不会被删除，之后可以用同一文件夹重新导入。` |
| 确认 | `删除`（danger） |
| 取消 | `取消`（默认焦点） |

**AC 用锁定子串**：正文须含 `当前首页预览` **与** `切回示例作品`（标题「展示」**不可**替代正文后果句）。

### 5.2 通用确认（非预览）

> 将移除画册「{title}」及其排版与预览记录。你电脑上的原始照片不会被删除，之后可以用同一文件夹重新导入。

**禁句（AC-PDG-02）**：不得出现 `切回示例`。  
**保留句**：须保留 `原始照片不会被删除`。

### 5.3 Toast

| 场景 | 文案 |
|------|------|
| 预览中删除成功 | `已删除「{title}」，已切回示例`（须同时含「已删除」与「切回示例」） |
| 非预览删除成功 | `已删除「{title}」` |
| 极端无法切示例 | `无法切换预览，删除已取消` |
| DELETE 失败 | 服务端 `message` 优先；否则 `删除失败，请重试` |
| 冷启动兜底（既有） | `原预览画册已不可用，已切回示例` |

### 5.4 状态机（删除当前预览）

```text
[Previewing A]
    → open delete menu
    → ConfirmPreviewDelete
         → cancel → [Previewing A]
         → confirm
              → DisconnectPreview (A → demo)  [preference cleared; media best-effort]
              → CardDeleting  [modal closed]
                   → success → [Demo + shelf without A]
                   → fail    → [Demo + error toast + card remains]
```

---

## 6. 技术实现要点（摸底清单）

| 工作流 | 疑似落点 | 备注 |
|--------|----------|------|
| R1.1 强确认 | `shelf-menu.js` `confirmDelete` | 读 `V2.bentoPreviewTripId` |
| R1.2 清 preference | `bento-tabs.js` `setBentoPreviewTripId(null)` + `source: "shelf_delete"` | 同步清 memory/storage 后即可发 DELETE；勿等全部图片 abort |
| R1.2 媒体释放 | `carousel.js` / `phone-strip.js` / `bento.js` | **新增** generation + 清 src；非现状 |
| R1.3 防重入 | `shelf-menu.js` / `shelf.js` / `trips-client.js` | in-flight Set；卡片禁用 |
| R1.4 双保险 | `shelf.js` `onTripDeleted` | 幂等 clear preference |
| 防复活 | `bento-preview-picker.js` `applyStored…` | 跳过 deleting / 刚删 ID |
| R2.1 deleting | `studio_jobs.py` | `_deleting_trip_ids` + begin/end；纳入 `is_trip_busy` |
| R2.1 on-demand | `derivatives.py` | **新增** `stop_or_join_on_demand`；避免锁内长 join |
| R2.1 静态 gate | `serve.py` `_serve_trip_static` | deleting 或目录已 rename → 404/410 |
| R2.1 rename | `trip_list_handlers.py` | 墓碑 `_deleting-*`；启动续删挂 `studio_lifecycle` / serve 启动 |
| R3.2 e2e | `test_studio_home_v2_ac_playwright.py` | 有状态 route；UI 设预览；fetch 瞬间采样 |
| 后端单测扩 | `test_studio_trip_delete.py` | busy、rename 失败、`E_TRIP_DELETE_FAILED`、deleting 静态 404 |
| 合同回写 | Homepage v2 §6.8.4 · DATA-CONTRACT | 结案必写 |

**禁止**：

- 仅在 `catch` 里 toast 而不清 preference；  
- DELETE 成功后才第一次 `clearBentoPreviewTripId` 作为唯一清口；  
- 用整页 `location.reload` 掩盖竞态；  
- 伪造 StudioJob 表示 deleting；  
- 在 PRD/注释中声称「前端 dispose = Windows 文件句柄已释放」。

---

## 7. 里程碑

| 里程碑 | 范围 | 出口 |
|--------|------|------|
| **M1（P0 止血）** | R1.1～R1.4；媒体尽力释放最小集；防复活最小集 | AC-PDG-01～04、06；AC-05 随卡片删除中一并交付（见下） |
| **M2（删除稳定）** | R2.1～R2.4；on-demand API；启动续删 | AC-PDG-05（若 M1 已交则可回归）、07、08、08b |
| **M3（契约闭合）** | R3.1～R3.2；邻接回写 | AC-PDG-09～10；主题 Done |

> **合入策略（联评）**：M1 可先合（用户侧止血）。M2 紧随或同车——避免「文案对了但 Windows / 预览页仍偶发卡死」。AC-PDG-05 不依赖扩展 `studioModal`，可在 M1 与卡片删除中态同车。  
> Windows 大样本可作手工/夜间，**不挡** M1；**挡**主题 Done（与 AC-07 挂钩）。

---

## 8. 遥测

| 事件 / 字段 | 用途 |
|-------------|------|
| `shelf_delete_confirm` + `was_previewing` | 强确认曝光 |
| `shelf_delete_cancel` + `was_previewing` | 取消率 |
| `shelf_delete_success` + `was_previewing` | 成功且曾预览 |
| `shelf_delete_fail` + `was_previewing` + `error` | 失败归因 |
| `bento_preview_select` `source=shelf_delete`（`trip_id: null`） | 断开预览可观测 |

`shelf_delete_fail` 若不在 allowlist，IMPLEMENTATION 须同步 allowlist（或复用现有失败埋点字段）。

---

## 9. 验收标准（AC-PDG-*）

| ID | 标准 | 验证 |
|----|------|------|
| **AC-PDG-01** | 当前预览册删除弹层：正文同时含锁定子串 `当前首页预览` 与 `切回示例作品`；标题为 `删除正在展示的画册？` | Playwright |
| **AC-PDG-02** | 非预览册删除弹层：含 `原始照片不会被删除`；**不出现** `切回示例` | Playwright |
| **AC-PDG-03** | 预览中点确认后：在 **DELETE 请求调用瞬间**，`localStorage['travelogue.studio.v2.bentoPreviewTripId'] === null`（键不存在或显式清除）、`#v2-bento-preview-select` 值为 `""`、可见 demo-flag 数 **= 2**；该 DELETE 不得早于断开完成 | Playwright：延迟 mock DELETE + 包装 `fetch` 采样 |
| **AC-PDG-04** | 成功：toast 同时含「已删除」与「切回示例」；目标卡在响应后 **500ms** 内离开书架 DOM；**设置按钮**（或约定控件）在 **5s** 内可点击 | Playwright + 有状态 list mock |
| **AC-PDG-05** | 删除未决期间：卡片/菜单删除禁用或 `aria-busy`；延迟 1s 内连续重入，**DELETE 网络次数 = 1** | Playwright（不测 modal 确认钮长时间 loading） |
| **AC-PDG-06a** | mock **409**：toast 含服务端 message；示例保持；preference 空；卡片仍在 | Playwright |
| **AC-PDG-06b** | mock **500** + JSON message：展示该 message；同上状态 | Playwright |
| **AC-PDG-06c** | mock **500** 无/非 JSON body：toast `删除失败，请重试`；同上状态 | Playwright |
| **AC-PDG-07** | 存在 on-demand 派生（test hook 模拟线程/barrier）时删除：至 204 **无无限挂起**（超时 **5s**）；目录已 rename 出逻辑树或已物理删除；join/stop 超时策略可测（建议 stop 预算 **2s**） | pytest 集成 + hook；Windows 夜间/手工补充大样本 |
| **AC-PDG-08** | 进入 deleting 后：针对该 tripId 的**新**静态 GET 在 **1s** 内 404/410；允许已开始的 GET 完成，但其不得阻塞 rename 超过重试预算 | 集成 |
| **AC-PDG-08b** | 首页预览 A + 独立预览页打开 A → 首页删除 A：首页 **5s** 内可交互且为示例；无 Page crash | Playwright 或脚本化双页 + 集成 |
| **AC-PDG-09** | AC-D14-04 冷启动不回退；并断言 preference storage 为空、`pageerror` 数 = 0 | 既有 e2e 加强 |
| **AC-PDG-10** | 热删除成功后硬刷新：仍为示例；**不得**使用会重灌 preference 的 `bentoPreviewTrip` URL；mock 列表持续排除已删册；`pageerror` = 0；刷新后设置按钮可点（`networkidle` 或等价 ≤10s） | Playwright |

**M1 门禁**：AC-PDG-01～05、06a～c 必绿（05 与卡片删除中同车）。禁止只改文案而不做「先清 preference」。  
**M2 门禁**：AC-PDG-07、08、08b。  
**主题 Done**：M1+M2+M3 + 邻接回写。

---

## 10. 风险与开放问题

| # | 项 | 状态 |
|---|-----|------|
| 1 | 后端删除选型 | **已锁** D-PDG-04（rename + 异步 + 启动续删） |
| 2 | 强确认是否含「预览不可用仍选中」 | **已锁** D-PDG-01：`bentoPreviewTripId` 相等即触发 |
| 3 | 删除失败重试入口 | **已锁草案**：M1 仅 toast；卡片仍在则可再次删除 |
| 4 | 前端 abort 图片请求 | **已锁**：尽力释放（R1.2 1b）；句柄安全归后端 |
| 5 | 409 与预览文案优先级 | **已锁**：先断开再 DELETE；409 不回滚示例 |
| 6 | 服务端预览租约 | **Park** |
| 7 | 离线删除：禁用 vs 先断开再失败 | **开放**：IMPLEMENTATION 二选一写死 |
| 8 | rename 失败后 deleting 标记保留还是清除 | **开放**：IMPLEMENTATION 写死且配测 |
| 9 | 重复 DELETE 在墓碑仍在时返回 204 还是 404 | **Should**：倾向对原 ID 404；幂等不报错惊吓用户 |
| 10 | 多标签页 preference 同步 | **Park / Should**：硬刷新兜底即可 |
| 11 | 跨进程持久删除队列 | **Park**：V1 墓碑启动续删足够 |

---

## 11. 变更记录

| 版本 | 日期 | 变更 |
|------|------|------|
| v0.1 | 2026-07-23 | 初稿 · 用户复现 + 代码探查 R-PDG-01～05 · 决策候选 D-PDG-01～06 · M1–M3 · AC-PDG-01～10 |
| v0.2 | 2026-07-23 | **Conditional Go** · 开发/测试联评回写：修正 D-PDG-02 过承诺；锁定 D-PDG-04 rename 主路径与 on-demand API；D-PDG-03 卡片删除中态；D-PDG-07 尽力清空仍 DELETE；D-PDG-08 独立预览页 M2 必验；AC 收紧（锁定短语、fetch 瞬间采样、06 分例、08b、有状态 mock）；补 R-PDG-06～08 |

---

## 附录 A · 关键代码锚点（探查时）

| 区域 | 路径 |
|------|------|
| 删除确认 / 菜单 | `templates/studio/homepage-v2/shelf-menu.js` |
| 删除后书架 | `templates/studio/homepage-v2/shelf.js` `onTripDeleted` |
| 预览 preference | `templates/studio/homepage-v2/store.js` · `bento-tabs.js` |
| carousel / phone dispose | `carousel.js` · `phone-strip.js`（现状不足 abort） |
| 背景 / bench probe | `bento.js` |
| 冷启动兜底 | `bento-tabs.js` `refreshBentoUserPreview` · `bento-preview-picker.js` `applyStoredBentoPreviewPreference` |
| Modal（无 loading API） | `templates/studio/studio-modal.js` |
| DELETE API | `travelogue/web/studio_handlers/trip_list_handlers.py` `handle_delete_trip` |
| Job / busy | `travelogue/web/studio_jobs.py` |
| 派生后台线程 | `travelogue/media/derivatives.py` `materialize_on_demand`（无私有 join 公共 API） |
| 静态资源 | `travelogue/web/serve.py` `_serve_trip_static` |
| 既有删除 API 测 | `tests/unit/web/test_studio_trip_delete.py` |
| 既有冷启动测试 | `tests/e2e/test_studio_home_v2_ac_playwright.py` `test_ac_d14_04_deleted_trip_fallback` |

## 附录 B · 与 AC-D14-04 的分工

| | AC-D14-04 | 本主题 AC-PDG-* |
|--|-----------|-----------------|
| 触发 | 打开首页时 preference 已指向不存在 trip | 用户在预览 A 时主动删除 A |
| 用户许可 | 无（修复损坏状态） | **必须**强确认 |
| 主修复手段 | 发现无效 → 清 preference | **先**清 preference → 再删 |
| 是否可替代本包 | **否** | — |

## 附录 C · 联评决议速查

| 当场拍板 | 结论 |
|----------|------|
| 后端主路径 | rename + 异步 rmtree + 启动续删 |
| AC-05 UI | 卡片/菜单删除中，不扩展 `studioModal` |
| 断开失败 | 尽力清空后仍 DELETE |
| 独立预览页 | M2 必验，不 Park |
| Go 门 | Conditional Go → 可开 IMPLEMENTATION / M1 |
