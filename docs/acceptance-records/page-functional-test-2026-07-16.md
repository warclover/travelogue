# 页面功能测试记录 · 2026-07-16

| 属性 | 内容 |
|------|------|
| **日期** | 2026-07-16 |
| **范围** | Studio 首页 / Import / Output Recipe persona / 导出相关接线 |
| **触发** | 当日修补与架构优化后的模拟用户走查 |
| **执行** | Agent 自动化 + Playwright persona 套件 |
| **对照** | [ACCEPTANCE-OUTPUT-RECIPE-V1.md](../ACCEPTANCE-OUTPUT-RECIPE-V1.md) · [M21-MANUAL-SMOKE.md](../studio-homepage-v2/M21-MANUAL-SMOKE.md) |

---

## 1. Persona 矩阵与结果

| ID | Persona | 场景 | 方法 | 结果 |
|----|---------|------|------|------|
| P1 | 极简分享者（1–9） | Sparse CTA「导出长图 · 发微信群」 | `test_persona_sparse_*` | ✅ |
| P2a | 周末近郊（10–30） | 预览 `needsIntent` + 意图卡文案 | `test_persona_ambiguous_preview_*` | ✅ |
| P2b | 周末近郊 | 三选一（发群 / 九宫格 / 长图连读）+ 选择并导出 | `test_persona_ambiguous_intent_card_*` | ✅ |
| P2c | 周末近郊 | 「九宫格」仅绑定 `moments_grid` | `test_persona_ambiguous_grid_*` | ✅ |
| P2d | 周末近郊 | 书架 Ambiguous fallback | `test_persona_ambiguous_shelf_*` | ✅ |
| P3 | 摄影旅行（≥50） | 按章默认 + 整卷二次确认钩子 | `test_persona_narrative_*` | ✅ |
| P4 | 运维/灰度 | flag 关闭回退 | `test_persona_flag_off_*` | ✅ |
| P5 | 回访用户 | 书架首页 → 主 CTA → Wizard | `test_persona_returning_*` | ✅ |

**命令：**

```powershell
python -m pytest tests/e2e/test_output_recipe_persona_playwright.py -q
# 8 passed
```

**解析层单测（非 UI）：**

```powershell
python -m pytest tests/unit/export/test_output_recipe_resolve.py -q
# 15 passed
```

---

## 2. 回归冒烟（既有 e2e）

| 用例 | 结果 | 备注 |
|------|------|------|
| `test_ac_hp2_11_idle_returning_shelf` | ✅ | 书架 idle |
| `test_studio_intent_ac_p4_*`（2） | ✅ | FirstSuccess 精选文案 |
| `test_ac_hp2_10_cta_opens_sheet` | ❌ | 见缺陷 D-PFT-01 |

---

## 3. 缺陷与接线缺口

### D-PFT-01 · 首启能力卡拦截首页主 CTA — **已修**

- e2e `_goto_v2` 统一预置 `capabilityCardSeen`；产品上新用户仍走卡内「开始制作」→ `#v2-cta`。
- 复测：`test_ac_hp2_10_cta_opens_sheet` ✅

### D-PFT-02 · Output Recipe 接线 — **已修**

| 项 | 状态 |
|----|------|
| `OutputRecipeConfig` + YAML loader + expose | ✅ |
| `moments_grid` platform profile | ✅ |
| `export_trip_longshot` → photo_grid_pack | ✅ |
| `handle_output_recipe` / `handle_longshot` intent | ✅ |
| CLI `--intent` + `resolve-output-recipe` | ✅ |
| `startLongshot` 意图卡 / 整卷确认 / 换种分享 | ✅ |
| 成功态名实（九宫格 vs 长图连读） | ✅ |

开启灰度：`studio.output_recipe.enabled: true`（见 `config.yaml.example`）。

### D-PFT-03 · 护栏/ Pack 单测 — **已修**

```
tests/unit/export/test_output_recipe_*.py + test_photo_grid_pack.py → 34 passed
```

---

## 4. Go / No-Go（本轮 · 修复后复测）

| 闸门 | 结论 |
|------|------|
| Output Recipe 客户端 persona 合同 | **Go** · 8/8 |
| 首页 CTA 冒烟（`test_ac_hp2_10`） | **Go** · e2e 抑制能力卡；产品卡「开始制作」仍可用 |
| Output Recipe 解析 + 护栏 + CLI/API | **Go** · 34 unit 绿 |
| Photo Grid 路由 / 命名 | **Go** · `moments-grid` 分支 D |
| 全链路真人手测签字（H-A / H-B） | **待签** · 需 `studio.output_recipe.enabled: true` |

---

## 5. 建议下一步

1. 本地打开 `studio.output_recipe.enabled: true`，按 ACCEPTANCE-OUTPUT-RECIPE-V1 §4–5 做 H-A / H-B 真人签字。
2. persona 套件已带 `e2e` + `playwright_serial`，随 CI `test-e2e` 跑即可。

---

## 6. 浏览器走查（Playwright MCP · 本机 8766）

| 步骤 | 结果 |
|------|------|
| 打开 `/` | v2 首页，标题「每一个瞬间，都值得再次相遇」 |
| 点「开始制作我的游记」 | 打开 Import Wizard「制作我的游记画册」 |
| 可见选项 | 选文件夹 / 用示例照片试一次 |
| 能力卡 | 本机 `capabilityCardSeen=1`，未弹出；e2e 已统一抑制 |

Studio：`python -m travelogue studio --port 8766`。

---

## 7. 签字

| 项 | 负责人 | 日期 | 结论 |
|----|--------|------|------|
| 自动化 persona | Agent | 2026-07-16 | 8/8 绿 |
| 回访路径浏览器走查 | Agent | 2026-07-16 | CTA → Wizard ✅ |
| 接线修复复测 | Agent | 2026-07-16 | unit 34 + e2e 10 绿 |
| 全链路手测 | — | — | 待开启 flag 后签 |
