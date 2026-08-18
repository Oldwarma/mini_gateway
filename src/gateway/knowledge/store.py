# spec: SPEC-002
"""声明存储：ClaimStore 抽象 + SqliteClaimStore（详细设计 §3、§4.11）。"""
from __future__ import annotations

import json
import re
import sqlite3
import threading
from typing import Optional, Protocol

from ..core.schemas import Claim, Entity, Evidence, Source
from ..exceptions import StoreError

_DDL = """
CREATE TABLE IF NOT EXISTS entities (
    id       TEXT PRIMARY KEY,
    name     TEXT NOT NULL,
    aliases  TEXT NOT NULL DEFAULT '[]',
    status   TEXT NOT NULL DEFAULT 'active'
);
CREATE TABLE IF NOT EXISTS sources (
    id     TEXT PRIMARY KEY,
    name   TEXT NOT NULL,
    url    TEXT,
    type   TEXT NOT NULL DEFAULT 'file',
    policy TEXT NOT NULL DEFAULT 'allowed',
    status TEXT NOT NULL DEFAULT 'active'
);
CREATE TABLE IF NOT EXISTS evidence (
    id          TEXT PRIMARY KEY,
    source_id   TEXT NOT NULL,
    title       TEXT NOT NULL,
    url         TEXT,
    content     TEXT NOT NULL,
    fingerprint TEXT NOT NULL DEFAULT ''
);
CREATE TABLE IF NOT EXISTS claims (
    claim_id   TEXT PRIMARY KEY,
    entity_id  TEXT NOT NULL,
    statement  TEXT NOT NULL,
    source_ref TEXT NOT NULL,
    page       TEXT,
    status     TEXT NOT NULL DEFAULT 'approved',
    created_at TEXT NOT NULL DEFAULT (datetime('now'))
);
CREATE VIRTUAL TABLE IF NOT EXISTS claims_fts USING fts5(entity_id, statement, claim_id);
CREATE TRIGGER IF NOT EXISTS claims_fts_ai AFTER INSERT ON claims BEGIN
    INSERT INTO claims_fts(entity_id, statement, claim_id)
    VALUES (new.entity_id, new.statement, new.claim_id);
END;
CREATE TRIGGER IF NOT EXISTS claims_fts_ad AFTER DELETE ON claims BEGIN
    DELETE FROM claims_fts WHERE claim_id = old.claim_id;
END;
"""


class ClaimStore(Protocol):
    """存储抽象（ADR-0001：可替换 pgvector 实现）。"""

    def upsert_entity(self, e: Entity) -> None: ...
    def upsert_source(self, s: Source) -> None: ...
    def upsert_evidence(self, ev: Evidence) -> None: ...
    def upsert_claim(self, c: Claim) -> None: ...
    def list_entities(self) -> list[Entity]: ...
    def get_entity(self, entity_id: str) -> Optional[Entity]: ...
    def get_evidence(self, evidence_id: str) -> Optional[Evidence]: ...
    def query_claims(self, entity_id: str, question: str, limit: int = 3) -> list[Claim]: ...
    def close(self) -> None: ...


def _fts_terms(question: str) -> str:
    """把问题拆词，构造 FTS5 MATCH 表达式（引号包裹，忽略空项）。"""
    tokens = re.split(r"\s+", question.strip())
    tokens = [t.strip('"\'') for t in tokens if t.strip()]
    return " AND ".join(f'"{t}"' for t in tokens) if tokens else ""


