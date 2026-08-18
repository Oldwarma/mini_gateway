# 智能体迷你网关 — 架构设计方案 (v1)

> 对应 spec：待建（架构确认后按代码区域创建 SPEC-00x）
> 相关 ADR：[ADR-0001](../adr/ADR-0001-tech-stack.md) · [ADR-0002](../adr/ADR-0002-entity-router-code-driven.md) · [ADR-0003](../adr/ADR-0003-composition-boundary.md) · [ADR-0004](../adr/ADR-0004-validation-gate.md) · [ADR-0005](../adr/ADR-0005-knowledge-layer-v1.md)
> 依据：《可追踪的Harness架构.md》（Agent = LLM + Harness）

## 1. 概述

实现《可追踪的Harness架构.md》理念的迷你版智能体网关：

- **Agent = LLM + Harness**：把 LLM 压缩到最小范围，用确定性代码包围它。
- **代码拥有控制层**：实体路由、声明选择、验证、追踪全部由代码完成；LLM 只在组合边界处负责"措辞"。
- **可追踪性**：每个答案可审计——选了哪些声明、走了哪条组合路径、验证结果如何。

## 2. 设计目标与非目标

### 目标（v1）
- 跑通"提问 → 实体路由 → 声明选择 → 合约构建 → 组合边界 → 七维验证门 → 可追踪响应"的**完整 Harness 闭环**。
- 知识层用轻量方式导入声明，支撑运行时演示。
- LLM 可替换（adapter），支持 OpenAI / Anthropic 切换。

### 非目标（v1 不做）
- 完整离线知识管线（自动抓取、LLM 声明抽取、人工审核流）→ 用轻量导入器替代（见 ADR-0005）。
- 多租户、高并发、分布式追踪。
- 监控面板 / 告警（Prometheus/Grafana）→ v1 用日志 + trace 表。
- 复杂 NER / 语义向量检索 → v1 用代码规则 + FTS（见 ADR-0001）。

## 3. 架构总览

三层，对应论文结构（每层精简）：

```
┌──────────────────────────────────────────────────────┐
│ 运行时引擎层 (runtime)                                  │
│                                                        │
│  POST /v1/ask                                          │
│    → 实体路由（代码规则，非 LLM）                        │
│    → 声明选择（SQL + FTS 过滤/排序）                     │
│    → 合约构建（Pydantic schema）                        │
│    → 组合边界（LLM 措辞 / 确定性模板回退）                │
│    → 七维验证门（全部通过才输出）                         │
│    → 响应构建 + 审计追踪                                 │
├──────────────────────────────────────────────────────┤
│ 知识层 (knowledge)                                     │
│  轻量导入器（JSON/YAML → claims store）                 │
│  SQLite 存储抽象（可换 pgvector）                        │
├──────────────────────────────────────────────────────┤
│ 基础设施层 (infra)                                     │
│  trace store（每次请求审计追踪）                         │
│  eval 框架（pytest，固定验证场景，CI 自动跑）             │
│  日志 / 配置（config.yaml：来源、策略、LLM provider）     │
└──────────────────────────────────────────────────────┘
```

## 4. 运行时数据流（一次提问的生命周期）

```
用户 POST /v1/ask {question}
  │
  ① API gateway 接收并校验请求
  ② 实体路由：代码规则 + 正则识别实体 entityId（不交给 LLM）
  ③ 声明选择：按 entityId 过滤 + FTS 相关性排序 → 候选声明列表
  ④ 合约构建：按实体类型生成 AnswerContract 结构（要点/依据/风险）
  ⑤ 组合边界（Composition Boundary）：
       - LLM 路径：声明 + 合约 → LLM 生成自然语言答案
       - 确定性路径：声明填入模板 → 答案（不调 LLM，作为回退）
       - 选择逻辑：默认 LLM，LLM 不可用/超时/无 key 时走模板
  ⑥ 七维验证门：并行检查，全部通过才能输出
  ⑦ 响应构建：组装答案 + 生成审计追踪记录 trace
  │
  └─ 失败处理：LLM 路径验证失败 → 回退模板路径 → 再失败 → 标记异常/熔断
```

## 5. 目录结构（目标代码布局）

```
mini_gateway/
├── src/gateway/
│   ├── main.py                 # FastAPI 入口（uvicorn）
│   ├── api/
│   │   ├── routes.py           # POST /v1/ask, GET /v1/traces/{id}, GET /health
│   │   └── deps.py             # 依赖注入（store / composer / gate）
│   ├── router/
│   │   └── entity_router.py    # 实体路由（代码规则 + 正则，非 LLM）
│   ├── selector/
│   │   └── claim_selector.py   # 声明选择（SQL 过滤 + FTS 排序）
│   ├── contract/
│   │   └── builder.py          # 合约构建（Pydantic AnswerContract）
│   ├── compose/
│   │   ├── boundary.py         # 组合边界：选路 + 回退逻辑
│   │   ├── llm_composer.py     # LLM 措辞（通过 core.llm adapter）
│   │   └── template_composer.py# 确定性模板填充
│   ├── validate/
│   │   └── gate.py             # 七维验证门（并行执行）
│   ├── response/
│   │   └── builder.py          # 响应组装 + trace 落库
│   ├── knowledge/
│   │   ├── ingest.py           # 轻量导入器（JSON/YAML → claims）
│   │   └── store.py            # 存储抽象 + SQLite 实现
│   ├── core/
│   │   ├── schemas.py          # Pydantic 模型（Claim/Evidence/Contract/Trace…）
│   │   ├── trace.py            # 追踪存储（audit trail）
│   │   ├── llm.py              # LLM adapter（OpenAI/Anthropic 可切换）
│   │   └── config.py           # 配置加载（config.yaml）
│   └── exceptions.py           # 领域异常（验证失败、路由失败等）
├── tests/                      # pytest 固定验证场景（对应 AC）
├── data/                       # 示例知识（claims.json 等）
├── config.yaml                 # 来源注册、使用策略、LLM provider
└── docs/                       # 本仓库的文档体系
```

