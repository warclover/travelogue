# Travelogue · 导出长图 2.0 验收标准

| 属性 | 内容 |
|------|------|
| **PRD** | [PRD-LONGSHOT-2.0.md](./PRD-LONGSHOT-2.0.md) v0.3.3 |
| **Cross-ref** | [research/GUIZANG-LONGSHOT-CROSSREF.md](./research/GUIZANG-LONGSHOT-CROSSREF.md) |
| **ADR** | [016-longshot-platform-export.md](./adr/016-longshot-platform-export.md) |
| **实施清单** | [IMPLEMENTATION-LONGSHOT-2.0.md](./IMPLEMENTATION-LONGSHOT-2.0.md) |
| **文档版本** | v0.1.0 |
| **状态** | Draft · QA 就绪 |
| **更新日期** | 2026-07-08 |

> **完成定义**
>
> - **Phase A（朋友圈）**：§3 自动化 + §4 手测 + §6 非回归 全部通过，且 **D-LNG2-02 已产品确认**（2026-07-08）。
> - **Phase B（小红书）**：在上述基础上 + §5 全部通过。
> - **Phase C（后端扩展）**：§7 CLI/stale 通过；无 Phase C 前端 AC。

---

## 1. 验收原则

1. **环境**：Studio `serve --studio` + Playwright 已安装；**http://** 访问预览页（非 `file://`）。
2. **样例 trip**：
   - **T-large**：≥80 张照片（推荐 `linzhi` 或同等规模），用于 **9 张**切分与性能。
   - **T-small**：**8–12 张照片**（D-LNG2-21），用于 **6–9 张降级**验收。
   - **T-tiny**：**1–5 张照片**，用于极小 trip（D-LNG2-22），期望 1–5 张 + 建议微信群。
   - **T-m14**：任意已渲染 trip，用于书架非回归。
3. **自动化**：每个 PR 合并前，§3 对应用例 **pytest 0 失败**。
4. **手测**：Phase A/B 发布前，§4/§5 由 **非实现者** 勾选。
5. **Telemetry**（可选）：§8 指标在 dogfood 环境采样 ≥7 天。

---

## 2. 已确认产品决策（验收前提）

| ID | 决策 | 确认状态 | 验收含义 |
|----|------|----------|----------|
| **D-LNG2-02** | 朋友圈 **目标 9 张**；8–12 张 trip **6–9 张**；1–5 张 trip 见 D-LNG2-22 | **✅ 已确认 2026-07-08** |
| **D-LNG2-21** | T-small = **8–12 张** photo | PRD 冻结 | 验收集不用 ≤12 泛化 |
| **D-LNG2-22** | 极小 trip 1–5 张 | PRD 冻结 | 不强制 6 张下限 |
| **D-LNG2-24** | 成功 Modal 无缩略条（Phase A） | PRD 冻结 | H-A-07 **跳过** |
| **D-LNG2-06** | 小红书默认 **letterbox** | PRD 冻结 | 默认 padMode 手测为留白边 |
| **D-LNG2-10** | 平台模式 **禁止 P1** | ADR-016 | P0 失败 · 文案见 D-LNG2-27 |
| **D-LNG2-14** | Job **原子写盘** | PRD 冻结 | 失败时无残缺 `*-moments-*.png` |

---

## 3. 自动化验收（AC-LNG2）

### 3.1 护栏与回归

| ID | 标准 | 测试 / 方法 | Phase | 通过 |
|----|------|-------------|-------|------|
| **AC-LNG2-05** | 请求 **无 `platform`** → 与 Longshot 1.x 行为一致 | `tests/test_export_longshot.py` 全绿 | A | ☐ |
| **AC-LNG2-05b** | `platform=wechat_chat` 显式传递 → 同 1.x | `tests/test_export_longshot.py` | A | ☐ |
| **AC-LNG2-05c** | 非法 `platform` → **400**，不静默回退 | `tests/test_studio_handlers_import_export.py` | A | ☐ |
| **AC-LNG2-10** | 书架「保存长图」仍为 scale=3 · photos · wechat_chat | `tests/test_studio_home_v2.py` · AC-M14 子集 | A | ☐ |

### 3.2 切分算法

