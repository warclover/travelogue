# Travelogue · 封面多样式产品需求文档（PRD · Cover Styles V6）

| 属性 | 内容 |
|------|------|
| **产品代号** | Travelogue |
| **文档版本** | v1.3.0 |
| **状态** | **M1+M2 代码门禁通过**（2026-07-10）· 有条件通过补丁已合入 · 视觉/E2E 走查后可封板 |
| **主题代号** | 「封面多样式 V6」— 以 5 套 Opening 皮肤 **替代** V5 三款；引入 **Cover Style Engine**、样式↔图片联合策展与使用说明（**不含**封底改版与完整管理后台） |
| **前置条件** | [PRD-COVER-STYLES-V5.md](./PRD-COVER-STYLES-V5.md) 已上线；[PRD-COVER-OPTIMIZATION-V4.md](./PRD-COVER-OPTIMIZATION-V4.md)；封面选图 v2（`cover_scoring_v2` / `pick_cover_asset_id`）；`cover-opening.hbs` / `cover-closing.hbs` 可用 |
| **关联文档** | [cover-styles-v6-five-concepts-wireframe.html](./wireframes/cover-styles-v6-five-concepts-wireframe.html)、[cover-styles-v6-hi-fi-adefg.html](./wireframes/cover-styles-v6-hi-fi-adefg.html)、[cover-selection-plan.md](./cover-selection-plan.md)、`schemas/trip.schema.json`；**封底 / 引擎收口** → [PRD-BOOKENDS-ENGINE-V1.md](./PRD-BOOKENDS-ENGINE-V1.md)（兑现原 `PRD-COVER-CLOSING-V1`，见 §8.3 / 附录 F） |
| **评审来源** | 2026-07-10 视觉评审 + Engine 讨论；**同日跨职能评审**（产品 / 架构 / UI·视觉 / 用户体验）→ 有条件通过；补丁见 v1.3.0 |
| **验收** | [ACCEPTANCE-COVER-STYLES-V6.md](./ACCEPTANCE-COVER-STYLES-V6.md)（对齐 §10 + M1/M2；视觉/E2E 待补齐后封板） |
| **实施清单** | [IMPLEMENTATION-COVER-STYLES-V6.md](./IMPLEMENTATION-COVER-STYLES-V6.md)（含 curate 挂点与锁定字段） |
| **更新日期** | 2026-07-10 |

> **定位**
>
> V5 解决了「三本相册长得一样」的同质化，但三款皮肤（`card-br` / `split-mat` / `magazine-head`）在艺术感与画册气质上不足：书名卡偏 UI、分屏偏商务模板、杂志顶题偏网页头图。V6 以 **5 套经高保真评审的封面皮肤** 全面替代 V5 枚举，并补齐 V5 刻意解耦留下的缺口——**样式与封面图互不感知**，导致「好图配错版式」。
>
> **产品共识（十一条铁律 · v1.3 拍板版）**
>
> 1. **一块 DOM，多套 CSS** — 仍不拆 `cover-opening.hbs`；用 `data-cover-opening` 分岔。  
> 2. **五款替代三款** — 新建游记 **只** 从 V6 五款分配；V5 三款退出创建池与 Studio 主选择器（见 §3.1 · **已拍板**）。  
> 3. **联合写入后锁定** — `meta.coverOpeningStyle` 与封面图在首次成功联合选型后锁定；`render` / 无 `force` 的 `curate` **不得** 重写（见 §3.5）。  
> 4. **样式 ↔ 图片联合选型** — 废除「纯 tripId 哈希均匀分配」作为主路径；改为候选图 × 适图画像联合打分（见 §6）。  
> 5. **规则为主，LLM 为辅** — 联合选型以规则 + 现有视觉特征为主；LLM/MLLM 仅可选平局裁判（见 §6.4）。  
> 6. **使用说明纳入本 PRD（P0）** — 机器 profile + Studio 一句话；与五款/联合选型同交付（见 §7、§8.1）。  
> 7. **P0 仅 Web / auto** — Mobile 封面维持现网；Studio **须明示** Web/Mobile 不同步。  
> 8. **窄屏回落** — Web &lt;1024px 时 **仅 CSS 呈现** 回落 `veil-footer`；`data-cover-opening` **保持** trip 原值（见 D-CSV6-24）。  
> 9. **封底改版不在本 PRD** — 现网 `cover-closing` **不回归即可**；精修与气质软配对另立 Closing PRD（见 §8.3 · **已拍板**）。  
> 10. **设计 token 以 §4.7 为真相源** — 与高保真冲突时先更新 token 表再实现；禁止散落硬编码。  
> 11. **Cover Style Engine** — Registry 为样式真相源；**样式管理**本 PRD 只做到启停库函数与配置，完整 Admin/实验室 UI 不作为本 PRD P0 主题（见 §5、§8.2）。

> **跨职能评审结论（2026-07-10）**：产品 / 架构 / UI·视觉 / 用户体验四席均为 **有条件通过**。v1.3.0 已合入阻塞项补丁；实施按 **M1 → M2**（§9）推进。纪要摘要见附录 G。

---

## 1. 背景与问题

### 1.1 现状摘要（V5 上线后）

| 维度 | 现状 | 用户 / 设计感知 |
|------|------|-----------------|
| **Opening 皮肤** | `card-br` / `split-mat` / `magazine-head` | 差异有，但艺术感弱，不如普通画册封面 |
| **样式分配** | `tripId` SHA256 `% 3`，1:1:1 | 「随机」但与内容无关 |
| **封面选图** | `pick_cover_asset_id` v2 logit（画幅/清晰/构图/人像/审美…） | 质量高，但 **不知道** 将用于哪款皮肤 |
| **样式↔图片** | **零耦合**（V5 铁律 #6 刻意为之） | 高保真好看依赖人工配对；产品无法复现 |
| **封底** | 单一 `cover-closing` + 独立选图 | 与 opening 多样式不对称 |
| **使用说明** | 无机器可读适图规则；Studio 仅有排版三选一标签 | 换版式时无「这张图适不适合」引导 |

### 1.2 问题陈述（P-CSV6-*）

| ID | 问题 | 影响 |
|----|------|------|
| **P-CSV6-01** | V5 三款视觉粗糙、感染力不足 | 首屏无法支撑「画册级」品牌承诺 |
| **P-CSV6-02** | 样式与封面图独立选型 | 好图配错版式；切带切脸、圆窗裁主体、巨字压关键信息 |
| **P-CSV6-03** | 纯哈希分配与内容无关 | 无法按构图/气质选最合适皮肤 |
| **P-CSV6-04** | 无适图画像 / 使用说明 | 策展无法自动化；用户换版式易踩坑 |
| **P-CSV6-05** | 封底与 opening 气质可能不对称 | **承认但本 PRD 不实施**；另立 Closing PRD（见 §8.3） |
| **P-CSV6-06** | 若保留 V5 三款 + 新增五款 = 8 枚举 | Studio 选择过载；维护与测试成本倍增 |

### 1.3 核心判断

> **用 5 款经评审的高保真皮肤整体替代 V5 三款**，比「叠加保留」更干净。  
> **联合选型（图 × 样式）** 是 V6 相对 V5 的真正产品跃迁；仅换皮肤而不匹配图片，仍会重复「人工高保真好看、自动分配翻车」。  
> **LLM 不是必要条件**；先把适图画像与规则联合打分做对，再可选接入短名单平局。  
> **本 PRD 主角是 Opening**；使用说明与引擎启停契约同交付；封底改版与完整样式管理后台 **刻意拆出**，避免一次范围爆炸（见 §8）。

### 1.4 设计评审收敛（2026-07-10）

