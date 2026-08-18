# spec: SPEC-007
"""依赖注入 + 主流程编排（详细设计 §5.1）。"""
from __future__ import annotations

import time
import uuid
from typing import Optional

from ..compose.boundary import compose as compose_answer
from ..contract.builder import build as build_contract
from ..core.config import Config, load_config
from ..core.llm import make_provider
from ..core.schemas import AnswerContract, AskResponse, ComposeResult, Trace
from ..core.trace import TraceStore
from ..exceptions import GateRejectedError
from ..knowledge.store import SqliteClaimStore
from ..response.builder import build as build_response
from ..router.entity_router import route as route_entity
from ..selector.claim_selector import select as select_claims


class GatewayDeps:
    """网关运行所需依赖：配置、存储、追踪、LLM provider。"""

    def __init__(self, config: Optional[Config] = None, db_path: str = "gateway.db"):
        self.config = config or load_config("config.yaml")
        self.db_path = db_path
        self.store = SqliteClaimStore(db_path)
        self.trace_store = TraceStore(db_path)
        self.provider = make_provider(self.config.llm)
        self.llm_configured = self.config.llm.provider in ("openai", "anthropic")

    def _write_trace(self, question, entity_id, selected_claims, result, trace_id) -> None:
        self.trace_store.create(Trace(
            trace_id=trace_id,
            request_id=f"req-{uuid.uuid4().hex[:6]}",
            question=question,
            entity_id=entity_id,
            selected_claims=selected_claims,
            composition_path=result.path,
            validation=result.validation,
            answer=result.answer,
            created_at=time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        ))

    def handle_ask(self, question: str, started_at: float) -> AskResponse:
        trace_id = f"tr-{uuid.uuid4().hex[:8]}"
        entities = self.store.list_entities()
        rr = route_entity(question, entities)

        # 实体无法识别 → 提示语 + 仍写 trace（可审计路由失败）
        if rr.entity_id is None:
            contract = AnswerContract(entity="", key_points=[], basis=[], risks=[], confidence=0.0)
            result = ComposeResult(
                answer="无法识别问题指向的实体，请补充公司名称。",
                path="template", llm_attempted=False, validation={},
            )
            return build_response(question, None, [], result, contract, self.trace_store, trace_id=trace_id)

        claims = select_claims(self.store, rr.entity_id, question, 3)
        contract = build_contract(rr.entity_id, claims)

        try:
            result = compose_answer(
                question=question,
                contract=contract,
                claims=claims,
                provider=self.provider,
                store=self.store,
                gate_budget=self.config.gate.latency_budget_seconds,
                composition_default=self.config.composition.default,
                trace_id=trace_id,
                started_at=started_at,
            )
        except GateRejectedError as e:
            e.trace_id = trace_id  # type: ignore[attr-defined]
            # 写失败 trace 供事后审计
            failed = ComposeResult(answer="", path="template", llm_attempted=False, validation=e.validation)
            self._write_trace(question, rr.entity_id, [c.claim_id for c in claims], failed, trace_id)
            raise

        return build_response(
            question, rr.entity_id,
            [c.claim_id for c in claims], result, contract, self.trace_store, trace_id=trace_id,
        )

    def close(self) -> None:
        self.store.close()
        self.trace_store.close()
