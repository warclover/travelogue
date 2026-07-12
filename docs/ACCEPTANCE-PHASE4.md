# Travelogue · Phase 4 验收标准

> **单轨入口**：[ACCEPTANCE.md](./ACCEPTANCE.md) · 当前发布闸门：[ACCEPTANCE-PHASE5.md](./ACCEPTANCE-PHASE5.md)

| 属性 | 内容 |
|------|------|
| **关联 PRD** | [PRD-PHASE4.md](./PRD-PHASE4.md) v0.4.3 |
| **UX 线框** | [archive/import-sheet/studio-import-sheet-v1.html](./archive/import-sheet/studio-import-sheet-v1.html)（已归档） |
| **代号** | P4-Intent |
| **更新日期** | 2026-06-06 |

---

## 1. 验收环境

- Windows 10/11 · Chrome/Edge 90+  
- `pip install -e ".[dev]"` · `python -m travelogue studio`  
- _fixture_：`tests/fixtures/intent/`（M18 交付）· 附录 A 双文件夹样例

---

## 2. 功能验收

| ID | 描述 | 步骤 | 通过 |
|----|------|------|------|
| **AC-P4-01** | Intent 带 | 首页填写杂志名 → 导入 → `trip.json` 中 `meta.title` 与输入一致 | ☑ 单测 + 预览 toolbar inline 保存 |
| **AC-P4-02** | 精选反馈 | 使用含 `精选/`+`素材/` 的相册 → 成功页含「N 张精选」 | ☑ `test_studio_intent_ac_p4.py` + `test_studio_intent_ac_p4_playwright.py`（FirstSuccess 第一行） |
| **AC-P4-03** | Peak 深链 | 导入完成点「打开预览」→ URL 含 `#screen-` 且首屏为内容屏 | ☑ 单测（`test_studio_entry.py`）；e2e 手测建议 |
| **AC-P4-04** | userNotes 进叙事 | `userNotes` 含固定词「慢走」→ narrate 后 hook/lead 含「慢走」 | ☑ brief 单测（`test_studio_intent.py`）；预览 PATCH intent 已接 |
| **AC-P4-05** | 附录 A 不回归 | `pytest tests/test_user_tier*.py -q` + AC-DF-02 | ☑ `phase4_acceptance_gate.py --skip-integration`（含 `test_user_tier.py` 非 integration） |
| **AC-P4-06** | memoryAnchors | 预览为 ch-01 填 2 条锚点 → 保存 → 重载仍存在；schema 通过 | ☑ 编辑 drawer + copy_patch 单测 |
| **AC-P4-07** | plan 城市 | 上传 plan.txt 列出「大阪」「京都」→ 章标题含两地（顺序一致）；golden 命中 ≥90% | ☑ |
| **AC-P4-07b** | plan fail-open | 上传空/乱码/>32KB plan → WARN 且 `intentHints` 不写 city；导入仍成功 | ☑ |
| **AC-P4-08** | NR-P4-01 | `g1_confirm_structure: false` 全自动 pipeline 与 Phase 2 同 stage 序列 | ☑ `test_studio_g1.py` mode A/B |
| **AC-P4-09** | 双写一致 | `apply_intent()` 后 `intent.title==meta.title` ∧ `intent.userNotes==trip.userNotes` ∧ `intent.places==meta.places`（PRD §4.1） | ☑ 单测（`test_studio_intent.py`） |
| **AC-P4-TEL-01** | telemetry | 提供 intent 的 trip 生成 `runs/studio-intent.json`，含 `hasUserNotes`/`featuredCount`/`planUploaded`/`tierMode` 等字段 | ☑ `test_studio_intent_telemetry.py` |

---

## 3. 首页极易用（Phase 4 · 对齐 AC-HP-26～29）

| ID | 描述 | 通过 |
|----|------|------|
| **AC-P4-HP-01** | 空态 10 秒内能说明「点制作杂志 → 选文件夹」 | ☐ |
| **AC-P4-HP-02** | 选夹→确认→开始制作后见进度；≤4 次点击（含系统选目录） | ☐ |
| **AC-P4-HP-05** | Importing 时无法 reopen panel | ☐ |
| **AC-P4-HP-06** | title 超长显示行内红字（附录 B） | ☐ |
| **AC-P4-HP-03** | 回访用户 5 秒内通过「继续编辑」进入预览 | ☐ |
| **AC-P4-HP-04** | 路径输入不在 Hero 首屏主视觉区 | ☐ |

## 3b. 无障碍验收（A11Y · 对齐 PRD §6.12/§6.13）

| ID | 描述 | 通过 |
|----|------|------|
| **AC-P4-A11Y-01** | 金钮前景/背景对比 ≥4.5:1（§6.12 定稿色，**不**用 `#d2a657`+白字 1.9:1）；sheet 正文 ≥4.5:1 | ☑ `--accent-ink: #1a1408`（≈9:1） |
| **AC-P4-A11Y-02** | sheet 焦点陷阱 + `Esc` 关闭 + `aria-labelledby=#studio-sheet-title` | ☑ `trapSheetFocus` · Tab 环回手测建议 |
| **AC-P4-A11Y-03** | `prefers-reduced-motion: reduce` 下无 coach 脉冲/bar 动画 | ☑ `test_studio_a11y_p4.py`（v2 loading bar `animation: none`） |

---

## 4. 体验验收（人工）

| ID | 描述 | 通过 |
|----|------|------|
| **UX-P4-01** | 5 人访谈：能复述精选/素材文件夹语义 | ☐ |
| **UX-P4-02** | **评估协议 P-EVAL**（PRD §2.1）：3 相册 × 无/全 intent 盲评，全 intent 胜 ≥55%（≥4/6 对） | ☐ |
| **UX-P4-03** | 可选字段全跳过仍 ≤20 分钟完成长图（G-P2-01） | ☐ |

---

## 5. 自动化

```powershell
python scripts/phase4_acceptance_gate.py --skip-integration
python -m pytest tests/test_studio_intent_ac_p4_playwright.py -q -m "e2e and playwright_serial"
pytest tests/test_studio_a11y_p4.py tests/test_studio_intent_ac_p4.py tests/test_studio_intent.py tests/test_studio_entry.py tests/test_studio_intent_telemetry.py tests/test_intent_plan.py tests/test_studio_g1.py tests/test_user_tier.py -q -m "not integration"
python scripts/validate_trip.py trips\<fixture-trip-id>
# telemetry 产物（导入完成后）：
# type runs\studio-intent.json
```

---

## 6. 发布门禁

- **M15–M19 代码主线** 已落地（含 telemetry · G1 UI · arcSegment peak 链）  
- **自动化已绿**：AC-P4-01/02/03/04/05/06/07/07b/08/09 · AC-P4-TEL-01 · AC-P4-A11Y-01/02/03  
- **发布前仍待人工**：AC-P4-HP-01～06 · UX-P4-01～03（P-EVAL）

> **进度（2026-06-06 · 自动化收口）**：`scripts/phase4_acceptance_gate.py` 聚合 59 项单测（CI `validate` job）；AC-P4-02 e2e 见 `test_studio_intent_ac_p4_playwright.py`（CI `test-e2e` job）。剩余 HP 手测、P-EVAL 盲评见 [IMPLEMENTATION-PHASE4.md](./IMPLEMENTATION-PHASE4.md)「发布前仍待人工」。