| ID | 标准 | 测试 / 方法 | Phase | 通过 |
|----|------|-------------|-------|------|
| **AC-LNG2-02** | 切点 **不穿过 photo cell 内部** | `tests/test_content_splitter.py` | A | ☐ |
| **AC-LNG2-02b** | scale=2/3 时 canvas 坐标 = css×scale | `tests/test_content_splitter.py` | A | ☐ |
| **AC-LNG2-02c** | DP 段高方差优于纯贪心（固定 fixture 断言） | `tests/test_content_splitter.py` | A | ☐ |
| **AC-LNG2-02w** | 切点 weight：首切点倾向 cover/章分隔（fixture） | `tests/test_content_splitter.py` | A | ☐ |
| **AC-LNG2-01** | T-large · moments → **9 张** | `tests/test_export_longshot_platform.py` | A | ☐ |
| **AC-LNG2-01b** | T-small（**8–12 张**）· moments → **6–9 张** + userHint | 集成测试 + fixture | A | ☐ |
| **AC-LNG2-01t** | T-tiny（**1–5 张**）· moments → **1–5 张** + 建议微信群 | 集成测试 | A | ☐ |

### 3.3 朋友圈产物

| ID | 标准 | 测试 / 方法 | Phase | 通过 |
|----|------|-------------|-------|------|
| **AC-LNG2-01c** | 文件名 `{title}-moments-01` … 连续零填充 | glob 断言 | A | ☐ |
| **AC-LNG2-09** | 页脚水印 **`{i}/{n}`**（n=实际张数） | 像素/快照抽检 | A | ☐ |
| **AC-LNG2-08** | 单段 >20MB → 降 scale 或 jpeg；仍失败 → 明确 error | mock 大图集成测试 | A | ☐ |
| **AC-LNG2-11** | Job **失败**后 trip 目录 **无**残缺 `*-moments-*.png` / `.part` | 集成测试 | A | ☐ |
| **AC-LNG2-12** | platform=moments · P0 失败 → **无 P1** · Job failed | mock P0 失败 | A | ☐ |
| **AC-LNG2-13** | `copyDisplay=photos` · moments 仍满足 AC-LNG2-02 | 集成测试 | A | ☐ |

### 3.4 小红书（Phase B）

| ID | 标准 | 测试 / 方法 | Phase | 通过 |
|----|------|-------------|-------|------|
| **AC-LNG2-03** | `slideCount=6` → 6 张 **1080×1440** PNG | 像素断言 ±2% | B | ☐ |
| **AC-LNG2-03b** | 默认 `padMode=letterbox` | 快照/边带检测 | B | ☐ |
| **AC-LNG2-03s** | safe area warn log（**非硬 fail** · D-LNG2-30） | 集成测试 mock | B+ | ☐ |
| **AC-LNG2-04** | auto N：常规 **5–9**；photo<12 → **3–6**；photo>48 → **≤10**（D-LNG2-31） | 公式单测 | B | ☐ |
| **AC-LNG2-04b** | 命名 `{title}-xhs-{nn}.png` | glob 断言 | B | ☐ |
| **AC-LNG2-04c** | auto userHint 含「笔记正文」类指引 | 集成测试 | B | ☐ |

### 3.5 stale 与列表

| ID | 标准 | 测试 / 方法 | Phase | 通过 |
|----|------|-------------|-------|------|
| **AC-LNG2-06** | 存在 `*-moments-*` 或 `*-xhs-*` · trip 更新后 `longshotStale=true` | `tests/test_studio_trips.py` | C | ☐ |
| **AC-LNG2-06b** | 仅 1.x 产物过期 · stale 仍为 true | 同上 | C | ☐ |

### 3.6 前端（Studio）

| ID | 标准 | 测试 / 方法 | Phase | 通过 |
|----|------|-------------|-------|------|
| **AC-LNG2-07** | Popover 含平台选项 · prefs 持久化 | `tests/test_preview_toolbar_v3.py` | A | ☐ |
| **AC-LNG2-07b** | `buildLongshotRequest` 携带 platform | `tests/test_longshot_client.py` | A | ☐ |
| **AC-LNG2-07c** | 选朋友圈时 **隐藏**「按章/完整」 | Playwright / DOM | A | ☐ |

---

## 4. Phase A 手测 · 朋友圈

**前置**：`studio.longshot2.enabled=true`，`platforms` 含 `wechat_moments`。

### 4.1 T-large（≥80 张）

