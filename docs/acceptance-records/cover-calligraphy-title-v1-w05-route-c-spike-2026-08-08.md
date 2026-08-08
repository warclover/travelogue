# PRD-COVER-CALLIGRAPHY-TITLE-V1 · W0.5 路线 C 完整 Spike

| 属性 | 内容 |
|------|------|
| **文档** | [PRD-COVER-CALLIGRAPHY-TITLE-V1.md](../PRD-COVER-CALLIGRAPHY-TITLE-V1.md)（**CAL**）§3 D-CAL-14/16/18/19 · §5.5 · §11 W0.5 · AC-CAL-11 · OQ-CAL-06/07 |
| **分支** | `feat/cover-calligraphy-title-v1` |
| **覆盖事项** | 补齐 §11 里程碑要求的「20～30 条真实/边界标题系统性验证」，替换掉此前仅 2 组标题的现场实测（v0.4.0）；解锁/钉定 AC-CAL-11 阈值 |
| **日期** | 2026-08-08 |
| **方式** | `scripts/title_art_route_c_spike.py`：26 条真实/边界标题（覆盖极短/极长、生僻字地名、多音字、数字英文混排、标点、叠字、古诗词句），逐条调用 `route_c.generate_raw`（模型 `wanx2.1-t2i-plus`，D-CAL-18 默认值）+ 复用 `vision_chat_completion`（`qwen-vl-plus`）做 OCR 回读，全量落盘图片 + JSON/MD 报告 |
| **结论** | **不通过——OCR 回读通过率 57.7%（15/26），远低于生产可用门槛；`route_c_enabled` 维持默认 `false`，路线 C 结论性地留在「候选/实验」层级，暂不升级为默认主路径（回答 OQ-CAL-06）；AC-CAL-11 阈值钉定为「单次生成 OCR 通过率 ≥ 90%」，当前实测远未达标，判定不通过** |

---

## 0. 一句话结论

用真实脚本跑了 26 条覆盖各类边界场景的标题，通义万相 `wanx2.1-t2i-plus` **提交/生成 100% 成功**（无超时、无内容审核拒绝），延迟稳定在 15～28 秒（均值 18s，可接受的后台异步等待）；但 **OCR 回读字形准确率只有 57.7%**——常见地名/纯数字几乎全对，**生僻字、古诗词句、标点符号、叠字**这几类系统性出错（缺笔/替换成形近字/整个词被换成完全不相关的字）。这个结果比 v0.4.0 仅测 2 组标题时乐观得多的印象低得多，证明"仅现场实测 2 组"确实不能代表真实分布（OQ-CAL-07 里当时就标注了这层风险，现在验证坐实）。

**结论：路线 C 不满足默认开启条件，`route_c_enabled` 继续保持 `false`；D-CAL-16 分层 fallback 机制（失败必静默降级路线 B）在这个通过率下是必需品，不是可选加固——大约每 2.3 条标题就有 1 条要靠它兜底。**

---

## 1. 样本设计

26 条标题按 12 个边界类别分配，5 款风格轮转（`i % 5`）覆盖，确保不是某一款 prompt 模板单独背锅：

| 类别 | 条数 | 设计意图 |
|------|------|----------|
| `baseline_control` | 1 | 复现 v0.4.0 现场实测过的"拾光"，做前后对照 |
| `extreme_short_1char` | 1 | 单字极短边界 |
| `rare_char_place` | 9 | **本 app 是游记工具，地名生僻字是真实高频场景**（甪直/涠洲岛/婺源/黟县/龟兹/阆中/措浪/硇洲/邺城），非人造压力测试 |
| `extreme_rare_stress` | 1 | 5 连超罕见字，探测准确率下限（不代表真实使用场景，纯压力测试） |
| `polyphone_place` | 2 | 多音字地名（厦门/重庆）——测字形是否正确，不测发音 |
| `digits_mixed` | 2 | 数字/单位混排 |
| `latin_mixed` | 2 | 中英混排（Vlog 类真实常见标题风格） |
| `punctuation` | 2 | 间隔号、省略号 |
| `common_scenic` | 2 | 热门地名基线对照（非边界） |
| `repeated_char` | 2 | 叠字（"秋"/"一"） |
| `long_boundary_8char` | 1 | 合同上限 8 字整（`contract.MAX_MAIN_CHARS`），含生僻地名字 |
| `poetic_phrase` | 1 | 古诗词句，测草书意境风格下的复杂字形 |

