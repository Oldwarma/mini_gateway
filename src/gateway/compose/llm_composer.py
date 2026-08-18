# spec: SPEC-005
"""LLM 措辞组合（详细设计 §4.6，ADR-0003：LLM 只管措辞，不做判断）。"""
from __future__ import annotations

from ..core.llm import LLMProvider
from ..core.schemas import AnswerContract, Claim


def compose(contract: AnswerContract, claims: list[Claim], provider: LLMProvider) -> str:
    evidence_lines = "\n".join(f"- {c.statement}（来源：{c.source_ref}）" for c in claims)
    prompt = (
        "你是答案措辞引擎，只负责把下面的声明组织成自然语言答案。\n"
        "不得引入声明之外的事实，不得做判断。\n\n"
        "【声明依据】\n"
        f"{evidence_lines}\n\n"
        "【答案合约】\n"
        f"{contract.model_dump_json(indent=2)}\n\n"
        "请输出符合合约结构的自然语言答案。"
    )
    return provider.complete(prompt)
