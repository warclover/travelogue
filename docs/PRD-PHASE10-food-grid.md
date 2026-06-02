# Travelogue · Phase 10 产品需求文档（PRD · Food Grid）

| 属性 | 内容 |
|------|------|
| **产品代号** | Travelogue |
| **文档版本** | v0.10.0-PHASE10 |
| **状态** | Draft · 依赖 Phase 9 Wave 3 |
| **Phase 10 代号** | 「同类 mundane 组屏」— Food / 标识类照片 grid 聚合 |
| **前置条件** | [PRD-PHASE9-E-subject-bridge.md](./PRD-PHASE9-E-subject-bridge.md) 已上线；[PRD-LAYOUT.md](./PRD-LAYOUT.md) screen planner 可用 |
| **关联文档** | 原 implementation plan（食物 grid）、`screen_planner_stages.py`、`subject_tagging.py` |
| **更新日期** | 2026-06-02 |

> **定位**：旅行相册中 **食物 / 咖啡 / 小物 / 标识** 等 mundane 照常连续出现且 **各占一屏** 导致单调。本 Phase 在 **章内** 将 ≥3 张同类聚合为 **square grid 屏**（复用 portrait-grid-8 模式）。

---

## 1. 背景

Photobook 类产品常见「食物拼贴页」。本项目已有 **portrait run → portrait-grid-8**；Phase 10 新增 **`try_food_grid`** 阶段。

**策略**：章内聚合（不跨章）；**3+ 张**触发；单 grid **最多 9 张**；超出拆多个 grid。

**范围（mundane 类）**：`food`, `meal`, `restaurant`, `coffee`, `cafe`, `dessert`, `drink`, `shop`, `sign`, `ticket`（tags 或 Phase 8 `semanticTag.category`）。

---

## 2. 目标与非目标

### 2.1 目标

| ID | 目标 |
|----|------|
| **G-P10-01** | 连续 ≥3 mundane 照 → 1 个 food-grid 屏 |
| **G-P10-02** | 横/竖/方比例均可入 grid（`fit: cover`） |
| **G-P10-03** | 与 portrait-grid 共存（先 food 再 portrait 或按 stage 顺序） |
| **G-P10-04** | `enable_food_grid=false` 回退现行为 |

### 2.2 非目标

- 跨章聚合 mundane
- 用户手动调整 grid（MVP）
- Phase 8 全量 11 类（可渐进增强检测）

---

## 3. 依赖

```text
PHASE9 cull → layoutEligible 池
PHASE9-E bridge → subject_class_for_asset 读 CLIP
PHASE10 → try_food_grid in screen_planner
（可选）PHASE8 food 类 → 检测更准
```

---

## 4. 功能规格

### 4.1 subject_tagging 扩展

| 函数 | 行为 |
|------|------|
| `is_mundane_clusterable(asset)` | 返回 `"food"` 或 None |
| `mundane_run_length(ids, assets_map, start)` | 连续 mundane 长度；`tolerance=1` 非 mundane 干扰 |

匹配：CLIP `subjectClass=food` · tags 词表 · Phase 8 `semanticTag.category in (food, signage)`（未来）。

### 4.2 screen_planner_stages

**`try_food_grid(ctx)`**：

1. `enable_food_grid` 且无 `pending_portraits`
2. `mundane_run_length` ≥ 3
3. 取 min(run, 9) 资产
4. pattern：`≥9→square-9`, `≥6→square-6`, `≥4→square-4`, `3→square-4`
5. `layoutHint=food-grid`

**插入位置**：`try_landscape_run` **之后**、portrait-family **之前**。

**`stage_flush_remaining_food()`**：章末 flush 剩余 ≥3 食物照。

### 4.3 配置

```yaml
curate:
  enable_food_grid: true
```

---

## 5. UI / UX

| 项 | Phase 10 |
|----|----------|
| Studio | **无** 新控件；成稿中 grid 屏自然呈现 |
| 预览 | 可选 `layoutHint=food-grid` 调试 badge（维护者 CSS，默认隐藏） |
| 用户感知 | **零**；仅成册视觉密度改善 |

---

## 6. 测试

| 用例 | 预期 |
|------|------|
| 3 food → square-4 grid | layoutHint=food-grid |
| 2 food → 无 grid | |
| food+1 landscape 干扰 | tolerance 仍触发 |
| enable_food_grid=false | 无 grid |
| portrait run + food run | 两种 grid 均出现 |

见 plan：`tests/test_food_grid.py`（10 cases）。

---

## 7. 验收

| ID | 条件 |
|----|------|
| **AC-P10-01** | `pytest tests/test_food_grid.py -v` |
| **AC-P10-02** | demo verify 无回归（demo 无食物照） |
| **AC-P10-03** | 含食物 fixture trip 人工抽检 grid 屏 |

---

## 8. 实施文件

| 文件 | 改动 |
|------|------|
| `subject_tagging.py` | mundane 检测 |
| `screen_planner_stages.py` | try_food_grid |
| `config.py` | enable_food_grid |
| `screen_planner.py` | 透传 |
| `tests/test_food_grid.py` | 新建 |

---

## 9. 修订记录

| 版本 | 日期 | 说明 |
|------|------|------|
| v0.10.0 | 2026-06-02 | 自 implementation plan 升格 PRD |
