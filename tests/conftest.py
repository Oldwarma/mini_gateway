# spec: SPEC-008
"""pytest 公共 fixture（临时 DB + 已导入示例数据 + HTTP 客户端）。"""
from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from src.gateway.api.deps import GatewayDeps
from src.gateway.api.routes import get_deps
from src.gateway.knowledge.ingest import ingest
from src.gateway.knowledge.store import SqliteClaimStore
from src.gateway.main import app


@pytest.fixture()
def gateway_deps(tmp_path):
    db = tmp_path / "test.db"
    ingest("data/claims.json", SqliteClaimStore(str(db)))
    deps = GatewayDeps(db_path=str(db))
    yield deps
    deps.close()


@pytest.fixture()
def client(gateway_deps):
    app.dependency_overrides[get_deps] = lambda: gateway_deps
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.pop(get_deps, None)
