# spec: SPEC-008
"""七场景验收（详细设计 §7）+ HTTP 接口契约（docs/design/api.md）。"""
from __future__ import annotations

import json
import time

import pytest

from src.gateway.compose.boundary import compose
from src.gateway.core.schemas import AnswerContract, Claim, ValidationContext
from src.gateway.exceptions import GateRejectedError
from src.gateway.validate.gate import run as run_gate


# ---------- T1 实体精确命中 ----------

def test_t1_entity_hit_and_selection(gateway_deps):
    r = gateway_deps.handle_ask("三星2024年营收是多少", time.time())
    assert r.contract.entity == "samsung"
    assert "c-0001" in r.contract.basis
    assert "营收" in r.answer
    assert r.composition_path in ("llm", "template")
    t = gateway_deps.trace_store.get(r.trace_id)
    assert t is not None
    assert "c-0001" in t.selected_claims
    assert t.validation["source_anchored"] is True


# ---------- T2 别名 / 全名命中 ----------

def test_t2_alias_and_name_match(gateway_deps):
    r_alias = gateway_deps.handle_ask("三星 2024 年营收", time.time())
    assert r_alias.contract.entity == "samsung"
    r_name = gateway_deps.handle_ask("三星电子 2024 年营收", time.time())
    assert r_name.contract.entity == "samsung"


# ---------- T3 路由失败 ----------

def test_t3_route_failure(gateway_deps):
    r = gateway_deps.handle_ask("今天的天气怎么样", time.time())
    assert "无法识别" in r.answer
    assert r.contract.confidence == 0.0
    assert r.composition_path == "template"
    t = gateway_deps.trace_store.get(r.trace_id)
    assert t is not None and t.entity_id is None  # 路由失败仍可审计


# ---------- T4 无 LLM key 回退模板 ----------

def test_t4_http_ask_uses_template_path(client):
    resp = client.post("/v1/ask", json={"question": "三星2024年营收是多少"})
    assert resp.status_code == 200
    body = resp.json()
    assert body["composition_path"] == "template"  # 本环境 provider=none
    assert "c-0001" in body["contract"]["basis"]
    assert body["trace_id"]


# ---------- T5 来源缺失被验证门拒绝 ----------

def test_t5_source_anchored_rejects_bad_claim(gateway_deps):
    ctx = ValidationContext(
        trace_id="tr-t5", question="q", entity_id="samsung",
        claims=[Claim(claim_id="c-bad", entity_id="samsung", statement="三星营收1万亿韩元",
                      source_ref="ev-nonexist#p1", status="approved")],
        answer="a", path="template", llm_attempted=False,
        started_at=time.time(), ended_at=time.time(),
    )
    report = run_gate(ctx, gateway_deps.store, 5.0)
    assert report.results["source_anchored"] is False
    assert report.all_pass is False


# ---------- T6 延迟超预算 ----------

def test_t6_latency_over_budget(gateway_deps):
    ctx = ValidationContext(
        trace_id="tr-t6", question="q", entity_id="samsung", claims=[],
        answer="a", path="template", llm_attempted=False,
        started_at=time.time() - 100.0, ended_at=time.time(),
    )
    report = run_gate(ctx, gateway_deps.store, 5.0)
    assert report.results["latency"] is False
    assert report.all_pass is False


# ---------- T7 组合冲突 ----------

def test_t7_composition_conflict(gateway_deps):
    ctx = ValidationContext(
        trace_id="tr-t7", question="q", entity_id="samsung",
        claims=[
            Claim(claim_id="c-a", entity_id="samsung", statement="三星2024年营收300.9万亿韩元",
                  source_ref="ev-0001#p12", status="approved"),
            Claim(claim_id="c-b", entity_id="samsung", statement="三星2024年营收320.9万亿韩元",
                  source_ref="ev-0001#p12", status="approved"),
        ],
        answer="a", path="template", llm_attempted=False,
        started_at=time.time(), ended_at=time.time(),
    )
    report = run_gate(ctx, gateway_deps.store, 5.0)
    assert report.results["composition"] is False
    assert report.all_pass is False


def test_compose_rejects_conflicting_claims(gateway_deps):
    claims = [
        Claim(claim_id="c-a", entity_id="samsung", statement="三星2024年营收300.9万亿韩元",
              source_ref="ev-0001#p12", status="approved"),
        Claim(claim_id="c-b", entity_id="samsung", statement="三星2024年营收320.9万亿韩元",
              source_ref="ev-0001#p12", status="approved"),
    ]
    contract = AnswerContract(entity="samsung", key_points=[c.statement for c in claims],
                              basis=[c.claim_id for c in claims], confidence=0.8)
    with pytest.raises(GateRejectedError):
        compose("三星营收", contract, claims, gateway_deps.provider, gateway_deps.store,
                5.0, composition_default="template", trace_id="tr-x", started_at=time.time())


# ---------- HTTP 接口契约（api.md） ----------

def test_http_trace_and_health(client):
    assert client.get("/health").json()["status"] == "ok"
    r = client.post("/v1/ask", json={"question": "三星2024年营收是多少"})
    tid = r.json()["trace_id"]
    t = client.get(f"/v1/traces/{tid}")
    assert t.status_code == 200
    assert t.json()["trace_id"] == tid
    assert t.json()["question"] == "三星2024年营收是多少"
    assert client.get("/v1/traces/not-exist").status_code == 404


def test_http_ask_validation_error(client):
    assert client.post("/v1/ask", json={"question": ""}).status_code == 422
    assert client.post("/v1/ask", json={}).status_code == 422


def test_http_ask_route_failure(client):
    resp = client.post("/v1/ask", json={"question": "今天的天气怎么样"})
    assert resp.status_code == 200
    assert "无法识别" in resp.json()["answer"]
    assert resp.json()["contract"]["confidence"] == 0.0


# ---------- ingest 校验（SPEC-002 AC-3） ----------

def test_ingest_rejects_bad_claims(tmp_path):
    from src.gateway.knowledge.ingest import ingest
    from src.gateway.knowledge.store import SqliteClaimStore

    bad = {
        "entities": [{"id": "e1", "name": "E1", "aliases": []}],
        "sources": [{"id": "s1", "name": "S1"}],
        "evidence": [{"id": "ev1", "source_id": "s1", "title": "t", "content": "c"}],
        "claims": [
            {"claim_id": "ok", "entity_id": "e1", "statement": "好声明", "source_ref": "ev1#p1"},
            {"claim_id": "bad-entity", "entity_id": "nobody", "statement": "实体未注册", "source_ref": "ev1#p1"},
            {"claim_id": "bad-source", "entity_id": "e1", "statement": "无来源", "source_ref": "ev-nope#p1"},
            {"claim_id": "bad-empty", "entity_id": "e1", "statement": "   ", "source_ref": "ev1#p1"},
        ],
    }
    p = tmp_path / "bad.json"
    p.write_text(json.dumps(bad), encoding="utf-8")
    store = SqliteClaimStore(str(tmp_path / "bad.db"))
    r = ingest(p, store)
    assert r.claims == 1
    assert len(r.rejected) == 3