| 开放项 | 决议 |
|--------|------|
| **O-V6-01** 概念池 | 批次一 A–E + 批次二 F–H 共 8 款线框 |
| **O-V6-02** 入选高保真 | **A / D / E / F / G**（否决 B 展厅、C 墨脊、H 斜切进入本轮实现） |
| **O-V6-03** E 切带位置 | 题带中线由约 61–62% **下移至 ≈ 72%**（给上半摄影更多呼吸） |
| **O-V6-04** 设计方向 | 赞同高保真视觉；进入 PRD 与联合策展设计 |
| **O-V6-05** 使用说明 / 联合选型 | **纳入本 PRD P0** |
| **O-V6-06** 是否保留 V5 三款 | **已拍板：不保留为创建选项**（R-V6-01） |
| **O-V6-07** Cover Style Engine | **赞同**：Registry + 契约；P0 先内核接口（见 §5）；完整 Admin 非本 PRD P0 主题 |
| **O-V6-08** 封底是否纳入本 PRD | **已拍板：不纳入实施**（R-V6-06）；仅边界 + Closing PRD |
| **O-V6-09** 样式管理后台 | **引擎启停契约纳入**；管理后台 / 实验室完整 UI **不作为本 PRD P0 主题**（见 §8.2） |
| **O-V6-10** 跨职能评审 | **有条件通过** → v1.3 补丁后按 M1/M2 开工 |

---

## 2. 目标与非目标

### 2.1 产品目标

| ID | 目标 | 验收口径 |
|----|------|----------|
| **G-CSV6-01** | 五套 Web 封面皮肤可用 | `veil-footer` / `folio-overlap` / `band-cut` / `cameo-aperture` / `type-monument` 均可渲染 |
| **G-CSV6-02** | 新建只分配 V6 五款 | `create_trip` / 联合策展写入的枚举 ∈ V6 五值 |
| **G-CSV6-03** | V5 三款退出主路径 | Studio「排版」不再列出 V5；创建哈希/联合选型不再产出 V5 |
| **G-CSV6-04** | 样式↔图片联合选型 | curate 后 `(coverOpeningStyle, coverAssetId)` 为联合分最优对（或文档化 fallback） |
| **G-CSV6-05** | 分配稳定 | 同一 trip 多次 `render` 样式与封面图不变（除非显式重配） |
| **G-CSV6-06** | 一屏完整 | 各样式 title/hook 截断后无封面纵向溢出；`100dvh` |
| **G-CSV6-07** | V4 能力保留 | Icon Dock、书名可编辑、Share 一致、Web 封面隐藏 trip-meta |
| **G-CSV6-08** | 老 trip 可渲染 | V5 枚举经 **兼容映射** 仍可打开（见 §3.1） |
| **G-CSV6-09** | 使用说明可达（P0） | 机器 profiles 存在；Studio 每款有一句话说明（§7） |
| **G-CSV6-10** | 封底不回归 | 现网 `cover-closing` 在 Web+epilogue 条件下仍可用；**本 PRD 不验收封底视觉改版** |
| **G-CSV6-11** | 可观测 | telemetry：样式分配来源（joint / fallback / manual / legacy-map）、联合分、五款分布 |
| **G-CSV6-12** | Cover Style Engine 可扩展 | 新增/停用样式只需注册表 + pack + profile；create / Studio / joint **不** 硬编码样式列表 |
| **G-CSV6-13** | 产品成功指标（上线后） | 见 §2.3；纳入发布后看板，非阻塞 M1 代码合并 |

### 2.2 非目标

- **不** 在 P0 实现 Mobile 五套皮肤（P2）
- **不** 以纯 LLM 作为样式/封面主选型器
- **不** 在本 PRD 实施封底精修、五分支封底、或 opening↔closing 气质软配对（→ Closing PRD，§8.3）
- **不** 为 5 款 opening 各做一套像素级镜像封底
- **不** 将完整「样式管理后台 / 封面实验室产品」作为本 PRD P0 交付（引擎库函数与配置覆盖仍做，§8.2）
- **不** 改动 Icon Dock / 任务舱业务逻辑
- **不** 要求五款共用同一 panel 几何（各样式独立 AC）
- **不** 在 P0 强制用户每次手动选样式（自动联合选型为默认）
- **不** 在 P0 做可视化拖拽「封面设计器」或独立微服务化的封面后台
- **不** 允许运营在无工程评审的情况下仅靠后台「发明」新布局几何

### 2.3 产品成功指标（上线后观测 · G-CSV6-13）

| 指标 | 口径（提案） | 告警 / 健康 |
|------|--------------|-------------|
| 人工改版式率 | 联合选型后 14 日内 Studio 修改 `coverOpeningStyle` 的 trip 占比 | 过高 → 检查 blurb/配对 |
| 人工改封面图率 | 联合选型后 7 日内改 `coverAssetId` 占比 | 过高 → 检查适图规则 |
| 五款分配分布 | 新建 trip 各 style 占比 | 单款 &gt;60% 持续 7 日 → 分布塌缩告警 |
| legacy 映射命中 | 渲染期 `legacy-map` 次数 | 仅观测，不作为失败 |
| hash-fallback 率 | `source=hash-fallback` 占比 | 过高 → 联合模块故障 |

---

## 3. 已拍板决策（D-CSV6）

### 3.1 替代策略：五款取代三款（**已拍板 · R-V6-01**）

| ID | 决策 | 说明 |
|----|------|------|
| **D-CSV6-01** | **新建游记只使用 V6 五款** | 创建池与 Studio 主选择器枚举 = 五值 |
| **D-CSV6-02** | **V5 三款退出产品主路径** | 不再作为「可新选」样式；文档标记 Deprecated |
| **D-CSV6-03** | **兼容映射（渲染期）** | 读到 V5 值时映射为 V6 后渲染（**默认不改写** trip.json；P1 可显式升级写回） |
| **D-CSV6-04** | **缺省 / 非法值** | → `veil-footer` |
| **D-CSV6-05** | **V5 CSS 退役节奏** | P0 正式路径走映射后的 V6；P2 删除 V5 CSS |
| **D-CSV6-06** | **多对一映射的产品接受** | `split-mat` 与 `magazine-head` 均 → `folio-overlap`；老用户沟通须说明「两款编辑向版式现统一为对页叠印」（§7.4） |

**兼容映射表（D-CSV6-03）**

| 遗留值（V5） | 映射至（V6） | 理由 |
|--------------|--------------|------|
| `card-br` | `veil-footer` | 同为全幅摄影 + 底缘文案；去掉 UI 卡 |
| `split-mat` | `folio-overlap` | 同为「图文分区」编辑感；避免继续商务棕栏 |
| `magazine-head` | `folio-overlap` | 同属编辑部气质；顶栏方案被对页叠印取代 |
| （无匹配） | `veil-footer` | 安全默认 |

### 3.2 数据与分配

| ID | 决策 | 说明 |
|----|------|------|
| **D-CSV6-10** | 字段路径仍为 `meta.coverOpeningStyle` | 见 §4.1 |
| **D-CSV6-11** | **create 占位 = `veil-footer`**（**已拍板 · R-V6-03**） | 首次 curate 前预览标注「临时预览」；curate 后可被联合结果替换 |
| **D-CSV6-12** | **禁止** 无种子 `random()` | 平局用 `tripId` 哈希 |
| **D-CSV6-13** | 无 force 的 curate / render **不** 重算已锁定封面 | 见 §3.5 |
| **D-CSV6-14** | Studio 手动换版式（**P0 最小交互**） | **主按钮 = 按新样式重荐封面图**；次要 = 保持当前图；选「保持」且 fit 低于阈值时显示一句非阻断灰字（完整黄条流仍可 P1） |
| **D-CSV6-15** | **Schema 兼容策略（已拍板）** | `trip.schema.json` 的 `coverOpeningStyle` **enum = V6 五值 ∪ V5 三值**（V5 标 deprecated）；**写入路径**（create / joint / Studio patch）**只允许** `list_assignable_styles()`；resolve 负责映射呈现 |
| **D-CSV6-16** | 删除创建时哈希主路径 | `create_trip` **不再** `assign_cover_opening_style` 三选一哈希；改写占位 + 等 curate |

