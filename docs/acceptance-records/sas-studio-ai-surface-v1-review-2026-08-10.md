# PRD-STUDIO-AI-SURFACE-V1 · 七席+1 评审纪要

| 属性 | 内容 |
|------|------|
| **文档** | [PRD-STUDIO-AI-SURFACE-V1.md](../PRD-STUDIO-AI-SURFACE-V1.md)（**SAS** · 预览 AI 应用面） |
| **关联** | [线框](../wireframes/studio-ai-surface-v1-wireframe.html) · [PRD-AI-RETURN-V1.md](../PRD-AI-RETURN-V1.md)（AIR）· [PRD-AI-CAPABILITY-PLATFORM-V1.md](../PRD-AI-CAPABILITY-PLATFORM-V1.md)（ACP）· [PRD-COVER-CALLIGRAPHY-TITLE-V1.md](../PRD-COVER-CALLIGRAPHY-TITLE-V1.md)（CAL）· [PRD-NO-AI-SURFACE-V1.md](../PRD-NO-AI-SURFACE-V1.md)（NAS） |
| **评审版本** | PRD **v0.1.0** → Must-Fix 回写后升 **v0.2.0** ✅ |
| **日期** | 2026-08-10 |
| **结论** | **有条件通过（Conditional Go · 可冻结策划；W1 以「Dock + Sheet 壳 + 杂志文案现网解冻 + 装帧标题主入口」Kickoff；三语气 / Intent·建议汇总不得假装已有后端）** |
| **编码** | ☑ **策划冻结（v0.2.0 · BLK 已关）**　☑ W1 壳+杂志+装帧　☑ W2 意图/建议/徽标/旧入口收敛　☑ W3 狗粮与埋点收口（见 ACCEPTANCE + dogfood 纪要） |
| **参评角色（七席 + 1）** | 产品 · 算法 · 架构 · 开发 · 测试/QA · 视觉/排版 · 用户体验（狗粮手测） · **典型用户（真实旅行者视角）** |
| **评审方式** | 分席只读 PRD §0～§13 · D/G/AC/OQ + 线框 F0–F6 + **对照现网**（`preview-toolbar/init-v3.js` Dock、`export_handlers.handle_narrate`、`title_art_handlers`、`features.js` 装帧标题、`chapter-panel.js` layoutSuggestions、`ai-surface.js`、`analytics.js` allowlist、`core.js` narrate） |
| **记录人** | 七席+1 联合纪要（跨职能模拟联评 · 基于 2026-08-10 PRD v0.1.0 + 代码事实核查） |
| **本纪要状态** | **已结案 · Conditional Go** · **PRD v0.2.0 已回写 BLK-SAS-01～05** |
| **审查基线** | 勾选≠自动烧 API · Fail-open · 与精修分权 · 不硬推能力卡 · 本地 Key · 不把 ops 塞进用户主路径 |

---

## 0. 会前宣读（主持人）

1. **切口**：SAS = 预览 Dock 一级「AI」+ Sheet 汇聚「会烧模型 / 需显式点」的动作；**不是**第二套 ACP，也不是重写 narrate Prompt。
2. **勿重开**：装帧风格白名单（CAL）、Agent 预算算法（ACP）、渠道包成功面（AIR F-AIR-03）——本场只审「入口 IA、门控诚实、与现网能力是否对齐、杂志文案解冻边界」。
3. **本场必拍**：Dock 落位是否对得上现网拥挤 Dock；「三语气」是否已有 API；`aiSurfaceEnabled` 是否覆盖装帧标题；AIR 仍 Draft 时 SAS 宣称「解冻整合」会不会双合同空转。
4. **列车**：关 BLK → v0.2 冻结；W1 可 Kickoff 但范围收窄为「壳 + 现网 narrate 解冻入口 + 装帧标题」；Intent/建议/徽标走 W2。

---

## 1. 总评（一句话）

