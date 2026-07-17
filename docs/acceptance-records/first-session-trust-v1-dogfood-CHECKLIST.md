# 首访可信 · 手测狗粮清单（F1–F5 · AC-FST-15）

| 属性 | 内容 |
|------|------|
| **对应** | [ACCEPTANCE-FIRST-SESSION-TRUST-V1.md](../ACCEPTANCE-FIRST-SESSION-TRUST-V1.md) · [线框](../wireframes/first-session-trust-v1-wireframe.html) |
| **用途** | QA-FST-05 / AC-FST-15 · 真人 N≥5（建议含 U1 分享者 · U3 空态首访 · U7 家庭组织者） |
| **原则** | **非实现者**勾选；W0 / W1 / W2 可分场；未勾齐不得对外宣布主题完成 |

---

## 0. 环境

```powershell
cd C:\Users\xiafe\Projects\travelogue
$empty = Join-Path $env:TEMP "travelogue-fst-dogfood"
New-Item -ItemType Directory -Force -Path $empty | Out-Null
$env:TRAVELOGUE_STUDIO_TRUST_LOCAL_ALBUM = "1"
python -m travelogue studio --no-open --host 127.0.0.1 --port 8778 --trips-dir $empty
```

浏览器打开 `http://127.0.0.1:8778/`，清该 origin 的 `localStorage` / `sessionStorage` 后刷新。

---

## 1. W0 · F1–F4（可等）

| # | 步骤 | 期望 | 勾选 |
|---|------|------|------|
| F1-a | 能力卡 → 开始制作 →「用示例照片试一次」→ 开始 | 进入导入忙碌壳 | ☐ |
| F1-b | 观察进度主句 | 离开 ingest 后主句**不再**仅为「已处理 N/N」；切到分章/文案/排版类人话 | ☐ |
| F1-c | 若出现「比预期久一些」 | 阶段主句仍可见（慢安抚仅次行） | ☐ |
| F2-a | Job 成功瞬间 | ≤1s 出现 FirstSuccess；忙碌壳关闭 | ☐ |
| F3-a | 打开卷轴 → Dock「发微信群」 | 进度为人话；**无**长期唯一「0%」；可有 indeterminate | ☐ |
| F4-a | 长图成功 | 主句含「已保存」；**无**「打开微信 / 按序发群」教学句 | ☐ |
| F4-b | 成功面主钮 | 文案「在文件夹中显示」且为实心主色 | ☐ |
| F4-c | 成功瞬间 | **未**自动弹出资源管理器 | ☐ |
| F4-d | 停留 ≥3s（或不点关闭） | 成功面仍可见 | ☐ |
| F4-e | 点击主钮 | 资源管理器定位到 PNG | ☐ |
| NR-01 | 空态/示例入口 | 向导与示例入口可用（FTUE 不回归） | ☐ |
| NR-02 | 无 AI Key | 示例仍可成稿（L0） | ☐ |

---

## 2. W1 · F5（敢秀）

| # | 步骤 | 期望 | 勾选 |
|---|------|------|------|
| F5-a | 示例成片封面/开篇 | 无「慢慢翻」「抬头看见…」「下次再见」 | ☐ |
| F5-b | 读者面图注/脚注 | 无相机 Make/Model（如 NIKON / iPhone 型号串） | ☐ |
| F5-c | 章名 | 无「*续」；同日多章为时段或（2）（3） | ☐ |
| F5-d | 噪音文件夹名导入（如 `王丹昙华林2`） | 封面 · FirstSuccess · 书架展示名一致且为回退名（非裸目录名） | ☐ |

---

## 3. W2 · 辑封

| # | 步骤 | 期望 | 勾选 |
|---|------|------|------|
| W2-a | 卷轴滚到封底 | 眉题为「辑封」或无英文化 Colophon 唯一眉题 | ☐ |
| W2-b | 统计张数 | 与版面/精选口径一致（不离谱偏大/偏小） | ☐ |

---

## 4. 埋点抽查（可选 · 本机 `?dev=1`）

在控制台或 `localStorage.travelogue.studio.eventRing` 中可见（有则勾）：

| 事件 | 场景 | 勾选 |
|------|------|------|
| `import_ui_terminal_ms` | 导入成功切 FirstSuccess | ☐ |
| `import_stage_stall` | 同主句停滞 >8s（狗粮失败时） | ☐ |
| `longshot_progress_mode` | 导出中 percent / indeterminate | ☐ |
| `longshot_success_visible_ms` | 成功面关闭/自动隐藏时 | ☐ |
| `longshot_reveal_auto_blocked` | 成功面展示且未自动 reveal | ☐ |

---

## 5. 签字（AC-FST-15）

| 角色 | 姓名 | 日期 | W0 | W1 | W2 | 备注 |
|------|------|------|----|----|----|------|
| 产品 | | | ☐ | ☐ | ☐ | |
| UX | | | ☐ | ☐ | ☐ | |
| 用户 U1（分享者） | | | ☐ | ☐ | ☐ | |
| 用户 U3（空态首访） | | | ☐ | ☐ | ☐ | |
| 用户 U7（家庭组织者） | | | ☐ | ☐ | ☐ | |

**完成宣布条件**：上表真人 ≥5 席主链通过（至少含 U1/U3/U7 各一），且产品列 W0+W1 勾齐。