class SqliteClaimStore:
    def __init__(self, db_path: str):
        self.db_path = db_path
        try:
            # check_same_thread=False：FastAPI 线程池会跨线程访问同一连接
            self._conn = sqlite3.connect(db_path, check_same_thread=False)
            self._conn.row_factory = sqlite3.Row
            self._lock = threading.RLock()
            with self._lock:
                self._conn.executescript(_DDL)
                self._conn.commit()
        except sqlite3.Error as e:
            raise StoreError(f"store init failed: {e}") from e

    # ---- 写入 ----

    def upsert_entity(self, e: Entity) -> None:
        with self._lock:
            self._conn.execute(
                "INSERT INTO entities (id, name, aliases, status) VALUES (?,?,?,?) "
                "ON CONFLICT(id) DO UPDATE SET name=excluded.name, aliases=excluded.aliases, status=excluded.status",
                (e.id, e.name, json.dumps(e.aliases, ensure_ascii=False), e.status),
            )
            self._conn.commit()

    def upsert_source(self, s: Source) -> None:
        with self._lock:
            self._conn.execute(
                "INSERT INTO sources (id, name, url, type, policy, status) VALUES (?,?,?,?,?,?) "
                "ON CONFLICT(id) DO UPDATE SET name=excluded.name, url=excluded.url, type=excluded.type, policy=excluded.policy, status=excluded.status",
                (s.id, s.name, s.url, s.type, s.policy, s.status),
            )
            self._conn.commit()

    def upsert_evidence(self, ev: Evidence) -> None:
        with self._lock:
            self._conn.execute(
                "INSERT INTO evidence (id, source_id, title, url, content, fingerprint) VALUES (?,?,?,?,?,?) "
                "ON CONFLICT(id) DO UPDATE SET source_id=excluded.source_id, title=excluded.title, url=excluded.url, content=excluded.content, fingerprint=excluded.fingerprint",
                (ev.id, ev.source_id, ev.title, ev.url, ev.content, ev.fingerprint),
            )
            self._conn.commit()

    def upsert_claim(self, c: Claim) -> None:
        with self._lock:
            self._conn.execute(
                "INSERT INTO claims (claim_id, entity_id, statement, source_ref, page, status) VALUES (?,?,?,?,?,?) "
                "ON CONFLICT(claim_id) DO UPDATE SET entity_id=excluded.entity_id, statement=excluded.statement, source_ref=excluded.source_ref, page=excluded.page, status=excluded.status",
                (c.claim_id, c.entity_id, c.statement, c.source_ref, c.page, c.status),
            )
            self._conn.commit()

    # ---- 读取 ----

    def list_entities(self) -> list[Entity]:
        with self._lock:
            rows = self._conn.execute("SELECT * FROM entities").fetchall()
        return [
            Entity(id=r["id"], name=r["name"], aliases=json.loads(r["aliases"] or "[]"), status=r["status"])
            for r in rows
        ]

    def get_entity(self, entity_id: str) -> Optional[Entity]:
        with self._lock:
            row = self._conn.execute("SELECT * FROM entities WHERE id=?", (entity_id,)).fetchone()
        if not row:
            return None
        return Entity(id=row["id"], name=row["name"], aliases=json.loads(row["aliases"] or "[]"), status=row["status"])

    def get_evidence(self, evidence_id: str) -> Optional[Evidence]:
        with self._lock:
            row = self._conn.execute("SELECT * FROM evidence WHERE id=?", (evidence_id,)).fetchone()
        if not row:
            return None
        return Evidence(id=row["id"], source_id=row["source_id"], title=row["title"], url=row["url"], content=row["content"], fingerprint=row["fingerprint"])

    def _row_to_claim(self, r: sqlite3.Row) -> Claim:
        return Claim(
            claim_id=r["claim_id"], entity_id=r["entity_id"], statement=r["statement"],
            source_ref=r["source_ref"], page=r["page"], status=r["status"],
        )

    def get_source(self, source_id: str) -> Optional[Source]:
        with self._lock:
            row = self._conn.execute("SELECT * FROM sources WHERE id=?", (source_id,)).fetchone()
        if not row:
            return None
        return Source(id=row["id"], name=row["name"], url=row["url"], type=row["type"], policy=row["policy"], status=row["status"])

    def list_sources(self) -> list[Source]:
        with self._lock:
            rows = self._conn.execute("SELECT * FROM sources ORDER BY id").fetchall()
        return [Source(id=r["id"], name=r["name"], url=r["url"], type=r["type"], policy=r["policy"], status=r["status"]) for r in rows]

    def list_evidence(self) -> list[Evidence]:
        with self._lock:
            rows = self._conn.execute("SELECT * FROM evidence ORDER BY id").fetchall()
        return [self._row_to_evidence(r) for r in rows]

    def _row_to_evidence(self, r: sqlite3.Row) -> Evidence:
        return Evidence(id=r["id"], source_id=r["source_id"], title=r["title"], url=r["url"], content=r["content"], fingerprint=r["fingerprint"])

    def list_claims(self, entity_id: Optional[str] = None) -> list[Claim]:
        """声明列表（声明管理 / 审计用），可按实体过滤。"""
        if entity_id:
            with self._lock:
                rows = self._conn.execute(
                    "SELECT * FROM claims WHERE entity_id = ? ORDER BY created_at", (entity_id,)
                ).fetchall()
        else:
            with self._lock:
                rows = self._conn.execute("SELECT * FROM claims ORDER BY created_at").fetchall()
        return [self._row_to_claim(r) for r in rows]

    def search_evidence(self, question: str, limit: int = 3) -> list[Evidence]:
        """doc-qa 用：按关键词在标题+内容上的命中数打分排序（v1 无向量）。"""
        terms = [t for t in re.split(r"\s+", question.strip()) if t]
        with self._lock:
            rows = self._conn.execute("SELECT * FROM evidence").fetchall()
        scored: list[tuple[int, sqlite3.Row]] = []
        for r in rows:
            text = f"{r['title']} {r['content']}"
            score = sum(1 for t in terms if t and t in text)
            if score:
                scored.append((score, r))
        scored.sort(key=lambda x: -x[0])
        return [self._row_to_evidence(r) for _, r in scored[:limit]]

    def query_claims(self, entity_id: str, question: str, limit: int = 3) -> list[Claim]:
        """实体过滤 + FTS5 相关性排序；无 FTS 命中时回退为按创建序取 N 条。"""
        terms = _fts_terms(question)
        if terms:
            try:
                with self._lock:
                    rows = self._conn.execute(
                        "SELECT c.* FROM claims c "
                        "JOIN claims_fts f ON f.claim_id = c.claim_id "
                        "WHERE c.entity_id = ? AND c.status = 'approved' AND claims_fts MATCH ? "
                        "ORDER BY rank LIMIT ?",
                        (entity_id, terms, limit),
                    ).fetchall()
                if rows:
                    return [self._row_to_claim(r) for r in rows]
            except sqlite3.Error:
                pass  # FTS 异常回退到普通查询
        with self._lock:
            rows = self._conn.execute(
                "SELECT * FROM claims WHERE entity_id = ? AND status = 'approved' ORDER BY created_at LIMIT ?",
                (entity_id, limit),
            ).fetchall()
        return [self._row_to_claim(r) for r in rows]

    def close(self) -> None:
        with self._lock:
            self._conn.close()
