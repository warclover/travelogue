# Travelogue · 智能排版开关页 产品需求文档（PRD）

| 属性 | 内容 |
|------|------|
| **产品代号** | Travelogue |
| **功能名称** | 智能排版能力开关页（LSE Capability Admin） |
| **文档版本** | v0.2-IMPLEMENTED |
| **状态** | 已实现 · 2026-06-08 |
| **页面路由** | `GET /lse-flags-admin`（Studio 内嵌后台，新独立子页面） |
| **关联文档** | [PRD-PHASE17-layout-strategy-engine.md](./PRD-PHASE17-layout-strategy-engine.md)、[ARCHITECTURE-OVERVIEW.md](./ARCHITECTURE-OVERVIEW.md) |
| **关联代码** | `travelogue/layout_engine/capabilities.py`、`travelogue/layout_engine/rollout.py`、`travelogue/layout_engine/readiness.py`、`travelogue/layout_engine/policy.py`、`travelogue/config/layout.py`、`travelogue/config/loader.py`、`travelogue/web/studio_handlers/layout_strategy_handlers.py`、`travelogue/web/studio_handlers/paths.py`、`travelogue/web/studio_pipeline.py`、`travelogue/layout_engine/strategies/default.yaml`、`travelogue/layout_engine/lse_policy.yaml` |
| **更新日期** | 2026-06-08 |

> **评审修订摘要（v0.1 → v0.2）**
>
> - **B1**：`traffic_percent` 不从 `config.yaml` 读，改为只读展示；v1 仅写引擎总开关 `enabled`（开启后短路 rollout，所有 trip 直接跑 LSE）。
> - **B2**：补 camelCase↔snake_case 键映射表；`patch_config_file` 新增 `layout.strategy_engine` 嵌套白名单块。
> - **M1**：`pace_profile` 全代码无消费者，从开关页移除（能力清单 10→9 项）。
> - **M2**：更正"立即生效"机制——依赖 pipeline 子进程重载磁盘配置；本页 GET 必须读盘最新值。
> - **M3**：引擎总开关从"风险"升级为"必做需求 §3.2"+ AC 强约束。
> - **M4**：审计日志 v1 降级为结构化日志行（非双人审批存储）。
> - **minors**：GET 复用 `readiness.py` 能力快照；提示 config.yaml 注释会丢失；PATCH 鉴权强于 GET。

---

## 1. 背景与动机

### 1.1 问题陈述

智能排版（LSE）历经多次升级，已实现一批对标业内典范的能力（显著性裁切、色调一致性、匈牙利槽位匹配、高光选片、编辑/对开提示、叙事节拍等）。但诊断发现：**这些能力在生产默认配置下几乎全部关闭，且整套 LSE 引擎处于 dogfood/0% 流量阶段，实际并未在主路径上运行**。

| 现状事实 | 来源 |
|----------|------|
| `saliency_scoring / tone_harmony / hungarian_assignment / segment_order_optimizer / highlight_windows / editorial_hints / quality_unified` 默认 `false` | `strategies/default.yaml`、`lse_policy.yaml` |
| `beat_profile` 默认 `flat`（无叙事节拍） | `strategies/default.yaml` |
| LSE 引擎总开关 `layout.strategy_engine.enabled` 默认 `false` | `config/layout.py:83` |
| `rollout.traffic_percent = 0`，`stage = dogfood`，仅 allowlist 命中 | `lse_policy.yaml:9-18` |
| **几乎所有能力仅在 LSE 适配器内被消费** | `layout_engine/adapter.py:106-134`（详见 §3.3） |

> 结论：要评估"算法升级到底有没有效果"，运营/研发需要一个**能开关这些能力、开启引擎、并能看到当前是否真正生效**的界面。当前只能手改 YAML/`config.yaml` 并重启，缺乏可视化、可解释入口。

### 1.2 目标

- 提供独立后台子页面，**集中开关 LSE 能力**。
- **同时提供 LSE 引擎总开关**，避免"开了能力却不生效"的假开关陷阱（§3.2）。
- 直观展示每项能力的**有效值（effective）与来源（config / 策略包）**。
- 写回后**下次排版立即生效**（无需重启服务，机制见 §5.4）。

### 1.3 非目标

- 不做权重/惩罚（weights/penalties）调参——属已有 LSE Inspector 范畴。
- 不做策略包 YAML 的版本发布/生命周期治理（走 GitOps）。
- 不对 C 端普通用户暴露；仅服务运营/研发治理（沿用 P17 章程）。
- v1 不引入双人审批工作流；不写灰度流量（见 §3.2、§8 升级路径）。