## 6. 核心数据模型（Pydantic + SQLite）

### 6.1 领域模型（core/schemas.py）

| 模型 | 关键字段 | 说明 |
| ---- | -------- | ---- |
| `Entity` | id, name, aliases[], status | 注册实体（对应论文"实体注册列表"） |
| `Source` | id, name, url, type, policy, status | 来源清单（对应论文 Source config） |
| `Evidence` | id, source_id, title, url, content, fingerprint | 证据记录（来源锚定的载体） |
| `Claim` | id, entity_id, statement, source_ref, page, status | 背书声明（来源锚定 + 实体归属） |
| `AnswerContract` | entity, key_points[], basis[], risks[], confidence | 答案结构合约（约束输出格式） |
| `AskRequest` | question | 用户提问 |
| `AskResponse` | answer, contract, trace_id, composition_path | 结构化答案 + 追踪引用 |
| `Trace` | trace_id, question, entity_id, selected_claims[], path, validation[], answer, timestamps | 完整审计追踪 |

### 6.2 存储（SQLite，knowledge/store.py + core/trace.py）

| 表 | 用途 | 对应论文 |
| -- | ---- | -------- |
| `entities` | 注册实体 | 实体注册 |
| `sources` | 来源清单 + 使用策略 | Source config |
| `evidence` | 证据记录 | Evidence Record |
| `claims` | 背书声明 | Claims store |
| `traces` | 每次请求的审计追踪 | Trace store |

> 存储层走抽象接口（`store.py`），v1 实现 SQLite + FTS5；后续可替换 PostgreSQL + pgvector（ADR-0001）。

## 7. 七维验证门（validate/gate.py）

对应论文 Contribution 四。**答案输出给用户之前，必须同时通过全部七项检查**：

| # | 检查维度 | 检查内容 |
| - | -------- | -------- |
| ① | 来源锚定 | 每个声明都有 source_ref + page，可溯源 |
| ② | 实体路由 | 声明归属的 entity 与路由结果一致 |
| ③ | 追踪完整性 | 本次请求的 trace 全链路记录完整 |
| ④ | 输出清洁 | 格式正确、无敏感词、无幻觉性断言 |
| ⑤ | 接口行为 | 组合边界按预期工作（路径选择正确） |
| ⑥ | 延迟 | 响应时间在预算内（如 < 5s） |
| ⑦ | 组合边界行为 | 多声明组合无事实冲突 |

失败处理：任一不通过 → 回退确定性模板路径 → 重新验证 → 仍失败 → 标记异常/熔断（见 §4 流程图）。

## 8. 可追踪性设计（核心）

- 每次请求写一条 `traces` 记录：选中了哪些声明、走了哪条组合路径、每项验证结果、最终答案。
- `GET /v1/traces/{id}` 暴露审计追踪，任何人可复核"这个答案为什么这样说"。
- 与文档体系一致：代码文件首行 `# spec: SPEC-NNN`；commit 带 spec 前缀。

## 9. 配置（config.yaml）

```yaml
sources:                      # 来源注册（对应论文 Source config）
  - id: sec-report
    name: 示例财报
    type: file
    path: data/claims.json
    policy: allowed

llm:
  provider: anthropic         # openai | anthropic | none
  model: claude-haiku-4-5
  api_key_env: ANTHROPIC_API_KEY

gate:
  latency_budget_seconds: 5

composition:
  default: llm                # llm | template
  fallback: template          # LLM 失败时回退
```

## 10. 部署与运行

- 单进程 FastAPI（`uvicorn src.gateway.main:app`），SQLite 文件本地存储。
- 示例知识：`python -m src.gateway.knowledge.ingest --input data/claims.json` 导入。
- 无 LLM key 也能运行（走确定性模板路径），方便先验证 Harness 闭环。

## 11. 演进路径（v2+）

| 维度 | v1 | 演进 |
| ---- | -- | ---- |
| 存储 | SQLite + FTS5 | PostgreSQL + pgvector（语义检索） |
| 知识层 | 轻量导入器 | 完整离线管线（fetch → 抽取 → promotion gate） |
| 观测 | 日志 + trace 表 | Prometheus / Grafana |
| 模型 | adapter 单实例 | 多模型切换 / 模型路由 |
| NER | 代码规则 + 正则 | 轻量 NER 模型（论文选型） |
