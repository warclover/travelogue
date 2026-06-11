# LTE · 屏级模板目录（patternId）

| 属性 | 内容 |
|------|------|
| **权威来源** | `travelogue/layout_templates/templates/screen-*.yaml` |
| **注册表** | `travelogue/layout_templates/registry.py` · `get_engine().list_active()` |
| **MCS 消费** | `travelogue/curation/mosaic/lte_adapter.py` · `mosaic_registry()` |
| **关联纲领** | [PRD-PRODUCT-LAYOUT-PRINCIPLES.md](./PRD-PRODUCT-LAYOUT-PRINCIPLES.md) |
| **用例草案** | [TEMPLATE-USE-CASES.md](./TEMPLATE-USE-CASES.md) |
| **更新日期** | 2026-06-11 |

**状态说明**

| status | 含义 | MCS / 注册表 |
|--------|------|----------------|
| `ga` | 正式发布 | `list_active()` 包含 |
| `experimental` | 实验（P19 SKU 等） | 包含；常配 `rollout.percent` |
| `beta` | 灰度 | 包含 |
| `deprecated` | 退役 | **不**进入 `list_active()` |

**rollout.percent**（P19）：`0` = 不进 rollout 候选；`15` = 按 tripId 约 15% 分桶；`100` = 全量；未配置 = 视为无 rollout 限制（与 100 等效于 MCS 额外候选逻辑）。

**config 覆盖**：`layout.template_engine.overrides.disable` 可从运行时 registry 移除模板（本地 `config.yaml` 当前禁用 `screen-mosaic-5-2p3l-equal`）。

---

## 1. 总览

| 类别 | 数量 |
|------|------|
| LTE YAML（`screen-*.yaml`） | 29 |
| 活跃（ga / experimental） | 26 |
| deprecated | 3 |
| 仅 planner、无 LTE YAML | 见 §4 |

---

## 2. LTE 活跃模板（26）

### 2.1 单张竖版（primitive · 9:16 舞台）

| patternId | displayName | 张数 | status | rollout | 说明 |
|-----------|-------------|------|--------|---------|------|
| `screen-portrait-1` | 单张竖版 | 1 | ga | — | 章末孤儿竖图 cover 满屏 |

### 2.2 单张横版 / 全幅（primitive）

| patternId | displayName | 张数 | 舞台 | status | rollout | 说明 |
|-----------|-------------|------|------|--------|---------|------|
| `screen-landscape-1` | 单张横版 | 1 | 16:9 | ga | — | 横/全景单开一屏 cover |
| `screen-full-frame` | 全幅单图 | 1 | 16:9 | ga | 100% | contain + blur fill，Collage 整图 |
| `screen-full-frame-bsp-3-2` | — | 1 | **3:2** | experimental | **0%** | BSP 视口探针；默认不进 rollout |

### 2.3 竖版多图 grid（primitive · 9:16）

| patternId | 张数 | status | MCS 窗族 | 说明 |
|-----------|------|--------|----------|------|
| `screen-portrait-2` | 2 | ga | — | 两列竖图 |
| `screen-portrait-3` | 3 | ga | MOSAIC_3 | 三竖并列 |
| `screen-portrait-4` | 4 | ga | MOSAIC_4 | 四宫格竖 |
| `screen-portrait-6` | 6 | ga | MOSAIC_6 | 六宫格竖 |
| `screen-portrait-9` | 9 | ga | MOSAIC_9 | 九宫格竖 |
| `screen-portrait-grid-8` | 8 | ga | MOSAIC_8 | 2×4 竖宫格 |

### 2.4 横版多图 grid / stack（16:9）

| patternId | 张数 | kind | status | MCS 窗族 | 说明 |
|-----------|------|------|--------|----------|------|
| `screen-landscape-2` | 2 | stack | ga | — | 两横叠放 |
| `screen-landscape-3` | 3 | stack | ga | MOSAIC_3 | 三横叠放 |
| `screen-landscape-4` | 4 | primitive | ga | MOSAIC_4 | 四宫格横 |
| `screen-landscape-6` | 6 | primitive | ga | MOSAIC_6 | 六宫格横 |
| `screen-landscape-9` | 9 | primitive | ga | MOSAIC_9 | 九宫格横 |

### 2.5 横竖混排（composite / primitive）

| patternId | 张数 | status | MCS 窗族 | 说明 |
|-----------|------|--------|----------|------|
| `screen-portrait-1-landscape-2` | 3 | ga | MOSAIC_3 | 1 竖 + 2 横 |
| `screen-portrait-2-landscape-2` | 4 | ga | MOSAIC_4 | 2 竖 + 2 横 |

### 2.6 五 / 六窗马赛克（composite · 16:9）

