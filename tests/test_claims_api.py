# spec: SPEC-011
"""声明管理 API 验收（界面录入 + promotion 实时校验）。"""
from __future__ import annotations


def test_claim_create_valid_via_api(client):
    resp = client.post("/v1/claims", json={
        "claim_id": "c-api1", "entity_id": "samsung", "statement": "测试声明",
        "source_ref": "ev-0001#p1",
    })
    assert resp.status_code == 200
    body = resp.json()
    assert body["accepted"] is True
    assert body["claim_id"] == "c-api1"


def test_claim_rejected_bad_source(client):
    resp = client.post("/v1/claims", json={
        "claim_id": "c-bad", "entity_id": "samsung", "statement": "x", "source_ref": "ev-nope#p1",
    })
    body = resp.json()
    assert body["accepted"] is False
    assert any("来源" in r for r in body["reasons"])


def test_claim_rejected_unregistered_entity(client):
    resp = client.post("/v1/claims", json={
        "claim_id": "c-bad2", "entity_id": "nobody", "statement": "x", "source_ref": "ev-0001#p1",
    })
    assert resp.json()["accepted"] is False


def test_claim_rejected_empty_statement(client):
    resp = client.post("/v1/claims", json={
        "claim_id": "c-bad3", "entity_id": "samsung", "statement": "   ", "source_ref": "ev-0001#p1",
    })
    assert resp.json()["accepted"] is False


def test_claims_list_filter_by_entity(client):
    client.post("/v1/claims", json={
        "claim_id": "c-f", "entity_id": "samsung", "statement": "过滤测试", "source_ref": "ev-0001#p1",
    })
    r = client.get("/v1/claims?entity_id=samsung")
    assert any(c["claim_id"] == "c-f" for c in r.json())


def test_entity_source_evidence_crud(client):
    assert client.post("/v1/entities", json={"id": "e-new", "name": "新实体", "aliases": []}).json()["id"] == "e-new"
    assert client.post("/v1/sources", json={"id": "s-new", "name": "新来源"}).json()["id"] == "s-new"
    assert client.post("/v1/evidence", json={
        "id": "ev-new", "source_id": "s-new", "title": "t", "content": "c",
    }).json()["id"] == "ev-new"
    # 证据要求来源已注册
    bad = client.post("/v1/evidence", json={"id": "ev-x", "source_id": "no-src", "title": "t", "content": "c"})
    assert bad.status_code == 400


def test_agents_http_endpoints(client):
    assert client.get("/v1/agents").status_code == 200
    assert client.post("/v1/agents/no-such/ask", json={"question": "q"}).status_code == 404
    r = client.post("/v1/agents/claim-info/ask", json={"question": "三星2024年营收是多少"})
    assert r.status_code == 200
    body = r.json()
    assert body["agent"] == "claim-info"
    assert body["trace_id"]


def test_traces_list_endpoint(client):
    r = client.post("/v1/ask", json={"question": "三星2024年营收是多少"})
    tid = r.json()["trace_id"]
    lst = client.get("/v1/traces")
    assert lst.status_code == 200
    assert any(t["trace_id"] == tid for t in lst.json())
    by_agent = client.get("/v1/traces?agent=claim-info")
    assert all(t["agent"] == "claim-info" for t in by_agent.json())
