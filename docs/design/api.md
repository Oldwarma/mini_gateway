# 智能体迷你网关 — API 接口文档 (v1)

> 对应 spec：待建
> 上层文档：[detailed-design.md](detailed-design.md) §4.1 · [architecture.md](architecture.md)
> 运行时：FastAPI 自动生成 OpenAPI（`/openapi.json`）与 Swagger UI（`/docs`），本文档为人工审核版。

## 1. 总览

- Base URL：`http://localhost:8000`
- 请求 / 响应均 `Content-Type: application/json`（UTF-8）
- 所有响应携带 `X-Trace-Id` 响应头（= trace_id，审计追溯的钥匙）
- 时间字段为 ISO 8601（UTC）

| 方法 | 路径 | 说明 |
| ---- | ---- | ---- |
| POST | `/v1/ask` | 提交提问，返回结构化答案 + 追踪引用 |
| GET | `/v1/traces/{trace_id}` | 查询一次请求的完整审计追踪 |
| GET | `/health` | 健康检查 |
| GET | `/docs` | Swagger UI（FastAPI 自动生成） |
| GET | `/openapi.json` | OpenAPI 规范 |

---

## 2. POST /v1/ask

提交一次提问，走完整 Harness 闭环（实体路由 → 声明选择 → 组合边界 → 验证门 → 追踪）。

### 请求体

```json
{
  "question": "三星2024年营收是多少"
}
```

| 字段 | 类型 | 必填 | 约束 |
| ---- | ---- | ---- | ---- |
| question | string | ✅ | 1 ~ 500 字符，去除首尾空白后非空 |

### 成功响应 `200 OK`

```json
{
  "answer": "三星电子2024年合并营收为300.9万亿韩元（依据：2024年报 p12）。",
  "contract": {
    "entity": "samsung",
    "key_points": ["三星2024年合并营收300.9万亿韩元"],
    "basis": ["c-0001"],
    "risks": [],
    "confidence": 0.9
  },
  "trace_id": "tr-8f3a1b2c",
  "composition_path": "llm"
}
```

| 字段 | 类型 | 说明 |
| ---- | ---- | ---- |
| answer | string | 自然语言答案（LLM 措辞或模板生成） |
| contract | object | 答案合约（`AnswerContract`，约束输出结构） |
| contract.entity | string | 路由到的实体 id；无法识别时为 `null` 语义（见分支） |
| contract.basis | string[] | 依据声明 claim_id 列表（可追溯的关键） |
| contract.confidence | number | 0~1，依据声明数与来源数加权 |
| trace_id | string | 本次请求审计追踪 ID（审计入口） |
| composition_path | string | `llm` 或 `template`（走的哪条组合路径） |

### 业务分支（均为 `200 OK`，语义由字段区分）

| 分支 | 表现 |
| ---- | ---- |
| 实体无法识别 | `answer` = "无法识别问题指向的实体，请补充公司名称。"；`contract.entity` = 空、`confidence` = 0；`composition_path` = `template` |
| LLM 回退 | 无 API key / LLM 超时 / LLM 答案验证失败 → 自动走确定性模板；`composition_path` = `template` |
| 声明为空 | 实体命中但无可用声明 → 模板路径给出"暂无可引用数据"式回答 |

### 错误响应

| 状态码 | 场景 | 响应体示例 |
| ------ | ---- | ---------- |
| `422` | question 缺失 / 空 / 超长 | Pydantic 校验详情（`detail[].loc` / `msg`） |
| `500` | 验证门双路径均失败（熔断） | `{"detail": "gate_rejected", "trace_id": "tr-..."}` |
| `500` | 存储层故障 | `{"detail": "internal_error"}` |

> 熔断时 `trace_id` 仍返回，供事后审计验证门为何全部拒绝。

---

## 3. GET /v1/traces/{trace_id}

查询一次提问的完整审计追踪——**"这个答案为什么这样说"的证据链**。

### 路径参数

| 参数 | 类型 | 说明 |
| ---- | ---- | ---- |
| trace_id | string | 来自 `/v1/ask` 响应的 `trace_id` |

### 成功响应 `200 OK`

```json
{
  "trace_id": "tr-8f3a1b2c",
  "request_id": "req-01",
  "question": "三星2024年营收是多少",
  "entity_id": "samsung",
  "selected_claims": ["c-0001"],
  "composition_path": "llm",
  "validation": {
    "source_anchored": true,
    "entity_match": true,
    "trace_complete": true,
    "output_clean": true,
    "interface": true,
    "latency": true,
    "composition": true
  },
  "answer": "三星电子2024年合并营收为300.9万亿韩元。",
  "created_at": "2026-08-18T08:12:30Z"
}
```

### 错误响应

| 状态码 | 场景 | 响应体 |
| ------ | ---- | ------ |
| `404` | trace_id 不存在 | `{"detail": "trace not found"}` |

---

## 4. GET /health

健康检查（探活 / 部署用）。

### 成功响应 `200 OK`

```json
{
  "status": "ok",
  "db": true,
  "llm_configured": false
}
```

| 字段 | 类型 | 说明 |
| ---- | ---- | ---- |
| status | string | `ok`（进程存活） |
| db | bool | 存储连接 / 表初始化是否正常 |
| llm_configured | bool | 是否配置了 LLM provider；`false` 表示 `/v1/ask` 将走模板路径 |

---

## 5. 审计一致性约定

- **追溯链**：`trace_id`（响应头 + 响应体）→ `GET /v1/traces/{trace_id}` → `selected_claims[]` → `claims.source_ref` → `evidence` → 原始来源 URL / 页码。任一答案都能走到原始证据。
- **不可变**：`traces` 表只写不删改；审计以它为准。
- **X-Trace-Id**：所有端点响应头返回 trace_id（`/health` 返回空），便于调用方串联日志。

## 6. 错误处理通用约定

- 错误响应体统一为 FastAPI 默认 `{"detail": ...}` 结构。
- 未列出的 5xx 一律 `{"detail": "internal_error"}`，细节只进服务端日志（含 trace_id，便于对账）。
