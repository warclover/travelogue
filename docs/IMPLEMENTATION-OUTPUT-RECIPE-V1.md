# Travelogue · 输出配方引擎 V1 实施任务清单

| 属性 | 内容 |
|------|------|
| **PRD** | [PRD-OUTPUT-RECIPE-V1.md](./PRD-OUTPUT-RECIPE-V1.md) **v1.1.0** |
| **验收** | [ACCEPTANCE-OUTPUT-RECIPE-V1.md](./ACCEPTANCE-OUTPUT-RECIPE-V1.md) |
| **ADR** | [016-longshot-platform-export.md](./adr/016-longshot-platform-export.md) 分支 D |
| **评审** | [output-recipe-v1-review-2026-07-14.md](./acceptance-records/output-recipe-v1-review-2026-07-14.md) |
| **状态** | Draft · **Phase A 开发中（M-OR.0～A3）** |
| **更新** | 2026-07-14 |

---

## 落地原则

1. **先解析后 UI**：`resolve_output_recipe` 单测绿再接意图卡。  
2. **Phase A 禁止假九宫格**：无 Writer 则无「九宫格」可点入口。  
3. **feature flag**：`studio.output_recipe.enabled` 可一键回退。  
4. **分支 A/B 零回归**：chat / moments scroll 行为不因 Recipe 层破坏。  
5. **分支 D 独立**：grid 不走 full longshot capture。  
6. **本清单 Phase A 已开工**（产品授权 2026-07-14）。

---

## 里程碑总览

| 里程碑 | 目标 | 周期（估） |
|--------|------|------------|
| **M-OR.0 合同** | ADR-016 D · YAML 骨架 · `E_OR_*` · flag | 2–3 日 |
| **M-OR.A1 解析** | resolve + kept_n + Band 单测 | 3–5 日 |
| **M-OR.A2 CTA/意图** | Sparse/Narrative CTA · Ambiguous 二选一 · 入口矩阵 | 3–5 日 |
| **M-OR.A3 回归** | 导出门面 C1 · LNG2 moments · 书架 | 2–3 日 |
| **M-OR.B0 grid 基础** | 分支 D Writer · 1:1 contain · 无三拼 | 1–2 周 |
| **M-OR.B1 三拼 + xhs 卡** | h_triple_stitch · Ambiguous 扩卡 · 诚实 xhs | 1–2 周 |
| **M-OR.C 持久化** | trip.output · prefs · API | 1 周 |
| **M-OR.D 扩展** | custom · IG hook_only | 后置 |

**Phase A ≈ M-OR.0～A3（约 1–2 周）**  
**Phase B ≈ M-OR.B0～B1（约 2–4 周）**

---

## M-OR.0 合同与护栏

| ID | 任务 | 建议位置 | 状态 |
|----|------|----------|------|
| DOC-OR-01 | PRD v1.1 / ACCEPTANCE / 本清单 / 评审回写 | `docs/` | ☑ 本文档任务 |
| DOC-OR-02 | ADR-016 增补分支 D | `docs/adr/016-…` | ☑ 本文档任务 |
| BE-OR-01 | `studio.output_recipe.enabled` + bands 配置键 | `config.py` / example | ☑ |
| BE-OR-02 | 分配 `E_OR_*` 写入 ERROR-CODES | `docs/ERROR-CODES.md` | ☑ |
| BE-OR-03 | presets/bands YAML 骨架（可先挂 `platform_profiles.yaml`） | `config/` | ☑ |

---

## M-OR.A1 解析层

| ID | 任务 | 建议位置 | 状态 |
|----|------|----------|------|
| BE-OR-10 | `kept_n` **单一计数函数**（对照 longshot `photo_count`） | `output_recipe/` 或 export 工具 | ☑ |
| BE-OR-11 | `resolve_output_recipe(...)` 纯函数 | `travelogue/export/output_recipe/` | ☑ |
| BE-OR-12 | entrypoint：`preview` / `shelf` / `cli` 分支 | 同上 | ☑ |
| BE-OR-13 | 单测 AC-OR-01～04、03b、10 | `tests/unit/…` | ☑ |
| BE-OR-14 | CLI `resolve-output-recipe` | CLI 入口 | ☑ |

---

## M-OR.A2 Studio 决策面