完整样本表、prompt 渲染逐条明细见脚本 `scripts/title_art_route_c_spike.py::TITLE_SAMPLES` 与原始报告 [`cover-calligraphy-title-v1-route-c-w05-spike-2026-08-08.md`](cover-calligraphy-title-v1-route-c-w05-spike-2026-08-08.md)。

---

## 2. 汇总数据

| 指标 | 数值 |
|------|------|
| 样本总数 | 26 |
| 生成成功数（无超时/审核拒绝） | 26（100%） |
| **OCR 回读通过率** | **15/26 = 57.7%** |
| 内容审核拒绝率 | 0%（本批次未触发） |
| 延迟 | 均值 18.0s / 最小 15.3s / 最大 28.3s / P95 19.2s |
| 单价 | DashScope 响应不含计费字段；已用 `generation_success=26` 张对照阿里云百炼控制台『用量/账单』页人工核算（见下方成本小节） |

### 分类别通过率

| 类别 | 总数 | OCR 通过 | 通过率 |
|------|------|----------|--------|
| baseline_control | 1 | 0 | 0% |
| extreme_short_1char | 1 | 1 | 100% |
| rare_char_place | 9 | 5 | 55.6% |
| extreme_rare_stress | 1 | 0 | 0% |
| polyphone_place | 2 | 1 | 50% |
| digits_mixed | 2 | 2 | **100%** |
| latin_mixed | 2 | 1 | 50% |
| punctuation | 2 | 1 | 50% |
| common_scenic | 2 | 2 | **100%** |
| repeated_char | 2 | 1 | 50% |
| long_boundary_8char | 1 | 1 | 100% |
| poetic_phrase | 1 | 0 | 0% |

**读法**：`digits_mixed`/`common_scenic`（热门地名 + 纯数字）稳定 100%；`rare_char_place`（真实高频场景）跌到 55.6%；`extreme_rare_stress`/`poetic_phrase`/`baseline_control`（本次单样本，v0.4.0 那次同一标题曾对过一次，扩样后暴露出扩散模型本身**非确定性**——同一标题不同次采样结果可能不同，2 组现场实测的"过"不能代表长期通过率）全部 0%。

---

## 3. 典型样例

### 3.1 通过：`稻城亚丁行`（common_scenic · casual-handwritten）

字形完全正确，笔画清晰，符合预期。

![通过样例](attachments/cover-calligraphy-title-v1-route-c-w05-spike-2026-08-08/19-casual-handwritten-common_scenic.png)

### 3.2 不通过：`婺源篁岭`（rare_char_place · casual-handwritten）

期望「婺源篁岭」，OCR 回读识别为「渡洒桦洛」——**四个字全部writing成完全不相关的形近字**，不是缺笔/多笔这种局部错误，是整体性的生僻字失败（"婺"字本身笔画结构复杂、"篁"字上竹下皇的组合都不是扩散模型训练数据里的高频字形）。这类错误人工一眼就能看穿，不存在"看起来像对但其实错了"的隐蔽风险，OCR 回读校验（D-CAL-19）能可靠拦截。

![不通过样例](attachments/cover-calligraphy-title-v1-route-c-w05-spike-2026-08-08/04-casual-handwritten-rare_char_place.png)

其余 24 条的生成图与逐条 OCR 识别文本见 [原始报告](cover-calligraphy-title-v1-route-c-w05-spike-2026-08-08.md) 明细表。

---

## 4. AC-CAL-11 阈值钉定