---

## 2. 用户与场景

| 角色 | 场景 |
|------|------|
| 算法/研发 | dogfood 阶段开启引擎 + 某能力，重跑 trip 对比成稿效果 |
| 运营 | 查看当前哪些能力实际在跑、引擎是否开启 |

主流程：进入 `/lse-flags-admin` → 看到**引擎状态横幅** + 能力清单（含有效值与来源）→ 开启引擎 / 切换能力开关 / 选择 beat profile → 保存 → 下次排版子进程按新配置运行。

---

## 3. 功能需求

### 3.1 能力清单与字段类型

合并语义（既有逻辑，`capabilities.effective_capabilities`）：**`effective = config OR 策略包默认`**；`beat_profile` 为 `config` 优先，仅当其为 `flat`/空时回退策略包。

| # | 能力 | 配置键（落盘 snake_case） | 类型 | 控件 | 默认 |
|---|------|---------------------------|------|------|------|
| 1 | 显著性裁切打分 | `saliency_scoring` | bool | 开关 | false |
| 2 | 色调一致性 | `tone_harmony` | bool | 开关 | false |
| 3 | 匈牙利槽位匹配 | `hungarian_assignment` | bool | 开关 | false |
| 4 | 统一质量模型 | `quality_unified` | bool | 开关 | false |
| 5 | 段内连贯重排 | `segment_order_optimizer` | bool | 开关 | false |
| 6 | 隐式反馈导出 | `implicit_feedback_export` | bool | 开关 | false |
| 7 | 高光选片窗口 | `highlight_windows` | bool | 开关 | false |
| 8 | 编辑/对开提示 | `editorial_hints` | bool | 开关 | false |
| 9 | **叙事节拍** | `beat_profile` | string 枚举 | **下拉** | `flat` |

> **`pace_profile` 已移除**（评审 M1）：`config.layout.capabilities.pace_profile` 字段存在，但**全代码库无任何业务代码读取它**（仅出现在定义/解析/合并处）。开放该开关会误导用户（开了无效），故 v1 不展示。如未来接线消费逻辑，再加回。

`beat_profile` 合法枚举（来自 `layout_engine/beat.py:29-44`）：**`flat`（无节拍）、`classic_magazine`（经典杂志：前段偏 hero、中段偏 mosaic/九宫、尾段偏竖图）、`dense_mid`（中段加密 mosaic）**。PATCH 时须校验取值在此白名单内，非法返回 400。

### 3.2 引擎总开关（必做需求，评审 M3 升级）

> **背景**：评审证实几乎所有能力仅在 LSE 适配器（`adapter.py`）内消费，而该路径是否运行取决于引擎门控。仅翻能力 flag 而不开引擎 ≈ 无效操作（假开关）。

| 项 | 配置/来源 | 类型 | 控件 | 说明 |
|----|-----------|------|------|------|
| **LSE 引擎总开关** | `layout.strategy_engine.enabled`（config.yaml） | bool | **开关（必做）** | `enabled=true` 会短路 rollout，使**所有 trip** 直接运行 LSE（`rollout.py:73-74`） |
| rollout stage | `lse_policy.yaml` / `lse_runtime.json` | string | **只读展示** | off/dogfood/… |
| 灰度流量 traffic_percent | 同上（**不在 config.yaml**） | float | **只读展示** | 见 §3.2 注 |
| allowlist / blocklist | 同上 | list | **只读展示** | — |

> **§3.2 注（评审 B1）**：`effective_rollout()` 只读 `lse_policy.yaml` 与 `data/lse_runtime.json` 的 `rollout`，**完全不读 config.yaml**（`rollout.py:53-68`）。因此 v1 **不通过本页写 traffic_percent**——只读展示即可。开启引擎总开关已足以让所有 trip 跑 LSE，满足 dogfood 验证需求。灰度写入留待路线 B（§8）。

### 3.3 能力消费点（实现参考·证明非假开关）

