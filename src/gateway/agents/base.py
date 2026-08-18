# spec: SPEC-010
"""Agent 抽象：每个智能体 = 一个标准接口（SPEC-010）。"""
from __future__ import annotations

from typing import Protocol

from ..core.schemas import AgentAnswer, AgentContext


class Agent(Protocol):
    """统一智能体接口：接收问题上下文，返回结构化答案。"""

    name: str
    version: str
    description: str

    def handle(self, ctx: AgentContext) -> AgentAnswer: ...
