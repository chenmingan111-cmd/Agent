# ES Query Copilot - 使用指南 (User Guide)

本文档旨在帮助开发者和数据分析师快速掌握 **ES Query Copilot** 的各项功能，通过 API 实现自然语言到 Elasticsearch 查询的转化与安全执行。

---

## 🚀 快速启动

前提：确保服务已通过 Docker 启动 (端口：8080)。

### 1. 访问控制台
打开浏览器访问 Swagger UI：  
👉 [http://localhost:8080/docs](http://localhost:8080/docs)  
（在这里可以直接发送请求进行测试）

---

## 📚 核心功能详解

### 1. 生成查询 (Draft)
**场景**：我不懂 ES 语法，想用人话查数据。

- **接口**：`POST /draft`
- **输入示例**：
  ```json
  {
    "index": "orders-*",
    "nl_query": "统计最近30天每天的销售总额，按时间排序",
    "mode": "preview",
    "user_context": {
      "timezone": "Asia/Shanghai"
    }
  }
  ```
- **输出**：返回生成的 DSL JSON 代码。您可以在业务系统中直接使用，或者发给 `/run` 接口执行。

### 2. 智能校验与修复 (Validate)
**场景**：我自己写的（或 AI 生成的）查询报错了，想自动修好。

- **接口**：`POST /validate`
- **输入示例**：
  ```json
  {
    "index": "orders-*",
    "dsl": {
      "query": { "term": { "title": "iphone" } } 
      // 假设 title 是 text 类型，用 term 查询其实是不对的
    }
  }
  ```
- **输出**：
  - `valid`: false
  - `auto_fixed`: true
  - `fixed_dsl`: corrected JSON (比如自动把 "title" 改为了 "title.keyword")

### 3. 安全执行 (Run)
**场景**：我想直接查数据，但不想把数据库查挂（需要风控）。

- **接口**：`POST /run`
- **功能点**：
  - **自动风控**：如果查询太宽泛（如无时间范围的 wildcard），会被拦截。
  - **深分页优化**：如果翻页超过 10000 条，后端会自动处理，无需担心性能。
- **输入示例**：
  ```json
  {
    "index": "orders-*",
    "dsl": { ... },
    "timeout_ms": 3000
  }
  ```

### 4. 结果解释 (Explain)
**场景**：为什么这条数据被搜出来了？评分是怎么算的？

- **接口**：`POST /explain`
- **输入**：`index`, `doc_id`, `dsl`
- **输出**：返回 Elasticsearch 的底层匹配解释，但经过了 JSON 格式化，更易于程序处理。

---

## ⚙️ 配置说明 (.env)

您可以通过修改项目根目录下的 `.env` 文件来调整行为：

| 变量名 | 默认值 | 说明 |
| :--- | :--- | :--- |
| `ES_URL` | `http://localhost:9200` | ES 地址 (Docker 内请用 host.docker.internal) |
| `LLM_MODEL` | `gpt-4o` | 使用的模型 (如 gpt-3.5-turbo, gpt-4) |
| `MAX_SIZE` | `200` | 单次查询最大返回条数 |
| `ALLOW_PROFILE` | `false` | 是否允许 profile 性能分析 (生产环境建议 false) |

---

## 🛠️ 常见问题 (FAQ)

**Q: 为什么 `/draft` 生成的字段不对？**  
A: 请运行 `python scripts/build_field_catalog.py`。Copilot 依赖于这个脚本生成的 `field_catalog.json` 来认知您的索引结构。

**Q: Docker 里连不上我本机的 ES？**  
A: 请将 `.env` 中的 `ES_URL` 修改为 `http://host.docker.internal:9200`，然后重启容器。

**Q: 支持哪些 ES 版本？**  
A: 完美支持 ES 7.x 和 8.x。
