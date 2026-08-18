# 智能体迷你网关 — 详细设计 (v1)

> 对应 spec：待建（开发前按代码区域建 SPEC-00x）
> 上层文档：[architecture.md](architecture.md)（概要架构）· 相关 ADR：[ADR-0001](../adr/ADR-0001-tech-stack.md) ~ [ADR-0005](../adr/ADR-0005-knowledge-layer-v1.md)
> 本文档把架构落地到：模块接口 / 数据结构 / DDL / 流程时序 / 异常 / 测试场景。

---

## 1. 模块接口总览

| 模块 | 文件 | 对外接口 | 职责 |
| ---- | ---- | -------- | ---- |
| api | `api/routes.py` | HTTP 路由 | 接收提问、暴露追踪查询 |
| router | `router/entity_router.py` | `route(question) -> RouterResult` | 实体路由（代码规则） |
| selector | `selector/claim_selector.py` | `select(entity_id, question, limit) -> list[Claim]` | 声明选择 |
| contract | `contract/builder.py` | `build(entity) -> AnswerContract` | 合约构建 |
| compose | `compose/boundary.py` | `compose(contract, claims) -> ComposeResult` | 组合边界（选路+回退） |
| validate | `validate/gate.py` | `run(ctx) -> ValidationReport` | 七维验证门 |
| response | `response/builder.py` | `build(...) -> AskResponse` | 响应组装 + 写 trace |
| knowledge | `knowledge/ingest.py` | `ingest(path) -> IngestReport` | 轻量导入 |
| knowledge | `knowledge/store.py` | `ClaimStore` 抽象 + SQLite 实现 | 存储 |
| core | `core/trace.py` | `TraceStore` | 追踪存储 |
| core | `core/llm.py` | `LLMProvider` protocol | LLM adapter |
| core | `core/config.py` | `load_config() -> Config` | 配置 |

依赖方向：`api → boundary → {selector, contract, validate} → store/trace/llm`（自顶向下，无循环依赖）。

---

## 2. 领域模型详细定义（core/schemas.py）

```python
from pydantic import BaseModel, Field
from typing import Optional

class Entity(BaseModel):
    id: str                                  # "samsung"
    name: str                                # "三星电子"
    aliases: list[str] = []                  # ["Samsung", "삼성"]
    status: str = "active"                   # active | inactive

class Source(BaseModel):
    id: str
    name: str
    url: Optional[str] = None
    type: str = "file"                       # file | api | web
    policy: str = "allowed"                  # allowed | review
    status: str = "active"

class Evidence(BaseModel):
    id: str                                  # "ev-0001"
    source_id: str
    title: str
    url: Optional[str] = None
    content: str
    fingerprint: str = ""                    # 内容哈希（防篡改标识）

class Claim(BaseModel):
    claim_id: str                            # "c-0001"
    entity_id: str                           # 锚① 实体归属
    statement: str                           # "三星2024年合并营收300.9万亿韩元"
    source_ref: str                          # 锚② "ev-0001#p12"（evidence_id + 定位）
    page: Optional[str] = None
    status: str = "approved"                 # approved | draft | deprecated

class AnswerContract(BaseModel):
    entity: str                              # 路由到的实体
    key_points: list[str] = []               # 关键要点（必答）
    basis: list[str] = []                    # 依据声明引用（claim_id）
    risks: list[str] = []                    # 风险/不确定项
    confidence: float = Field(0.0, ge=0, le=1)

class AskRequest(BaseModel):
    question: str = Field(min_length=1, max_length=500)

class AskResponse(BaseModel):
    answer: str
    contract: AnswerContract
    trace_id: str
    composition_path: str                    # "llm" | "template"

class Trace(BaseModel):
    trace_id: str
    request_id: str
    question: str
    entity_id: Optional[str] = None
    selected_claims: list[str] = []          # claim_id 列表
    composition_path: Optional[str] = None   # llm | template
    validation: dict = {}                    # 七维验证报告
    answer: Optional[str] = None
    created_at: str
```

