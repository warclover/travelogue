# Travelogue · 一句话选风格 V1 产品需求文档（PRD）

| 属性 | 内容 |
|------|------|
| **产品代号** | Travelogue Studio |
| **文档版本** | **v0.2.0** |
| **状态** | **M0–M2 结案**（[七席](./acceptance-records/lvp-layout-vibe-picker-v1-review-2026-08-03.md) · AC-06 三册差异小 · M3 延期） |
| **DOC-STATUS** | **active** |
| **主题代号** | 「一句话选风格」— **LVP**（Layout Vibe Picker） |
| **触发来源** | [INSIGHT-FLIPIN…](./INSIGHT-FLIPIN-COMPETITIVE-ANALYSIS-2026-08-03.md) · [战略优先级复盘](./INSIGHT-STRATEGIC-PRIORITY-REVIEW-2026-08-03.md) §五 #1 · 2026-08-03 算法收口后需要用户侧出口 |
| **前置条件** | MTSO **已转正 GA** · MEGC **默认 on** · MSA **默认 off（盲评不通过）** · SSG look **Hold** |
| **关联文档** | [MTSO](./PRD-MOSAIC-TEMPLATE-SELECTION-OPTIMIZATION-V1.md) · [MEGC](./PRD-MOSAIC-EQUAL-GRID-CONTRACT-V1.md) · [MSA](./PRD-MOSAIC-SLOT-ADAPTATION-V1.md) · [SSG](./PRD-SMART-SHOT-GROUPING-V1.md) · [CAD](./PRD-COVER-ART-DIRECTION-V1.md) · [FTUE](./PRD-FTUE-OPTIMIZATION-V1.md) · [智能排版开关页](./PRD-智能排版开关页.md)（**研发后台**，非本主题） |
| **评审纪要** | [lvp-layout-vibe-picker-v1-review-2026-08-03.md](./acceptance-records/lvp-layout-vibe-picker-v1-review-2026-08-03.md)（结案）· [模板](./acceptance-records/lvp-layout-vibe-picker-v1-review-TEMPLATE.md) |
| **验收** | [ACCEPTANCE-LAYOUT-VIBE-PICKER-V1.md](./ACCEPTANCE-LAYOUT-VIBE-PICKER-V1.md) |
| **实施** | [IMPLEMENTATION-LAYOUT-VIBE-PICKER-V1.md](./IMPLEMENTATION-LAYOUT-VIBE-PICKER-V1.md) |
| **更新日期** | 2026-08-03 |

> **v0.2.0 相对 v0.1.0（七席回写 · 2026-08-03）**
>
> 1. **Conditional Go**：可 Kickoff M0/M1；M2 挡 BLK-03/04；M3 延期。  
> 2. **D-LVP-01 改写**：V1 = **1 推荐 + 1 实验**（删除「两个正式」歧义）。  
> 3. **O-01～03 关闭**；新增 **D-LVP-09 回滚合同** · **AC-LVP-08**。  
> 4. 优先级链：`trip.studio.layoutVibe` > 进程 overlay > 仓库默认。

> **定位**
>
> 算法专题已经能出可接受成册，但用户面对的仍是工程布尔开关。  
> LVP **不发明新几何算法**，只把已落地栈收成 **用户能懂的风格句**。
>
> **一句话目标**：用户选「杂志成册（推荐）」或「更贴照片比例（实验）」；默认 = 当前 GA 栈；实验才开 MSA 并知情同意分页可能变化。

---

## 0. 边界

| 主题 | LVP 做 | LVP 不做 |
|------|--------|----------|
| **MTSO / MEGC / MSA** | 映射到 vibe → 配置剖面 | 不改选型/闸/调轨公式 |
| **SSG** | V1 **不暴露** look；scene 保持现网 | 不在人脸门修好前承诺换装拆组 |
| **LSE 开关页** | 无关 | 仍是研发 `/lse-flags-admin` |
| **CAD 封面导演** | 可同屏邻近，但合同分离 | 不接管 Opening/Closing 选图 |
| **商业化 / 付款** | 不在范围 | — |

---

## 1. 问题

1. 仓库默认已是「MTSO on + MEGC on + MSA off」，但 Studio **没有产品语言**说明气质。  
2. MSA 有实验价值，但盲评不通过且有 pacing 副作用——需知情入口，不能裸开布尔。  
3. Flipin 用一句风格问题完成绑定；本产品缺这层**收编出口**。

---

## 2. 目标 / 非目标

### 2.1 目标

| ID | 目标 |
|----|------|
| **G-01** | 用户可见 **恰好两卡**（推荐 + 实验），每条一句人话 + 一句后果 |
| **G-02** | 默认 vibe = 当前 GA 栈（无需改配置即等价） |
| **G-03** | 切换 vibe 后「下次 layout/render」生效；可回默认 |
| **G-04** | 映射表写进 trip，可观测、可狗粮、可回滚 |

### 2.2 非目标

