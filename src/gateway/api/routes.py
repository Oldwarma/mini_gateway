# spec: SPEC-007
"""HTTP 接口：统一智能体入口（SPEC-010）+ 声明管理（SPEC-011）+ 审计 + 界面。"""
from __future__ import annotations

from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import FileResponse, RedirectResponse

from ..agents.registry import UnknownAgentError
from ..core.schemas import (
    AskRequest,
    AskResponse,
    Claim,
    ClaimCreate,
    ClaimCreateResult,
    Entity,
    EntityCreate,
    Evidence,
    EvidenceCreate,
    Source,
    SourceCreate,
    Trace,
)
from ..exceptions import GatewayError
from ..knowledge.ingest import validate_claim
from .deps import GatewayDeps

router = APIRouter()

_deps: GatewayDeps | None = None


def get_deps() -> GatewayDeps:
    """单例依赖：避免每次请求重开连接。"""
    global _deps
    if _deps is None:
        _deps = GatewayDeps()
    return _deps


# ---------- 智能体统一入口（SPEC-010） ----------


@router.get("/v1/agents")
def list_agents(deps: GatewayDeps = Depends(get_deps)) -> list[dict]:
    return deps.gateway.list_agents()


@router.post("/v1/agents/{name}/ask", response_model=AskResponse)
def agent_ask(name: str, req: AskRequest, deps: GatewayDeps = Depends(get_deps)) -> AskResponse:
    try:
        return deps.gateway.ask(name, req.question)
    except UnknownAgentError as e:
        raise HTTPException(status_code=404, detail=str(e)) from e
    except GatewayError as e:
        raise HTTPException(
            status_code=500,
            detail={"detail": "gateway_error", "trace_id": getattr(e, "trace_id", "")},
        ) from e


@router.post("/v1/ask", response_model=AskResponse)
def ask(req: AskRequest, deps: GatewayDeps = Depends(get_deps)) -> AskResponse:
    """向后兼容：委派给 claim-info 智能体。"""
    try:
        return deps.gateway.ask("claim-info", req.question)
    except GatewayError as e:
        raise HTTPException(
            status_code=500,
            detail={"detail": "gateway_error", "trace_id": getattr(e, "trace_id", "")},
        ) from e


# ---------- 审计追踪 ----------


@router.get("/v1/traces", response_model=list[Trace])
def list_traces(limit: int = Query(50, ge=1, le=200), agent: str | None = None,
                deps: GatewayDeps = Depends(get_deps)) -> list[Trace]:
    return deps.trace_store.list(limit=limit, agent=agent)


@router.get("/v1/traces/{trace_id}", response_model=Trace)
def get_trace(trace_id: str, deps: GatewayDeps = Depends(get_deps)) -> Trace:
    trace = deps.trace_store.get(trace_id)
    if trace is None:
        raise HTTPException(status_code=404, detail="trace not found")
    return trace


# ---------- 声明管理（SPEC-011） ----------


@router.get("/v1/entities", response_model=list[Entity])
def list_entities(deps: GatewayDeps = Depends(get_deps)) -> list[Entity]:
    return deps.store.list_entities()


@router.post("/v1/entities", response_model=Entity)
def create_entity(body: EntityCreate, deps: GatewayDeps = Depends(get_deps)) -> Entity:
    entity = Entity(id=body.id, name=body.name, aliases=body.aliases, status=body.status)
    deps.store.upsert_entity(entity)
    return entity


@router.get("/v1/sources", response_model=list[Source])
def list_sources(deps: GatewayDeps = Depends(get_deps)) -> list[Source]:
    return deps.store.list_sources()


@router.post("/v1/sources", response_model=Source)
def create_source(body: SourceCreate, deps: GatewayDeps = Depends(get_deps)) -> Source:
    source = Source(id=body.id, name=body.name, url=body.url, type=body.type, policy=body.policy, status=body.status)
    deps.store.upsert_source(source)
    return source


@router.get("/v1/evidence", response_model=list[Evidence])
def list_evidence(deps: GatewayDeps = Depends(get_deps)) -> list[Evidence]:
    return deps.store.list_evidence()


@router.post("/v1/evidence", response_model=Evidence)
def create_evidence(body: EvidenceCreate, deps: GatewayDeps = Depends(get_deps)) -> Evidence:
    if deps.store.get_source(body.source_id) is None:
        raise HTTPException(status_code=400, detail=f"source {body.source_id} not registered")
    ev = Evidence(id=body.id, source_id=body.source_id, title=body.title, url=body.url,
                  content=body.content, fingerprint=body.fingerprint)
    deps.store.upsert_evidence(ev)
    return ev


@router.get("/v1/claims", response_model=list[Claim])
def list_claims(entity_id: str | None = None, deps: GatewayDeps = Depends(get_deps)) -> list[Claim]:
    return deps.store.list_claims(entity_id)


@router.post("/v1/claims", response_model=ClaimCreateResult)
def create_claim(body: ClaimCreate, deps: GatewayDeps = Depends(get_deps)) -> ClaimCreateResult:
    """提交声明：实时 promotion 校验，通过才写入（SPEC-011）。"""
    reasons = validate_claim(body, deps.store)
    if reasons:
        return ClaimCreateResult(accepted=False, claim_id=body.claim_id, reasons=reasons)
    deps.store.upsert_claim(Claim(
        claim_id=body.claim_id, entity_id=body.entity_id, statement=body.statement.strip(),
        source_ref=body.source_ref, page=body.page, status="approved",
    ))
    return ClaimCreateResult(accepted=True, claim_id=body.claim_id, reasons=[])


# ---------- 健康与界面 ----------


@router.get("/health")
def health(deps: GatewayDeps = Depends(get_deps)) -> dict:
    return {"status": "ok", "db": True, "llm_configured": deps.llm_configured,
            "agents": len(deps.registry.list())}


def _ui(name: str) -> Path:
    return Path(__file__).resolve().parent.parent / "ui" / name


@router.get("/", include_in_schema=False)
def root() -> RedirectResponse:
    return RedirectResponse(url="/chat")


@router.get("/chat", include_in_schema=False)
def chat_page() -> FileResponse:
    return FileResponse(_ui("chat.html"), media_type="text/html")


@router.get("/claims", include_in_schema=False)
def claims_page() -> FileResponse:
    return FileResponse(_ui("claims.html"), media_type="text/html")


@router.get("/traces", include_in_schema=False)
def traces_page() -> FileResponse:
    return FileResponse(_ui("traces.html"), media_type="text/html")


@router.get("/agents", include_in_schema=False)
def agents_page() -> FileResponse:
    return FileResponse(_ui("agents.html"), media_type="text/html")