> **八席一致 Conditional Go：预览要有一级 AI 入口、杂志文案解冻进 Sheet、勾选不自动烧钱——方向对、线框可用；但 v0.1 有五处会在 Kickoff 后翻车——（1）D-SAS-02 写的 Dock 顺序是理想化「精修→AI→播放→导出」，现网 v4 实际是「返回 | 播放 | 分章 | 精修 | 文件夹 | 导出…」，落位合同必须按现网重写；（2）AC-SAS-08 / F-SAS-05 要求三语气 `voice`，但 `POST /__travelogue/narrate` 现网不接受、也不消费 `voice`，AIR 三语气仍是 Draft 合同——若 W1 假装已有会假绿；（3）铁律把一切动作套进 D-ACP-14 AND，但 `title-art/resolve` 现网不经 `aiSurfaceEnabled` 硬门闩，与杂志文案/ACP Agent 门控不同，必须分动作门控表；（4）AIR 主题本身未 Go，SAS 写「解冻整合」易变成两个 Draft 互相指——须钉死 W1 杂志文案 = **现网 narrate 入口解冻**（确认框+配置引导+busy），不含渠道包/三语气；（5）§7 新增 `ai_sheet_*` 事件未进 `analytics.js` allowlist，不写进 AC 会再次假绿。关 BLK 后升 v0.2；W1 可开工，W2 再接 Intent/建议汇总。**

---

## 2. 分席表决

| 席位 | 表决 | 一句话 |
|------|------|--------|
| **产品** | **Conditional Go** | 发现性切口对，杂志文案进 Sheet 也符合「解冻要有可见权威入口」。但不要把 AIR 整包（语气+渠道）绑进 SAS W1，否则又变成悬置双主题。W1 讲清楚「能生成杂志感」，语气/渠道仍归 AIR 后续切片。 |
| **算法** | **Conditional Go** | UI 不碰算法即可。提醒：Intent「重新解析」与 Layout 建议采纳仍是 advisory；Sheet 文案不要承诺「一键改好整本结构」。建议长度继续吃 SHD-ACP-02（≤28/36）。 |
| **架构** | **Conditional Go** | Sheet 复用既有 API、不平行造密钥——对。但门控叙事把 ACP AND、NAS surface、CAL title-art、narrate Key 揉成一句铁律，会误导实现；要一张**分动作门控矩阵**当唯一真源。 |
| **开发** | **Conditional Go** | W1 若含：新 Dock 钮 + 新 Sheet（含与精修/分章互斥）+ narrate 迁入 + title-art 双入口同步 + 意图 + 建议列表 + 徽标 unread + 旧入口收敛 + 窄屏——单人一周不现实。必须按 PRD §8 真切开：W1 壳+杂志+装帧；W2 建议/意图。另：Dock 现已挤（分章/播放/文件夹），「AI」插入点要写死相对节点，不能写散文。 |
| **测试 / QA** | **Conditional Go** | AC-SAS-05（勾选零外呼）可测且关键。AC-SAS-08（语气）现网无法测到绿。AC-SAS-12 未开闸零外呼需明确是否含 title-art（现网 refine 仍可点）。埋点 allowlist 必须进 AC。 |
| **视觉 / 排版** | **Conditional Go** | 右侧 Sheet 与精修同侧可以，但要互斥 + 复用 `preview-sheet-open` 一类 body 态，避免双遮罩/z-index 打架。Dock 再加文案钮，「AI」桌面用短标、窄屏图标——同意 D-SAS-01。建议卡片文案长度跟 CTS/ACP 硬顶。 |
| **用户体验（狗粮手测）** | **Conditional Go** | 狗粮痛点就是「有 AI 找不到」。F4 未开闸仍露按钮——可以，但文案别吓人；「了解如何开启」不能链到空白页。装帧标题十几秒：同意可关面板，但完成后要有 toast，否则用户以为没跑。 |
| **典型用户（真实旅行者视角）** | **Conditional Go** | 我只关心：①点开 AI 会不会自己扣我的 Key 钱；②「AI」和「精修」我到底用哪个改封面/改字；③生成杂志文案会不会把我刚改好的句子冲掉；④没配 Key 时那个按钮是不是在骂我没配好。这四条写进人话承诺我才安心。 |