**推荐写入时序（P0）**

```
create_trip
  → meta.coverOpeningStyle = "veil-footer"   # 占位；Studio 标「临时预览」
  → curation.coverJointLocked = false
run_curate
  → 若 coverJointLocked：跳过联合重写（除非 force）
  → 否则 pick_cover_style_and_asset + apply_joint_pick
       → 写 coverAssetId / coverByLayout.web + coverOpeningStyle
       → coverJointLocked = true
       → coverStyleExplain = {...}
render / assemble
  → resolve_style_id（含 legacy_map）→ data-cover-opening
  → 注意：DOM 用 resolve 后 id；trip.json 可仍为 V5（不静默写回）
```

### 3.3 渲染与 DOM

| ID | 决策 | 说明 |
|----|------|------|
| **D-CSV6-20** | `data-cover-opening` 绑在 section | 值为 **resolve 后** 的 id |
| **D-CSV6-21** | 块结构不变 | `cover-hero` + panel |
| **D-CSV6-22** | `web` / `auto` 应用五套；`mobile` 忽略 | Studio 脚注明示不同步 |
| **D-CSV6-23** | Share / draft / longshot 同源 | |
| **D-CSV6-24** | 窄屏回落 | `@media (max-width: 1023px)`：**仅 CSS 呈现**等同 `veil-footer`；**不改** `data-cover-opening` 属性；Studio 预览 **同一断点** |
| **D-CSV6-25** | Web 封面不展示 trip-meta | |
| **D-CSV6-26** | title/hook 默认 ≤2 行；巨字 ≤3 行 | **已拍板 · R-V6-04** |
| **D-CSV6-27** | 书名字体（**已拍板 · R-V6-08**） | Opening 书名优先 **衬线栈**：`"Noto Serif SC", "Songti SC", "STSong", Georgia, serif`；UI/place/hook 可用无衬线；缺字回退雅黑栈 |
| **D-CSV6-28** | Icon Dock | 右上安全区建议 ≥56×56；`z-index` 高于 fog/panel 文案；五款均须可点（AC 扩至全款） |
| **D-CSV6-29** | accent 选用 | 深底文案用 `#7cb89a`；浅底/纸白用 `#3d6b5a` |

### 3.4 E 切带位置（已评审）

| ID | 决策 | 说明 |
|----|------|------|
| **D-CSV6-30** | 题带中线 **≈ 72%** | AC：70%–74% |
| **D-CSV6-31** | 切带垂直安全区 | 惩罚 focal/人脸 ∈ **[0.66, 0.78]** |

### 3.5 锁定与 curate 集成（**评审阻塞项 · 已拍板**）

| ID | 决策 | 说明 |
|----|------|------|
| **D-CSV6-50** | 锁字段 | `curation.coverJointLocked: bool`（名称实施可微调，须单一真相） |
| **D-CSV6-51** | 置锁时机 | `apply_joint_pick` 成功后 `true`；manual「重荐图」成功后保持 `true` |
| **D-CSV6-52** | 清锁 / force | 仅：`force_recover`、用户确认「重新精选封面」、或显式 API `repick_cover_for_style` |
| **D-CSV6-53** | 与现网关系 | **包装** `sync_trip_covers`：web 路径改走 joint；mobile 仍 `pick_cover_asset_id`；**禁止** 无条件每次 curate 覆盖已锁 web 封面 |
| **D-CSV6-54** | manual 切换 | 写 `coverStyleExplain.source = "manual"`；若选重荐图则只在该 style 下重选 asset 并保持锁 |
| **D-CSV6-55** | 低分仍配对 | 若最优 `joint` &lt; 配置阈值：仍写入最优对 + explain 标记 `low_confidence=true`；telemetry 计数；**不** 静默改回哈希（除非联合模块关闭） |

**集成伪代码（实施必须对齐）**

```text
def sync_trip_covers(trip, *, force=False):
    # mobile: 现有 pick_cover_asset_id（可保留每次刷新策略或独立锁，P0 不强制与 web 同锁）
    sync_mobile_cover(trip)

    if trip.curation.coverJointLocked and not force:
        return  # web style+cover 不动

    if joint_enabled:
        explain = pick_cover_style_and_asset(trip, layout="web")
        apply_joint_pick(trip, explain, lock=True)
    else:
        explain = hash_fallback_pick(trip)
        apply_joint_pick(trip, explain, lock=True)
```

---

## 4. 封面样式目录（V6 五款）

### 4.1 枚举定义

| 值 | 显示名 | 概念代号 | 气质 | 状态 |
|----|--------|----------|------|------|
| `veil-footer` | 雾底题签 | A | 电影感 · 沉浸 | **P0 · 新默认基线** |
| `folio-overlap` | 对页叠印 | D | 编辑部 · 字咬图 | **P0** |
| `band-cut` | 切带题名 | E | 强识别 · 胶片条 | **P0** |
| `cameo-aperture` | 圆窗肖像 | F | 纪念章 · 圆窗 | **P0** |
| `type-monument` | 巨字碑 | G | 海报 · 字压一切 | **P0** |

```json
"meta": {
  "coverOpeningStyle": "veil-footer"
}
```

**Schema（P0 须更新 · D-CSV6-15）**

```json
"coverOpeningStyle": {
  "type": "string",
  "enum": [
    "veil-footer",
    "folio-overlap",
    "band-cut",
    "cameo-aperture",
    "type-monument",
    "card-br",
    "split-mat",
    "magazine-head"
  ],
  "description": "Web cover opening skin. V6 assignable: first five. Last three deprecated (legacy trips only; resolve maps to V6)."
}
```

> **写入层**（create / `apply_joint_pick` / Studio patch）校验 ∈ `list_assignable_styles()`。  
> **resolve 层**接受 V5 三值并映射。勿在 schema 中删除 V5，否则存量 validate 失败。

Studio 选择器文案区分 A/G：雾底 =「沉浸题签」；巨字 =「海报巨字」（降低列表混淆）。

### 4.2 `veil-footer` · 雾底题签（A · 默认基线）

| 属性 | 规格 |
|------|------|
| **构图** | `cover-hero` 全幅；底部软雾渐变（非实心卡）；panel 底缘左对齐 |
| **雾高** | 约 **48%** 视口高，上缘软过渡至透明 |
| **文案** | place（accent 小字距）→ title（衬线）→ 细线 → hook |
| **panel** | `max-width: min(680px, 74%)`；无 box-shadow 浮层、无左侧色条 |
| **一屏** | `100dvh` |
| **替代关系** | 取代 `card-br` 的产品角色 |

### 4.3 `folio-overlap` · 对页叠印（D）

| 属性 | 规格 |
|------|------|
| **构图** | 左 **≈11%** 纸白边；摄影占右侧；大标题从纸白压入画面 |
| **place** | 纸白边内竖排跑题 |
| **title** | 超大衬线，可 2 行；主体落在纸白侧保证对比 |
| **托底** | panel 纸白→透明水平渐隐 |
| **accent** | 短粗线（品牌绿）分隔 title / hook |
| **替代关系** | 承接原 `magazine-head` / 部分 `split-mat` 的编辑气质 |

### 4.4 `band-cut` · 切带题名（E）

| 属性 | 规格 |
|------|------|
| **构图** | 全幅摄影；水平题带横切 |
| **题带中线** | **≈ 72%** 视口高（D-CSV6-30） |
| **题带结构** | 三栏：`place` \| `title` \| `hook` |
| **变体** | E1 纸白半透明带（默认）；E2 墨色带（深图/高对比场景，可由 token 或自动亮度切换，P1） |
| **无 hook** | 中栏 title 居中，左右可空或仅 place |
| **风险** | 切到人脸/主体 → 靠联合选型安全区（D-CSV6-31） |

