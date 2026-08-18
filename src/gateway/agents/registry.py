# spec: SPEC-010
"""智能体注册表：注册 / 获取 / 列表。"""
from __future__ import annotations

from typing import Optional

from ..exceptions import GatewayError
from .base import Agent


class UnknownAgentError(GatewayError):
    """未知智能体 —— API 层映射 404。"""


class AgentRegistry:
    def __init__(self) -> None:
        self._agents: dict[str, Agent] = {}

    def register(self, agent: Agent) -> None:
        self._agents[agent.name] = agent

    def get(self, name: str) -> Optional[Agent]:
        return self._agents.get(name)

    def require(self, name: str) -> Agent:
        agent = self._agents.get(name)
        if agent is None:
            raise UnknownAgentError(f"unknown agent: {name}")
        return agent

    def list(self) -> list[Agent]:
        return list(self._agents.values())
