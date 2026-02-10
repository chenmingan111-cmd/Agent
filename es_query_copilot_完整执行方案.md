# ES Query Copilot（自然语言 → Elasticsearch DSL）完整执行方案
> 版本：v1.0  
> 日期：2026-02-10  
> 目标读者：你 + 任何代码生成 AI（GPT/Claude/Cursor 等）  
> 使用方式：把本文档整段喂给 AI，让它按步骤生成代码并执行

---

## 0. 一句话目标

构建一个 **可上线的 ES Query Copilot**：  
用户输入自然语言，系统输出：

1. 可执行 Elasticsearch Query DSL  
2. 可读解释（为什么这样写）  
3. 风险等级（低/中/高）  
4. 通过校验后的一键执行结果

---

## 1. 交付范围（MVP）

### 1.1 必须实现
- `POST /draft`：NL → DSL（只生成，不执行） 
- `POST /validate`：校验 DSL + 自动修复（最多 2 轮）
- `POST /run`：执行查询（仅允许通过校验的 DSL）
- `POST /explain`：解释单条文档为何命中/不命中
- `field_catalog`：字段白名单（来自 mapping + field caps）
- 风险评分与阻断策略
- 30 条回归样例 + 自动化测试

### 1.2 暂不实现（v2）
- 多租户复杂权限体系
- 自动在线学习（只留人工反馈）
- 可视化拖拽式查询构建器

---

## 2. 技术选型（固定）

- **语言**：Python 3.11+
- **后端**：FastAPI + Uvicorn
- **ES 客户端**：elasticsearch-py（8.x）
- **模型调用**：可替换（OpenAI/Anthropic/本地模型）
- **测试**：pytest
- **部署**：Docker Compose（MVP）
- **前端**：简易单页（可先不做，Postman/Swagger 先跑通）

---

## 3. 成功标准（DoD）

- 首次 DSL 校验通过率 ≥ 85%
- 自动修复后二次通过率 ≥ 95%
- 高风险查询阻断率 = 100%
- 非 profile 模式下，P95 响应时间 < 2.5s
- 回归集（30 条）通过率 ≥ 90%

---

## 4. 项目结构（让 AI 严格按此生成）

```text
es-query-copilot/
  app/
    main.py
    api/
      draft.py
      validate.py
      run.py
      explain.py
      health.py
    core/
      config.py
      schema.py
      prompt.py
      risk.py
      fixer.py
      field_catalog.py
      errors.py
    services/
      es_client.py
      llm_client.py
      pipeline.py
    models/
      dto.py
  scripts/
    build_field_catalog.py
    seed_eval_set.py
  tests/
    test_draft.py
    test_validate.py
    test_run.py
    test_guardrails.py
  data/
    field_catalog.json
    eval_queries.json
  .env.example
  requirements.txt
  docker-compose.yml
  README.md
```

---

## 5. 环境变量（.env）

```bash
APP_ENV=dev
APP_PORT=8080

ES_URL=http://localhost:9200
ES_USER=elastic
ES_PASSWORD=changeme
ES_DEFAULT_INDEX=orders-*

LLM_PROVIDER=openai
LLM_MODEL=gpt-5-mini
LLM_API_KEY=your_key

MAX_VALIDATE_RETRY=2
MAX_SIZE=200
MAX_FROM_SIZE=10000
DEFAULT_TIMEOUT_MS=2000
ALLOW_PROFILE=false
```

---

## 6. 依赖（requirements.txt）

```txt
fastapi==0.115.0
uvicorn[standard]==0.30.6
pydantic==2.9.2
python-dotenv==1.0.1
elasticsearch==8.15.1
httpx==0.27.2
tenacity==9.0.0
pytest==8.3.3
pytest-asyncio==0.24.0
```

---

## 7. API 合约（必须一字不差支持）

## 7.1 POST /draft
### Request
```json
{
  "index": "orders-*",
  "nl_query": "最近7天失败订单，按国家聚合前10",
  "mode": "preview",
  "user_context": {
    "timezone": "Asia/Singapore"
  }
}
```