| ID | 非目标 |
|----|--------|
| **N-01** | 新开几何算法或平行模板库 |
| **N-02** | 暴露 `score_mul` / `deltaThreshold` 等调参 |
| **N-03** | V1 做「每页不同 vibe」 |
| **N-04** | V1 把 SSG look / vision 绑进 vibe |
| **N-05** | 替换封面 CAD / 文案引擎 |
| **N-06** | 第三卡「全关优化 / 经典栈」 |

---

## 3. 已拍板决策（七席锁定 · v0.2.0）

| ID | 决策 |
|----|------|
| **D-LVP-01** | V1 = **1 推荐**（`magazine_default`）+ **1 实验**（`fit_photo_experimental`）；`film_wide` **不交付** |
| **D-LVP-02** | 推荐 ≡ GA：`selection_optimization=on` · `equal_grid_contract=on` · `slot_adaptation=off` |
| **D-LVP-03** | 实验才打开 MSA；UI 标「实验」+ 说明「可能改变章节篇幅」；须二次确认 |
| **D-LVP-04** | **禁止**在 LVP 里单独开关 MTSO/MEGC |
| **D-LVP-05** | SSG look **不进** V1；scene 不因 vibe 关闭 |
| **D-LVP-06** | 入口：精修一等「成册风格」+ 导入完成后 **弱提示一次**（可关）；**不做**全屏阻塞 Wizard |
| **D-LVP-07** | 持久化：`trip.studio.layoutVibe`；优先级 **trip > 进程 overlay > 仓库默认** |
| **D-LVP-08** | 与 `/lse-flags-admin` 正交；只写 mosaic 剖面 |
| **D-LVP-09** | **回滚**：下线入口或清除 `layoutVibe` → 行为 ≡ 推荐 / GA；不卸载 MTSO/MEGC |

### 3.1 开放问题 · 已结案

| ID | 结案 |
|----|------|
| **O-01** | ✅ 精修一等 + 导入后弱提示一次 |
| **O-02** | ✅ V1 不影响 CAD |
| **O-03** | ✅ 不要第三卡 |

---

## 4. Vibe 合同（V1）

| vibeId | 用户可见文案（草案） | 后果一句话 | 配置映射 |
|--------|----------------------|------------|----------|
| `magazine_default` | **杂志成册（推荐）** | 宽画幅节奏稳，单反 3:2 少进扁四宫 | MTSO on · MEGC on · MSA **off** |
| `fit_photo_experimental` | **更贴照片比例（实验）** | 加权拼图轨道更贴原图，章节页数可能变 | MTSO on · MEGC on · MSA **on** |

---

## 5. 体验草图

1. 精修 Sheet「画册」：`成册风格` → 两张大卡（与封面版式同级）。  
2. 选实验卡 → 二次确认（分页风险 + 可改回推荐）。  
3. 写 `layoutVibe`，触发 layout/render；复用现有等待面。  
4. 卡面不展示算法缩写。

---

## 6. 里程碑

| 里程碑 | 内容 | 合码门 |
|--------|------|--------|
| **M0** | 七席锁定 · PRD v0.2 | 本纪要 Conditional Go |
| **M1** | 配置剖面 + 持久化 + 单测（AC-01～03/07/08） | BLK-02/05/06 |
| **M2** | Studio 两卡 UI + 确认文案 + 三册狗粮 | BLK-03/04 · AC-04～06 |
| **M3** | （可选）与 CAD 同屏编组 | 默认延期 |

---

## 7. 风险

| 风险 | 缓解 |
|------|------|
| 两卡「没差别」 | 狗粮用含加权屏 trip；允许记录「本册差异小」 |
| MSA 分页抱怨 | 二次确认 + 一键回推荐 |
| 本机 YAML 冲突 | D-07 优先级链 + 单测 |
| 范围膨胀 | N-01～N-06 |

---

## 8. AC 摘要

详见 [ACCEPTANCE-LAYOUT-VIBE-PICKER-V1.md](./ACCEPTANCE-LAYOUT-VIBE-PICKER-V1.md)。

| ID | 摘要 |
|----|------|
| **AC-LVP-01** | `magazine_default` ≡ 仓库 GA 默认 |
| **AC-LVP-02** | `fit_photo_experimental` 仅多开 `slot_adaptation.enabled` |
| **AC-LVP-03** | `layoutVibe` 持久化，重开仍在 |
| **AC-LVP-04** | UI 不出现算法缩写（帮助除外） |
| **AC-LVP-05** | 实验无二次确认不可保存 |
| **AC-LVP-06** | 三册狗粮；无加权可记「差异小」 |
| **AC-LVP-07** | 不改写 SSG look / LSE flags |
| **AC-LVP-08** | 清 vibe / 下线入口 → ≡ 推荐 / GA |

---

## 9. 变更记录

| 版本 | 日期 | 说明 |
|------|------|------|
| v0.2.0 | 2026-08-03 | 七席 Conditional Go 回写；D-01 改写；O 关闭；D-09 / AC-08 |
| v0.1.0 | 2026-08-03 | 初稿 |
