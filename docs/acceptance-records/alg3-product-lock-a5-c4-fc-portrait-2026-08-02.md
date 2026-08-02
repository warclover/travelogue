# ALG-V3 · 产品口锁定（A5 / C4–C5 / fine_craft / 竖版单张）

| 属性 | 内容 |
|------|------|
| **日期** | 2026-08-02 |
| **状态** | **已锁定**（产品确认：全部按建议） |
| **PRD** | [PRD-ALGORITHM-OPTIMIZATION-V3.md](../PRD-ALGORITHM-OPTIMIZATION-V3.md) |
| **IMPL** | [IMPLEMENTATION-ALGORITHM-OPTIMIZATION-V3.md](../IMPLEMENTATION-ALGORITHM-OPTIMIZATION-V3.md) |
| **评审** | [algorithm-v3-prd-review-2026-08-01.md](./algorithm-v3-prd-review-2026-08-01.md) Should #8 |

> 本文件是编码合同。改口须新开 acceptance-record 并回写本表状态。

---

## 锁定摘要

| ID | 结论 | 默认成片影响 |
|----|------|--------------|
| **PL-A5** | Look 参考默认 `first`；EMA/medoid **仅 opt-in** | 无（默认路径） |
| **PL-VC04** | VC-ALG3-04 主尺 = **`patternId`**；阈默认 **2** | 无（维持现网） |
| **PL-C5** | diversity holdback：**观测 + flag，默认 off** | 无 |
| **PL-FC** | vision **不**绑 fine_craft Tab；**cohort SSOT** 延续 OQ-02=C | 无 |
| **PL-PS** | 竖版单张：**本波不改默认策略**；下一候选挂 `layoutDensity` | 无 |

---

## PL-A5 · Look EMA / medoid

| 项 | 锁定 |
|----|------|
| 现状锚点 | `look_split.split_look_segments` 以段内 **first frame** 为 reference |
| 默认 | `look_reference_mode = first`（或等价键名；未合码前行为 ≡ 今日） |
| Opt-in | `ema` / `medoid` 仅 config / cohort / dogfood；**禁止**抬生产默认 |
| 可观测 | skip / mode 写入漏斗或 `algoV3` 摘要字段（编码期钉 schema） |
| 退出 | 默认路径 look 分段与合入前一致；must-green 绿 |

**禁止**：本波把 EMA/medoid 设为全局默认。

---

## PL-VC04 / PL-C4 · 节奏语义（VC-ALG3-04）

| 项 | 锁定 |
|----|------|
| 主尺 | **`patternId` streak**（与 `max_consecutive_same_pattern` / `check_max_consecutive_same_pattern` 一致） |
| 阈值 | 默认 **2**（维持现网；改阈值另开产品口） |
| `layout_kind` | **不作**本波 VC-04 主尺；现 `screen_layout_kind`（hero\|grid）过粗，扩 kind 表属另波 |
| C4 编码范围 | 统一文档/遥测口径到 `patternId`；必要时补 streak 仪表（评审 Should #7） |
| 盲评 | 问4 节奏另记；不挡本锁编码 |

**禁止**：在未扩 kind 合同前，把 VC-04 改判为 layout_kind 主尺。

---

## PL-C5 · diversity holdback

| 项 | 锁定 |
|----|------|
| 默认 | **off**（生产路径零变化） |
| 形态 | 观测项 + 可选 flag / cohort；与 MCS diversity 配置对齐，不平行造第二套 |
| 抬默认 | 须盲评问4 + 独立产品口 |

---

## PL-FC · fine_craft 入口 × vision（兑现评审 Should #8）

| 项 | 锁定 |
|----|------|
| Vision SSOT | 继续 **`vision.cohort_trip_ids`**（空=无人；`*`=仅 dogfood） |
| fine_craft | 保留导入模式 + `layoutDensity` 等既有 UI；**不**因选精细制作自动开 vision |
| 文案 / Help | 与 FE-ALG3-S04 对齐：「默认关；内部名单可开」；禁全局 auto 营销 |
| 否决 | 设置页向普通用户暴露「场景分析总开关」或 fine_craft→隐式入 cohort |

**OQ-02**：维持 **C**；狗粮后再议 A（全局 auto）。

---

## PL-PS · 竖版单张

| 项 | 锁定 |
|----|------|
| 本波 | **不改**默认 flush / penalty / 配额策略；竖单仍作 fallback |
| 相邻已合 | food-grid 优先于 pending（#45）保持；**不**借机抬竖单占比 |
| 下一候选 | 仅 `fine_craft` 下按 `layoutDensity` 分档（`hero_first` 允许多竖单倾向，`collage_first` 更抑）——**另 PR，须产品再开** |
| 否决 | 本波为「多出竖单」改全局默认 |

---

## 编码启动顺序（本锁之后）

1. **可开（默认不成片）**：A5 opt-in 键 + skip 可观测；C4 口径/遥测；C5 flag 骨架（默认 off）。  
2. **不必开**：fine_craft↔vision 接线；竖版单张默认策略。  
3. **仍挡宣称**：W1b / A4 人评盲评 PENDING。  
4. **仍暂缓**：B5（AAD）· W4 · 全局 scoring/vision auto · 竖单 `layoutDensity` 分档。

---

## 签字

| 角色 | 结论 |
|------|------|
| 产品 | **全部按建议**（2026-08-02 会话确认） |
| 记录 | Cursor Agent · 落盘本页 |
