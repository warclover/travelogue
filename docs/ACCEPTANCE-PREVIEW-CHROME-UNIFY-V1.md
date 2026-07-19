# 预览 Chrome 收敛 V1 · 验收清单

| 属性 | 内容 |
|------|------|
| **对应合同** | [产品原则](./acceptance-records/preview-chrome-unify-v1-product-note-2026-07-19.md) · [D-PCU-07～12](./acceptance-records/preview-chrome-unify-v1-decisions-2026-07-19.md) · [评审](./acceptance-records/preview-chrome-unify-v1-review-2026-07-19.md) |
| **线框** | [preview-chrome-unify-v1-wireframe.html](./wireframes/preview-chrome-unify-v1-wireframe.html)（Scheme A / MF-07） |
| **分支** | `feat/preview-chrome-unify-v1` |
| **状态** | **合入准备就绪（本地验收）** · GitHub Actions 额度可能不可用 → 以本地套件 + 狗粮为准 |
| **日期** | 2026-07-19 |

---

## 1. AC 结论

| ID | 结论 | 证据 |
|----|------|------|
| **AC-PCU-01** | Pass | 默认预览无黄 G1 / 无底舱 G1 / 无独立 badge；可点长图 |
| **AC-PCU-02** | Pass | 主路径结构已锁定语义；实验 OFF 可直接导出 |
| **AC-PCU-03** | Pass | Dock「分章」开关轻面板；Esc/× 无残留 |
| **AC-PCU-04** | Pass | 管道态仅 D-STAT；完成态折叠 |
| **AC-PCU-05** | Pass | Help 仅 Dock `?`（无左上 FAB） |
| **AC-PCU-06** | Pass | Strip 默认无 G1 |
| **AC-PCU-07** | Pass | 实验 ON：自动开分章 + pending；确认并继续 → rendered |
| **AC-PCU-08** | Pass | 分章 ⟷ 精修互斥 |
| **AC-PCU-09** | Pass | CTA `#c4a574` / 墨炭壳抽检 |
| **AC-PCU-10** | Pass | 390 窄屏触控 ≥40px、主控可见不裁切 |

---

## 2. 狗粮签字（典型用户模拟）

| 人设 | 场景 | 结论 |
|------|------|------|
| A 主路径 ~80% | 静默验货 → 长图 | Pass |
| B 轻不满 ~15% | tip → 分章跳章 → Esc | Pass |
| C 深编辑 ~5% | 分章后开精修互斥 | Pass |
| D 窄屏手机 | 390 触控与可见性 | Pass |
| E 困惑用户 | Help H2 提「分章」 | Pass |
| F 播放 | 入口可达 present | Pass |

环境：Windows · Studio `http://127.0.0.1:8766` · `demo-album` · 2026-07-19。

---

## 3. 本地验收命令（替代 CI）

```powershell
cd C:\Users\xiafe\Projects\travelogue
python -m pytest `
  tests/unit/web/test_help_onboarding_v1.py `
  tests/unit/web/test_preview_toolbar_v3.py `
  tests/unit/web/test_studio_ux_p3.py `
  -q --tb=line
# 2026-07-19 本地：47 passed
```

---

## 4. 后置（不挡合入）

| ID | 说明 |
|----|------|
| SF-05 | 埋点 `chap_panel_open` / 直接导出率抽检 |
| SF-06 | 无 G1 分章质量样例集（算法并行） |
| SF-07 | Scheme A 亮景实机抽检 |

---

## 5. 合入注意事项

- **勿带入**：`config/output_recipe_*.yaml`、根目录 `qa-*.png`、`trips/perf-*`
- PR 注明：`CI skipped if Actions minutes exhausted · local suite green`
- 实验开关 `g1ConfirmStructure` 默认应保持 **OFF**（产品主路径）；ON 仅旧工作流/实验