### Response
```json
{
  "dsl": {
    "size": 0,
    "query": {
      "bool": {
        "filter": [
          {"range": {"@timestamp": {"gte": "now-7d/d", "lte": "now"}}},
          {"term": {"status.keyword": "failed"}}
        ]
      }
    },
    "aggs": {
      "by_country": {
        "terms": {"field": "country.keyword", "size": 10}
      }
    }
  },
  "explanation": [
    "时间范围映射为 @timestamp 的 range 过滤",
    "失败状态使用 keyword 字段进行精确匹配",
    "国家聚合使用 terms 聚合并限制前10"
  ],
  "risk": {
    "level": "low",
    "reasons": []
  },
  "confidence": 0.92
}
```

## 7.2 POST /validate
### Request
```json
{
  "index": "orders-*",
  "dsl": {
    "query": {"match": {"title": "payment failed"}}
  }
}
```

### Response
```json
{
  "valid": true,
  "errors": [],
  "auto_fixed": false,
  "fixed_dsl": null,
  "warnings": []
}
```

## 7.3 POST /run
### Request
```json
{
  "index": "orders-*",
  "dsl": {
    "size": 20,
    "query": {
      "bool": {
        "filter": [{"term": {"status.keyword": "failed"}}]
      }
    },
    "sort": [{"@timestamp": "desc"}]
  },
  "timeout_ms": 2000
}
```

### Response
```json
{
  "took": 31,
  "timed_out": false,
  "hits": {
    "total": 124,
    "items": []
  },
  "aggs": {},
  "warnings": []
}
```

## 7.4 POST /explain
### Request
```json
{
  "index": "orders-*",
  "doc_id": "A1B2C3",
  "dsl": {
    "query": {"term": {"status.keyword": "failed"}}
  }
}
```

### Response
```json
{
  "matched": true,
  "explanation": {
    "value": 1.0,
    "description": "weight(status.keyword:failed in 0)"
  }
}
```

---

## 8. 关键数据模型（Pydantic）

```python
class DraftRequest(BaseModel):
    index: str
    nl_query: str
    mode: Literal["preview", "execute"] = "preview"
    user_context: dict = {}

class DraftResponse(BaseModel):
    dsl: dict
    explanation: list[str]
    risk: dict
    confidence: float

class ValidateRequest(BaseModel):
    index: str
    dsl: dict

class ValidateResponse(BaseModel):
    valid: bool
    errors: list[str] = []
    auto_fixed: bool = False
    fixed_dsl: dict | None = None
    warnings: list[str] = []
```

---

## 9. 生成流程（核心 Pipeline）

```mermaid
flowchart TD
A[用户自然语言] --> B[/draft: LLM 生成 DSL]
B --> C[字段白名单校验]
C --> D[/validate: ES validate query]
D -->|失败| E[auto-fix 修复]
E --> D
D -->|成功| F[风险评分]
F -->|高风险| G[阻断/要求确认]
F -->|低中风险| H[/run: ES search]
H --> I[返回结果 + 可读解释]
```

---

## 10. 字段目录构建（field_catalog）

## 10.1 目的
防止 LLM 随意使用不存在字段或错误字段类型（text vs keyword）。

## 10.2 每日构建脚本逻辑
1. 调用 mapping 拉字段
2. 调用 field capabilities 拉 searchable / aggregatable
3. 输出 `data/field_catalog.json`

## 10.3 结构示例
```json
{
  "orders-*": {
    "status.keyword": {"type": "keyword", "searchable": true, "aggregatable": true},
    "status": {"type": "text", "searchable": true, "aggregatable": false},
    "@timestamp": {"type": "date", "searchable": true, "aggregatable": true},
    "amount": {"type": "double", "searchable": true, "aggregatable": true}
  }
}
```

---

## 11. Prompt 设计（可直接给代码生成 AI）

