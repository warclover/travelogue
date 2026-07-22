# CSC W3b · 配置用户档 / research 分层

| 属性 | 内容 |
|------|------|
| **日期** | 2026-07-22 |
| **DOC-STATUS** | active |
| **PRD** | CSC §7.2 |

---

## 分层

| 层 | 文件 | 内容 |
|----|------|------|
| **用户档** | [`config.user.example.yaml`](../../config.user.example.yaml) | L0 运维根 + L1≤10 结果旋钮（当前 3） |
| **research / 全量** | [`config.yaml.example`](../../config.yaml.example) | 深参、实验旗标、算法细节；对照用 |
| **代码默认** | `AppConfig` | 未写入 yaml 的键走默认；False 防火墙见 Recipe |

## 迁移说明

1. **新用户**：复制 `config.user.example.yaml` → `config.yaml`。  
2. **已有全量 config.yaml**：可继续用；Studio「常用」只暴露 L1（见设置库存）。research 键不必删，但不进用户短文。  
3. **新增用户可见旋钮**：须走 L1 预算替换（≤10），并同步 `happy_path_recipe.L1_RESULT_KEYS` + 键表 md。  
4. **新增实验旗标**：只进 research example / 代码默认 False，禁止净增进用户档。

## 验收对照

- 用户档 example 中显式结果旋钮数 ≤10（当前 3）。  
- `config.yaml.example` 文首指向用户档。  
- Recipe 单测仍锁 Danger 默认 False。