**汇总**：**8/8 Conditional Go**。

**对齐评分**

| 维度 | 分（/10） | 说明 |
|------|-----------|------|
| 问题→方案因果完整度 | **8** | 发现性缺口真实；线框与 IA 对齐 |
| 与既有 AI 主题边界 | **7** | 方向清；与 AIR 切片边界 v0.1 偏糊 |
| 工程可开工性（W1） | **6** | 壳+入口可开；voice/意图捆绑拉分 |
| AC 可测性 / 防假绿 | **5** | 语气 AC 与 allowlist 缺口明显 |
| 对独立开发者的现实性 | **6** | 需严格执行 W1/W2 切开 |
| 用户可感知的信任与成本 | **7** | 铁律方向对；门控分动作后更稳 |

---

## 3. 事实核查（对照现网）

| # | 断言 | 会中核查 |
|---|------|---------|
| **F-01** | 预览 Dock v4 顺序为「精修 →（AI）→ 播放 → 导出」 | ❌ **不属实**：`init-v3.js` 在 menuWrap 前插入 **播放** 与 **分章**；其后还有 **文件夹**、导出 split 等。理想化顺序不能直接当实施合同 |
| **F-02** | `POST /__travelogue/narrate` 支持请求体 `voice` | ❌ **不属实**：`handle_narrate` 只读 `tripId`；`run_studio_llm_narrate` 无 voice 参数；全库 `llm_narrate` 无 voice 产品字段 |
| **F-03** | narrate 受 `aiSurfaceEnabled` 硬门闩 | ✅ `export_handlers.handle_narrate` 在 Key 检查前 403（NAS BE-NAS-02） |
| **F-04** | title-art resolve 同样受 `aiSurfaceEnabled` 门闩 | ❌ **不属实**：`title_art_handlers.handle_post_resolve_title_art` **无** surface 检查；精修内装帧标题在 NAS 默认面仍可能可达 |
| **F-05** | 装帧标题「勾选≠生成」已在精修落地 | ✅ `features.js`：`data-title-art-routec-check` + 点击 `data-title-art-btn` 才 POST resolve |
| **F-06** | layoutSuggestions 已有章面板消费 | ✅ `chapter-panel.js` 读 `entry.layoutSuggestions` |
| **F-07** | `ai_sheet_open` 等事件已在 analytics allowlist | ❌ **不属实**：`analytics.js` 有 `llm_narrate_*` / `title_art_*` / `intent_brief_applied`，**无** `ai_sheet_*` |
| **F-08** | narrate 在 `structure_draft` 会 409 | ✅ 属实（须先分章确认）；v0.1 未写入 Sheet 状态机 |
| **F-09** | NAS 默认面已切断 Dock→narrate | ✅ `init-v3.js` 注释 M11；与「SAS 重新挂权威入口」叙事一致 |
| **F-10** | AIR 三语气 / 渠道包 v2 已工程落地 | ❌ AIR 仍 Draft；渠道/voice 未进 narrate 主链 |

---

## 4. 全场共识

1. **要有一级 AI 入口**——发现性问题成立，线框 F0/F1 可作为视觉合同。
2. **杂志文案必须进 Sheet（解冻）**——同意 D-SAS-06 产品意图；但 W1 范围 = **现网 narrate 能力的入口解冻**，不是 AIR 全量。
3. **勾选不烧 API、建议只读采纳、Fail-open**——维持铁律。
4. **必须按现网重写 Dock 落位**，并规定与分章面板/精修的互斥矩阵。
5. **必须分动作门控表**，停止用一句 D-ACP-14 覆盖 title-art。
6. **W1/W2 切开写死**：意图汇总、建议徽标、旧入口大收敛可 W2；不挡 W1 壳与杂志/装帧。
7. **埋点进 allowlist** 与 AC 绑定，防假绿。

