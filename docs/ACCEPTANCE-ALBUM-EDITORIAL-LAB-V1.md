# ACCEPTANCE · 画册编辑试验床 V1（AEL）

| 属性 | 内容 |
|------|------|
| **对应 PRD** | [PRD-ALBUM-EDITORIAL-LAB-V1.md](./PRD-ALBUM-EDITORIAL-LAB-V1.md) **v0.2.1**（合同源 §12） |
| **实施** | [IMPLEMENTATION-ALBUM-EDITORIAL-LAB-V1.md](./IMPLEMENTATION-ALBUM-EDITORIAL-LAB-V1.md) |
| **评审** | [ael-album-editorial-lab-v1-review-2026-08-13.md](./acceptance-records/ael-album-editorial-lab-v1-review-2026-08-13.md) · Conditional Go · BLK-AEL-01～08 已回写 |
| **狗粮** | [ael-local-dogfood-GUIDE.md](./acceptance-records/ael-local-dogfood-GUIDE.md) |
| **DOC-STATUS** | **active** |
| **更新日期** | 2026-08-13 |

> **用法**：默认面 `album_editorial_lab.enabled=false`（仓库默认）。带 **〔lab〕** 的用例须本机打开实验旗，且与默认面 **分 job**。  
> **回归尺**：模板 id 序列 + 槽朝向分配（D-AEL-24）。**禁止**像素哈希。  
> **勾选**：✅ 自动化已锁 · ☑ 合同/文档已齐待合码 · ☐ 未做。  
> **正交**：AEL ⊥ 小红书/海报默认（AC-ECC-01 单测不得改红）· ⊥ EDC W3 · ⊥ MSA（`slot_adaptation` 保持 off）。

---

## 0. 编码启动门（M0 · 本文交付）

| ID | 检查项 | 结果 |
|----|--------|------|
| **AC-AEL-W0-01** | PRD v0.2.1 + 七席 Conditional Go · BLK-AEL-01～08 已回写 · 探针参考页产品补记 | ✅ |
| **AC-AEL-W0-02** | 本 ACCEPTANCE + IMPLEMENTATION 已拆（SHD-AEL-04） | ✅ 本文 |
| **AC-AEL-W0-03** | 列车：M0 文档 → **L0 隔离** → L1 SSC → L2 角色 → L3 探针；**禁止**单 PR 塞满 | ✅ IMPL §1 |
| **AC-AEL-W0-04** | L1 合码前合同可读：PROBE 独立 registry · 禁止 import mosaic · 异 AR 才换槽 · cfg 穿线 · 默认环零 judge | ✅ PRD D-AEL-21～28 |
| **AC-AEL-W0-05** | 狗粮三册钉名 + GUIDE | ✅ OQ-01 · GUIDE |

**M0 通过后可 Kickoff L0 合码。** L1 合码仍挡 BLK 合同在代码里可测（见 IMPLEMENTATION §1）。

---

## 1. 冻结常量

| 常量 | 值 | 用途 |
|------|-----|------|
| 成熟库规模 | **28** | `len(CARD_TEMPLATES)` / `_ALL_TEMPLATES` |
| 探针混出 V1 | **4** | `probe-square` / `probe-tall` / `probe-wide` / `probe-hero-mix`；`card-4` 对照不进 `PROBE_TEMPLATES` |
| 探针评测-only | **1** | `probe-triptych`（p18）；可进 registry，禁止进默认 mix allowlist |
| 探针 registry 上限 | **5** | 混出 4 + 评测 1；p33 几何不进 |
| contain 纸色 | **`(245, 245, 243)`** | `DEFAULT_BG`（OQ-03） |
| `group_face_min` | **3** | D-AEL-28 |
| 探针每 spread | **≤1** | D-AEL-13 |
| 探针正文占比 | **≤0.20** | 不含 ABE 封面/封底 |
| L2 1 槽卡占比硬顶 | **GA + 10 个百分点** | OQ-05 |
| SSC 墙钟预算 | **8000 ms** / ≤250 张正文池 | NFR-02；超则只解高风险槽（L1 消费，L0 落键） |
| 狗粮三册 | `demo-d6697c8dca` · `demo-2025` · `demo-49cbe46479` | OQ-01 |
| 盲评 | ≥1 产品 + 1 非作者；打乱 A/B | 与 EDC OQ-05 同口径 |

