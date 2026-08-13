# IMPLEMENTATION · 画册编辑试验床 V1（AEL）

| 属性 | 内容 |
|------|------|
| **文档版本** | **v0.1.2** |
| **对应 PRD** | [PRD-ALBUM-EDITORIAL-LAB-V1.md](./PRD-ALBUM-EDITORIAL-LAB-V1.md) **v0.2.1** |
| **验收** | [ACCEPTANCE-ALBUM-EDITORIAL-LAB-V1.md](./ACCEPTANCE-ALBUM-EDITORIAL-LAB-V1.md) |
| **评审** | [ael-album-editorial-lab-v1-review-2026-08-13.md](./acceptance-records/ael-album-editorial-lab-v1-review-2026-08-13.md) · Conditional Go |
| **狗粮** | [ael-local-dogfood-GUIDE.md](./acceptance-records/ael-local-dogfood-GUIDE.md) · [config-ael-dogfood.example.yaml](./config-ael-dogfood.example.yaml) |
| **DOC-STATUS** | **active** |
| **状态** | **L1 合码中（PR-B）** · L0 已合 master（#66）· 默认 off |
| **更新日期** | 2026-08-13 |

> **定位**：把 AEL PRD v0.2.1 + 七席展开为可执行任务卡。  
> **铁律**：M0 → L0 → L1 → L2 → L3；**禁止**单 PR 塞满；**禁止**把探针写入 `_ALL_TEMPLATES`；**禁止** export import `layout_engine.mosaic`；**禁止**改 xhs/海报默认 `plan_*`。  
> **本刀**：PR-B / L1 SSC（T-AEL-10～17）。T-AEL-18 三册盲评为出门门，不挡合码。  
> **禁止**：探针上场、换模板、改卡数、打开 MSA、改 xhs/海报默认。

---

## 0. 已锁定决策（实施源）

以 PRD §3 / §10 + 评审 §4～§7 为准。实施高频引用：

| ID | 一句话 |
|----|--------|
| **D-AEL-01** | 只动画册；xhs/mp/海报不读探针、不改 contain 默认 |
| **D-AEL-07 / 21** | L1 失败链：异 AR 同卡换槽 → contain；等权宫格不换槽 |
| **D-AEL-11 / 23** | 权威 `crop_solver`；crop_risk 下沉此处；禁止 import `msa_fit` |
| **D-AEL-14 / 22** | `PROBE_TEMPLATES` 独立；禁止写入 `_ALL_TEMPLATES` / `CARD_TEMPLATES` / `AVAILABLE_SLOT_COUNTS` |
| **D-AEL-24** | 回归 = 模板 id 序列 + 槽朝向；禁止像素哈希 |
| **D-AEL-25** | L1 绿→EDC W1；L2 绿→EDC W2；不挡 EDC W0；≠ EDC W3 |
| **D-AEL-26** | L1–L3 默认环零 judge / LLM |
| **D-AEL-27** | L0 把 cfg 穿进 `export_collage_pack` album 分支（现网 `_ = cfg`） |
| **D-AEL-28** | 合影人数 `max(faceCount, len(faces))`；皆 0 不当 group |
| **D-AEL-29** | 现网画册无 FRP；L2 只禁美食升主槽 |
| **D-AEL-30** | registry 最多 5；默认 mix 4；`probe-triptych` 评测-only |
| **D-AEL-31** | p33 标签映射进现有角色表；几何不进 PROBE |

### 0.1 L1 合码挡门（文档已齐 · 代码待落）

| BLK | 要求 | 文档 | 代码 |
|-----|------|------|------|
| **01 / 22** | 探针独立 registry | ✅ PRD/AC | ☐ L0 可先落空 dict |
| **02 / 23** | 禁止 import mosaic | ✅ | ☐ L1 |
| **03 / 24** | 序列回归非像素 | ✅ AC-03 | ☐ L0 |
| **04 / 21** | 异 AR 才换槽 | ✅ AC-25 | ☐ L1 |
| **07 / 27** | cfg 穿线 | ✅ AC-24 | ☐ L0 |
| **08 / 26+28** | 合影口径 + 零 judge | ✅ | ☐ L1 |
| **05 / 29** | FRP 假回归 | ✅ AC-12 | ☐ L2 |
| **06 / 25** | 通行证拆开 | ✅ AC §6 | —（排期） |

