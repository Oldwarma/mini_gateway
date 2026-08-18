# spec: SPEC-010
"""统一智能体网关：路由 → 智能体执行 → 统一验证 → 统一审计（SPEC-010）。"""
from __future__ import annotations

import time
import uuid

from .agents.registry import AgentRegistry
from .core.config import Config
from .core.schemas import AgentAnswer, AgentContext, AnswerContract, AskResponse, Trace
from .core.trace import TraceStore
from .exceptions import GatewayError
from .knowledge.store import ClaimStore


def _uniform_validation(ctx: AgentContext, answer: AgentAnswer, now: float, budget: float) -> dict:
    """统一通用验证（网关层，所有智能体都过）：agent 已知 / 答案非空 / 结构完整 / 延迟预算。"""
    elapsed = (now - ctx.started_at) if ctx.started_at else 0.0
    return {
        "agent_known": True,
        "answer_nonempty": bool(answer.answer.strip()),
        "answer_structure": isinstance(answer.data, dict),
        "latency": elapsed <= budget,
    }


class AgentGateway:
    """统一管理多个智能体：入口 `ask(agent, question)`。"""

    def __init__(self, registry: AgentRegistry, store: ClaimStore, trace_store: TraceStore, config: Config):
        self.registry = registry
        self.store = store
        self.trace_store = trace_store
        self.config = config

    def list_agents(self) -> list[dict]:
        return [
            {"name": a.name, "version": a.version, "description": a.description}
            for a in self.registry.list()
        ]

    def ask(self, agent_name: str, question: str) -> AskResponse:
        agent = self.registry.require(agent_name)  # 未知 → UnknownAgentError → 404
        started = time.time()
        trace_id = f"tr-{uuid.uuid4().hex[:8]}"
        ctx = AgentContext(agent=agent_name, question=question, trace_id=trace_id, started_at=started)

        try:
            answer = agent.handle(ctx)
        except GatewayError as e:
            # 失败也记审计（含领域验证报告，便于事后查为什么拒）
            ev = getattr(e, "validation", {}) or {}
            self._write_trace(trace_id, agent_name, question, None, {"error": str(e), **ev})
            e.trace_id = trace_id  # type: ignore[attr-defined]
            raise

        now = time.time()
        uniform = _uniform_validation(ctx, answer, now, self.config.gate.latency_budget_seconds)
        merged = {**answer.validation, **uniform}
        self._write_trace(trace_id, agent_name, question, answer, merged)

        contract = AnswerContract(**(answer.data.get("contract") or {})) if answer.data.get("contract") else AnswerContract()
        return AskResponse(
            answer=answer.answer,
            contract=contract,
            trace_id=trace_id,
            composition_path=answer.path,
            agent=agent_name,
        )

    def _write_trace(self, trace_id: str, agent_name: str, question: str,
                     answer: AgentAnswer | None, validation: dict) -> None:
        data = answer.data if answer else {}
        trace = Trace(
            trace_id=trace_id,
            agent=agent_name,
            request_id=f"req-{uuid.uuid4().hex[:6]}",
            question=question,
            entity_id=data.get("entity"),
            selected_claims=data.get("claims") or [],
            composition_path=answer.path if answer else None,
            validation=validation,
            answer=answer.answer if answer else None,
            created_at=time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        )
        self.trace_store.create(trace)
