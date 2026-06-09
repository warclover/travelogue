# Travelogue · 文案优化产品需求文档（PRD）

| 属性 | 内容 |
|------|------|
| **产品代号** | Travelogue |
| **文档版本** | v1.1.0 |
| **状态** | Draft · 跨职能评审已收敛 |
| **主题代号** | 「轻文案 · 点睛之笔」 |
| **前置条件** | Phase 9 质量闸口稳定；visual-journal 模板可用；`copy-toggle` / `inline-edit` 基础能力已上线 |
| **交付形态** | 以图片为主的视觉游记；AI 生成极短点睛文案；用户可一键纯照片、点击即改 |
| **关联文档** | [IMPLEMENTATION-COPY-OPTIMIZATION.md](./IMPLEMENTATION-COPY-OPTIMIZATION.md)、[ACCEPTANCE-COPY-OPTIMIZATION.md](./ACCEPTANCE-COPY-OPTIMIZATION.md)、[PRD-PHASE11-copy-optimization.md](./PRD-PHASE11-copy-optimization.md)、[NARRATIVE-PROMPTS.md](./NARRATIVE-PROMPTS.md)、`travelogue/services/llm_narrate.py`、`travelogue/services/decor_line.py`、`templates/visual-journal/copy-toggle.js`、`templates/visual-journal/inline-edit.js` |
| **更新日期** | 2026-06-09 |

> **产品共识（四条铁律）**
>
> 1. **短**：不要长文案，点睛之笔即可——**全书**以 3～5 句、合计几十字的 AI 点缀为主（非每章 3～5 句）。
> 2. **可藏**：用户 **一键隐藏全部文案**，进入纯照片模式；照片永远是主角。
> 3. **可改**：用户 **点击文案即进入编辑**，改完保存到 `trip.json`，生成器不得覆盖用户编辑。
> 4. **图主文辅**：游记以 **图片为主、文字为辅**；文案只点一下，**切勿画蛇添足**。

> **实施原则（跨职能评审 v1.1）**
>
> **走心 = 用用户已有信号（voice、anchors、note）点一下，而不是 AI 替用户升华。**

---

## 1. 背景与问题陈述

### 1.1 背景

Travelogue 交付物是 **杂志风视觉 HTML 游记**，不是博客或 AI 写作工具。用户导入照片后，系统会自动生成 hook、章导语、图注、结语等字段。当前 pipeline 能「填槽」，但用户普遍感知为：

- 文案 **抢镜**——像在解释照片，而非陪衬；
- 语气 **泛化**——合理但不像「我的那次旅行」；
- 体量 **偏多**——每张图、每章都想写满，违背视觉游记形态。

### 1.2 核心判断

> 文案优化难点不在「会不会写」，而在「是否知道用户当时的情绪与关注点」。
>
> 仅靠 EXIF 城市与通用提示词，模型只能输出 **合理但不属于用户** 的句子。  
> 因此本产品采用：**极短输出 + 私人锚点 + 混合生成管线 + 多候选重排 + 用户可随时关掉或改掉**。

### 1.3 当前问题对照

| 问题 | 现状 | 目标 |
|------|------|------|
| 文案角色过重 | `hook/lead/caption/epilogue` 填槽策略偏满 | 默认 **sparse**：章级 1 句点缀，lead/caption 可空 |
| decorLine 模板化 | `_template_candidates` 规则拼接，易产出「留在这一章」类凑句 | **混合管线**：voice 直通 + 有条件 LLM K 候选 |
| 视觉/事件事实不足 | fact 以 title/tags/city 为主，缺事件型信号 | fact 层升级；**不足则 skip** |
| 单次生成波动大 | hook/caption 有 LLM；decorLine 无 LLM 多候选 | 统一两阶段 + K 候选 + 重排 |
| 用户控制不足 | decorLine 未 inline-edit；两个 hide 按钮易混淆 | 点缀字段全覆盖可改；**单一纯照片主开关** |
| AI 味 / 导游词 | 禁用词表不完整 | 扩展 `_GENERIC_RE` 至 narrate；prompt 加负向示例 |

### 1.4 跨职能评审摘要（2026-06-09）