---

## 3. 数据模型（SQLite DDL）

```sql
-- 实体注册表（ADR-0002：实体路由的依据）
CREATE TABLE IF NOT EXISTS entities (
    id       TEXT PRIMARY KEY,
    name     TEXT NOT NULL,
    aliases  TEXT NOT NULL DEFAULT '[]',     -- JSON array
    status   TEXT NOT NULL DEFAULT 'active'
);

-- 来源清单（对应论文 Source config）
CREATE TABLE IF NOT EXISTS sources (
    id     TEXT PRIMARY KEY,
    name   TEXT NOT NULL,
    url    TEXT,
    type   TEXT NOT NULL DEFAULT 'file',
    policy TEXT NOT NULL DEFAULT 'allowed',
    status TEXT NOT NULL DEFAULT 'active'
);

-- 证据记录（来源锚定的载体）
CREATE TABLE IF NOT EXISTS evidence (
    id          TEXT PRIMARY KEY,
    source_id   TEXT NOT NULL REFERENCES sources(id),
    title       TEXT NOT NULL,
    url         TEXT,
    content     TEXT NOT NULL,
    fingerprint TEXT NOT NULL DEFAULT ''
);

-- 背书声明（Claims store）
CREATE TABLE IF NOT EXISTS claims (
    claim_id   TEXT PRIMARY KEY,
    entity_id  TEXT NOT NULL REFERENCES entities(id),
    statement  TEXT NOT NULL,
    source_ref TEXT NOT NULL,
    page       TEXT,
    status     TEXT NOT NULL DEFAULT 'approved',
    created_at TEXT NOT NULL DEFAULT (datetime('now'))
);

-- 全文索引（FTS5，ADR-0001）
CREATE VIRTUAL TABLE IF NOT EXISTS claims_fts USING fts5(
    entity_id, statement, content='claims', content_rowid='rowid'
);
```

同步策略：`claims` 表用 trigger 把新行同步进 `claims_fts`；查询走 FTS5 的 `rank` 排序。

追踪表（core/trace.py，每次请求一条）：

```sql
CREATE TABLE IF NOT EXISTS traces (
    trace_id         TEXT PRIMARY KEY,
    request_id       TEXT NOT NULL,
    question         TEXT NOT NULL,
    entity_id        TEXT,
    selected_claims  TEXT NOT NULL DEFAULT '[]',   -- JSON array of claim_id
    composition_path TEXT,                          -- llm | template
    validation       TEXT NOT NULL DEFAULT '{}',    -- JSON 七维报告
    answer           TEXT,
    created_at       TEXT NOT NULL DEFAULT (datetime('now'))
);
```

---

## 4. 各模块详细设计

### 4.1 api/routes.py

```python
# POST /v1/ask
# request : {"question": "三星2024年营收多少？"}
# 200     : {"answer","contract","trace_id","composition_path"}
# 422     : 请求校验失败（空问题/超长）
# 500     : 验证门全部失败（熔断）→ {"detail": "gate_rejected", "trace_id"}
@app.post("/v1/ask")
async def ask(req: AskRequest) -> AskResponse: ...

# GET /v1/traces/{trace_id}
# 200 : Trace | 404 : 不存在
@app.get("/v1/traces/{trace_id}")
async def get_trace(trace_id: str) -> Trace: ...

# GET /health -> {"status": "ok", "db": true, "llm_configured": bool}
```

### 4.2 router/entity_router.py（ADR-0002）

```python
@dataclass
class RouterResult:
    entity_id: Optional[str]
    matched_rule: Optional[str]      # 命中哪条规则，可追溯
    confidence: float                # 1.0 精确 / 0.8 别名 / 0.6 正则

def route(question: str, entities: list[Entity]) -> RouterResult:
    # 三层规则，逐级放宽：
    #  1) 实体全名精确匹配（大小写不敏感）
    #  2) 别名列表匹配（entities.aliases）
    #  3) 正则模式匹配（如 r"三星.{0,4}(2024|营收)"）
    # 全部未命中 → RouterResult(None, None, 0.0)
```