PRD 原文（v0.3.0）：「路线 C 输出的 OCR 回读校验通过率达 **W0.5 Spike 钉定阈值**方可进入生产候选池」——阈值当时留空，本次 Spike 补上：

- **阈值定为「单次生成 OCR 通过率 ≥ 90%」**：低于此值意味着超过 1/10 的用户会触发 D-CAL-16 fallback（即他们精心设置的封面标题实际展示的是路线 B 兜底字体，而非期望的艺术字），体感上"经常不生效"，不适合作为默认体验。
- **本次实测 57.7%，判定不通过**——AC-CAL-11 结论为 ❌，`route_c_enabled` 继续默认 `false`。
- **回答 OQ-CAL-06**（路线 C 何时从候选升级为默认）：当前数据下**明确不升级**；且鉴于扩散模型的非确定性（同一标题不同次生成结果可能不同），即便某次小样本达标也不能一次性判定"通过"，建议长期作为**用户可选的高级项**（Studio 面板里显式勾选"尝试 AI 艺术字"，明确告知有一定概率会静默回退到默认样式），而非面向全量用户默认开启的主路径。

---

## 5. 分类观察 → 后续可探索方向（不在本次 Spike 范围内落地）

以下是数据驱动的观察，供后续排期参考，**均未在本次任务中实现代码**：

1. **常见地名 + 纯数字场景已经足够可靠（100%）**——如果未来想让路线 C 在小范围场景下默认开启，可考虑给 `route_c_enabled` 加一层**标题内容预筛选**（比如用常用字表过一遍，命中率高的才走路线 C，命中率低的直接走路线 B，不浪费一次生成+超时等待），而不是全量标题都无差别尝试。**✅ 已落地（v0.6.8，D-CAL-21，[`char_frequency.py`](../../travelogue/cover_engine/title_art/char_frequency.py)）**：对本次 26 条样本回测，允许尝试 17/26，尝试子集通过率 57.7%→64.7%——纯粹降本增效，**不足以单独解锁 `route_c_enabled` 默认开启**（仍差 90% 门槛一大截）。
2. **重试机制的潜在收益**：本次 26 条无一超时/审核拒绝，说明"生成慢/生成失败"不是主要矛盾，"生成了但字不对"才是；由于扩散采样非确定性，"OCR 不过就重试一次再判定失败"理论上能在可接受的额外延迟/成本下提升有效通过率，但**需要另一轮 Spike 验证重试后的边际收益**才能下结论，本次未测。
3. **标点/叠字属于已知可预期的弱点**（省略号被吃掉、叠字变形），产品侧可考虑在标题合同层（§4）直接对这两类做规则化处理（比如叠字/标点不参与路线 C，改用路线 B），比等 diffusion 模型本身变好更可控。

---

## 6. 成本核算方法说明

DashScope 图像合成接口响应体不含计费字段，脚本本身不硬编码单价数字（避免供应商调价后误导）。核算方式：生成成功张数（26）对照阿里云百炼控制台『用量与账单』页面的实际扣费金额，除以张数得出单张单价。**本记录不代为填写具体金额**，需要产品/运营在控制台自行核对当期账单后补充。

---

## 附件

- 原始报告（JSON/MD，含 26 条完整明细）：
  - [`cover-calligraphy-title-v1-route-c-w05-spike-2026-08-08.md`](cover-calligraphy-title-v1-route-c-w05-spike-2026-08-08.md)
  - [`cover-calligraphy-title-v1-route-c-w05-spike-2026-08-08.json`](cover-calligraphy-title-v1-route-c-w05-spike-2026-08-08.json)
- 26 张生成图片：`attachments/cover-calligraphy-title-v1-route-c-w05-spike-2026-08-08/`
- 复现脚本：`scripts/title_art_route_c_spike.py`（`python scripts/title_art_route_c_spike.py --dry-run` 可不调 API 预览样本分配；正式跑需 `$env:DASHSCOPE_API_KEY`）