| 步骤 | 操作 | 预期 | 通过 |
|------|------|------|------|
| H-A-01 | 预览页 → 导出设置 → 选 **朋友圈** | Popover 显示「预计 9 张（内容少时可能 6–9 张）」 | ☐ |
| H-A-02 | 确认 · 点主按钮 | CTA 为 **「导出 9 张朋友圈配图」**（或等价文案） | ☐ |
| H-A-03 | 等待 Job 完成 | 成功 Modal · **9 张**（T-large 常态） | ☐ |
| H-A-04 | 查看文件列表 / 文件夹 | `*-moments-01` … `*-moments-09` 连续 | ☐ |
| H-A-05 | 目视切分质量 | 无照片从中间「切半」 | ☐ |
| H-A-06 | 成功 Modal | 含 **publishGuide**（01→09 选图步骤） | ☐ |
| H-A-07 | ~~缩略条~~ | **Phase A 跳过**（D-LNG2-24 · v2.0.1） | N/A |
| H-A-08 | 「在文件夹中显示」 | explorer 打开且定位首张 | ☐ |
| H-A-09 | 页脚水印 | 每张底部 **i/9** | ☐ |

### 4.2 T-small（8–12 张 · D-LNG2-21 降级）

| 步骤 | 操作 | 预期 | 通过 |
|------|------|------|------|
| H-A-10 | 选朋友圈 · 照片 8–12 | toast 可选建议微信群（<15 时） | ☐ |
| H-A-11 | 完成导出 | 输出 **6–9 张** | ☐ |
| H-A-12 | 阅读 userHint | 「内容较少 · 已生成 N 张」 | ☐ |
| H-A-13 | 页脚水印 | **i/N**（N=实际张数） | ☐ |
| H-A-14 | 产品确认 | sparse 6–9 降级可接受 | ✅ 已确认 |

### 4.2b T-tiny（1–5 张 · D-LNG2-22）

| 步骤 | 操作 | 预期 | 通过 |
|------|------|------|------|
| H-A-10b | 选朋友圈 · 1–5 张照片 | 不阻断 | ☐ |
| H-A-11b | 完成导出 | **1–5 张**（不凑满 6 张） | ☐ |
| H-A-12b | userHint | 建议改用 **微信群长图** | ☐ |

### 4.3 失败与边界

| 步骤 | 操作 | 预期 | 通过 |
|------|------|------|------|
| H-A-15 | 模拟 Job 失败（如断 Playwright） | 无残留 moments 半成品 | ☐ |
| H-A-16 | 长图 Job 进行中再点导出 | 409 busy Toast | ☐ |
| H-A-17 | 首次选朋友圈 | coach mark **仅出现一次** | ☐ |

---

## 5. Phase B 手测 · 小红书

**前置**：`platforms` 含 `xiaohongshu`。

| 步骤 | 操作 | 预期 | 通过 |
|------|------|------|------|
| H-B-01 | 选小红书 · 张数 **6** · letterbox | 请求含 platform + slideCount | ☐ |
| H-B-02 | Job 成功 | 6 个 `*-xhs-*.png` | ☐ |
| H-B-03 | 图片属性 | 各 **1080×1440** | ☐ |
| H-B-04 | 默认填充 | **留白边**（非默认 smart_crop） | ☐ |
| H-B-05 | auto 张数 | 显示估算 N · 产出合理 | ☐ |
| H-B-06 | 成功 Modal | 含小红书 **发布步骤**（保存相册 → 发笔记） | ☐ |
| H-B-07 | App 导入（真机/模拟） | 6 张可一次多选加入笔记 | ☐ |
| H-B-08 | smart_crop flag **关** | UI 不展示或 disabled smart_crop | ☐ |

---

## 6. 非回归清单（NR-LNG2）

| ID | 标准 | 通过 |
|----|------|------|
| **NR-LNG2-01** | M14 书架保存长图：3× · photos · 无 platform 字段 | ☐ |
| **NR-LNG2-02** | 预览页 full/photos toggle 不影响 wechat_chat 导出 | ☐ |
| **NR-LNG2-03** | CLI 无新 flag 时 = 1.x | ☐ |
| **NR-LNG2-04** | wechat_chat 分段仍可用 P1 + F-LNG-10 文案 | ☐ |
| **NR-LNG2-05** | `copy-display.css` photos 语义（无 hook/decorLine） | ☐ |
| **NR-LNG2-06** | `index-longshot.html` 无 Studio Chrome 注入 | ☐ |
| **NR-LNG2-07** | 游记页 FAB 降级路径不暴露 platform preset | ☐ |
| **NR-LNG2-08** | zip 高级导出不因 longshot2 回归 | ☐ |