---

## 1. PR 切片与退出

| PR | 里程碑 | 任务卡 | 退出（最低） | 风险 |
|----|--------|--------|--------------|------|
| **M0** | 文档 | T-00 | AC-W0-01～05 | 低 |
| **PR-A** | **L0** | T-01～08 | AC-01/02/03/09/17/21/24 | 中（共享入口） |
| **PR-B** | **L1** | T-10～18 | AC-04～08/23/25；出门 AC-18 | 中（contain 观感） |
| **PR-C** | **L2** | T-20～25 | AC-10～12/22；出门 AC-19 | 中（选型软分） |
| **PR-D** | **L3** | T-30～35 | AC-13～16；出门 AC-20 | 狗粮挡 |

**合并规则**：M0 未入库不得开 PR-A；PR-A 未绿不得合 PR-B；PR-B 不得把探针写入成熟库；PR-D 失败只关 `probes`，保留 L1/L2。

---

## 2. 任务卡 · M0（本文交付）

### T-AEL-00 · 文档列车落地

| 项 | 内容 |
|----|------|
| **动作** | PRD v0.2.0 入库；七席纪要；拆 ACCEPTANCE/IMPL；狗粮 GUIDE + example YAML；DOC-STATUS / README 挂链 |
| **验收** | AC-AEL-W0-01～05 |
| **估时** | 0.5d |
| **状态** | ✅ 本文 |

---

## 3. 任务卡 · PR-A（L0 隔离）· 下一刀合码

**本波明确不做**：`solve_slot_focal` 接线、contain 绘槽、角色规则、探针几何、Studio 面板文案、改 `plan_cards` 打分、改 ABE。

### T-AEL-01 · 配置壳 `AlbumEditorialLabConfig`

| 项 | 内容 |
|----|------|
| **动作** | 新建 `travelogue/config/album_editorial.py`：dataclass 嵌套 `enabled` / `crop` / `roles` / `probes`，字段对齐 PRD §10.1；另加 `crop.max_solve_ms: 8000`（NFR-02，L1 才消费） |
| **解析** | `config/loader.py` + `AppConfig.album_editorial_lab`；未知键 **fail-loud**；父 `enabled=false` ⇒ 子项无效（effective crop/roles/probes 皆 false） |
| **默认** | 全 false；`face_hard_gate=true` 不可从配置关成 false（读入后强制 true，或未知键式拒绝 `false`） |
| **样例** | `docs/config-ael-dogfood.example.yaml`（已有草稿）；合码时 `config.yaml.example` 加注释块，**不要**把 enabled 写成 true |
| **验收** | 解析往返；父 OFF → effective 全关；`face_hard_gate: false` 被拒绝或强制 true |
| **估时** | 0.5d |

### T-AEL-02 · `cfg` 穿进 collage_pack（D-AEL-27）

| 项 | 内容 |
|----|------|
| **动作** | `export_collage_pack` 停止 `_ = cfg`。`longshot.py` 调用处传入 `get_config()`（或既有 cfg）。**仅** `platform==album_spread` 读取 `album_editorial_lab` |
| **验收** | AC-AEL-24；xhs 调用不依赖 AEL 子键 |
| **估时** | 0.5d |
| **锚点** | `travelogue/export/collage_pack.py` · `travelogue/export/longshot.py` |

### T-AEL-03 · effective helper

| 项 | 内容 |
|----|------|
| **动作** | `effective_ael(cfg, platform) -> EffectiveAel`：非 album → 全关；album + 父关 → 全关；父开则返回子开关。供 L1+ 使用，L0 只断言「全关时 plan/render 与今日相同」 |
| **验收** | 单测四组合：非 album / 父关 / 父开子关 / 父开 crop 开（L0 对最后一种 **仍不得改变选型**，因 L1 未接线） |
| **估时** | 0.3d |

### T-AEL-04 · 空 `PROBE_TEMPLATES` 占位（BLK-01 形状）

| 项 | 内容 |
|----|------|
| **动作** | `card_templates.py` 增加 `PROBE_TEMPLATES: dict[str, CardTemplate] = {}`。**禁止**把任何现网 28 套或未来探针放进 `_ALL_TEMPLATES` 以外的合并函数，除非调用方显式传入 album+probes.enabled |
| **验收** | `len(_ALL_TEMPLATES)==28`；`CARD_TEMPLATES.keys().isdisjoint(PROBE_TEMPLATES)`；`AVAILABLE_SLOT_COUNTS` 与现网一致 |
| **估时** | 0.2d |