### 4.5 `cameo-aperture` · 圆窗肖像（F）

| 属性 | 规格 |
|------|------|
| **构图** | 石青径向底；居中圆形取景窗；窗下徽章式题名 |
| **圆窗** | 直径 ≈ **48vh**；金环双描边 |
| **文案** | 居中：place → title → hook |
| **裁切** | `border-radius: 50%` + `object-fit: cover`；强依赖 focal 居中 |
| **风险** | 超宽全景、主体贴边 → 适图规则重罚 |

### 4.6 `type-monument` · 巨字碑（G）

| 属性 | 规格 |
|------|------|
| **构图** | 全幅摄影 + 暗罩；字为视觉主体 |
| **结构** | 上 place / 中巨字 title / 下 hook（flex 撑满） |
| **字号** | `clamp(3.4rem, 7.5vw, 5.4rem)` 量级 |
| **title 行数** | **最多 3 行**（D-CSV6-26） |
| **暗罩** | 保证浅色图上白字对比 ≥ AC |
| **风险** | 过长书名折行难看 → 适图/文案侧偏好短标题或联合分降权 |

### 4.7 设计 Token（**设计签字版 · 以高保真收编**）

> 真相源：本节 + [cover-styles-v6-hi-fi-adefg.html](./wireframes/cover-styles-v6-hi-fi-adefg.html)。冲突时先改本节再改 CSS。

| Token | 用途 | 值 |
|-------|------|-----|
| `--cover-font-title` | 书名衬线栈 | `"Noto Serif SC", "Songti SC", "STSong", Georgia, serif` |
| `--cover-veil-fog` | 雾渐变（底→顶） | `rgba(8,7,6,.92) 0%` → `.62 38%` → `.18 72%` → `0 100%` |
| `--cover-veil-fog-height` | 雾区高度 | `48%` |
| `--cover-veil-panel-max` | 题签最大宽 | `min(680px, 74%)` |
| `--cover-veil-title-size` | A 书名 | `clamp(2rem, 3.8vw, 2.75rem)` / weight 600 |
| `--cover-veil-place-size` | place | `11px` / tracking `0.32em` / `#7cb89a` |
| `--cover-veil-hook` | hook | `0.95rem` / `rgba(245,243,240,.78)` |
| `--cover-folio-margin` | 纸白边 | `11%` |
| `--cover-folio-paper` | 纸白 | `#f7f5f2` |
| `--cover-folio-panel-width` | D panel | `min(54%, 540px)` |
| `--cover-folio-fade` | 托底渐隐 | `95deg`：`rgba(247,245,242,.98) 0%` → `.94 58%` → `0 100%` |
| `--cover-folio-title-size` | D 书名 | `clamp(2.35rem, 4.6vw, 3.35rem)` |
| `--cover-band-center` | 切带中线 | `72%` |
| `--cover-band-pad` | 题带内边距 | `20px clamp(32px, 4.5vw, 52px)` |
| `--cover-band-paper` | 纸白带 | `rgba(247,245,242,0.94)` |
| `--cover-band-ink` | 墨色带（P1） | `rgba(16,15,14,0.90)` |
| `--cover-band-title-size` | E 书名 | `clamp(1.45rem, 2.8vw, 2.05rem)` |
| `--cover-cameo-ground` | 展底 | 径向 `#343c42` → `#232a2f` → `#1a1f23` |
| `--cover-cameo-size` | 圆窗 | `min(48vh, 400px)` |
| `--cover-cameo-ring` | 金环 | 内 `0 0 0 1px rgba(196,165,116,.35)` + 垫环 `12px #232a2f` + 外 `13px rgba(196,165,116,.28)` |
| `--cover-monument-dim` | 巨字暗罩 | `160deg`：`rgba(6,8,10,.55) 0%` → `.28 45%` → `.5 100%` |
| `--cover-monument-title-size` | G 书名 | `clamp(3.4rem, 7.5vw, 5.4rem)` / weight 700 |
| `--cover-accent-deep` | 浅底强调 | `#3d6b5a` |
| `--cover-accent-soft` | 深底强调 | `#7cb89a` |
| `--cover-dock-safe` | Dock 避让 | 右上 ≥ `56×56`；`z-index ≥ 40` |

**对比度测法（AC-CSV6-16）**：① token 静态对比（纸白/墨底上的字）达 AA；② 摄影底上的白字依赖雾/暗罩——联合选型对 `text_safe_regions` 平均 luma 设门槛，或 P0 保证雾底不透明度不低于上表停点。

### 4.8 空状态 / 降级（每款须实现）

| 样式 | 无 hook | 无 place | title 触顶 |
|------|---------|----------|------------|
| **veil-footer** | 去掉细线；title 与底边距保持 | 隐藏 place 行 | 2 行 clamp |
| **folio-overlap** | 去掉 accent 细线；hook 区塌缩 | 竖排跑题可空 | 2 行 |
| **band-cut** | 左右可空；title 居中 | 左栏空 | 1–2 行 |
| **cameo-aperture** | 仅 place+title | 隐藏 place | 2 行居中 |
| **type-monument** | 仅 place+巨字 | 隐藏 place | **3 行** |

---

## 5. Cover Style Engine（封面样式引擎）

### 5.1 动机与边界

V6 起封面款数会继续增减（本轮 5 款上架、V5 三款退役、未来可能复活 B/C/H）。若样式列表继续散落在 `cover_opening_style.py` 元组、`trip.schema.json` enum、Studio `features.js`、打分 if 分支中，每次增删都是全仓改动。

**引擎目标**：把「上架 / 停用 / 预览 / 联合选型可读目录」收成单一能力域，使新增封面接近「交契约 + 注册」，停用接近「改生命周期状态」。

**引擎不是**：

| 不做 | 原因 |
|------|------|
| 可视化拖拽搭封面 CMS | 易破 DOM 铁律、难测、难联合选型 |
| 独立微服务 | 本阶段痛点是契约，不是网络边界 |
| 运营无评审即可发明布局 | 布局几何留在代码/设计评审流 |

**引擎是（进程内模块）**：

```
Admin / 封面实验室（P0.5+）
        ↓
CoverStyleRegistry（目录 + 生命周期）
CoverStyleProfile（适图画像 + blurb）
        ↓
JointCurator（只消费 active 目录）
        ↓
Renderer（data-cover-opening + CSS pack；一块 DOM）
```

建议包路径（实施可微调，须单一入口）：`travelogue/cover_engine/`（或 `travelogue/services/cover_styles/`），**禁止** 在 `assemble.py` / Studio 再维护第二份样式常量列表。

### 5.2 样式生命周期

| 状态 | 含义 | 创建联合选型 | Studio 主选择器 | 老 trip 渲染 |
|------|------|--------------|-----------------|--------------|
| `draft` | 开发中 / 设计预览 | ❌ | ❌（实验室可见） | ❌（除非显式 `?cover_style=` 调试） |
| `active` | 已上架 | ✅ | ✅ | ✅ |
| `retired` | 已停用，不再新选 | ❌ | ❌ | ✅（仍 resolve） |

**P0 决策**

| ID | 决策 |
|----|------|
| **D-CSV6-40** | 五款 V6 样式以 `active` 注册；V5 三款以 `retired` + legacy 映射注册（或不注册、仅走 `legacy_map`） |
| **D-CSV6-41** | `list_assignable_styles()` **只** 返回 `active` |
| **D-CSV6-42** | `resolve_cover_opening_style(trip)`：合法 active/retired id 原样返回；V5 id 经 `legacy_map`；非法 → 默认 `veil-footer` |
| **D-CSV6-43** | P0 **不要求** 持久化后台 DB；Registry 可由代码注册表 + 可选 JSON/YAML 覆盖（启停/权重）合并而成 |

