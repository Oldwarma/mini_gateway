# spec: SPEC-003
"""实体路由（详细设计 §4.2，ADR-0002：代码规则驱动，非 LLM）。"""
from __future__ import annotations

import re
from typing import Optional

from ..core.schemas import Entity, RouterResult


def route(question: str, entities: list[Entity]) -> RouterResult:
    """三层规则逐级放宽：全名精确 → 别名 → 问句包含实体名/别名。"""
    q = question.strip()
    if not q:
        return RouterResult()

    # 第 1 层：实体全名精确匹配（大小写不敏感）
    for e in entities:
        if q.lower() == e.name.lower():
            return RouterResult(entity_id=e.id, matched_rule="exact_name", confidence=1.0)

    # 第 2 层：别名精确匹配
    for e in entities:
        for alias in e.aliases:
            if q.lower() == alias.lower():
                return RouterResult(entity_id=e.id, matched_rule="alias", confidence=0.9)

    # 第 3 层：问句中包含实体名或别名（正则搜索）
    for e in entities:
        for name in [e.name] + e.aliases:
            if name and re.search(re.escape(name), q, re.IGNORECASE):
                return RouterResult(entity_id=e.id, matched_rule=f"contains:{name}", confidence=0.7)

    return RouterResult()