## 11.1 System Prompt（DSL 生成）
```text
你是 Elasticsearch Query DSL 专家。你的任务是把用户自然语言查询转换为可执行 DSL。
硬性规则：
1) 仅输出 JSON，不要 Markdown。
2) 仅可使用 field_catalog 中存在的字段。
3) 过滤优先使用 bool.filter，精确匹配优先 keyword 字段。
4) 需要聚合时优先 terms/date_histogram。
5) 默认加 size 上限（<=200）和合理 sort。
6) 避免 query_string；除非用户明确要求语法搜索。
7) 时间范围缺失时，不自动猜测超大范围；默认最近7天（可配置）。
8) 不要使用昂贵/危险特性（如无限 wildcard、无边界脚本）。
输出格式：
{
  "dsl": {...},
  "explanation": ["..."],
  "confidence": 0.0~1.0
}
```

## 11.2 Repair Prompt（自动修复）
```text
你是 DSL 修复器。已知 validate 错误信息和原始 DSL。
请在尽量保持语义不变的情况下修复 DSL，优先：
- text 字段用于 term/聚合时改为对应 keyword 字段
- 日期格式和 range 边界修正
- size/from 超限修正
- 删除无效字段
只返回修复后的 JSON DSL。
```

---

## 12. 校验与自动修复策略（最多 2 轮）

## 12.1 校验步骤
- Step A：本地 JSON Schema 校验（结构正确）
- Step B：字段白名单 + 类型规则校验
- Step C：调用 ES validate API
- Step D：失败则调用 repair prompt 修复，再走 A~C
- Step E：超过 2 轮仍失败 -> 返回人类可读错误

## 12.2 常见自动修复规则
- `term` 用在 `text` 字段 -> 换 `.keyword`
- `terms agg` 用在不可聚合字段 -> 换可聚合字段或报错
- `size > MAX_SIZE` -> 截断
- `from + size > MAX_FROM_SIZE` -> 切 `search_after`

---

## 13. 风险评分（阻断策略）

## 13.1 评分因子（示例）
- wildcard 前缀匹配：+40
- query_string：+25
- script 查询：+40
- size > 200：+20
- 未加时间范围且索引为日志类：+20
- 聚合层级 > 3：+15

## 13.2 等级
- 0~29：low（直接执行）
- 30~59：medium（执行但提示）
- 60+：high（阻断，需用户确认或改写）

---

## 14. 深分页策略（必须实现）

- 当 `from + size <= 10000`：允许普通分页
- 当 `from + size > 10000`：自动切换 `PIT + search_after`
- `scroll` 仅用于导出场景，不用于交互式分页

---

## 15. 核心业务函数（伪代码）

```python
def draft_dsl(index: str, nl_query: str, catalog: dict) -> dict:
    # 1) 调 LLM 按 system prompt 生成
    # 2) 解析 JSON
    # 3) 结构化检查
    return result

def validate_and_fix(index: str, dsl: dict, max_retry: int = 2):
    for i in range(max_retry + 1):
        local_ok, local_errors = local_validate(dsl)
        if not local_ok:
            dsl = local_fix(dsl, local_errors)
            continue

        es_ok, es_errors = es_validate(index, dsl)
        if es_ok:
            return True, dsl, []
        if i < max_retry:
            dsl = llm_repair(dsl, es_errors)
        else:
            return False, dsl, es_errors

def run_query(index: str, dsl: dict, timeout_ms: int):
    risk = score_risk(dsl)
    if risk["level"] == "high":
        raise HighRiskBlockedError(risk)

    dsl = enforce_limits(dsl)
    return es_search(index, dsl, timeout_ms=timeout_ms)
```

---

## 16. 测试计划（30 条回归）

## 16.1 `data/eval_queries.json` 格式
```json
[
  {
    "nl_query": "最近7天失败订单按国家前10",
    "index": "orders-*",
    "must_contain": ["range", "status.keyword", "terms"],
    "must_not_contain": ["query_string"]
  }
]
```

## 16.2 测试类型
- 单元测试：风险评分、字段校验、修复器
- 集成测试：draft→validate→run 全链路
- 回归测试：30 条样例持续跑