### 5.3 上架契约（每款样式必须交付）

| # | 交付物 | P0 |
|---|--------|-----|
| 1 | `id` / `label` / `status` / `sort_order` | **必做** |
| 2 | CSS：`data-cover-opening="<id>"` 规则 + §4.7 token | **必做** |
| 3 | `CoverStyleProfile`（prefer / avoid / text_safe_regions） | **必做** |
| 4 | `studio_blurb`（用户一句话） | **必做** |
| 5 | `preview_asset_ids` 或仓库内 fixture 路径（≥1 张「该款最合适」样例） | **必做** |
| 6 | `narrow_fallback`（默认 `veil-footer`） | **必做** |
| 7 | `closing_family` 提示（可空；P1 封底软配对用） | P0 可空字段 |
| 8 | 视觉回归快照或最小 Playwright 钩子 id | **必做**（可先挂 AC id） |

未满足 1–6、8 → 不得标为 `active`。

### 5.4 P0 必做接口（API 契约）

> 下列为 **P0 开工必须落地的 Python 接口**（名称可微调，语义不可缺）。调用方：`trip_factory` / `curate` / `assemble` / Studio API / 测试。  
> **验收原则**：全仓 `grep` 不得再出现第二份「V6 五款 id 元组」作为业务真相源（测试 fixture 除外）。

#### 5.4.1 类型（概念）

```text
CoverStyleStatus = "draft" | "active" | "retired"

CoverStyleRecord:
  id: str
  label: str
  status: CoverStyleStatus
  sort_order: int
  studio_blurb: str
  narrow_fallback: str          # 通常 "veil-footer"
  closing_family: str | None    # P0 可 None
  css_hook: str                 # 等于 id；data-cover-opening 值
  profile: CoverStyleProfile
  preview_fixtures: list[str]   # asset id 或相对路径
  legacy_aliases: list[str]     # 如 card-br → 本 record（若用映射表则可外置）

CoverStyleProfile:
  prefer: dict                  # 结构化规则；实施定义 schema
  avoid: dict
  text_safe_regions: list[dict] # 归一化框 {x,y,w,h} 可选
  title_max_lines: int          # 默认 2；type-monument=3

CoverJointExplain:
  source: str                   # "joint-v6" | "hash-fallback" | "manual" | "legacy-map"
  style_id: str
  asset_id: str
  joint: float
  quality: float
  fit: float
  avoid_penalty: float
```

#### 5.4.2 Registry — **P0 必做**

| 接口 | 签名（概念） | 行为 |
|------|----------------|------|
| **`get_registry`** | `() -> CoverStyleRegistry` | 进程内单例/工厂；合并代码注册 + 可选覆盖配置 |
| **`list_styles`** | `(*, status: Status \| None = None) -> list[CoverStyleRecord]` | 按 `sort_order`；`status=None` 返回全部 |
| **`list_assignable_styles`** | `() -> list[CoverStyleRecord]` | **仅 `active`**；供联合选型与 Studio 主列表 |
| **`get_style`** | `(style_id: str) -> CoverStyleRecord \| None` | 精确查找（含 retired） |
| **`get_default_style_id`** | `() -> str` | 返回 `veil-footer`（可配置，但 P0 固定） |
| **`resolve_style_id`** | `(raw: str \| None) -> str` | 空/非法 → default；V5 alias → 映射后 id；retired 保持 id（仍可渲染） |
| **`legacy_map`** | `(raw: str) -> str \| None` | `card-br`→`veil-footer` 等；无映射返回 None |
| **`is_assignable`** | `(style_id: str) -> bool` | status == active |
| **`register_style`** | `(record: CoverStyleRecord) -> None` | **进程内注册**（启动时调用）；P0 不要求热更新 HTTP API |

#### 5.4.3 Profile / 适图 — **P0 必做**

| 接口 | 签名（概念） | 行为 |
|------|----------------|------|
| **`get_profile`** | `(style_id: str) -> CoverStyleProfile` | 无则抛错或回退空 profile（测试须覆盖） |
| **`style_fit_score`** | `(asset: dict, profile: CoverStyleProfile) -> float` | 归一化或 logit 同量纲；只读 asset 特征 |
| **`style_avoid_penalty`** | `(asset: dict, profile: CoverStyleProfile) -> float` | ≥0；忌讳命中增大 |
| **`style_fit_below_threshold`** | `(asset, style_id, *, threshold?) -> bool` | Studio「是否提示重选图」（阈值可配置） |

#### 5.4.4 Joint Curator — **P0 必做**

| 接口 | 签名（概念） | 行为 |
|------|----------------|------|
| **`iter_joint_candidates`** | `(trip, *, layout="web", k=8) -> list[asset]` | 复用现有封面候选池 / Top-K 质量序 |
| **`score_pair`** | `(asset, style_id) -> CoverJointExplain` | 计算单对 joint 分 |
| **`pick_cover_style_and_asset`** | `(trip, *, layout="web") -> CoverJointExplain` | 主路径：在 `list_assignable_styles()` × Top-K 上取最优；平局 `tripId` 哈希 |
| **`apply_joint_pick`** | `(trip, explain, *, lock=True) -> trip` | 写入 `coverAssetId` / `coverByLayout` / `meta.coverOpeningStyle` / `curation.coverStyleExplain` |
| **`hash_fallback_pick`** | `(trip) -> CoverJointExplain` | 联合关闭时：`active` 列表上 `hash % n` + 原 `pick_cover_asset_id` |

> **约束**：`pick_cover_style_and_asset` **禁止** 内联写死五款 id；必须 `list_assignable_styles()`。

#### 5.4.5 Render 解析 — **P0 必做**

| 接口 | 签名（概念） | 行为 |
|------|----------------|------|
| **`resolve_cover_opening_style`** | `(trip: dict) -> str` | 薄封装 → `resolve_style_id(meta.coverOpeningStyle)`；替换现 `cover_opening_style.resolve_*` 真相源 |
| **`assignable_style_ids`** | `() -> tuple[str, ...]` | Schema / 测试辅助；来自 Registry |
| **`studio_style_options`** | `() -> list[{id,label,blurb,sort_order}]` | Studio「排版」API/注入；**仅 active** |

#### 5.4.6 预览台（实验室）— **P0 最小必做 / P0.5 完整 UI**

| 接口 | P0 | 行为 |
|------|----|------|
| **`list_preview_matrix`** | **必做** | `() -> list[{style_id, fixture_ref, blurb}]`：每个 active（+可选 draft）× 其 preview fixture |
| **`render_preview_context`** | **必做** | `(style_id, asset_ref, *, title/hook/place?) -> dict`：供 Handlebars/静态预览页组装，不写 trip |
| **封面实验室 HTTP/页面** | P0.5 | 矩阵预览 UI；P0 可用脚本/`docs/wireframes` 或内部 route 打通 `list_preview_matrix` 即可算接口达标 |

#### 5.4.7 管理决策（启停）— **P0 配置面必做，UI 可延后**

| 接口 | P0 | 行为 |
|------|----|------|
| **`set_style_status`** | **必做（库函数）** | `(style_id, status) -> None`：校验非法迁移（如直接删 id）；写覆盖配置 |
| **`set_style_weight` / sort_order** | **必做（库函数）** | 影响 Studio 排序与可选加权（联合选型 P0 可不读 weight，但接口预留） |
| **Admin HTTP API** | P1 | 鉴权后调用上述库函数；P0 可用配置文件/代码注册变更 |

**P0 停用路径（无 Admin UI 时）**：改覆盖配置或注册表 `status=retired` → 部署/热载 → `list_assignable_styles` 立即变少；老 trip 仍 `resolve` 成功。

