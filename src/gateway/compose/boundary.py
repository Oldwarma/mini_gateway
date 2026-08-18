# spec: SPEC-005
"""组合边界（详细设计 §4.5，ADR-0003）：默认 LLM 措辞，失败回退确定性模板。"""
from __future__ import annotations

import time
from typing import Optional

from ..core.llm import LLMProvider
from ..core.schemas import AnswerContract, Claim, ComposeResult, ValidationContext
from ..exceptions import GateRejectedError
from ..knowledge.store import ClaimStore
from ..validate.gate import run as run_gate
from . import llm_composer, template_composer


def compose(
    question: str,
    contract: AnswerContract,
    claims: list[Claim],
    provider: LLMProvider,
    store: ClaimStore,
    gate_budget: float,
    composition_default: str = "llm",
    trace_id: str = "",
    started_at: Optional[float] = None,
) -> ComposeResult:
    """选择组合路径并做验证；双路径失败抛 GateRejectedError（携带最后验证报告）。"""
    started = started_at or time.time()

    def _ctx(answer: str, path: str, attempted: bool) -> ValidationContext:
        return ValidationContext(
            trace_id=trace_id,
            question=question,
            entity_id=contract.entity,
            claims=claims,
            answer=answer,
            path=path,
            llm_attempted=attempted,
            started_at=started,
            ended_at=time.time(),
        )

    # 无声明 → 直接确定性模板（不尝试 LLM）
    if not claims:
        answer = template_composer.compose(contract, claims)
        report = run_gate(_ctx(answer, "template", False), store, gate_budget)
        if not report.all_pass:
            raise GateRejectedError(validation=report.results)
        return ComposeResult(answer=answer, path="template", llm_attempted=False, validation=report.results)

    # 主路径：LLM 措辞 → 验证
    if composition_default == "llm":
        try:
            answer = llm_composer.compose(contract, claims, provider)
        except Exception:
            answer = None  # 无 key / 超时 / 异常 → 回退
        if answer:
            report = run_gate(_ctx(answer, "llm", True), store, gate_budget)
            if report.all_pass:
                return ComposeResult(answer=answer, path="llm", llm_attempted=True, validation=report.results)

    # 回退路径：确定性模板 → 验证
    answer = template_composer.compose(contract, claims)
    report = run_gate(_ctx(answer, "template", composition_default == "llm"), store, gate_budget)
    if report.all_pass:
        return ComposeResult(
            answer=answer, path="template", llm_attempted=(composition_default == "llm"),
            validation=report.results,
        )

    raise GateRejectedError(validation=report.results)
