# spec: SPEC-005
"""确定性模板组合（详细设计 §4.7，ADR-0003：不调 LLM，原样呈现声明）。"""
from __future__ import annotations

from ..core.schemas import AnswerContract, Claim


def compose(contract: AnswerContract, claims: list[Claim]) -> str:
    if not claims:
        return f"关于 {contract.entity} 暂无可引用的数据。"
    lines = [f"关于 {contract.entity} 的要点："]
    for c in claims:
        lines.append(f"- {c.statement}（来源：{c.source_ref}）")
    return "\n".join(lines)