---

## 7. Phase C · CLI 与 stale 手测

| 步骤 | 操作 | 预期 | 通过 |
|------|------|------|------|
| H-C-01 | `export-longshot T --platform wechat_moments` | 产出 moments 前缀 | ☐ |
| H-C-02 | `export-longshot T --platform xiaohongshu --slide-count 6` | 6×1080×1440 | ☐ |
| H-C-02b | `export-longshot T --platform instagram --slide-count 4` | 4×1080×1350 · `-ins-` | ☑ |
| H-C-02c | `export-longshot T --platform douyin_cover` | 1×1080×1920 · `-douyin-cover.png` | ☑ |
| H-C-02d | `export-longshot T --platform custom --width 720 --height 960 --slide-count 3` | 3×720×960 · `-custom-` | ☑ |
| H-C-03 | 编辑 trip 后首页 | **长图可更新** stale 徽章 | ☐ |
| H-C-04 | Studio UI | **无** Ins/微博/抖音 菜单项（Phase C 仅后端） | ☑ |

---

## 8. 性能与产品指标（G-LNG2-07/08/09）

| ID | 标准 | 条件 | 通过 |
|----|------|------|------|
| **PF-LNG2-01** | Phase A moments P95 耗时 | 同 T-large · scale=2 | ≤ 1.x 同 trip **150%** | ☐ |
| **PF-LNG2-02** | 平台模式 Job 成功率 | dogfood ≥7 天 | ≥ **95%** | ☐ |
| **PF-LNG2-03** | moments 导出占比 | 上线 30 天 | ≥ **10%** of longshot exports | ☐ |

---

## 9. 发布闸门（Go / No-Go）

### Phase A 上线

| 闸门 | 要求 |
|------|------|
| **G-A-1** | §3 Phase A 自动化 **全部 ☐→☑** |
| **G-A-2** | §4 T-large + T-small 手测 **全部通过**（H-A-14 已确认） |
| **G-A-3** | §6 NR-LNG2-01～07 **通过** |
| **G-A-4** | PF-LNG2-01 采样通过 |
| **G-A-5** | `studio.longshot2.platforms` 灰度含 `wechat_moments` |

### Phase B 上线

| 闸门 | 要求 |
|------|------|
| **G-B-1** | Phase A 已上线 ≥1 周 · PF-LNG2-02 达标 |
| **G-B-2** | §3 Phase B + §5 手测全通过 |

### Phase C 上线

| 闸门 | 要求 |
|------|------|
| **G-C-1** | §7 + AC-LNG2-06 CLI/stale 通过 |
| **G-C-2** | 文档 SHARING §2.5 · CLI-SPEC 已更新 |

---

## 10. 缺陷分级（验收期间）

| 级别 | 定义 | 处理 |
|------|------|------|
| **S0** | 数据丢失 · 残缺文件残留 · wechat_chat 回归 | **阻塞发布** |
| **S1** | photo 切半 · 错误张数 >9 · P1 在 platform 模式触发 | **阻塞 Phase A/B** |
| **S2** | userHint 缺失 · CTA 未动态 · 水印 i/n 错误 | 修复后发布 |
| **S3** | 文案 · 间距 · coach 偶现 | 可随 patch |

---

## 11. 验收记录模板

```markdown
## Longshot 2.0 验收记录

| 项 | 值 |
|----|-----|
| 日期 | YYYY-MM-DD |
| 版本 / commit | |
| 验收人 | |
| Phase | A / B / C |
| T-large tripId | |
| T-small tripId | |

### 结论
- [ ] Phase A Go
- [ ] Phase B Go
- [ ] Phase C Go

### 未通过 AC
- AC-LNG2-xx：…

### D-LNG2-02 备注
- T-small 实际张数：_
- userHint：_
- 产品确认 sparse 降级：✅
```

---

## 12. 版本记录

| 版本 | 日期 | 说明 |
|------|------|------|
| v0.1.0 | 2026-07-08 | 初稿 |
| v0.1.1 | 2026-07-08 | 对齐 PRD v0.3.2：T-small 8–12 · T-tiny · 缩略条 N/A |
| v0.1.2 | 2026-07-08 | Guizang：AC-LNG2-02w/04/03s · slideCount 校准 |
