# CSC W0 · Studio 设置面库存（CSC-W0-05）

| 属性 | 内容 |
|------|------|
| **日期** | 2026-07-22 |
| **分支** | `feat/csc-w0-recipe` |
| **对照代码** | `templates/studio/studio-home-v2.html` · `js/advanced.js` · `homepage-v2/storage-settings.js` · `config/loader.py` PATCH 白名单 · `studio_config_expose` |
| **用途** | W1 常用/高级分层与 `l1_keys` 派生的输入；本波**不改 UI** |

---

## 1. 设置 Popover 控件库存

| UI 控件 ID | 用户可见标签 | 所在区 | 绑定 | 建议档 | 备注 |
|------------|--------------|--------|------|--------|------|
| `v2-theme-select` | 首页配色 | 外观 | 客户端 theme（非 AppConfig） | **UI-local** | 不影响成册管线 |
| `studio-cfg-clustering` | 行程识别 | 导入与分析 | `clustering.enabled` TriState | **L1** | PATCH 白名单；默认 auto |
| `studio-cfg-vision` | 场景分析 | 导入与分析 | `vision.enabled` TriState | **L1** | 默认关；开则更慢 |
| `studio-cfg-g1` | 导入后先确认章节 | 说明与实验选项 | `studio.g1_confirm_structure` | **Danger / Advanced** | 打断截取路径；须二次展开 |
| `studio-cfg-layout-scoring` | 智能排版（实验） | 说明与实验选项 | `layout.scoring.enabled` | **Advanced** | 实验；勿进常用 |
| `studio-llm-settings-entry` | 配置写作引擎… | AI 文案 | `llm.*` / secrets | **L0** | 运维/密钥；不成册必需 |
| `studio-cfg-copy-source` | 导入时复制源文件 | 存储与磁盘 | `ingest.copy_source_files` | **L1** | 影响磁盘与后续导入 |
| `studio-storage-cleanup-btn` | 清理磁盘… | 存储与磁盘 | 动作 API（非 bool 旋钮） | **Ops action** | 非 Recipe 键 |
| Dev / 退出等 | 更多 | 条件显示 | internal | **Research / Dev** | 不进首趟 |

**现状分层信号（已部分符合 F-CSC）**

- 「说明与实验选项」已是 `<details>` 二次折叠 → G1 / scoring 已在 Advanced 口袋。  
- 缺口：尚无机器可读 `l1_keys`；expose 仍可能透出 strategyEngine 等只读态。

---

## 2. PATCH / expose 对照

| 键（API） | PATCH | expose | 建议 |
|-----------|-------|--------|------|
| `clustering.enabled` | ✅ | ✅ | L1 |
| `vision.enabled` | ✅ | ✅ | L1 |
| `layout.scoring.enabled` | ✅ | ✅ | Advanced |
| `studio.g1ConfirmStructure` | ✅ | ✅ | Danger · 保持默认 false |
| `ingest.copySourceFiles` | ✅ | （storage 路径） | L1 |
| `studio.layoutTemplatesInternal` | ✅（白名单有） | ✅ | Research · **不得进常用 UI** |
| `layout.strategy_engine.*` | ✅（capabilities） | 只读 enabled | Research · admin 面 |
| `tripsDir` | — | ✅ | L0 |

---

## 3. Admin / 研究入口（须与主 CTA 隔离）

| 入口 | 路径/条件 | 建议 |
|------|-----------|------|
| LSE flags admin | `/lse-flags-admin` + internal | Research · 禁止链入首页主 CTA |
| Templates admin | `/templates-admin` | Research |
| `layout_templates_internal` | config 布尔 | Danger/Research · UI 不暴露 |

---

## 4. W1 派生目标（本表承诺）

1. **常用区**仅渲染 Recipe.`l1_keys`（见键表）。  
2. G1 / scoring 维持在「说明与实验选项」，文案标注实验/慎用。  
3. LLM / theme 保持现位：LLM=L0，theme=UI-local。  
4. 不在本波新增设置控件。