可追踪：`matched_rule` 与 `confidence` 记入 trace。

### 4.3 selector/claim_selector.py

```python
def select(entity_id: str, question: str, limit: int = 3) -> list[Claim]:
    # 1) 实体过滤（硬约束）：WHERE entity_id = ?
    # 2) 相关性排序：把 question 拆词 → FTS5 MATCH statement → ORDER BY rank
    # 3) 无 FTS 命中时回退为 status='approved' 按创建序取 N 条
    # 4) 仅返回 status='approved' 的声明
```

### 4.4 contract/builder.py

```python
def build(entity_id: str, claims: list[Claim]) -> AnswerContract:
    # 按实体类型选择合约模板（v1 通用模板）：
    #   key_points ← 声明的要点骨架（statement 截取）
    #   basis     ← [c.claim_id for c in claims]   # 依据声明
    #   confidence ← 声明数与来源数加权
```

### 4.5 compose/boundary.py（ADR-0003）

```python
@dataclass
class ComposeResult:
    answer: str
    path: str                    # "llm" | "template"
    llm_attempted: bool = False

def compose(contract: AnswerContract, claims: list[Claim],
            gate: ValidationGate, cfg: Config) -> ComposeResult:
    if not claims:                        # 无声明 → 直接走模板兜底/拒绝
        return _template(contract, claims)

    # 主路径：LLM 措辞 → 验证
    if cfg.composition.default == "llm":
        answer = llm_composer.compose(contract, claims)
        if _gate_pass(gate, path="llm", answer=answer):
            return ComposeResult(answer, "llm", llm_attempted=True)

    # 回退：确定性模板 → 验证
    answer = template_composer.compose(contract, claims)
    if _gate_pass(gate, path="template", answer=answer):
        return ComposeResult(answer, "template", llm_attempted=True)

    raise GateRejectedError()             # 两条路径都不过 → 熔断（api 层 → 500）
```

### 4.6 compose/llm_composer.py

```python
def compose(contract, claims, provider: LLMProvider) -> str:
    prompt = f"""
你是答案措辞引擎，只负责把下面的声明组织成自然语言答案。
不得引入声明之外的事实，不得做判断。

【声明依据】
{_format_claims(claims)}

【答案合约】
{contract.model_dump_json(indent=2)}

请输出符合合约结构的自然语言答案。
"""
    return provider.complete(prompt)
```

### 4.7 compose/template_composer.py

```python
def compose(contract, claims) -> str:
    # 确定性模板（不调 LLM）：
    #   "关于 {entity} 的要点：\n" + "- {statement}（来源：{source_ref}）..."
    #   无自由发挥，仅原样呈现声明
```

### 4.8 validate/gate.py（ADR-0004）

```python
@dataclass
class ValidationContext:
    question: str
    entity_id: Optional[str]
    claims: list[Claim]
    answer: str
    path: str
    trace: Trace

@dataclass
class ValidationReport:
    results: dict[str, bool]   # check 名 → 通过?
    all_pass: bool

def run(ctx: ValidationContext, store: ClaimStore) -> ValidationReport:
    checks = [
        check_source_anchored,   # ① 每 claim 有 source_ref 且 evidence 存在
        check_entity_match,      # ② claim.entity_id == ctx.entity_id
        check_trace_complete,    # ③ trace 字段齐全（question/claims/path）
        check_output_clean,      # ④ 敏感词/空答案/越界断言
        check_interface,         # ⑤ path 与 llm_attempted 一致性
        check_latency,           # ⑥ 全程耗时 < config.gate.latency_budget
        check_composition,       # ⑦ 组合声明无事实冲突（同实体矛盾语句）
    ]
    # 并行执行（asyncio.gather 或线程池），逐项记入 results
```

### 4.9 response/builder.py