| patternId | displayName | 张数 | status | rollout | 说明 |
|-----------|-------------|------|--------|---------|------|
| `screen-mosaic-5-main-portrait-3land` | — | 5 | ga | — | 主竖 + 3 横（legacy 迁移） |
| `screen-mosaic-5-2p3l-equal` | 五图·双竖 hero+三横 | 5 | ga | 100% | P16 旗舰 2P+3L；**本地 config 可 disable** |
| `screen-mosaic-5-hero-3-2-plus-4` | 五图·加权轨道 hero | 5 | ga | 100% | 加权轨道主 hero + 四配图 |
| `screen-mosaic-5-main-hero-plus-4` | mosaic·5·main·hero·plus·4 | **6** | ga | — | 3×3 舞台 6 槽位（主 hero 2×2 + 余格） |
| `screen-mosaic-6-main-hero-plus-5` | — | 6 | ga | — | 6 窗主图 + 5 格 |

### 2.7 P19 设计师 SKU（experimental）

| patternId | displayName | 张数 | rollout | 说明 |
|-----------|-------------|------|---------|------|
| `screen-justified-row` | justified·portrait row | 4–8 | 100% | Flickr 式不等宽竖行；`kind: justified` |
| `screen-spread-folio` | spread·folio dual hero | 2 | 15% | 对开双横 hero |
| `screen-asymmetric-hero` | asymmetric·hero+sidebar | 4 | 15% | 左主图 + 右侧栏条 |
| `screen-whitespace-hero` | whitespace·hero | 1 | **0%** | 留白 hero；默认关闭 rollout |

---

## 3. deprecated（3 · 不进活跃注册表）

| patternId | 张数 | 说明 |
|-----------|------|------|
| `screen-mosaic-5-2portrait-3land-balanced` | 5 | 2 竖 + 3 横平衡版（已由 2p3l-equal 等替代） |
| `screen-mosaic-5-3portrait-2land-balanced` | 5 | 3 竖 + 2 横平衡版 |
| `screen-mosaic-5-main-landscape-2portrait-2land` | 5 | 主横 + 2 竖 2 横 |

---

## 4. 无 LTE YAML · screen_planner 专用 patternId

由 `travelogue/curation/screen_planner.py` 生成，**不在** LTE 注册表；无 `photoCount` YAML 元数据。

| patternId | 典型用途 | 说明 |
|-----------|----------|------|
| `screen-breath-pause` | 节奏留白 | 无照片槽；章节呼吸 |
| `screen-panorama-1` | 全景单张 | 超宽图 cover |
| `screen-tall-1` | 超高单图 | contain |
| `screen-plate` | Folio lite 章首 | 与 portrait-1 舞台类似 |
| `screen-square-1` … `screen-square-9` | 方图 grid | 1/2/3/4/6/9 方图宫格 |
| `screen-spread` | 对开（legacy id） | CSS 映射存在；LTE 侧为 `screen-spread-folio` |

---

## 5. MCS 统一窗族（`lte_policy.yaml`）

窗大小 → 优先 pattern 列表（其余同张数活跃模板经 rollout 作 extras）：

| 窗大小 n | 默认族成员 |
|----------|------------|
| 3 | portrait-3, landscape-3, portrait-1-landscape-2 |
| 4 | portrait-2-landscape-2, portrait-4, landscape-4 |
| 5 | mosaic-5-main-portrait-3land, mosaic-5-2p3l-equal |
| 6 | mosaic-5-main-hero-plus-4, mosaic-6-main-hero-plus-5, portrait-6, landscape-6 |
| 8 | portrait-grid-8 |
| 9 | portrait-9, landscape-9 |

**无 MOSAIC_2 / MOSAIC_7 窗族**；2 张、7 张依赖 portrait-2、landscape 栈或 planner 单张逻辑。

---

## 6. 张数优先级（P-LAY-01 · 2026-06-11）

| 档位 | 张数 n | 产品态度 | 现网模板（活跃） |
|------|--------|----------|------------------|
| **P0 重点** | **4** | 可变化形式多 · **继续扩 SKU** | portrait-4, landscape-4, 2竖+2横, asymmetric-hero(4) |
| **P0 重点** | **5** | 同上 · mosaic 主战场 | main-portrait-3land, 2p3l-equal, hero-3-2-plus-4, justified 4–8 |
| **P0 重点** | **6** | 同上 | portrait-6, landscape-6, mosaic-6-main-hero-plus-5, main-hero-plus-4（6槽） |
| **维持** | **7** | **非重点 · 已够用** | 无专窗；由 planner 拆窗或邻近尺寸兜底 |
| **维持** | **8** | **非重点 · 已够用** | portrait-grid-8, justified-row |
| **维持** | **9** | **非重点 · 已够用** | portrait-9, landscape-9 |
| 基础 | 1–3 | 单张 + 简单混排 | 竖/横单、portrait-2/3、landscape 栈、1竖+2横 等 |
| 禁止 | >9 | — | validator V-P16-12 |

**Backlog 原则**：新模板 PR **默认只接 4–6 张**；7–9 仅修 bug / 回归，不主动扩构图族。

---

## 7. 修订记录

| 版本 | 日期 | 说明 |
|------|------|------|
| v1.0 | 2026-06-11 | 初版：29 YAML + planner 专用 ID + MCS 窗族 + P-LAY 缺口 |
| v1.1 | 2026-06-11 | 张数优先级：4/5/6 P0；7/8/9 维持 |
