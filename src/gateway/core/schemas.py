# spec: SPEC-001
"""领域模型（详细设计 §2）。"""
from __future__ import annotations

from typing import Optional

from pydantic import BaseModel, Field


class Entity(BaseModel):
    """注册实体（实体路由的依据）。"""

    id: str
    name: str
    aliases: list[str] = []
    status: str = "active"


class Source(BaseModel):
    """来源清单（对应论文 Source config）。"""

    id: str
    name: str
    url: Optional[str] = None
    type: str = "file"
    policy: str = "allowed"
    status: str = "active"


class Evidence(BaseModel):
    """证据记录（来源锚定的载体）。"""

    id: str
    source_id: str
    title: str
    url: Optional[str] = None
    content: str
    fingerprint: str = ""


class Claim(BaseModel):
    """背书声明（来源锚定 + 实体归属）。"""

    claim_id: str
    entity_id: str
    statement: str
    source_ref: str
    page: Optional[str] = None
    status: str = "approved"


class AnswerContract(BaseModel):
    """答案结构合约（约束输出格式）。"""

    entity: str = ""
    key_points: list[str] = []
    basis: list[str] = []
    risks: list[str] = []
    confidence: float = Field(0.0, ge=0.0, le=1.0)


class AskRequest(BaseModel):
    question: str = Field(min_length=1, max_length=500)


class AskResponse(BaseModel):
    answer: str
    contract: AnswerContract
    trace_id: str
    composition_path: str
    agent: str = ""


class RouterResult(BaseModel):
    """实体路由结果（可追溯：命中哪条规则）。"""

    entity_id: Optional[str] = None
    matched_rule: Optional[str] = None
    confidence: float = 0.0


class ComposeResult(BaseModel):
    """组合边界结果。"""

    answer: str = ""
    path: str = "template"  # llm | template
    llm_attempted: bool = False
    validation: dict = {}


class ValidationContext(BaseModel):
    """七维验证门输入上下文。"""

    trace_id: str = ""
    question: str = ""
    entity_id: Optional[str] = None
    claims: list[Claim] = []
    answer: str = ""
    path: str = "template"
    llm_attempted: bool = False
    started_at: float = 0.0
    ended_at: float = 0.0


class ValidationReport(BaseModel):
    """七维验证门结果。"""

    results: dict[str, bool] = {}
    all_pass: bool = False


class Trace(BaseModel):
    """完整审计追踪（每次请求一条）。"""

    trace_id: str
    request_id: str
    question: str
    agent: str = ""
    entity_id: Optional[str] = None
    selected_claims: list[str] = []
    composition_path: Optional[str] = None
    validation: dict = {}
    answer: Optional[str] = None
    created_at: str = ""


class AgentContext(BaseModel):
    """智能体调用上下文（统一网关注入）。"""

    agent: str = ""
    question: str = ""
    trace_id: str = ""
    started_at: float = 0.0


class AgentAnswer(BaseModel):
    """智能体返回：答案 + 领域数据 + 领域验证结果 + 组合路径。"""

    answer: str = ""
    data: dict = {}
    validation: dict = {}
    path: str = "template"


# ---- 声明管理（SPEC-011）创建模型 ----

class EntityCreate(BaseModel):
    id: str = Field(min_length=1)
    name: str = Field(min_length=1)
    aliases: list[str] = []
    status: str = "active"


class SourceCreate(BaseModel):
    id: str = Field(min_length=1)
    name: str = Field(min_length=1)
    url: Optional[str] = None
    type: str = "file"
    policy: str = "allowed"
    status: str = "active"


class EvidenceCreate(BaseModel):
    id: str = Field(min_length=1)
    source_id: str
    title: str = Field(min_length=1)
    url: Optional[str] = None
    content: str = Field(min_length=1)
    fingerprint: str = ""


class ClaimCreate(BaseModel):
    claim_id: str = Field(min_length=1)
    entity_id: str
    statement: str
    source_ref: str
    page: Optional[str] = None
    status: str = "approved"


class ClaimCreateResult(BaseModel):
    accepted: bool
    claim_id: Optional[str] = None
    reasons: list[str] = []
