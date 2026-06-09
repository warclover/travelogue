# Travelogue · 文案优化验收标准

| 属性 | 内容 |
|------|------|
| **关联 PRD** | [PRD-COPY-OPTIMIZATION.md](./PRD-COPY-OPTIMIZATION.md) v1.1.0 |
| **关联实施** | [IMPLEMENTATION-COPY-OPTIMIZATION.md](./IMPLEMENTATION-COPY-OPTIMIZATION.md) |
| **代号** | COPY-OPT · Lite Copy v1.1 |
| **更新日期** | 2026-06-09 |
| **状态** | Active · P0–P4 工程完成 · 盲评 AC-COPY-17 待人工 |

---

## 1. 验收环境

- `pip install -e ".[dev]"`；
- draft 预览：`python -m travelogue serve trips/<id>`；
- fixture：现有 demo trip + 含 voice/anchors 的专项 fixture。

---

## 2. P0 验收（必过）

| ID | 条件 | 验证方式 |
|----|------|----------|
| **AC-COPY-01** | 默认 scope=frame；全书点缀中位数 ≤120 字 | 脚本统计 + `test_copy_optimization.py` |
| **AC-COPY-02** | decorLine ≤30 字；超长拒绝 | `test_phase11_decor_line.py` + 新测 |
| **AC-COPY-03** | fact 不足且无 voice → decorLine 空，无模板凑句 | `test_copy_optimization.py::test_skip_empty_facts` |
| **AC-COPY-04** | 纯照片隐藏 L1～L4（含 decorLine/caption） | `test_phase11_copy_toggle_regression.py` |
| **AC-COPY-05** | decorLine 可 inline-edit 并持久化到 trip.json | 手动 serve + `test_copy_optimization.py` |
| **AC-COPY-06** | `edited=true` 字段 regenerate 不覆盖 | `test_narrate.py` · decorLine 用例 |

---

## 3. P1 验收（走心管线）

| ID | 条件 | 验证方式 |
|----|------|----------|
| **AC-COPY-07** | 有 voice 章：decorLine 候选含 voice 精简句且重排优先 | 单测 + mock LLM |
| **AC-COPY-08** | fact≥2 且无高质量 voice 时调用 LLM K=3；fact 不足不调用 | mock 计数 |
| **AC-COPY-09** | 工具栏默认仅「纯照片」主开关；隐藏导语在二级 | 手动 UX + render 断言 |
| **AC-COPY-10** | 禁用词/泛化词命中较基线下降 | `scripts/copy_opt_acceptance.py` |
| **AC-COPY-11** | prompt 负向示例生效：盲测套话率下降 | 离线样本（≥20 章） |

---

## 4. P2 验收（UX / 意图）

| ID | 条件 | 验证方式 |
|----|------|----------|
| **AC-COPY-12** | 无 copyIntent 时被动推断仍提升 intent_fit | 对比单测 |
| **AC-COPY-13** | copyIntent UI 可选、可跳过、不阻塞导出 | Studio 流程 |
| **AC-COPY-14** | 同章 decorLine 与 lead 互斥 | narrate 集成测 |
| **AC-COPY-15** | 首次 draft 展示编辑提示且仅一次 | 手动 + localStorage 断言 |
| **AC-COPY-16** | 纯照片态不可进入 contenteditable | `inline-edit.js` 测 |

---

## 5. P3 验收（灰度 / 盲评）

| ID | 条件 | 验证方式 |
|----|------|----------|
| **AC-COPY-17** | 盲评 30 章：≥80%「不抢镜 / 像我的旅行」 | `docs/acceptance-records/copy-opt-blind-review.json` |
| **AC-COPY-18** | `photos_only_rate` 不高于基线 +10% | 灰度指标 |
| **AC-COPY-19** | 配置关闭回退 scope=full legacy 行为 | 配置切换回归 |
| **AC-COPY-20** | `pytest` narrate/render/schema/phase11 全绿 | CI |

---

## 6. 非回归（NR-COPY）

| ID | 条件 |
|----|------|
| **NR-COPY-01** | `hook/epilogue/caption` legacy 字段不退化 |
| **NR-COPY-02** | 旧 trip 无 decorLine 兼容（按空处理） |
| **NR-COPY-03** | longshot / mobile 导出 respect photos-only |
| **NR-COPY-04** | present 面无 `data-editable` |
| **NR-COPY-05** | `travelogue demo verify` 通过 |

---

## 7. 指标验收（观测 · 非硬门禁）

| 指标 | 参考 | 说明 |
|------|------|------|
| `copy_total_chars` 中位数 | 60～120 | 主体验指标 |
| `decor_line_fill_rate` | 60%～85% | **观测**，可低于下限 |
| `decor_line_empty_rate` | — | fact/voice 不足章占比，越高越诚实 |
| `generic_phrase_hits` | ↓ | 较 P11 基线 |
| `inline_edit_retention_rate` | 100% | edited 保护 |
| `intent_adoption_rate` | — | 观测 |

**硬门禁 KPI：** AC-COPY-17（盲评）、AC-COPY-18（隐藏率）、NR-COPY-*（回归）。

---

## 8. 修订记录

| 版本 | 日期 | 说明 |
|------|------|------|
| v1.0.0 | 2026-06-09 | 对齐 PRD v1.1；P0–P3 分层验收 |