#### 5.4.8 P0 接口总表（检查清单）

| ID | 接口 | 优先级 |
|----|------|--------|
| **API-CSE-01** | `get_registry` / 启动注册五款 active | P0 |
| **API-CSE-02** | `list_assignable_styles` | P0 |
| **API-CSE-03** | `get_style` / `get_profile` | P0 |
| **API-CSE-04** | `resolve_style_id` + `legacy_map` | P0 |
| **API-CSE-05** | `get_default_style_id` | P0 |
| **API-CSE-06** | `style_fit_score` / `style_avoid_penalty` | P0 |
| **API-CSE-07** | `pick_cover_style_and_asset` / `apply_joint_pick` | P0 |
| **API-CSE-08** | `hash_fallback_pick` | P0 |
| **API-CSE-09** | `studio_style_options` | P0 |
| **API-CSE-10** | `list_preview_matrix` / `render_preview_context` | P0 |
| **API-CSE-11** | `set_style_status`（库函数 + 配置覆盖） | P0 |
| **API-CSE-12** | `style_fit_below_threshold` | P0（供 P1 UI；P0 先单测） |
| **API-CSE-13** | 封面实验室页面 | P0.5 |
| **API-CSE-14** | Admin HTTP 启停 API | P1 |
| **API-CSE-15** | LLM 平局 `break_joint_tie` | P1 可选 |

### 5.5 调用关系（P0）

```text
create_trip
  └─ coverOpeningStyle = get_default_style_id()  # veil-footer 占位
  └─ coverJointLocked = false

run_curate → sync_trip_covers（§3.5 包装）
  ├─ mobile: pick_cover_asset_id（既有）
  └─ web:
       if locked and not force: skip
       else pick_cover_style_and_asset → apply_joint_pick(lock=True)

assemble / render
  └─ resolve_cover_opening_style(trip)  # legacy_map；不写回
       └─ data-cover-opening="{{resolved_id}}"

Studio 排版 Sheet
  └─ studio_style_options()
  └─ 换版式：默认 repick_cover_for_style；或 keep + 弱提示

运维停用
  └─ set_style_status(id, "retired")
```

### 5.5.1 相对 CSE 总表的增补（评审后）

| ID | 接口 | 优先级 |
|----|------|--------|
| **API-CSE-16** | `repick_cover_for_style(trip, style_id)` | **P0**（Studio 换版式主路径） |
| **API-CSE-17** | telemetry `record_cover_joint_event(...)` | **P0**（在 apply 时打点） |
| API-CSE-10 | `list_preview_matrix` | P0 契约可测；**不**挡 M1 视觉合并 |
| API-CSE-11 | `set_style_status` | P0 库函数；**不**挡 M1 |

### 5.6 新增一款封面的标准流程（引擎启用后）

1. 设计高保真 + 适图画像  
2. 实现 CSS pack（`data-cover-opening`）  
3. 构造 `CoverStyleRecord`（`draft`）+ profile + preview fixture  
4. `register_style`；实验室 `list_preview_matrix` 过目  
5. AC / 快照通过 → `set_style_status(..., "active")`  
6. **不改** `assemble` / Studio 硬编码列表（自动出现在 `studio_style_options`）

### 5.7 非目标（引擎专章）

- P0 不做多租户、权限审计日志（完整 Admin → 另 PRD / §8.2）  
- P0 不做样式 semver（`veil-footer@2`）；破坏性改版先直接改 CSS  
- **封底不入本引擎 P0 五分支**；`closing_family` 字段可预留为空，供 Closing PRD 使用（§8.3）

---

## 6. 样式 ↔ 图片联合策展

### 6.1 问题回顾

高保真评审中「样式与图片互相衬托」来自人工选图。现网 `coverOpeningStyle` 与 `coverAssetId` **互不知晓**，无法产品化该效果。联合选型 **必须** 通过 §5 引擎的 `list_assignable_styles` + `get_profile`，不得维护平行样式表。

### 6.2 适图画像（机器可读 · 规范）

每款皮肤的 `CoverStyleProfile` 挂在 Registry 记录上（§5.3 / §5.4.3）：

| 字段 | 含义 |
|------|------|
| `prefer` | 加分条件（focal 带、明暗分区、画幅、中心性…） |
| `avoid` | 重罚 / 硬过滤条件 |
| `text_safe_regions` | 文案区大致矩形（归一化），用于对比度与避让 |
| `title_max_lines` | 默认 2；`type-monument` = 3 |
| `studio_blurb` | 在 Record 上；用户可见一句话（§7） |

特征须绑定现网字段：`focalPoint` / `salientBox` / faces / `meanLuma` 等（见 cover scoring v2）。

#### 6.2.1 五款适图摘要

| 样式 | 偏好 | 忌讳 / 惩罚 |
|------|------|-------------|
| **veil-footer** | 主体偏上（focal y ≲ 0.55）；下半可暗；情绪大场面 | 主体贴底；极浅高光导致雾区字对比不足 |
| **folio-overlap** | 右 2/3 有景；左缘相对干净可让字 | 主体全集中在左 30%；需读脸的大特写偏左 |
| **band-cut** | 中上部有完整景物；地平线/空景；风景大场面 | focal/人脸落在切带安全带 **[0.66, 0.78]**；信息全在下 1/4 |
| **cameo-aperture** | 主体近中心；可圆裁；人像/地标居中 | 主体贴边；超宽全景；多主体分散 |
| **type-monument** | 可压暗的氛围/纹理底；短标题更佳 | 必须看清的人脸主图；极浅背景导致暗罩违和 |

### 6.3 联合选型算法与公式（P0）

```
joint = quality_norm
      + w_fit  * style_fit_score(asset, profile)
      - w_avoid * style_avoid_penalty(asset, profile)

默认：w_fit = 0.35，w_avoid = 0.50
quality_norm = 由 cover_scoring_v2 logit 归一化到可比量纲（配置键 curate.cover_joint.*）
```

```
1. iter_joint_candidates(trip) → Top-K（复用 score_ranked，禁止全池重扫；K 默认 5–8）
2. for asset × list_assignable_styles(): score_pair
3. max joint；平局 tripId 哈希
4. apply_joint_pick → lock
```

**Mobile**：P0 仍独立选竖图；不写 V6 opening 皮肤到 mobile 呈现。

### 6.3.1 黄金集与抽检（产品验收）

| 项 | 要求 |
|----|------|
| 每款样式 | ≥2 应加分 fixture + ≥2 应重罚 fixture（单测） |
| 上线前 | 人工抽检 ≥20 本真实/半真实 trip 的联合结果 |
| 权重变更 | 须回归黄金集后方可合并 |

### 6.4 LLM / MLLM 角色

| 层级 | 是否使用 | 说明 |
|------|----------|------|
| **主路径** | ❌ | 规则 + 现有特征 |
| **aesthetic MLLM** | ✅ 可保留 | 质量小幅 boost；不直接选 style |
| **平局裁判** | P1 默认关 | `break_joint_tie` |
| **纯 LLM 选样式** | ❌ | |

### 6.5 Fallback

| 条件 | 行为 |
|------|------|
| 无合格候选图 | default style + 现有封面回退链 |
| 联合关闭 | `hash_fallback_pick`；`source=hash-fallback` |
| 用户锁定样式 | `repick_cover_for_style` |
| joint 过低 | D-CSV6-55：仍写最优 + `low_confidence` |

---

## 7. 封面使用说明（双份）

> **范围**：使用说明 **纳入本 PRD，且为 P0 必达**（§8.1）。

### 7.1 给机器

- Registry `CoverStyleProfile`  
- 黄金集单测（§6.3.1）  
- `coverStyleExplain` **P0 写入**；完整折叠面板 UI 可为 P1  