```python
def build(req: AskRequest, result: ComposeResult,
          report: ValidationReport, selected: list[Claim],
          trace_store: TraceStore) -> AskResponse:
    # 组装 AskResponse + 生成 trace_id
    # 把 {selected_claims, composition_path, validation} 写入 traces 表
    # 返回 response（answer, contract, trace_id, path）
```

### 4.10 knowledge/ingest.py（ADR-0005）

```python
@dataclass
class IngestReport:
    sources: int; evidence: int; claims: int
    rejected: list[str]        # 被拒声明及原因

def ingest(path: str, store: ClaimStore) -> IngestReport:
    # 读取 JSON/YAML：
    #   1) 写入/更新 sources, evidence
    #   2) 逐条 claim 校验（promotion 轻量版）：
    #      - source_ref 指向的 evidence 必须存在        → 否则拒绝
    #      - entity_id 必须存在于 entities 注册表       → 否则拒绝
    #      - statement 非空、长度 <= 200               → 否则拒绝
    #      - 通过 → status='approved' 写入 claims
    #   rejected 收集所有拒绝原因，报告给用户
```

### 4.11 knowledge/store.py

```python
class ClaimStore(Protocol):        # 存储抽象（ADR-0001，可换 pgvector）
    def upsert_entity(self, e: Entity) -> None: ...
    def upsert_source(self, s: Source) -> None: ...
    def upsert_evidence(self, ev: Evidence) -> None: ...
    def upsert_claim(self, c: Claim) -> None: ...
    def list_entities(self) -> list[Entity]: ...
    def get_evidence(self, evidence_id: str) -> Optional[Evidence]: ...
    def query_claims(self, entity_id: str, question: str, limit: int) -> list[Claim]: ...

class SqliteClaimStore(ClaimStore):   # v1 实现
    # 内部：sqlite3 连接 + DDL（§3）+ claims_fts 同步 trigger
    # query_claims: SELECT ... WHERE entity_id=? AND rowid IN
    #               (SELECT rowid FROM claims_fts WHERE claims_fts MATCH ?) ORDER BY rank LIMIT ?
```

### 4.12 core/trace.py

```python
class TraceStore:
    def create(self, trace: Trace) -> None: ...
    def get(self, trace_id: str) -> Optional[Trace]: ...
    # 每次请求 main 流程调用一次 create（post-hoc 一次写入）
```

### 4.13 core/llm.py

```python
class LLMProvider(Protocol):
    def complete(self, prompt: str, model: str | None = None) -> str: ...

class AnthropicProvider(LLMProvider): ...   # env ANTHROPIC_API_KEY
class OpenAIProvider(LLMProvider): ...      # env OPENAI_API_KEY
class NullProvider(LLMProvider):            # 无 key 时抛出 → 触发模板回退
    def complete(self, prompt, model=None): raise NoLLMConfiguredError()
```

Provider 由 `core/config.py` 根据 `config.yaml` 的 `llm.provider` 注入。

### 4.14 core/config.py

```python
@dataclass
class LLMConfig:    provider: str; model: str; api_key_env: str
@dataclass
class GateConfig:   latency_budget_seconds: float
@dataclass
class CompositionConfig: default: str; fallback: str
@dataclass
class Config:
    llm: LLMConfig
    gate: GateConfig
    composition: CompositionConfig
    sources: list[Source]

def load_config(path: str = "config.yaml") -> Config: ...
```

---

## 5. 关键流程时序

### 5.1 主流程（一次提问）

```
client → routes.ask
  → trace_store 初始化 Trace(trace_id=uuid)
  → router.route(question) → entity_id
  → selector.select(entity_id, question) → claims
  → contract.build(entity_id, claims) → contract
  → boundary.compose(contract, claims) → ComposeResult
      ├─ LLM 路径（default=llm）→ provider.complete → answer
      └─ 验证门 run(ctx) → 通过 → path=llm
  → response.build → AskResponse + 写 traces 表
  → 200 返回
```

### 5.2 回退（LLM 失败 / 无 key / 验证不过）