---

## 2. L0 · 隔离 + cfg 穿线（合码波）

| ID | 期望 | 结果 |
|----|------|------|
| **AC-AEL-01** | 父关 ≡ 现网画册 GA（含 ABE 封面/封底、focal cover、模板序列）。不得少写现网 cover | ☐ |
| **AC-AEL-02** | `enabled=true` 但 `crop/roles/probes` 全 false ≡ GA（正文卡模板序列与关旗相同） | ☐ |
| **AC-AEL-03** | 开 AEL 旗导出小红书 / 公众号 / 海报：模板 id 序列 + 槽朝向分配与关旗一致。禁止像素哈希 | ☐ |
| **AC-AEL-24** | `export_collage_pack` **album** 分支读取 AEL 配置（不再 `_ = cfg`）；xhs/mp 分支不读 AEL 子键 | ☐ |
| **AC-AEL-09** 〔全程〕 | NAS 关闸零 LLM/VL；L0 默认环不 import `travelogue.llm` / `travelogue.ai` | ☐ |
| **AC-AEL-17** 〔全程〕 | 无运行时生成模板的 public API（L0 不新增 generator） | ☐ |
| **AC-AEL-21** 〔全程〕 | 导出路径不把 `slot_adaptation.enabled` 置 true；默认仍 off | ☐ |

**L0 不测**：contain、换槽、角色、探针上场（那些是 L1–L3）。L0 可先落空的 `PROBE_TEMPLATES={}`，并断言 `CARD_TEMPLATES` 不含探针 id。

```powershell
python -m pytest tests/unit/export/test_ael_l0_isolation.py tests/unit/export/test_collage_pack.py tests/unit/export/test_card_renderer.py -q
```

`test_card_renderer.py::test_render_card_covers_every_pixel_no_background_bleed` **必须保持绿**（AC-ECC-01）。

---

## 3. L1 · 保主体裁切增量（28 套 · 默认 off）

合码前提：L0 绿；PROBE 未写入 `_ALL_TEMPLATES`；export **不** import `travelogue.layout_engine.mosaic`。

| ID | 期望 | 结果 |
|----|------|------|
| **AC-AEL-04** | 单人像脸贴上/下缘夹具：不得 cover 切脸；contain 或**异 AR** 同卡换槽 | ☐ |
| **AC-AEL-05** | `max(faceCount,len(faces))=4` 合影进竖槽：不得切掉窗内任一脸；换宽槽或 contain。皆 0 不当 group | ☐ |
| **AC-AEL-06** | 3:2 风景、天际在上 20%：高 crop_risk 不得硬 cover；contain 或换横槽 | ☐ |
| **AC-AEL-07** | 相对 `crop.enabled=false`：卡数与模板 id 序列 **不漂移** | ☐ |
| **AC-AEL-08** | 槽内 contain 底色 = `(245,245,243)`；无页级半幅空白（孤卡仍单卡宽） | ☐ |
| **AC-AEL-23** | `travelogue.export` 不 import `travelogue.layout_engine.mosaic`（静态/importlinter 或单测扫） | ☐ |
| **AC-AEL-25** | `card-9-grid-equal`（槽 AR 全同）：L1 失败走 contain，**不**因换槽改变朝向分配 | ☐ |
| **AC-AEL-18** | 三册盲评 A 维 on≥off；人像砍头红线为零；卡数/模板序列不漂（§1 常量） | ☐ L1 出门 |

朝向错配仍禁止（AC-ECC-04 精神）：不得用 contain 掩盖装错朝向。

```powershell
python -m pytest tests/unit/export/test_ael_l1_ssc.py tests/unit/layout_engine/test_crop_risk_export.py -q
```

---

