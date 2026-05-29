# Travelogue · Phase 5 验收标准

> **单轨入口**：[ACCEPTANCE.md](./ACCEPTANCE.md)

| 属性 | 内容 |
|------|------|
| **关联 PRD** | [PRD-PHASE5.md](./PRD-PHASE5.md) v0.5.4 |
| **关联** | [ACCEPTANCE.md](./ACCEPTANCE.md)（单轨入口）· [IMPLEMENTATION-PHASE5.md](./IMPLEMENTATION-PHASE5.md) |
| **代号** | P5-Polish · 双路径交付 |
| **更新日期** | 2026-05-30 |

---

## 1. 验收环境

- Windows 10/11 · Chrome/Edge 90+  
- `pip install -e ".[dev]"` · Playwright（长图）  
- 启动：`python -m travelogue studio` 或 `start-studio.bat`  
- _fixture_：50–100 张相册 · 含 `精选/`+`素材/`（推荐）  
- 无痕窗口或关闭浏览器扩展（避免 modal 干扰）

---

## 2. 路径 A · 零编辑主 KPI

### UX-P5-80-01（权威 · Tier 0）

| 项 | 规格 |
|----|------|
| **Persona** | 非开发者 · 无 LLM Key 可 stub |
| **禁止** | 感受/plan/锚点 · drawer · ★ · 改文案 |
| **允许** | 选夹 · 跳过默认名 · 成功页 **生成长图** · 可选 ≤10s 预览 |
| **计时** | 双击 bat → PNG 在资源管理器中可见 · **≤ 15 分钟** |
| **通过** | AC-P2-02 微信可读 · success chips 含精选数（AC-P4-02） |
| **记录** | [phase5-zero-edit.json](./acceptance-records/phase5-zero-edit.json) |

| ID | 描述 | 步骤 | 通过 |
|----|------|------|------|
| **AC-P5-A-01** | 成功页主 CTA | 导入完成 → 主按钮为「生成长图」· **无** 5s 自动跳预览 | ☐ |
| **AC-P5-A-02** | 长图 Job | 点生成长图 → 进度可见 → 成功 reveal 文件夹 | ☐ |
| **AC-P5-A-03** | 长图体积 | 单张或分段 PNG · 微信可发 · ≤20MB/段（L2） | ☐ |
| **AC-P5-A-04** | 长图宽度 | iPhone 15 Pro Max 可读 · 非 390 窄条（L1） | ☐ |
| **AC-P5-A-05** | toolbar 极简 | 预览首屏：返回 · 保存长图 · 文件夹 · ⋯更多编辑 | ☐ |
| **AC-P5-A-06** | 409 人话 | 连点导入/busy → toast「排队中」非「导入失败」 | ☐ |

---

## 3. 路径 B · 卷轴定性 KPI

### UX-P5-SCROLL-01（Tier 0）

| 项 | 规格 |
|----|------|
| **Persona** | 3–5 名未见过产品者 |
| **URL** | share 态 entry（P5-S7）· 本地 serve |
| **通过** | ≥3/5 「哇/高级/像杂志」· 滚动完成率 ≥70% · 封面停留 >3s |
| **记录** | [phase5-scroll-qualitative.json](./acceptance-records/phase5-scroll-qualitative.json) |

| ID | 描述 | 通过 |
|----|------|------|
| **AC-P5-B-01** | auto profile | &lt;20 张 trip 打开为 soft breath · 无用户选 profile | ☐ |
| **AC-P5-B-02** | share 态 | web-view URL 无 Studio preview toolbar | ☐ |
| **AC-P5-B-03** | 章节分隔 | 多章 trip 章间有全出血分隔屏（S2 · Tier 1 不阻塞 A） | ☐ |
| **AC-P5-B-04** | epilogue | 滚到底有总结封底（S4 · Tier 1） | ☐ |
| **AC-P5-B-05** | screenplay | 可选全屏放映 · hash 深链可用（S8 · 加分） | ☐ |

---

## 4. 排版地基（两路径共享）

| ID | 描述 | 通过 |
|----|------|------|
| **AC-P5-C-01** | 封面 C2 | 群分享封面非截图/人像大头 · 小相册 ≤15 张体验可接受 | ☐ |
| **AC-P5-C-02** | 排版冲刺 QS-01 | 10 相册调优版胜 ≥8/10 · 见 sprint 记录 | ☐ |
| **AC-P5-C-03** | 双 curate D1 | 长图 ≤10–15 屏 · web 全量 · 同一 trip.json | ☐ |

---

## 5. 成功页双路径

| ID | 描述 | 通过 |
|----|------|------|
| **AC-P5-UX-01** | 双 CTA | 主=生成长图 · 次=打开卷轴预览 · 路径提示可见 | ☐ |
| **AC-P5-UX-02** | 次 CTA 卷轴 | 打开为 entry/share URL · Lenis/breath 生效 | ☐ |

---

## 6. 自动化

```powershell
python -m pytest tests/test_studio_a11y_p4.py tests/test_studio_entry.py tests/test_reading_p5.py tests/test_reading_auto_breath.py -q
python scripts/e2e_studio_smoke.ps1
```

---

## 7. 发布门禁（Phase 5 Done）

> **单轨入口**：[ACCEPTANCE.md](./ACCEPTANCE.md) · 记录目录：[acceptance-records/README.md](./acceptance-records/README.md)

Phase 5 **不替代** Phase 2–4 AC，但发布前须满足：

| 类别 | 必达项 |
|------|--------|
| **路径 A Tier 0** | UX-P5-80-01 · AC-P5-A-01～03 · AC-P5-C-01 · AC-P2-02 |
| **路径 B Tier 0** | AC-P5-B-01/02 · UX-P5-SCROLL-01 · AC-P5-C-02 |
| **体验** | AC-P4-HP-01～06 · AC-P4-A11Y-03 |
| **工程** | e2e smoke · CLI-SPEC 同步 |
| **不阻塞** | AC-P5-B-03～05 · P-EVAL · P5-C1 beam 实验 |

---

## 8. 变更记录

| 日期 | 说明 |
|------|------|
| 2026-05-30 | 初稿：双路径 AC · UX-P5-80-01 · UX-P5-SCROLL-01 |
| 2026-05-30 | 链至 ACCEPTANCE.md 单轨入口（P5-12.2） |