### T-AEL-05 · 诊断骨架（可选但建议 L0 做）

| 项 | 内容 |
|----|------|
| **动作** | album 导出 job 旁路写 `*.ael.json`（或 result.diagnostics）：`aelEnabled` / 子开关 / `templateIds[]` / `probeCount=0`。关旗可不写文件 |
| **验收** | 关旗无新文件或字段全关；开旗子关时 templateIds 与 GA 相同 |
| **估时** | 0.3d |

### T-AEL-06 · L0 隔离单测

| 项 | 内容 |
|----|------|
| **动作** | 新建 `tests/unit/export/test_ael_l0_isolation.py` |
| **覆盖** | AC-01/02/03/24；用现有 collage fixture 或最小 trip；比较 **模板 id 列表 + 每槽 role/朝向**，禁止 hash PNG |
| **平台** | 至少 `xiaohongshu` + `album_spread`；公众号可与 xhs 同源抽一条 |
| **估时** | 0.8d |

### T-AEL-07 · ECC 回归不得改红

| 项 | 内容 |
|----|------|
| **动作** | PR-A 必跑：`test_card_renderer.py`（含铺满底色）· `test_card_grouper.py` · `test_collage_pack.py` · `test_card_bookends.py` |
| **验收** | 全绿；AC-ECC-01 单测仍断言 `fit==cover` 且无大块底色 |
| **估时** | 含在 T-06 |

### T-AEL-08 · 用户面零暴露

| 项 | 内容 |
|----|------|
| **动作** | 确认 Studio 导出面板 **不**出现 AEL / 实验旗 / 算法缩写。本波不改 templates/studio |
| **验收** | 静态：无新增 copy 键；手测导出仍一键 |
| **估时** | 0.1d |

**L0 退出**：AC-AEL-01/02/03/09/17/21/24 单测绿；ECC 回归绿。

---

## 4. 任务卡 · PR-B（L1 SSC）大纲

L0 未绿不得开工。详细几何以实现时补卡，此处钉挂点，避免两套求解器。

| ID | 动作 | 验收 |
|----|------|------|
| **T-AEL-10** | 把 `msa_fit.crop_risk_for_pair` / `aspect_mismatch` / `_focal_near_edge` **下沉**到 `crop_solver.py`（或 `layout_contract/crop_risk.py`）。`msa_fit` 改为 re-export 以保持 MSA 行为。export **只** import `crop_solver` | AC-23 |
| **T-AEL-11** | `card_renderer` 支持槽级 `fit=contain`：letterbox 进槽，底色 `DEFAULT_BG`；diag 可 per-slot。xhs 调用仍全 cover | AC-08；ECC 铺满单测不红 |
| **T-AEL-12** | album 在 `assign_photos_to_slots` 之后跑 SSC：`solve_slot_focal`；人脸 clipped → contain 或异 AR 换槽；无 face 时用 crop_risk 阈值 contain | AC-04/06 |
| **T-AEL-13** | 异 AR 同卡匈牙利/既有 rebind；等权宫格跳过换槽（AC-25） | AC-07/25 |
| **T-AEL-14** | 合影保护框 = faces 并集；人数口径 D-AEL-28 | AC-05 |
| **T-AEL-15** | `max_solve_ms`：超时则仅高 crop_risk 槽求解，其余 focal cover | NFR-02 |
| **T-AEL-16** | 默认环 **不**调用 mosaic_judge | AC-09/D-26 |
| **T-AEL-17** | 夹具 + `test_ael_l1_ssc.py`；断言 L1 不改模板序列 | AC-04～07 |
| **T-AEL-18** | 三册盲评 GUIDE；出门 AC-18。contain 多时文案见 GUIDE「白边」 | AC-18 |

**L1 不做**：换模板、改卡数、探针上场、改 ABE、打开 MSA。

---

## 5. 任务卡 · PR-C（L2 角色）大纲