| 能力 | 消费位置 |
|------|----------|
| saliency_scoring | `layout_engine/adapter.py:106,130` |
| tone_harmony | `layout_engine/adapter.py:108,131` |
| hungarian_assignment | `layout_engine/adapter.py:115` |
| beat_profile | `layout_engine/adapter.py:132` → `beat.py` |
| quality_unified | `adapter.py:134` → `mosaic/scorer.py:89,253`、`candidates.py:122` |
| highlight_windows | `adapter.py:118`、`screen_planner_attach.py:178` |
| editorial_hints | `curation/curate.py:1127` |
| segment_order_optimizer | `curate.py:625`、`replan.py:69`（部分在引擎关时亦可触发） |
| implicit_feedback_export | `layout_engine/studio_feedback.py:25` |
| ~~pace_profile~~ | **无消费者（移除）** |

---

## 4. 页面设计（线框）

```
┌─────────────────────────────────────────────────────────────┐
│  智能排版能力开关 (LSE Capabilities)        [刷新] [保存变更]   │
├─────────────────────────────────────────────────────────────┤
│  ⚠ 引擎状态横幅                                                │
│  LSE 引擎: ● 关闭 (enabled=false)                             │
│  rollout: stage=dogfood  traffic=0%  (只读)                   │
│  → 引擎关闭时，下方能力开关不会实际生效，请先开启引擎          │
│  [ ○—— 开启 LSE 引擎 ]                                         │
├─────────────────────────────────────────────────────────────┤
│  能力开关                          有效值  来源     操作        │
│  ─────────────────────────────────────────────────────────── │
│  显著性裁切打分 saliency_scoring     ✗     config   [ ○——]     │
│  色调一致性     tone_harmony         ✗     config   [ ○——]     │
│  匈牙利槽位匹配 hungarian_assignment ✗     config   [ ○——]     │
│  统一质量模型   quality_unified      ✗     config   [ ○——]     │
│  段内连贯重排   segment_order        ✗     config   [ ○——]     │
│  隐式反馈导出   implicit_feedback    ✗     config   [ ○——]     │
│  高光选片窗口   highlight_windows    ✗     config   [ ○——]     │
│  编辑/对开提示  editorial_hints      ✗     config   [ ○——]     │
│  叙事节拍       beat_profile       [ flat ▾ ]                  │
│                  (flat / classic_magazine / dense_mid)        │
├─────────────────────────────────────────────────────────────┤
│  生效说明: 有效值 = config OR 策略包默认。来源标"策略包"的项   │
│  无法在此关闭(OR 语义)。保存后下次排版子进程重载生效。        │
└─────────────────────────────────────────────────────────────┘
```

设计要点：

- 每行三段信息：能力名 / **有效值**（`effective_capabilities` 实际算出）/ **来源**（config 还是策略包）/ 操作控件。
- 顶部横幅醒目展示引擎状态；引擎关闭时对"已开能力"给出告警（AC-6）。
- `beat_profile` 用下拉（flat / classic_magazine / dense_mid），非开关。
- 来源为"策略包"的项标注"不可在此关闭"（OR 语义限制，§6 坑②）。

---

## 5. 技术方案

### 5.1 写回路线（已定）

**路线 A：写 `config.yaml` 的 `layout.strategy_engine.capabilities` 与 `layout.strategy_engine.enabled`，单人操作 + 结构化审计日志，不上双人审批。**

理由：

1. 运行时 `effective_capabilities()` 直接读 config.yaml 的 capabilities，写此处立即（下次排版）生效。
2. 当前 dogfood 实验阶段，目的是开能力看效果；双人审批属过度工程。
3. 复用既有 `PATCH /__travelogue/config` 同款 `patch_config_file` 写回链路。
4. API 设计为通用 capabilities GET/PATCH，未来切换写入目标到 `data/lse_runtime.json` + 审批（路线 B）时前端不动。

### 5.2 键映射表（评审 B2）

HTTP 层用 camelCase，落盘与加载器用 snake_case，handler 负责双向映射：

| API（camelCase） | config.yaml 落盘路径（snake_case） |
|------------------|-------------------------------------|
| `engineEnabled` | `layout.strategy_engine.enabled` |
| `capabilities.saliencyScoring` | `layout.strategy_engine.capabilities.saliency_scoring` |
| `capabilities.toneHarmony` | `…capabilities.tone_harmony` |
| `capabilities.hungarianAssignment` | `…capabilities.hungarian_assignment` |
| `capabilities.qualityUnified` | `…capabilities.quality_unified` |
| `capabilities.segmentOrderOptimizer` | `…capabilities.segment_order_optimizer` |
| `capabilities.implicitFeedbackExport` | `…capabilities.implicit_feedback_export` |
| `capabilities.highlightWindows` | `…capabilities.highlight_windows` |
| `capabilities.editorialHints` | `…capabilities.editorial_hints` |
| `capabilities.beatProfile` | `…capabilities.beat_profile`（string） |