```
compose:
  LLM 路径 → NullProvider 抛 NoLLMConfiguredError
           → 或验证门失败
  ↓ 回退
  template_composer → answer（确定性模板）
  → 验证门 run → 通过 → path=template → 200
  → 仍失败 → raise GateRejectedError → api 层 500 + trace 记 composition_path=None, validation=失败报告
```

### 5.3 实体路由失败

```
router.route → entity_id=None
  → api 层返回 200，contract.confidence=0，composition_path=template
  → answer = "无法识别问题指向的实体，请补充公司名称。"
  → 仍写 trace（记录路由失败，可审计）
```

---

## 6. 异常与错误处理

```python
class GatewayError(Exception): pass
class NoLLMConfiguredError(GatewayError): pass   # 触发模板回退（非致命）
class GateRejectedError(GatewayError): pass      # 验证门双路径失败 → 500/熔断
class StoreError(GatewayError): pass             # 存储层故障 → 500
```

| 异常 | 触发点 | HTTP |
| ---- | ------ | ---- |
| 请求校验失败（Pydantic） | routes | 422 |
| `NoLLMConfiguredError` | compose 内部捕获 → 回退模板 | — |
| `GateRejectedError` | compose 双路径失败 | 500 + `detail: gate_rejected` + trace_id |
| `StoreError` | store/trace | 500 |
| 未知异常 | 任意 | 500（内部日志 + 熔断） |

---

## 7. 测试场景（tests/，对应验收标准）

eval 框架（pytest，CI 自动跑）——固定验证场景：**问题 + 期望声明 + 期望信号**（对应论文 Eval framework）。

| # | 场景 | 问题 | 期望声明 | 期望信号 |
| - | ---- | ---- | -------- | -------- |
| T1 | 实体精确命中 | "三星2024年营收是多少" | c-0001 | path=llm 或 template，trace 含 c-0001 |
| T2 | 别名命中 | "Samsung 2024 营收" | c-0001 | entity=samsung |
| T3 | 路由失败 | "今天的天气" | — | 返回"无法识别实体"，trace 记录路由失败 |
| T4 | 无 LLM key | 任意 | c-0001 | path=template（回退生效） |
| T5 | 验证①来源缺失 | 手工注入 source_ref 无效的 claim | — | 该 claim 不进入答案 |
| T6 | 延迟预算 | 任意 | c-0001 | 耗时 < 5s（检查⑥） |
| T7 | 组合冲突 | 两条互相矛盾声明 | — | 检查⑦拒绝 → 回退/熔断 |

---

## 8. 追踪记录格式示例（traces 表一行）

```json
{
  "trace_id": "tr-8f3a...",
  "request_id": "req-01",
  "question": "三星2024年营收是多少",
  "entity_id": "samsung",
  "selected_claims": ["c-0001"],
  "composition_path": "llm",
  "validation": {
    "source_anchored": true, "entity_match": true, "trace_complete": true,
    "output_clean": true, "interface": true, "latency": true, "composition": true
  },
  "answer": "三星电子2024年合并营收为300.9万亿韩元（来源：2024年报 p12）。",
  "created_at": "2026-08-18T..."
}
```

---

## 9. 配置示例（config.yaml）

```yaml
llm:
  provider: anthropic       # openai | anthropic | none
  model: claude-haiku-4-5
  api_key_env: ANTHROPIC_API_KEY

gate:
  latency_budget_seconds: 5

composition:
  default: llm              # llm | template
  fallback: template

sources:
  - id: sec-report
    name: 示例财报
    type: file
    path: data/claims.json
    policy: allowed
```

---

## 10. 演进预留

- **存储换 pgvector**：`ClaimStore` 接口不变，新增 `PgVectorClaimStore`；`query_claims` 改向量检索（ADR-0001）。
- **完整离线管线**：`ingest.py` 替换为 fetch → 抽取 → promotion gate 的流水线（ADR-0005）。
- **NER 增强**：`router` 内部规则层之上加轻量 NER 模型（ADR-0002）。
- **监控**：trace 表 + 指标暴露 `/metrics`（Prometheus 格式）供 Grafana。