| ID | 动作 | 验收 |
|----|------|------|
| **T-AEL-20** | 共享纯函数 `editorial_role_for_asset(asset) -> (role, group)`，枚举与 EDC 相同；放 `layout_contract` 或 `curation` 浅模块，供日后 EDC W2 import。p33 五标签按 PRD §6.1 表翻译，不新增 token | AC-10/22 |
| **T-AEL-21** | `plan_cards` 增加可选 `assets_by_path`（默认 None）。xhs **不传**。album L2 用角色软分微调**同槽数**成熟候选 | SHD-01 · AC-07 精神：L2 允许记账卡数 |
| **T-AEL-22** | 软聚类：同 scene 尽量同卡；**不许空槽**；切不开则忽略 | N-AEL-07 |
| **T-AEL-23** | 美食：`subjectClass=food` 不得配主槽/vista；不确定不降级 | AC-12 |
| **T-AEL-24** | 1 槽卡占比 ≤ GA+10pp 单测 | OQ-05 |
| **T-AEL-25** | 三册盲评出门 AC-19 | AC-19 |
| **T-AEL-26** | 单测：p33 标签 → 现有枚举可翻译；断言无 `small` / `main-photo` 键 | AC-22/27 |

---

## 6. 任务卡 · PR-D（L3 探针）大纲

| ID | 动作 | 验收 |
|----|------|------|
| **T-AEL-30** | **4** 套混出矩形探针写入 **`PROBE_TEMPLATES` 仅**：`probe-square`（p22 2×2 1:1）· `probe-tall`（p21 两列铺满）· `probe-wide`（p08 16:9 + 余高填满）· `probe-hero-mix`（p12 大方+两竖）。md 可放 `docs/templates/card-aspect-3x4/probes/` | AC-13 |
| **T-AEL-30b** | 第 5 套 `probe-triptych`（p18 三列铺满）写入同一 registry；默认 / 示例 `allowlist` **不得**含该 id；夹具可单独写入 | AC-26 |
| **T-AEL-31** | L3 环：成熟卡 SSC 通过且本 spread 无探针 → 尝试 1 张（仅 allowlist 内）；失败回退 | AC-14/15 |
| **T-AEL-32** | `allowlist` 空 ⇒ 即使 `probes.enabled` 也不选 | AC-13 |
| **T-AEL-33** | 关 probes 保留 L1/L2 | AC-16 |
| **T-AEL-34** | `AVAILABLE_SLOT_COUNTS` 不读探针 | AC-13 |
| **T-AEL-35** | 夹具 100% + 三册出门（混出 4）；失败则 probes 长期 off。triptych 夹具单独跑，不过门不升混出 | AC-20/26 |
| **T-AEL-36** | 断言无 p33 几何 id | AC-27 |

---

## 7. 明确不实施（本主题 V1）

- 运行时生成模板 / 异形遮罩 / 胶带 / 卡内标题
- 改 16:9 / 长图 / LVP / breath / 扉页
- 打开 `slot_adaptation`
- Studio 导出面板算法开关
- 对 ABE 封面封底跑 SSC
- 第二套 `editorialRole` 枚举
- p33 五槽几何进 `PROBE_TEMPLATES`
- 把 `probe-triptych` 写进仓库默认 mix allowlist
- 把 `docs/templates/card-aspect-3x4/*.md` 当运行时 glob 源（现网是 Python 编译镜像；保持）

---

## 8. 建议 pytest 文件（合码时新建）

| 文件 | 波次 |
|------|------|
| `tests/unit/export/test_ael_l0_isolation.py` | L0 |
| `tests/unit/config/test_album_editorial_config.py` | L0 |
| `tests/unit/export/test_ael_l1_ssc.py` | L1 |
| `tests/unit/layout_engine/test_crop_risk_reexport.py` | L1（msa_fit 仍绿） |
| `tests/unit/export/test_ael_l2_roles.py` | L2 |
| `tests/unit/export/test_ael_l3_probes.py` | L3 |

---

## 9. 变更记录

| 版本 | 日期 | 说明 |
|------|------|------|
| v0.1.2 | 2026-08-13 | PR-B / L1：crop_risk 下沉 crop_solver；album SSC；msa_fit re-export。T-18 盲评仍出门。 |
| v0.1.1 | 2026-08-13 | 对齐 PRD v0.2.1：T-AEL-26/30b/36；混出 4 + triptych 评测-only。 |
| v0.1.0 | 2026-08-13 | M0 拆文。下一刀仅 PR-A / L0。 |