### 5.3 API 契约

**读**

```
GET /__travelogue/layout-strategies/capabilities
→ 200
{
  "ok": true,
  "engineEnabled": false,
  "rollout": { "stage": "dogfood", "trafficPercent": 0, "allowlistTripIds": [...], "blocklistTripIds": [...] },   // 只读
  "capabilities": {
    "saliencyScoring":       { "effective": false, "fromConfig": false, "fromPack": false },
    "toneHarmony":           { "effective": false, "fromConfig": false, "fromPack": false },
    "hungarianAssignment":   { "effective": false, "fromConfig": false, "fromPack": false },
    "qualityUnified":        { "effective": false, "fromConfig": false, "fromPack": false },
    "segmentOrderOptimizer": { "effective": false, "fromConfig": false, "fromPack": false },
    "implicitFeedbackExport":{ "effective": false, "fromConfig": false, "fromPack": false },
    "highlightWindows":      { "effective": false, "fromConfig": false, "fromPack": false },
    "editorialHints":        { "effective": false, "fromConfig": false, "fromPack": false },
    "beatProfile":           { "effective": "flat", "fromConfig": "flat", "fromPack": "flat", "options": ["flat","classic_magazine","dense_mid"] }
  }
}
```

GET 实现：复用 `effective_capabilities(cfg, pack)`、`capabilities_from_pack(pack)`（区分 config vs pack 来源）、`lse_rollout_snapshot(cfg)`（rollout 只读）。`cfg` 须 `load_config(studio_config_path)` **读盘最新值**，不可用进程缓存（评审 M2）。可参考 `readiness.py:w3b12_rollout_ready` 的聚合写法。

**写**

```
PATCH /__travelogue/layout-strategies/capabilities
body: {
  "engineEnabled": true,
  "capabilities": { "saliencyScoring": true, "toneHarmony": true, "beatProfile": "classic_magazine" }
}
→ 200 { "ok": true, "engineEnabled": true, "rollout": {...}, "capabilities": { ...回显有效值... } }
→ 400 当 beatProfile 不在枚举内
```

PATCH 实现：camel→snake 映射后调 `patch_config_file(target, mapped_patch)`；写后记审计日志（§5.5）；返回体重新 `load_config` 后用 `effective_capabilities` 回显。

### 5.4 "立即生效"机制（评审 M2 更正）

- 渲染/策展在**子进程**中执行，子进程启动即重载磁盘配置：

```326:327:travelogue\web\studio_pipeline.py
        get_config(reload=True, path=cfg_path)
    cfg = app_config or get_config()
```

- 因此写 config.yaml 后，**下次排版自动读到新值，无需重启服务**。
- 注意：现有 `handle_config` PATCH **不刷新**主进程的 `get_config()` 单例缓存。故**本页 GET 必须 `load_config(studio_config_path)` 读盘**，否则刚保存的值在页面上不刷新。
- 不需要也不应在 handler 里强行 `reset_config_cache()` 影响其他正在进行的请求。

### 5.5 审计日志（评审 M4 降级）

v1 不接双人审批存储；每次成功 PATCH 写一条结构化日志（`logging`）：

```
[lse-flags-admin] capability change by role=<role> host=<host>: {changed: {...before→after...}}
```

未来路线 B 再升级为 `config_governance` 审计 + 回滚。

### 5.6 鉴权（评审 m4）

- 复用 `layout_strategy_handlers._auth`（`require_admin_api_access` + `require_template_role`，loopback 默认 `template_admin`）。
- 复用 `_lse_internal`（非 loopback 且无 `studio.layout_templates_internal=true` → 403）。
- **PATCH 比 GET 更严**：GET 最低 `viewer`；PATCH 要求 `template_admin`。

---

## 6. 风险与边界（坑）