| 角色 | 关键结论 |
|------|----------|
| 产品 | 主 KPI 不看 fill_rate；考核隐藏率、编辑保留率、盲评走心分 |
| 算法 | 瓶颈在 fact 输入；voice/anchors 优先于 tags；无 fact 则空 |
| AI/LLM | decorLine 需接 LLM；voice 精简作候选 #1；temperature 偏低 |
| UX | 合并「纯照片」主开关；首次 draft 轻提示「点一下可改」 |
| 前端 | decorLine 补 `data-editable`；纯照片与编辑互斥 |
| 内容 | lead 默认退役；decorLine 与 lead 互斥去重；caption 多数 skip |

---

## 2. 目标与非目标

### 2.1 产品目标

| ID | 目标 | 衡量方式 |
|----|------|----------|
| **G-COPY-01** | 全书 AI 点缀 **3～5 句、几十字级** | scope=frame 下 `hook+decorLine+epilogue` 中位数 ≤120 字 |
| **G-COPY-02** | 章级 1 句点睛，≤30 字，**可空** | schema + validator；**空输出合法** |
| **G-COPY-03** | 文案弱存在感，不抢图 | 盲评 ≥80%「点到即止」 |
| **G-COPY-04** | 一键纯照片无回归 | `photos-only` 隐藏 L1～L4 |
| **G-COPY-05** | 点击即改 + `edited` 保护 | 含 decorLine 全部点缀字段 |
| **G-COPY-06** | 贴合事实与用户信号 | 事实一致性 ≥90%；有 voice/anchors 章走心分更高 |
| **G-COPY-07** | 可灰度可回滚 | 配置开关回退 legacy |

### 2.2 主 KPI 与观测指标（v1.1 修订）

**主 KPI（考核）：**

| 指标 | 目标 |
|------|------|
| `photos_only_rate` | 不高于基线 +10% |
| `inline_edit_retention_rate` | 用户改后 regenerate 不覆盖率 100% |
| `blind_review_heartfelt_score` | ≥80%「像我的旅行 / 不抢镜」 |
| `generic_phrase_hits` | 较基线持续下降 |

**观测项（不硬考核 fill_rate，避免逼凑句）：**

| 指标 | 观测范围 |
|------|----------|
| `decor_line_fill_rate` | 参考 60%～85%，可低于下限 |
| `decor_line_empty_rate` | fact/voice 不足章占比 |
| `copy_total_chars` | 中位数 60～120 |
| `intent_adoption_rate` | copyIntent 填写占比 |

### 2.3 非目标

- 不做长段落、小说式叙事；
- 不做每张图必有一句 caption；
- 不做独立富文本编辑器；
- P11 不强依赖 VLM（P11.2 试点）；
- 不改变 Pattern / 排版主导地位。

---

## 3. 已拍板决策（D-COPY）

| ID | 决策 | 结论 |
|----|------|------|
| **D-COPY-01** | 产品定位 | **图主文辅** |
| **D-COPY-02** | 默认体量 | **全书** 3～5 句；章级最多 1 句 `decorLine` |
| **D-COPY-03** | 章级字数 | `decorLine` ≤30 字；lead 默认空（scope=frame） |
| **D-COPY-04** | 全书导读 | hook ≤56、epilogue ≤80；均可空 |
| **D-COPY-05** | 图注 | **稀疏**：有 voice 精简 ASR；无 voice 多数 skip；≤40 字 |
| **D-COPY-06** | 生成风格 | 轻描淡写；**禁止解释照片意义** |
| **D-COPY-07** | 失败策略 | fact/voice 不足 → **留空** |
| **D-COPY-08** | 隐藏文案 | **纯照片**为默认暴露的主开关；「隐藏导语」收二级 |
| **D-COPY-09** | 编辑 | draft 点击即改；`edited: true` 后 skip regenerate |
| **D-COPY-10** | 信号优先级 | **voice > memoryAnchors > copyIntent（被动推断）> tags > EXIF** |
| **D-COPY-11** | decorLine 管线 | **混合**：voice/note 直通 → 规则候选 → 有条件 LLM K=3 → 重排 |
| **D-COPY-12** | copyIntent | **被动优先**（从 voice/anchors 推断）；Studio **可选**主动填写 |
| **D-COPY-13** | lead 与 decorLine | **互斥**：同章 decorLine 有值时 lead 不生成；validator 去重 |
| **D-COPY-14** | 兼容 | 保留 legacy 字段；`scope=full` 为 Studio 高级项 |