### 7.2 给用户（Studio）

| 样式 | blurb（默认） |
|------|----------------|
| 雾底题签 | 适合主体偏上、下半可暗的大场面，像电影开场。 |
| 对页叠印 | 适合右侧有景、左侧可留白的照片，标题会压在画面上。 |
| 切带题名 | 适合风景与有天空分界的照片；题带偏下，人物请勿落在画面下部。 |
| 圆窗肖像 | 适合主体居中、可被圆形裁切的一张。 |
| 巨字碑 | 适合氛围感强、可压暗的底图；书名宜短。 |

**P0 交互（评审后加严）**

| 项 | 规格 |
|----|------|
| 排版选项 | `studio_style_options()` + blurb；**建议**带 preview 小图 |
| 换版式 | **主 CTA：按新样式重荐封面图**；次要：保持当前图（D-CSV6-14） |
| 保持且低 fit | 一句非阻断灰字，如「当前封面图可能不太适合此版式」 |
| 首次联合完成后 Toast | **每 trip 仅一次**（localStorage 按 tripId）；见下 |
| 「为何选这款」一行 | P0 薄方案：用 explain 映射模板句挂在预览旁或 Sheet 顶（不必完整面板） |
| Web/Mobile 不同步 | Studio 脚注：「手机封面版式与电脑不同，以手机效果为准」 |
| 窄屏说明 | 「较窄的电脑窗口下，封面会简化为雾底题签以保证可读」 |
| create 占位 | 预览角标/文案「临时预览 · 精选后更新」 |

**Toast 文案（定稿）**

> 已为这本游记选了「{label}」，并配了更合适的封面图。可在「排版」中更换。

触发：首次 `apply_joint_pick` 成功后的 Studio Web 预览；非每次打开。

### 7.3 explain → 人话模板（P0）

| 信号 | 示例句 |
|------|--------|
| cameo 中心 | 「主体较居中，适合圆窗」 |
| band 避开 | 「避开了题带压到人物」 |
| veil 主体偏上 | 「主体偏上，适合雾底题签」 |
| low_confidence | 「备选有限，已选相对最合适的一款」 |
| manual | 「由你手动选定」 |

### 7.4 老 trip 沟通（P0）

Studio **首次**打开仍含 V5 `coverOpeningStyle` 的 trip 时，温和说明一次：

> 封面已按新画册风格呈现；你的原始设定未改写。  
> （若原为 split-mat / magazine-head）原先两款编辑向版式，现统一呈现为「对页叠印」。

---

## 8. 范围边界专章：使用说明 · 样式管理 · 封底

> **结论**：使用说明 → **P0**；样式管理 → **引擎契约 P0，后台产品不做**；封底 → **不实施改版（已拍板）**。

### 8.1 使用说明 — 纳入本 PRD（P0）

详见 **§7**。无 blurb / profile 则联合选型与换版式护栏不成立。

### 8.2 样式管理 — 引擎纳入，管理后台不纳入本 PRD P0

| 本 PRD 做 | 本 PRD 不做 |
|-----------|-------------|
| API-CSE-01～12、16～17 | 带鉴权 Admin 产品化（CSE-14） |
| `set_style_status` + 配置覆盖 | 多角色权限、审计、发布流 |
| `list_preview_matrix` 可测 | 强制实验室完整 UI（CSE-13 = P0.5，非 M1 门禁） |

### 8.3 封底 — 不纳入本 PRD 实施（**已拍板 · R-V6-06**）

现网封底 **不回归**（G-CSV6-10 / **AC-CSV6-32**）。精修与软配对 → [PRD-BOOKENDS-ENGINE-V1.md](./PRD-BOOKENDS-ENGINE-V1.md)（原规划名 `PRD-COVER-CLOSING-V1` 的超集；附录 F）。  
开合气质债为已知债；发布说明中承认，不作为 V6 Opening 回归缺陷。

### 8.4 一览表

| 主题 | 写入本 PRD？ | 本 PRD 实现？ | 详见 |
|------|--------------|---------------|------|
| Opening 五款 | ✅ | ✅ M1 | §4 |
| Engine 内核 + 锁定 | ✅ | ✅ M1–M2 | §3.5、§5 |
| 联合选型 | ✅ | ✅ M2 | §6 |
| 使用说明 / Toast / 老 trip 说明 | ✅ | ✅ M2（blurb 可随 M1） | §7 |
| 换版式默认重荐 | ✅ | ✅ M2 | D-CSV6-14 |
| 实验室完整 UI | 提及 | ❌ P0.5 | §8.2 |
| Admin 后台 | 提及 | ❌ | §8.2 |
| 封底改版 | 仅边界 | ❌ | §8.3 |

---

## 9. 范围与阶段

### 9.1 里程碑（评审后拆分）

| 里程碑 | 目标 | 门禁 |
|--------|------|------|
| **M1** | 五款 CSS 可渲染 + Engine Registry + resolve/legacy + Schema 兼容 + Studio 五选一（可读 blurb） | AC 皮肤 + 兼容 + CSE-01～05/09；**可不** 开联合默认 |
| **M2** | 联合选型默认开 + 锁定 + Toast/说明 + 换版式重荐 + telemetry | AC 联合 + 锁定集成测 + §7 P0 交互 |
| **P0.5** | 实验室页 | 非封板条件 |
| **P1+** | 不适配黄条增强、explain 面板、Admin HTTP、Closing PRD | 另排期 |

### 9.2 P0 总清单（M1+M2）

1. Engine 内核（含 CSE-16/17）与五款注册  
2. 五款 CSS + §4.7 token + §4.8 空状态  
3. Schema V6∪V5；写入仅 assignable  
4. `sync_trip_covers` 包装 + `coverJointLocked`  
5. 联合选型 + 黄金集  
6. Studio：`studio_style_options`、Toast、老 trip 说明、换版式默认重荐  
7. 窄屏 CSS 回落；Dock 安全区  
8. 封底不回归  
9. Telemetry + ACCEPTANCE / IMPLEMENTATION 文档  

### 9.3 P1（另排期）

换版式增强提示、explain 面板、band 墨色自动、LLM 平局、legacy 显式写回升级、Admin HTTP、**Closing PRD**。

### 9.4 P2

Mobile 多皮肤；删 V5 CSS；按 §5.6 上架更多款；完整管理后台。

---

## 10. 验收标准（AC-CSV6 · 草案）

### 10.1 替代与兼容

| ID | 则 |
|----|-----|
| **AC-CSV6-01** | 新建 trip 写入的 style ∈ assignable |
| **AC-CSV6-02** | Studio 仅展示 active 五款 |
| **AC-CSV6-03** | 遗留 `card-br` → 呈现 `veil-footer` |
| **AC-CSV6-04** | 遗留 split/magazine → 呈现 `folio-overlap` 且一屏无溢出 |
| **AC-CSV6-05** | 含 V5 值的 trip.json 通过 schema validate |

### 10.2 五款皮肤

| ID | 则 |
|----|-----|
| **AC-CSV6-10** | `veil-footer`：无实心卡；软雾；Dock 可点 |
| **AC-CSV6-11** | `folio-overlap`：纸白边；title 压入 |
| **AC-CSV6-12** | `band-cut`：中线 70%–74% |
| **AC-CSV6-13** | `cameo-aperture`：圆裁；题名在窗下 |
| **AC-CSV6-14** | `type-monument`：巨字；title ≤3 行不溢出 |
| **AC-CSV6-15** | 无 hook 时仍一屏可读（§4.8） |
| **AC-CSV6-16** | 对比度按 §4.7 测法 |
| **AC-CSV6-17** | &lt;1024px CSS 回落 veil；attribute 不变 |
| **AC-CSV6-18** | 五款 Dock 均可点 |

### 10.3 联合选型与锁定

