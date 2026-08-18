# spec: SPEC-010
"""外部智能体适配器（http-agent）：把外部 HTTP 服务接入网关，统一验证 + 审计。"""
from __future__ import annotations

from typing import Optional

import httpx

from ..core.schemas import AgentAnswer, AgentContext
from ..exceptions import GatewayError
from .base import Agent


class HttpAgent(Agent):
    def __init__(self, name: str, url: str, description: str = "",
                 client: Optional[httpx.Client] = None):
        self.name = name
        self.url = url
        self.version = "1.0"
        self.description = description or f"外部智能体（HTTP: {url}）"
        self._client = client

    def handle(self, ctx: AgentContext) -> AgentAnswer:
        try:
            if self._client is not None:
                resp = self._client.post(self.url, json={"question": ctx.question})
            else:
                resp = httpx.post(self.url, json={"question": ctx.question}, timeout=20.0)
            resp.raise_for_status()
            data = resp.json()
        except Exception as e:
            raise GatewayError(f"external agent {self.name} failed: {e}") from e
        answer = (data or {}).get("answer", "")
        if not answer:
            raise GatewayError(f"external agent {self.name} returned empty answer")
        return AgentAnswer(
            answer=answer,
            data={
                "external": True,
                "upstream": self.url,
                "contract": {"entity": (data or {}).get("agent", ""), "key_points": [], "basis": [], "confidence": 0.0},
            },
            validation={"external_ok": True},
            path="external",
        )
