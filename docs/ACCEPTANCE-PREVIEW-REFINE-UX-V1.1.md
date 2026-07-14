# 精修可用性优化 V1.1 · 验收清单

| 属性 | 内容 |
|------|------|
| **对应 PRD** | [PRD-PREVIEW-REFINE-UX-V1.1.md](./PRD-PREVIEW-REFINE-UX-V1.1.md) v0.2.1 |
| **实施清单** | [IMPLEMENTATION-PREVIEW-REFINE-UX-V1.1.md](./IMPLEMENTATION-PREVIEW-REFINE-UX-V1.1.md) |
| **评审纪要** | [preview-refine-ux-v1.1-review-2026-07-14.md](./acceptance-records/preview-refine-ux-v1.1-review-2026-07-14.md) |
| **线框** | [preview-refine-ux-v1.1-wireframe.html](./wireframes/preview-refine-ux-v1.1-wireframe.html) |
| **状态** | **代码就绪 · 待手测补签**（S1 / AC 真机） |
| **日期** | 2026-07-14 |
| **静态门禁** | `tests/unit/web/test_preview_toolbar_v3.py` · M1/M2 markers ✅ |

---

## 1. 里程碑完成度

| 里程碑 | 状态 | 说明 |
|--------|------|------|
| **M1 P0** | ✅ 代码 | 模式 ≠ 面板；Dock「完成」；chip / tip；关面板 CTA |
| **M2 P1** | ✅ 代码 | 这本净化；迁移 tip；封面缩略图；导出 Tab；hint 收敛 |
| **M3 P2** | ✅ 代码 | 「给这本游记的一句话」；手机封面首次展开；pull quote `\201C` |
| **M4** | ⏳ | 本清单 + S1 手测记录 |
| **Park** | — | PK-01～04 不在本主题 |

---

## 2. AC-REFUX 手测清单

| ID | 用例 | 期望 | 结果 |
|----|------|------|------|
| **AC-REFUX-01** | 开精修 → Esc | 面板关，`refine=on`，★ 可见可点 | ⏳ |
| **AC-REFUX-02** | 面板关时点 ★ | 成功切换精选；Task Dock「更新版面」 | ⏳ |
| **AC-REFUX-03** | 点 Dock「完成」 | `refine=off`，★ 隐藏 | ⏳ |
| **AC-REFUX-04** | 「这本 · 整本故事」 | 无锚点 / 章意图 /「当前章」 | ⏳ |
| **AC-REFUX-05** | 正文「这页」 | 可见本章名与锚点 | ⏳ |
| **AC-REFUX-06** | 封面候选 | UI 无 `asset-` 明文（仅 title/调试） | ⏳ |
| **AC-REFUX-07** | 「导出」首屏 | 无 zip / LLM / 放映；在「更多工具」内 | ⏳ |
| **AC-REFUX-08** | LLM off | 「生成」禁用 +「生成不可用 · 未配置写作引擎」 | ⏳ |
| **AC-REFUX-09** | 零精修导出 | 仍 ≤1 次点击（无 pending） | ⏳ |
| **AC-REFUX-10** | Share | 无精修壳 | ⏳ |
| **AC-REFUX-11** | V1 导出拦截 | pending 时不可静默旧导出 | ⏳ |
| **AC-REFUX-12** | Sheet 说教 | 「更新版面」重复 hint ≤1 | ⏳ |
| **AC-REFUX-13** | 面板开再点 Dock「精修」 | 关面板，`refine` 仍 on | ⏳ |
| **AC-REFUX-14** | 面板已关时 Esc | 不退出模式 | ⏳ |
| **AC-REFUX-15** | pending 时点「完成」 | 退出模式 + toast + Task Dock 仍在 | ⏳ |
| **AC-REFUX-16** | 首次打开「这本」 | 一次迁移 tip「章节锚点与意图已移到「这页」」 | ⏳ |
| **AC-REFUX-S1** | 新手脚本（MF-06） | 无旁白完成标精选（建议 N≥5） | ⏳ |

---

## 3. 入口迁移自检（相对 V1）

| 能力 | V1.1 入口 | 自检 |
|------|-----------|------|
| 精修模式 | Dock「精修」进入；「完成」退出；关面板保模式 | ⏳ |
| ★ / 拼图 | 画面（模式 on）；「这页」可镜像 | ⏳ |
| 章锚点 / 章意图 / 重写文案 | **「这页」**（正文屏） | ⏳ |
| 杂志名 / 给这本游记的一句话 | **「这本 · 整本故事」** | ⏳ |
| 封面 / 封底缩略图 | **「这本 · 首尾装帧」** | ⏳ |
| 手机封面对照 | 首尾装帧内「手机封面 · 预览手机效果」（首次展开） | ⏳ |
| 导出 prefs | Dock ▾ + Tab「导出」同 prefs | ⏳ |
| zip / 文件夹 / 阅读 / 放映 / LLM | 「导出 → 更多工具」 | ⏳ |
| 更新版面 | Task Dock 主 CTA（Sheet 不刷屏） | ⏳ |

---

## 4. 工程静态门禁

```text
python -m pytest tests/unit/web/test_preview_toolbar_v3.py -q -k "not smoke"
```

关键用例：

- `test_preview_refine_ux_v11_m1_mode_panel_decouple_markers`
- `test_preview_refine_ux_v11_m2_markers`

---

## 5. S1 新手脚本（MF-06）

详见 [acceptance-records/preview-refine-ux-v1.1-s1-2026-07-14.md](./acceptance-records/preview-refine-ux-v1.1-s1-2026-07-14.md)。

**通过标准**：无旁白下，参与者能完成「打开精修 → 收起面板 → 在照片上点 ★ →（可选）更新版面」。

---

## 6. Go / No-Go

| | 标准 |
|--|------|
| **Go** | AC-REFUX-01～08、12～16 手测 ✅；静态门禁绿；V1 导出拦截 / Share 不回归 |
| **Conditional Go** | S1 未跑满 N≥5，但内部狗粮 AC-01～03/13～15 已过（与评审一致） |
| **No-Go** | 关面板后 `refine=off`；「这本」仍混装章字段；封面 UI 仍露 `asset-` 明文 |
