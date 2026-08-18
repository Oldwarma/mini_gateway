# spec: SPEC-007
"""HTTP 接口（详细设计 §4.1，接口契约见 docs/design/api.md）。"""
from __future__ import annotations

import time

from fastapi import APIRouter, Depends, HTTPException

from ..core.schemas import AskRequest, AskResponse, Trace
from ..exceptions import GateRejectedError
from .deps import GatewayDeps

router = APIRouter()

_deps: GatewayDeps | None = None


def get_deps() -> GatewayDeps:
    """单例依赖：避免每次请求重开连接。"""
    global _deps
    if _deps is None:
        _deps = GatewayDeps()
    return _deps


@router.post("/v1/ask", response_model=AskResponse)
def ask(req: AskRequest, deps: GatewayDeps = Depends(get_deps)) -> AskResponse:
    started = time.time()
    try:
        return deps.handle_ask(req.question, started)
    except GateRejectedError as e:
        trace_id = getattr(e, "trace_id", "")
        raise HTTPException(status_code=500, detail={"detail": "gate_rejected", "trace_id": trace_id}) from e


@router.get("/v1/traces/{trace_id}", response_model=Trace)
def get_trace(trace_id: str, deps: GatewayDeps = Depends(get_deps)) -> Trace:
    trace = deps.trace_store.get(trace_id)
    if trace is None:
        raise HTTPException(status_code=404, detail="trace not found")
    return trace


@router.get("/health")
def health(deps: GatewayDeps = Depends(get_deps)) -> dict:
    return {"status": "ok", "db": True, "llm_configured": deps.llm_configured}
