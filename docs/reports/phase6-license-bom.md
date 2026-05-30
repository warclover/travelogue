# Phase 6 · License BOM

| 属性 | 内容 |
|------|------|
| **阶段** | P6-Stability |
| **关联 PRD** | [PRD-PHASE6.md](../PRD-PHASE6.md) §16 |
| **更新日期** | 2026-05-30 |

---

## 1. 分级规则

| 级别 | 定义 | 策略 |
|------|------|------|
| L0 | 商用友好（MIT/Apache/BSD） | 默认可用 |
| L1 | 条件商用 | 备案后可用 |
| L2 | 非商用/限制许可 | 仅实验，禁止默认链路 |

---

## 2. 组件台账

| component | license | level | usage_scope | commercial_status | fallback | owner | status |
|-----------|---------|-------|-------------|-------------------|----------|-------|--------|
| scikit-learn (HDBSCAN/DBSCAN) | BSD-3-Clause | L0 | default (vision extra) | 可商用 | DBSCAN 固定参数 | 算法 | active |
| numpy | BSD-3-Clause | L0 | default (vision extra) | 可商用 | — | 工程 | active |
| opencv-python-headless | Apache-2.0 | L0 | default (vision extra) | 可商用 | Pillow 几何 | 工程 | active |
| Pillow | HPND (PIL) | L0 | default | 可商用 | — | 工程 | active |
| PyYAML | MIT | L0 | default | 可商用 | — | 工程 | active |
| jsonschema | MIT | L0 | default | 可商用 | — | 工程 | active |
| typer | MIT | L0 | default | 可商用 | — | 工程 | active |
| open-clip-torch | MIT | L0 | experiment (clip extra) | 可商用 | heuristic 向量 | 算法 | optional |
| torch | BSD-style | L0 | experiment (clip extra) | 可商用 | heuristic 向量 | 算法 | optional |
| playwright | Apache-2.0 | L0 | dev/e2e only | 可商用 | — | QA | dev-only |

---

## 3. 发布门禁检查

| 检查项 | 结论 |
|--------|------|
| BOM 是否完整 | ☑ Phase 6 新增链路已登记 |
| L2 组件是否进入默认链路 | ☑ 无 L2 进入默认路径 |
| 替代方案是否可执行 | ☑ CLIP 不可用时 heuristic 回退 |
| 审核签字是否完成 | ☐ 待产品/技术签字 |

---

## 4. 审核签字

| 角色 | 负责人 | 结论 | 日期 |
|------|--------|------|------|
| 技术负责人 | 待填 | 通过 / 拒绝 | 待填 |
| 产品负责人 | 待填 | 通过 / 拒绝 | 待填 |
| 产品总监 | 待填 | 最终放量 / 回退 | 待填 |

---

## 5. 变更记录

| 日期 | 说明 |
|------|------|
| 2026-05-30 | 模板创建 |
| 2026-05-30 | 填入 pyproject 依赖与 Phase 6 算法组件 |