---

## 5. Must-Fix（阻塞 · 升 v0.2 前关闭）

| ID | 议题 | 要求（冻结一字面） | 挡 | 状态 |
|----|------|-------------------|----|------|
| **BLK-SAS-01** | Dock 落位与现网不符 | 重写 **D-SAS-02**：AI 插入点以现网 v4 为真源——默认插在 **「精修」右侧（menu-wrap 之后、导出区之前）**；桌面短标「AI」，窄屏图标。§4.1 附「相对节点」说明；线框 F0 注记「示意，以 D-SAS-02 为准」。 | W1→v0.2 | ✅ **已回写 v0.2.0** |
| **BLK-SAS-02** | 三语气 AC 假绿 | **AC-SAS-08 降级**：W1 只验收「生成杂志感文案」（现网 narrate，无 `voice`）。三语气 UI/API 标为 **依赖 AIR**，另立 AC-SAS-08b（AIR voice 落地后），不挡 SAS W1 Done。F-SAS-05.2 同步删「W1 必须可选 voice」。 | W1→v0.2 | ✅ **已回写 v0.2.0** |
| **BLK-SAS-03** | 门控混写 | 新增 **D-SAS-15 分动作门控矩阵**（surface / capability / key / CAL 旗标）；修订铁律第 4 条：禁止再写「一切动作 = D-ACP-14 AND」。title-art 保持 CAL 既有门控（可在 surface 关时仍从精修次入口使用，除非产品另拍「surface 关则双隐藏」——默认 **不**强行给 title-art 加 NAS 403）。 | W1→v0.2 | ✅ **已回写 v0.2.0** |
| **BLK-SAS-04** | 与 AIR 双 Draft 空转 | 新增 **D-SAS-16**：SAS W1 杂志文案 = 现网 `POST /narrate` 入口解冻（确认、busy、失败归因、配置引导、`source=ai_sheet`）；**不含**渠道包 UI、**不含**三语气。AIR 仍拥有 Prompt/渠道/语气产品语义；SAS 拥有预览壳。PRD §12 关系图同步。 | W1→v0.2 | ✅ **已回写 v0.2.0** |
| **BLK-SAS-05** | 埋点 allowlist | §7 明确：W1 合并前必须把 `ai_sheet_open` / `ai_sheet_close` / `ai_sheet_action_click` / `ai_sheet_action_result`（及 gate_view 若做）写入 `templates/studio/js/analytics.js` allowlist；**AC-SAS-17** 改为可自动断言 allowlist 含上述事件。 | W1→v0.2 | ✅ **已回写 v0.2.0** |

**Should-Fix（不阻塞 v0.2，挡后续里程碑）**

| ID | 建议 | 状态 |
|----|------|------|
| **SHD-SAS-01** | Sheet 状态机写入 `structure_draft` → 杂志文案 CTA 说明「请先在分章确认」（对齐全 F-08） | ✅ W1 |
| **SHD-SAS-02** | AI Sheet 与精修共用/对齐 body class（如 `preview-sheet-open`）与 z-index，避免双开残影；并与**分章面板**互斥或降级规则写清 | ✅ W1（AI 用 `preview-ai-sheet-open`） |
| **SHD-SAS-03** | 建议卡片文案长度：优先 ≤28 字、硬顶 36（对齐 SHD-ACP-02） | ✅ W2 |
| **SHD-SAS-04** | 杂志文案生成对用户手改字段的覆盖策略：确认框补一句「将重写版心文案（含你改过的句子）」或提供保留手改 OQ | ✅ W1 |
| **SHD-SAS-05** | Dock 拥挤：若窄屏放不下，优先保 导出/精修/AI，文件夹可进溢出菜单（另评，不挡 W1） | ✅ W2（≤720 隐藏文件夹） |
| **SHD-SAS-06** | 「了解如何开启」须落到真实帮助锚点或内测说明页，禁止死链 | ✅ W1（Sheet 内联说明） |

---