| ID | 任务 | 建议位置 | 状态 |
|----|------|----------|------|
| FE-OR-01 | 主 CTA 词表随 Band（附录 C） | `longshot-export-panel.js` 等 | ☑ |
| FE-OR-02 | Ambiguous 意图卡：发群 / 长图连读；**选择并导出** | 同上 | ☑ |
| FE-OR-03 | 「先选不导出」+ 记住偏好（默认关） | 同上 | ☑ 先选不导出；记住偏好 UI 未做（默认关） |
| FE-OR-04 | `layoutPending` 优先于意图卡 | 与导出门面协作 | ☑ |
| FE-OR-05 | 书架 Ambiguous fallback + 弱提示 | 书架导出 | ☑ |
| FE-OR-06 | Narrative≥50 副文；整卷二次确认 | 导出面板 | ☑ |
| FE-OR-07 | 成功态：类型名 + guide；失败「换种分享方式」 | task-dock / modal | ☑ |
| FE-OR-08 | **无**九宫格可点入口（或即将推出 disabled） | UI 护栏 | ☑ |
| BE-OR-20 | `POST /longshot` 接受 `intent`；服务端先 resolve | `export_handlers.py` | ☑ |
| BE-OR-21 | CLI `--intent`；与 `--platform` 冲突表 | CLI | ☑ |

---

## M-OR.A3 回归与发布护栏

| ID | 任务 | 状态 |
|----|------|------|
| QA-OR-01 | AC-OR-08 / NR-EXP-C1～C3 签字 | ☐ 静态护栏已加；手测/Playwright 签字待 |
| QA-OR-02 | LNG2 moments + 书架 M14 子集 | ☑ 单测护栏 |
| QA-OR-03 | 文案/代码扫描：无九宫格→scroll | ☑ |
| BE-OR-30 | flag off 回退单测 AC-OR-13 | ☑ |
| TEL-OR-01 | `output_recipe_resolve` / `intent_*` 事件 | ☑ |

---

## M-OR.B0 分支 D · grid 基础

| ID | 任务 | 建议位置 | 状态 |
|----|------|----------|------|
| BE-OR-40 | `moments_grid_writer`：1:1 contain；N=`min(9,kept_n)` | 新模块 | ☑ |
| BE-OR-41 | 路由：`engine=photo_grid` → 分支 D | `longshot.py` | ☑ |
| BE-OR-42 | 原子写盘（复用 Writer 模式） | 同上 | ☑ |
| BE-OR-43 | 专用 publishGuide（九宫格） | YAML | ☑ |
| FE-OR-20 | Ambiguous 卡启用「九宫格」；名实 AC-OR-11b | UI | ☑ |
| QA-OR-10 | AC-OR-09 / 09b / 07b·grid CLI | ☑ |

---

## M-OR.B1 三拼 + xhs 主卡

| ID | 任务 | 状态 |
|----|------|------|
| BE-OR-50 | `h_triple_stitch`（横仅与横拼） | ☐ |
| FE-OR-21 | xhs 主卡弱权重 + 诚实标注 | ☐ |
| FE-OR-22 | 连读降为子项 / ▾ | ☐ |
| QA-OR-11 | AC-OR-14、15；H-B 手测 | ☐ |

---

## M-OR.C / M-OR.D（后置摘要）

| ID | 任务 | Phase |
|----|------|-------|
| BE-OR-60 | `trip.json` `output` 字段读写 | C |
| BE-OR-61 | GET/PUT output-recipe API | C |
| FE-OR-30 | band preference | C |
| BE-OR-70 | custom 白名单 | D |
| BE-OR-71 | `instagram_carousel` hook_only preset | D |

---

## `--intent` / `--platform` 优先级（实施冻结建议）

| 情况 | 行为 |
|------|------|
| 仅 `--intent` | intent → preset → engine |
| 仅 `--platform` | 映射为兼容 intent 后 resolve |
| 两者一致 | OK |
| 两者冲突 | **400** / 非 0；不 silent |

---

## 开工检查单（代码启动前）

- [ ] 产品确认 **开始 Phase A 开发**（本文档任务完成 ≠ 开工）  
- [ ] PRD v1.1 + ACCEPTANCE + ADR-016 D 已合并文档主干  
- [ ] 指定 `kept_n` 函数负责人  
- [ ] 分配 `E_OR_*` 号段  

---

## 版本记录

| 版本 | 日期 | 说明 |
|------|------|------|
| v1.0.0 | 2026-07-14 | 初稿 · 对齐 Conditional Go · **明确未开工代码** |
