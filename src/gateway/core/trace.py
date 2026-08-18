# spec: SPEC-001
"""追踪存储（详细设计 §3、§4.12）。"""
from __future__ import annotations

import json
import sqlite3
import threading
from typing import Optional

from ..exceptions import StoreError
from .schemas import Trace

_TRACES_DDL = """
CREATE TABLE IF NOT EXISTS traces (
    trace_id         TEXT PRIMARY KEY,
    request_id       TEXT NOT NULL,
    question         TEXT NOT NULL,
    entity_id        TEXT,
    selected_claims  TEXT NOT NULL DEFAULT '[]',
    composition_path TEXT,
    validation       TEXT NOT NULL DEFAULT '{}',
    answer           TEXT,
    created_at       TEXT NOT NULL DEFAULT (datetime('now'))
);
"""


class TraceStore:
    """审计追踪存储：只写不删改（审计一致性约定）。"""

    def __init__(self, db_path: str):
        self.db_path = db_path
        try:
            self._conn = sqlite3.connect(db_path, check_same_thread=False)
            self._conn.row_factory = sqlite3.Row
            self._lock = threading.RLock()
            with self._lock:
                self._conn.executescript(_TRACES_DDL)
                self._conn.commit()
        except sqlite3.Error as e:
            raise StoreError(f"trace store init failed: {e}") from e

    def create(self, trace: Trace) -> None:
        try:
            with self._lock:
                self._conn.execute(
                    "INSERT INTO traces (trace_id, request_id, question, entity_id, selected_claims, composition_path, validation, answer, created_at) "
                    "VALUES (?,?,?,?,?,?,?,?,?)",
                    (
                        trace.trace_id,
                        trace.request_id,
                        trace.question,
                        trace.entity_id,
                        json.dumps(trace.selected_claims, ensure_ascii=False),
                        trace.composition_path,
                        json.dumps(trace.validation, ensure_ascii=False),
                        trace.answer,
                        trace.created_at,
                    ),
                )
                self._conn.commit()
        except sqlite3.Error as e:
            raise StoreError(f"trace write failed: {e}") from e

    def get(self, trace_id: str) -> Optional[Trace]:
        with self._lock:
            row = self._conn.execute("SELECT * FROM traces WHERE trace_id=?", (trace_id,)).fetchone()
        if not row:
            return None
        return Trace(
            trace_id=row["trace_id"],
            request_id=row["request_id"],
            question=row["question"],
            entity_id=row["entity_id"],
            selected_claims=json.loads(row["selected_claims"] or "[]"),
            composition_path=row["composition_path"],
            validation=json.loads(row["validation"] or "{}"),
            answer=row["answer"],
            created_at=row["created_at"],
        )

    def close(self) -> None:
        with self._lock:
            self._conn.close()
