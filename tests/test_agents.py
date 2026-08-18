# spec: SPEC-010
"""Agent 抽象与统一网关验收。"""
from __future__ import annotations

import time

import httpx
import pytest

from src.gateway.agents.http_agent import HttpAgent
from src.gateway.agents.registry import UnknownAgentError
from src.gateway.core.schemas import AgentContext


def test_list_agents_has_builtin(gateway_deps):
    names = {a["name"] for a in gateway_deps.gateway.list_agents()}
    assert {"claim-info", "doc-qa"} <= names


def test_agent_ask_claim_info(gateway_deps):
    r = gateway_deps.gateway.ask("claim-info", "三星2024年营收是多少")
    assert r.agent == "claim-info"
    assert "c-0001" in r.contract.basis
    t = gateway_deps.trace_store.get(r.trace_id)
    assert t.agent == "claim-info"
    assert t.validation["agent_known"] is True
    assert t.validation["source_anchored"] is True


def test_agent_ask_doc_qa(gateway_deps):
    r = gateway_deps.gateway.ask("doc-qa", "随便问问")
    assert r.agent == "doc-qa"
    assert "未在文档证据" in r.answer


def test_unknown_agent_raises(gateway_deps):
    with pytest.raises(UnknownAgentError):
        gateway_deps.gateway.ask("no-such-agent", "q")


def test_http_agent_with_mock_transport():
    def handler(request):
        return httpx.Response(200, json={"answer": "外部答案"})

    client = httpx.Client(transport=httpx.MockTransport(handler))
    agent = HttpAgent("ext", "http://mock", client=client)
    ans = agent.handle(AgentContext(agent="ext", question="q", trace_id="tr-1", started_at=time.time()))
    assert ans.answer == "外部答案"
    assert ans.data["external"] is True


def test_http_agent_failure_raises_gateway_error():
    from src.gateway.exceptions import GatewayError

    def handler(request):
        return httpx.Response(500, json={})

    client = httpx.Client(transport=httpx.MockTransport(handler))
    agent = HttpAgent("ext", "http://mock", client=client)
    with pytest.raises(GatewayError):
        agent.handle(AgentContext(agent="ext", question="q", trace_id="tr-1", started_at=time.time()))