| ID | 则 |
|----|-----|
| **AC-CSV6-20** | 切带忌讳图不得成为 band-cut 最优对（有替代时） |
| **AC-CSV6-21** | 圆心构图 cameo fit 显著更高 |
| **AC-CSV6-22** | 成功联合时 `source=joint-v6` |
| **AC-CSV6-23** | fallback 可启动且标记 `hash-fallback` |
| **AC-CSV6-24** | `coverJointLocked=true` 时无 force 的二次 curate **不** 改 web style+cover |
| **AC-CSV6-25** | `repick_cover_for_style` 只改 asset（或按设计改 pair）并保持锁 |

### 10.4 使用说明与沟通

| ID | 则 |
|----|-----|
| **AC-CSV6-30** | 五款 blurb 非空且 Studio 可见 |
| **AC-CSV6-31** | 首次联合后 Toast 文案符合 §7.2；每 trip 一次 |
| **AC-CSV6-33** | 换版式主按钮为重荐图 |
| **AC-CSV6-34** | 老 V5 trip 首次打开出现 §7.4 说明一次 |

### 10.5 封底（仅不回归）

| ID | 则 |
|----|-----|
| **AC-CSV6-32** | 既有条件下 `cover-closing` 仍渲染、不报错 |

### 10.6 Cover Style Engine

| ID | 则 |
|----|-----|
| **AC-CSV6-40** | assignable ≡ Studio ≡ joint 候选集 |
| **AC-CSV6-41** | retired 后不可新选；旧 trip 仍可 resolve |
| **AC-CSV6-42** | 无硬编码五元组业务真相源 |
| **AC-CSV6-43** | legacy_map 单测 |
| **AC-CSV6-44** | preview_matrix 每 active ≥1 fixture |
| **AC-CSV6-45** | CSE-01～12、16～17 契约测 |

---

## 11. 风险与缓解

| 风险 | 缓解 |
|------|------|
| 五款测试矩阵膨胀 | 共享 DOM；每款快照 |
| 联合翻车 | 黄金集 + 抽检 + low_confidence |
| 分布塌缩 | §2.3 看板 + 启停/调权 |
| 老用户静默换皮 | §7.4 说明；不写回 JSON |
| 二次 curate 冲掉封面 | §3.5 锁定 |
| Schema 打爆存量 | D-CSV6-15 双枚举 |
| 开合气质债 | 发布说明 + Closing PRD |
| 范围回潮 | §8 门禁 |
| A/G 选择器混淆 | 文案区分 + 缩略图 |

---

## 12. 开放项

| 项 | 状态 | 决议 |
|----|------|------|
| **R-V6-01** 五替三 | **已拍板** | §3.1 |
| **R-V6-02** 映射不写回 | **已拍板** | P0 不写回 |
| **R-V6-03** create 占位 | **已拍板** | `veil-footer` |
| **R-V6-04** 巨字 3 行 | **已拍板** | 允许 |
| **R-V6-05** band 墨色自动 | P1 | 保持 |
| **R-V6-06** 封底 | **已拍板** | 不实施；Closing PRD |
| **R-V6-07** LLM 平局 | P1 默认关 | 保持 |
| **R-V6-08** 字体栈 | **已拍板** | 衬线优先（D-CSV6-27） |
| **R-V6-09** 包路径 | 工程默认 | `travelogue/cover_engine/` |
| **R-V6-10** 启停存储 | 工程默认 | 代码 + YAML/JSON 覆盖 |
| **R-V6-11** 实验室 | P0.5 | 非 M1 门禁 |
| **R-V6-12** Admin 后台 | 另 PRD | §8.2 |

---

## 13. 修订记录

| 版本 | 日期 | 变更 |
|------|------|------|
| v1.0.0 | 2026-07-10 | 初稿 |
| v1.1.0 | 2026-07-10 | §5 Cover Style Engine |
| v1.2.0 | 2026-07-10 | §8 范围边界；封底移出 |
| v1.3.0 | 2026-07-10 | **跨职能评审有条件通过补丁**：锁定/curate 集成、Schema 双枚举、token 收编、空状态、KPI/黄金集、Toast/换版式/老 trip 沟通、M1→M2、开放项拍板、附录 G |

---

## 附录 A · 与 V5 / V4 关系

| 项 | V4 | V5 | V6 |
|----|----|----|-----|
| 默认皮肤 | 右下书名卡 | `card-br` | **`veil-footer`** |
| 皮肤数量 | 1 | 3 | **5（替代 3）** |
| 分配 | 无 | tripId 哈希 | **联合选型 + 锁定** |
| Schema | — | 三值 | **V6∪V5（写入仅 V6）** |
| 封底 | 探索中 | 单一 closing | **本 PRD 不改版** |
| DOM | `cover-opening` | 不拆 | **不拆** |

## 附录 B · 用户故事

| ID | 作为 | 我想要 | 以便 |
|----|------|--------|------|
| **US-V6-01** | 读者 | 被封面打动 | 愿意下翻 |
| **US-V6-02** | 作者 | 自动选好版式和封面图 | 少操心 |
| **US-V6-03** | 作者 | 看懂每款适合什么图 | 换版式不踩坑 |
| **US-V6-04** | 作者 | 换版式时默认重配图 | 纠错省心 |
| **US-V6-05** | 读者 | 仍有封底 | 开合不断裂（仅不回归） |
| **US-V6-06** | 老用户 | 被告知风格升级 | 不感到被偷偷改掉 |
| **US-V6-07** | 工程 | Registry 上架/retired | 不改散落枚举 |
| **US-V6-08** | 设计 | 实验室矩阵预览 | 决策有据（P0.5） |

## 附录 C · 线框与高保真索引

| 产物 | 路径 |
|------|------|
| 概念线框 | [wireframes/cover-styles-v6-five-concepts-wireframe.html](./wireframes/cover-styles-v6-five-concepts-wireframe.html) |
| 高保真 | [wireframes/cover-styles-v6-hi-fi-adefg.html](./wireframes/cover-styles-v6-hi-fi-adefg.html) |

## 附录 D · 未入选概念

| 概念 | ID | 去向 |
|------|-----|------|
| 展厅裱框 | B | §5.6 可上架 |
| 墨脊竖题 | C | 素材库 |
| 斜切色面 | H | 素材库 |

## 附录 E · P0 接口速查

| ID | 接口 | 备注 |
|----|------|------|
| API-CSE-01～12 | 见 §5.4.8 | M1–M2 |
| API-CSE-13 | 实验室页 | P0.5 |
| API-CSE-14 | Admin HTTP | 另 PRD |
| API-CSE-15 | `break_joint_tie` | P1 |
| API-CSE-16 | `repick_cover_for_style` | **P0** |
| API-CSE-17 | `record_cover_joint_event` | **P0** |

## 附录 F · 移交 Closing PRD 备忘

| 项 | 说明 |
|----|------|
| 文档 | `PRD-COVER-CLOSING-V1.md` |
| 时机 | V6 Opening 稳定后 |
| 范围 | 精修单一封底；选图；可选 2–3 气质族 |
| 禁止 | 5×5；阻塞已上线 Opening |

## 附录 G · 跨职能评审纪要摘要（2026-07-10）

| 席位 | 裁决 |
|------|------|
| 产品 | 有条件通过 |
| 架构 | 有条件通过 |
| UI·视觉 | 有条件通过 |
| 用户体验 | 有条件通过 |

**阻塞项（已在 v1.3 关闭）**：R-V6-01/03/06/08；锁定与 `sync_trip_covers`；Schema 双枚举；token 收编；Toast/换版式默认重荐/老 trip 说明；M1→M2；KPI/黄金集。

**共识**：五替三 + 联合选型 + 使用说明 P0；封底/Admin 拆出；Engine 进程内 Registry。

---

**文档结束**