## 4. L2 · 角色匹配

合码前提：L1 出门门（或至少夹具全绿 + 增量默认仍 off）。

| ID | 期望 | 结果 |
|----|------|------|
| **AC-AEL-10** | 规则单测：竖脸→portrait；宽无人脸→vista；`max(faceCount,len(faces))≥3`→group；皆 0 不当 group | ☐ |
| **AC-AEL-11** | 无 vista/portrait 时 detail 允许主槽（降级合法） | ☐ |
| **AC-AEL-12** | 美食不得升为 vista/主槽；朝向硬门不破；无空槽。**不**验收「FRP 回归」 | ☐ |
| **AC-AEL-22** | `editorialRole` 枚举 ⊆ `{vista,portrait,detail,sequence,unused}`，与 EDC 可翻译。p33 五标签按 PRD §6.1 表映射，不新增枚举 | ☐ |
| **AC-AEL-27** | `PROBE_TEMPLATES` 无 p33 几何 id | ☐ |
| **AC-AEL-19** | 三册盲评：角色反例可指认下降；1 槽卡占比 ≤ GA+10pp | ☐ L2 出门 |

```powershell
python -m pytest tests/unit/export/test_ael_l2_roles.py -q
```

---

## 5. L3 · 探针混出（默认 off）

合码前提：L1+L2 出门；混出 4 套只在 `PROBE_TEMPLATES`；`probe-triptych` 若已写入 registry 则不得出现在默认 mix allowlist。

| ID | 期望 | 结果 |
|----|------|------|
| **AC-AEL-13** | 不在 allowlist / 非 album / `probes.enabled=false` → 永不选用；`CARD_TEMPLATES` 不含探针 id；`AVAILABLE_SLOT_COUNTS` 不因探针改变 | ☐ |
| **AC-AEL-14** | 每 spread 探针卡 ≤1；正文占比 ≤0.20 | ☐ |
| **AC-AEL-15** | 探针 SSC 失败 → 该卡回退成熟模板 | ☐ |
| **AC-AEL-16** | 只关 `probes` 后 L1/L2 行为保留 | ☐ |
| **AC-AEL-20** | 夹具 100%；狗粮**混出**探针卡无新砍头红线，A 维 ≥ 同册成熟卡；未过则 probes 保持 off | ☐ L3 出门 |
| **AC-AEL-26** | 默认 / 示例 `allowlist` 不含 `probe-triptych`；空 allowlist 不选探针；夹具 job 可单独写入该 id | ☐ |

```powershell
python -m pytest tests/unit/export/test_ael_l3_probes.py -q
```

---

## 6. 通行证（不在本表「出门」里验收 EDC）

| 门 | 本表绿了允许 | 本表绿了仍禁止 |
|----|--------------|----------------|
| L1 出门 | Kickoff EDC W1 | 打开 MSA；抄 contain 进 16:9 默认 |
| L2 出门 | Kickoff EDC W2 | 第二套角色枚举 |
| L3 出门 | 画册混 **4** 套探针 | 探针进 16:9 默认库；**自动**升 P-triptych 进混出；**EDC W3** |
| 任何波次 | — | 用画册观感代替 EDC §7 五维门 |

EDC W0 **不挡**。

---

## 7. 明确不验收（本主题）

- 卡内标题 / 胶带 / 微倾 / 异形遮罩
- p33 五槽几何当第 6 套探针
- 16:9 预览、9:16 长图、breath、扉页
- ABE 封面封底 SSC
- 「看起来已经是那 40 页」
- 像素级 PNG 对比
- FRP 封面 demote 在画册路径上「回归」

---

## 8. 变更记录

| 版本 | 日期 | 说明 |
|------|------|------|
| v0.1.1 | 2026-08-13 | 对齐 PRD v0.2.1：混出 4 + triptych 评测-only；p33 角色映射；AC-26/27。 |
| v0.1.0 | 2026-08-13 | Kickoff 拆文。源：PRD v0.2.0 §12 + 七席 BLK/OQ 结案。 |
