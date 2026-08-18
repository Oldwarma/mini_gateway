# spec: SPEC-007
"""依赖注入 + 统一网关装配（SPEC-010）：注册所有智能体并暴露 AgentGateway。"""
from __future__ import annotations

from typing import Optional

from ..agents.claim_info import ClaimInfoAgent
from ..agents.doc_qa import DocQaAgent
from ..agents.http_agent import HttpAgent
from ..agents.registry import AgentRegistry
from ..core.config import Config, load_config
from ..core.llm import make_provider
from ..core.trace import TraceStore
from ..gateway import AgentGateway
from ..knowledge.store import SqliteClaimStore


class GatewayDeps:
    """装配配置 / 存储 / 追踪 / LLM provider，注册全部智能体到统一网关。"""

    def __init__(self, config: Optional[Config] = None, db_path: str = "gateway.db"):
        self.config = config or load_config("config.yaml")
        self.db_path = db_path
        self.store = SqliteClaimStore(db_path)
        self.trace_store = TraceStore(db_path)
        self.provider = make_provider(self.config.llm)
        self.llm_configured = self.config.llm.provider in ("openai", "anthropic")

        registry = AgentRegistry()
        registry.register(ClaimInfoAgent(self.store, self.provider, self.config))
        registry.register(DocQaAgent(self.store))
        for ext in self.config.external_agents:
            registry.register(HttpAgent(ext.name, ext.url, ext.description))
        self.registry = registry
        self.gateway = AgentGateway(registry, self.store, self.trace_store, self.config)

    def handle_ask(self, question: str, started_at: float):
        """向后兼容：/v1/ask 委派到 claim-info 智能体。"""
        return self.gateway.ask("claim-info", question)

    def close(self) -> None:
        self.store.close()
        self.trace_store.close()