## 6. 典型用户提问 Q&A

| 提问 | 会中回应（对应决策） |
|------|----------------------|
| ① 点开 AI 会不会自己扣钱？ | 副标题「不自动消耗额度」+ 勾选不请求（AC-SAS-05）+ 生成前确认（杂志文案） |
| ② AI 和精修有啥区别？ | COPY-SAS-08：版式/书衣/手工改字用精修；要模型生成用 AI；互斥打开（D-SAS-04） |
| ③ 生成杂志文案会冲掉我改过的字吗？ | SHD-SAS-04：确认框必须诚实；W1 默认行为 = 现网 narrate 覆盖策略，不假装「智能合并」 |
| ④ 没配 Key 按钮还在，是不是坏了？ | D-SAS-07：可见为发现性；Sheet 引导配置，不报整单失败（D-SAS-12） |

---

## 7. 对 OQ 的会中倾向（不替代产品终裁）

| OQ | 会中倾向 | 是否升 BLK |
|----|----------|------------|
| **OQ-SAS-01**（AI vs 智能） | 维持 **AI** | 否 |
| **OQ-SAS-02**（正式包隐藏高级） | **隐藏** | 否 |
| **OQ-SAS-03**（精修装帧次入口） | W1 保留 | 否 |
| **OQ-SAS-04**（徽标是否含杂志） | 仅排版建议 | 否 |
| **OQ-SAS-05**（Sheet 内同步钩子） | 否 | 否 |
| **（新增）title-art 是否纳入 NAS 403** | 默认不纳入（BLK-SAS-03） | 已进 D-SAS-15 |

---

## 8. 里程碑裁定

| 里程碑 | 本场裁定 |
|--------|----------|
| **策划冻结（v0.2）** | **批准**：关 BLK-SAS-01～05 后 |
| **W1（壳 + 杂志现网解冻 + 装帧主入口）** | **批准 Kickoff** |
| **W2（意图 / 建议 / 徽标 / 旧入口收敛）** | **不批开工**直至 W1 AC-SAS 壳与杂志/装帧项绿 |
| **W3（狗粮 + 埋点收口）** | 维持；可与 AIR 语气切片并行但不阻塞 SAS Done（无 voice） |

---

## 9. 签核

| 席位 | 签字（模拟） | 日期 |
|------|--------------|------|
| 产品 | Conditional Go · W1 不绑 AIR 全量 | 2026-08-10 |
| 算法 | Conditional Go · advisory 话术勿过度承诺 | 2026-08-10 |
| 架构 | Conditional Go · 分动作门控矩阵 | 2026-08-10 |
| 开发 | Conditional Go · Dock 相对节点 + W1 瘦身 | 2026-08-10 |
| 测试 / QA | Conditional Go · 去掉 voice 假绿 AC · allowlist | 2026-08-10 |
| 视觉 / 排版 | Conditional Go · Sheet 互斥与 z-index | 2026-08-10 |
| 用户体验 | Conditional Go · 完成后 toast · 开启链别死 | 2026-08-10 |
| **典型用户** | Conditional Go · 四条信任承诺落实 | 2026-08-10 |

---

## 10. 下一步（主持人交办）

1. ✅ **BLK-SAS-01～05 回写** PRD **v0.2.0**。
2. 线框 F0 增加「落位以 D-SAS-02 为准」注记；F1 杂志卡去掉 W1 语气选择器（或标「AIR 后续」）。
3. ✅ 拆 `ACCEPTANCE-STUDIO-AI-SURFACE-V1.md` / `IMPLEMENTATION-STUDIO-AI-SURFACE-V1.md`；W3 狗粮见 `sas-studio-ai-surface-v1-w3-dogfood-2026-08-10.md`。
4. **不**在本主题 Kickoff 时默认可改 `aiSurfaceEnabled` 正式发版默认值（仍受 OQ-AIR-01）。
5. ✅ 主题编码收口（W1～W3）；合入 master 后可并行 AIR / OQ-AIR-01 狗粮样本。