---

## 17. 观测与审计（必须）

- 每次请求记录：
  - request_id
  - 原始 nl_query
  - 生成 dsl
  - validate 错误
  - auto-fix 前后 diff
  - 风险分
  - 执行耗时 / 是否超时
- 错误分级：
  - 用户错误（输入不可解析）
  - 系统错误（LLM/ES 不可用）
  - 风险阻断（策略拒绝）

---

## 18. 安全与权限（MVP 必备）

- 索引白名单（禁止任意 index）
- 字段白名单（禁止越权字段）
- profile 模式仅 admin
- 限流（每用户每分钟上限）
- 敏感字段脱敏（返回前处理）

---

## 19. 3天执行排期（真正可落地）

## Day 1
- 初始化项目与依赖
- 完成 `field_catalog` 脚本
- 完成 `/draft`（固定 prompt + JSON 输出）
- 写 10 条 smoke 测试

## Day 2
- 完成 `/validate` + auto-fix
- 完成 `/run` + 风险评分
- 接入日志审计
- 补到 20 条回归样例

## Day 3
- 完成 `/explain`
- 完成深分页切换策略
- 补齐 30 条回归
- Docker 化 + README + 一键启动

---

## 20. 一键启动命令（本地）

```bash
# 1) 安装依赖
python -m venv .venv
source .venv/bin/activate  # Windows 用 .venv\Scripts\activate
pip install -r requirements.txt

# 2) 配置环境变量
cp .env.example .env
# 修改 ES_URL/ES_USER/ES_PASSWORD/LLM_API_KEY

# 3) 生成字段目录
python scripts/build_field_catalog.py --index "orders-*"

# 4) 启动服务
uvicorn app.main:app --host 0.0.0.0 --port 8080 --reload

# 5) 运行测试
pytest -q
```

---

## 21. 给“代码生成 AI”的最终指令（可直接复制）

```text
你现在是资深后端工程师。请根据我给你的《ES Query Copilot 完整执行方案》生成一个可运行项目。
硬性要求：
1) 使用 Python + FastAPI，按文档中的目录结构创建完整代码。
2) 实现 /draft /validate /run /explain /health 五个接口。
3) 实现 field_catalog 构建脚本（mapping + field caps）。
4) validate 失败后自动修复最多 2 轮。
5) 实现风险评分与高风险阻断。
6) 实现 from+size 超限时自动切 PIT+search_after。
7) 输出 requirements.txt、.env.example、docker-compose.yml、README.md。
8) 编写 pytest，至少 30 条回归样例（可先给示例数据）。
9) 任何函数都要加类型注解和必要异常处理。
10) 先给出完整文件树，再按文件逐个输出代码，不要省略。
```

---

## 22. 验收清单（你对 AI 结果打勾）

- [ ] 项目可 `uvicorn` 启动
- [ ] Swagger 可调用四大接口
- [ ] 不存在字段会被拦截/修复
- [ ] 高风险查询会阻断
- [ ] 30 条回归样例可执行
- [ ] README 说明可让新人 30 分钟跑通

---

## 23. 常见故障与修复

1. **LLM 输出非 JSON**  
   - 修复：加 JSON schema 校验 + 重试一次 + 截断非 JSON 前后缀

2. **text 字段做 terms 聚合报错**  
   - 修复：改用 `.keyword`（若不存在则返回可读错误）

3. **深分页报错或性能差**  
   - 修复：自动切换 `PIT + search_after`

4. **查询超时**  
   - 修复：缩小时间范围、减少聚合层级、降低 size、加 filter

---

## 24. 下一步（v1.1）

- 加入“建议改写”按钮（例如：把 `query_string` 改写为 bool/filter）
- 增加“保存查询模板”
- 增加“业务词典/同义词”支持
- 增加 A/B prompt 评测与自动回归报告

---

如果你已经把这份文档喂给 AI，但生成质量不稳定，下一步就把 AI 产出的代码贴给我，我会按模块帮你做“逐文件纠偏”。
