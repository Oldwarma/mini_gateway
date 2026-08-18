# spec: SPEC-010
"""声明信息智能体（claim-info）：可追踪声明问答（重构自原 deps.handle_ask）。"""
from __future__ import annotations

import time

from ..compose.boundary import compose as compose_answer
from ..contract.builder import build as build_contract
from ..core.config import Config
from ..core.llm import LLMProvider
from ..core.schemas import AgentAnswer, AgentContext, AnswerContract
from ..knowledge.store import ClaimStore
from ..router.entity_router import route as route_entity
from ..selector.claim_selector import select as select_claims
from .base import Agent


class ClaimInfoAgent(Agent):
    name = "claim-info"
    version = "1.0"
    description = "声明信息问答：基于背书声明做可追踪问答（实体路由 → 声明选择 → 组合边界 → 七维验证门）"

    def __init__(self, store: ClaimStore, provider: LLMProvider, config: Config):
        self.store = store
        self.provider = provider
        self.config = config

    def handle(self, ctx: AgentContext) -> AgentAnswer:
        question = ctx.question
        started = ctx.started_at or time.time()

        # 1) 实体路由（代码规则，ADR-0002）
        route_result = route_entity(question, self.store.list_entities())

        # 2) 无法识别实体 → 友好提示（仍可审计）
        if route_result.entity_id is None:
            contract = AnswerContract(entity="", key_points=[], basis=[], risks=[], confidence=0.0)
            return AgentAnswer(
                answer="无法识别问题指向的实体，请补充公司名称。",
                data={"entity": None, "claims": [], "contract": contract.model_dump(), "route": route_result.model_dump()},
                validation={"entity_route": False},
                path="template",
            )

        # 3) 声明选择 → 合约构建
        claims = select_claims(self.store, route_result.entity_id, question, 3)
        contract = build_contract(route_result.entity_id, claims)

        # 4) 组合边界（LLM 措辞 / 模板回退，内部跑七维验证门）
        result = compose_answer(
            question=question,
            contract=contract,
            claims=claims,
            provider=self.provider,
            store=self.store,
            gate_budget=self.config.gate.latency_budget_seconds,
            composition_default=self.config.composition.default,
            trace_id=ctx.trace_id,
            started_at=started,
        )

        return AgentAnswer(
            answer=result.answer,
            data={
                "entity": route_result.entity_id,
                "claims": [c.claim_id for c in claims],
                "contract": contract.model_dump(),
                "path": result.path,
                "route": route_result.model_dump(),
            },
            validation=result.validation,
            path=result.path,
        )