| # | 坑 | 处置 |
|---|----|------|
| ① | **假开关**：仅翻能力 flag 而引擎关闭时 LSE 不进主路径 | §3.2 引擎开关定为必做；横幅告警；AC-6 强约束 |
| ② | **OR 合并语义**：`effective = config OR pack`，策略包某能力为 true 则无法在此关闭 | UI 对"来源=策略包"项标注不可关闭；当前策略包全 false，config 控制力完整 |
| ③ | **traffic_percent 不在 config.yaml** | v1 只读展示；不写（B1） |
| ④ | **beat_profile 非法值** | PATCH 校验 `flat/classic_magazine/dense_mid`，非法 400 |
| ⑤ | **config.yaml 注释丢失**：`yaml.safe_dump` 重写整文件，抹掉手写注释 | PRD 注明；建议 config.yaml 不放关键注释，或后续改增量写 |
| ⑥ | **全局影响**：写 config.yaml + 开引擎影响所有 trip 成稿 | dogfood 阶段符合预期；文案提示"全局生效" |
| ⑦ | **并发写**：`patch_config_file` 读-改-写无锁 | 单用户 dogfood 可接受，PRD 注明限制 |
| ⑧ | **死字段 `capabilities_defaults`**：`lse_policy.yaml` 该段未接线 | 本期不依赖；接线非本期范围 |

---

## 7. 验收标准（AC）

- **AC-1** 访问 `/lse-flags-admin` 返回开关页，列出 9 项能力 + 引擎状态横幅；不出现 `pace_profile`。
- **AC-2** GET API 返回每项 `effective`/`fromConfig`/`fromPack`，与 `effective_capabilities()` 一致；rollout 字段只读。
- **AC-3** 切换任一布尔开关并保存后，**新建一次** `load_config` 读盘 GET 回显更新；新一次排版 `capability_flags_snapshot` 反映新值（无需重启）。
- **AC-4** `beat_profile` 下拉仅 `flat/classic_magazine/dense_mid`；写非法值返回 400。
- **AC-5** 开启/关闭引擎总开关后，`config.yaml` 的 `layout.strategy_engine.enabled` 正确写入，GET 回显更新。
- **AC-6** 当"有能力开启但引擎关闭"时，页面显示告警横幅。
- **AC-7** 鉴权：非内网或权限不足访问 API 返回 403；PATCH 要求 `template_admin`。
- **AC-8** 每次 PATCH 写一条结构化审计日志（操作者 + 变更前后值）。

---

## 8. 升级路径（未来，非本期）

- **路线 B（生产灰度）**：写入目标从 config.yaml 切到 `data/lse_runtime.json`，复用 `config_governance` 双人审批 + 审计 + 回滚；扩 `LSE_PATCH_KEYS` 含 capabilities 与 rollout，并在 `effective_capabilities` 叠加 runtime overlay；本页可写 `traffic_percent`。前端 API 契约不变。
- 接线 `lse_policy.yaml` 的 `capabilities_defaults` 作为集中默认值层（补齐死字段）。
- 与 LSE Inspector（weights/penalties）合并为统一治理面板。
- `pace_profile` 接线消费逻辑后加回开关。

---

## 9. 开发任务拆解与代码锚点（开发就绪）

| # | 任务 | 文件 / 锚点 | 状态 |
|---|------|-------------|------|
| 1 | 路径常量 | `web/studio_handlers/paths.py` | ✅ |
| 2 | 后端 handler | `web/studio_handlers/layout_strategy_handlers.py` | ✅ |
| 3 | 路由分发 | `web/studio_routes.py` | ✅ |
| 4 | 静态页 handler | `web/studio_handlers/static_handlers.py` | ✅ |
| 5 | 配置写回 | `config/loader.py` | ✅ |
| 6 | 前端页面 | `templates/studio/lse-flags-admin.html` | ✅ |
| 7 | 审计日志 | handler 内 `logging` | ✅ |
| 8 | 测试 | `tests/test_studio_lse_flags_admin.py`（含鉴权/快照/审计） | ✅ |
| 9 | 文档 | `README.md`、`RUNBOOK-DOGFOOD.md`、PRD 访问说明 | ✅ |

### 访问方式

```bash
travelogue studio   # 默认 http://127.0.0.1:8766
# 浏览器：http://127.0.0.1:8766/lse-flags-admin
# API：GET/PATCH /__travelogue/layout-strategies/capabilities
```

LSE 开关页顶部可返回 `/templates-admin`。

### 关键复用点
- `capabilities.effective_capabilities` / `capability_flags_snapshot` / `capabilities_from_pack`
- `rollout.lse_rollout_snapshot` / `effective_rollout`
- `readiness.w3b12_rollout_ready`（聚合写法参考）
- `config.loader.patch_config_file`（写回模式）
- `layout_strategy_handlers._auth` / `_lse_internal`（鉴权）