---

## 4. 文案层级与字数预算

### 4.1 层级定义

（同 v1.0：L0 标题 → L1 hook/epilogue → L2 decorLine 主战场 → L3 lead 默认关 → L4 caption 稀疏）

### 4.2 字数预算

| 字段 | 上限 | scope=frame 默认 |
|------|------|------------------|
| `meta.hook` | 56 | 生成（可空） |
| `chapters[].decorLine` | 30 | 生成（可空） |
| `chapters[].lead` | 80 | **不生成** |
| `items[].caption` | 40 | **不生成** |
| `epilogue` | 80 | 多章可选 |

**全书预算：** 3～5 句、约 60～120 字；单章 on-screen AI 文案 ≤1 句。

### 4.3 内容原则

1. **具体 > 抽象**（anchors、voice 事件细节）
2. **留白 > 说破**（禁升华）
3. **原声 > 润色**（voice 精简优先）
4. **空 > 凑**（禁「留在这一章」类模板句）

**禁用词（扩展）：**  
综上所述、值得一提的是、不可否认、众所周知、总而言之、美不胜收、令人难忘、换句话说；  
以及泛化词：值得、美好、精彩、瞬间、回忆、旅程、旅行、风景、照片、记录（见 `decor_line._GENERIC_RE`，同步至 narrate）。

---

## 5. 生成策略

### 5.1 信号优先级与 copyIntent

| 优先级 | 信号 | 说明 |
|--------|------|------|
| 1 | `voiceExcerpt` | ASR 精简后可 **直通** decorLine/caption 候选 |
| 2 | `memoryAnchors` | 事件型锚点 |
| 3 | `copyIntent` | 被动推断优先；用户可选 mood/focus/note |
| 4 | `userNotes` / `travelNotes` | trip 级 grounding |
| 5 | `tags` | CLIP 视觉标签，权重低于 voice/anchors |
| 6 | `places` / EXIF | 最低；非 userSet 不覆盖 editorialSubject |

**copyIntent 交互：** 默认折叠、可选；有 voice 的章可 **跳过** 意图采集；「应用到后续章节」保留。

### 5.2 decorLine 混合管线（v1.1 · D-COPY-11）

```text
章内 assets（voice / anchors / tags / copyIntent）
        ↓
[Step 0] fact 充分性检查 → 不足则直接输出 ""
        ↓
[Step 1] chapter_facts（事件型 fact 列表，voice/anchors 优先于 tags）
        ↓
[Step 2] 候选池（合并去重，K≥3）
         · voice 精简句（若有，权重最高）
         · copyIntent.note 微调（若有）
         · 规则模板（仅作兜底）
         · LLM 单句（仅 fact≥2 且无高质量 voice 时调用）
        ↓
[Step 3] 重排（factual / brevity / anti_generic / style_fit / intent_fit）
        ↓
score < threshold → ""；否则输出 best
```

**LLM 调用策略：** temperature 0.3～0.5；全书 decorLine 可 batch；fact 不足 **禁止** 调用以免脑补。

### 5.3 hook / caption / epilogue

沿用 `llm_narrate` 两阶段思路；prompt 增加 **负向示例**：

- Bad：「这次旅行令人难忘。」
- Good：「雨太大，先回酒店拿伞。」

caption：有 voice → 精简改写；无 voice → skip（scope=frame 默认 skip 全部）。

### 5.4 Scope 默认

| scope | hook | decorLine | lead | caption |
|-------|------|-----------|------|---------|
| `frame`（**默认**） | ✓ | ✓ | ✗ | ✗ |
| `frame_chapters` | ✓ | ✓ | 首尾章 | ✗ |
| `full` | ✓ | ✓ | ✓ | 稀疏 |

---

## 6. 交互与 UX

### 6.1 纯照片模式（v1.1 修订）

**主开关（P1）：** 工具栏默认只暴露 **「纯照片 ⟷ 显示文案」**（`#photos-only-toggle`）。

