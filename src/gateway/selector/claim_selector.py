# spec: SPEC-004
"""声明选择（详细设计 §4.3）：实体过滤 + FTS5 相关性排序，仅返回 approved。"""
from __future__ import annotations

from ..core.schemas import Claim
from ..knowledge.store import ClaimStore


def select(store: ClaimStore, entity_id: str, question: str, limit: int = 3) -> list[Claim]:
    """按实体过滤并从存储检索相关声明。"""
    return store.query_claims(entity_id, question, limit)
