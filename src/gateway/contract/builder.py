# spec: SPEC-004
"""合约构建（详细设计 §4.4）：把选中声明结构化为 AnswerContract。"""
from __future__ import annotations

from ..core.schemas import AnswerContract, Claim


def build(entity_id: str, claims: list[Claim]) -> AnswerContract:
    """生成答案合约：key_points 为声明要点，basis 为依据声明，confidence 按声明/来源数加权。"""
    if not claims:
        return AnswerContract(entity=entity_id, key_points=[], basis=[], risks=[], confidence=0.0)

    basis = [c.claim_id for c in claims]
    key_points = [c.statement for c in claims]
    source_count = len({c.source_ref.split("#", 1)[0] for c in claims if c.source_ref})
    confidence = min(1.0, 0.5 + 0.15 * len(claims) + 0.1 * source_count)
    return AnswerContract(
        entity=entity_id,
        key_points=key_points,
        basis=basis,
        risks=[],
        confidence=round(confidence, 2),
    )