**二级（longshot / 高级）：** 「隐藏导语 / 显示导语」保留——仅隐藏 L1～L3，图注策略独立。

**要求：** 纯照片下 L1～L4 全隐藏；与 inline-edit **互斥**（纯照片态不可进入编辑）。

### 6.2 点击编辑

| 字段 | edit path | 状态 |
|------|-----------|------|
| `meta.hook` | `meta.hook` | ✓ |
| `epilogue` | `epilogue` | ✓ |
| `chapters[].lead` | `chapters[n].lead` | ✓ |
| `items[].caption` | `assets.{id}.caption` | ✓ |
| `chapters[].decorLine` | `chapters[n].decorLine` | ✓ |

**首次 draft 进入：** 3 秒轻 toast「点一下文案可修改」（仅一次，localStorage 记已展示）。

### 6.3 视觉层级

decorLine / hook 字号低于章标题；空不占位；有 voice 的 card 可选弱标注「来自你的录音」。

---

## 7. 数据模型与配置

（同 v1.0；`curation.copyStyle.phase` 建议值 `lite-copy-v1.1`）

```yaml
narrative:
  scope: frame
  decor_line_enabled: true
  decor_line_max_chars: 30
  decor_line_candidates: 3
  decor_line_allow_empty: true
  decor_line_llm_enabled: true      # v1.1 新增：fact 足时启用 LLM 候选
  decor_line_voice_first: true      # v1.1 新增：voice 直通优先
  decor_line_intent_enabled: true
  decor_line_intent_optional: true
  decor_line_min_fact_count: 2      # v1.1 新增：低于此值 skip
  max_auto_fix_retries: 2
```

---

## 8. 模块改造范围

见 [IMPLEMENTATION-COPY-OPTIMIZATION.md](./IMPLEMENTATION-COPY-OPTIMIZATION.md) 任务清单。

---

## 9. 验收标准

见 [ACCEPTANCE-COPY-OPTIMIZATION.md](./ACCEPTANCE-COPY-OPTIMIZATION.md)。

---

## 10. 分期交付（v1.1 优先级）

| 优先级 | 里程碑 | 交付 |
|--------|--------|------|
| **P0** | M1 策略收敛 | scope=frame 默认；fact 不足 skip；decorLine inline-edit |
| **P1** | M2 走心管线 | voice 直通；decorLine LLM K 候选；单一纯照片主开关 |
| **P2** | M3 意图与 UX | copyIntent 被动推断 + 可选 Studio；首次编辑提示；lead/decor 互斥 |
| **P3** | M4 质量与灰度 | 负向 prompt；禁用词扩展；轻量 VLM 试点（P11.2）；盲评灰度 |

---

## 11. 风险与缓解

| 风险 | 缓解 |
|------|------|
| 模板 decorLine 冒充优化完成 | P1 必须接 voice + LLM；规则模板仅兜底 |
| fill_rate KPI 逼凑句 | 改观测项；考核 empty_rate + 盲评 |
| hook + decorLine + lead 叠加 | scope + D-COPY-13 互斥 |
| 两 hide 按钮混淆 | P1 合并主开关 |
| serve 依赖导致保存失败 | Studio 明示 + 导出前检查 |

---

## 12. 开放问题

| ID | 问题 | v1.1 决议 |
|----|------|-----------|
| **OQ-01** | decorLine 位置 | 章标题下（不变） |
| **OQ-02** | full scope 暴露 | Studio 高级项 |
| **OQ-03** | VLM | P11.2 试点，每章 1～2 代表图 |
| **OQ-04** | 导出面编辑 | 否，仅 draft + serve |
| **OQ-05** | decorLine LLM vs 规则 | **混合**（§5.2） |
| **OQ-06** | copyIntent 必填？ | **否**，被动推断优先 |

---

## 13. 修订记录

| 版本 | 日期 | 说明 |
|------|------|------|
| v1.1.0 | 2026-06-09 | 跨职能评审：混合 decorLine 管线、KPI 修订、UX 主开关、信号优先级、工程任务拆单 |
| v1.0.0 | 2026-06-09 | 初稿：四条铁律、轻文案全链路 |
