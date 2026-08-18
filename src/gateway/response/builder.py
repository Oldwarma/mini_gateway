# spec: SPEC-006
"""响应组装（详细设计 §4.9）：组装 AskResponse + 写审计追踪。"""
from __future__ import annotations

import time
import uuid
from typing import Optional

from ..core.schemas import AnswerContract, AskResponse, ComposeResult, Trace
from ..core.trace import TraceStore


def build(
    question: str,
    entity_id: Optional[str],
    selected_claims: list[str],
    result: ComposeResult,
    contract: AnswerContract,
    trace_store: TraceStore,
    trace_id: Optional[str] = None,
) -> AskResponse:
    """生成 trace_id、写 traces 表，返回结构化响应。"""
    trace_id = trace_id or f"tr-{uuid.uuid4().hex[:8]}"
    trace = Trace(
        trace_id=trace_id,
        request_id=f"req-{uuid.uuid4().hex[:6]}",
        question=question,
        entity_id=entity_id,
        selected_claims=selected_claims,
        composition_path=result.path,
        validation=result.validation,
        answer=result.answer,
        created_at=time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
    )
    trace_store.create(trace)
    return AskResponse(
        answer=result.answer,
        contract=contract,
        trace_id=trace_id,
        composition_path=result.path,
    )
