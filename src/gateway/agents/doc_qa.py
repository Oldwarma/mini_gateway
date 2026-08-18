# spec: SPEC-010
"""文档问答智能体（doc-qa）：按关键词检索证据（文档切片）→ 确定性模板答案，来源可锚定。"""
from __future__ import annotations

from ..core.schemas import AgentAnswer, AgentContext
from ..knowledge.store import ClaimStore
from .base import Agent


class DocQaAgent(Agent):
    name = "doc-qa"
    version = "1.0"
    description = "文档问答：从文档证据库按关键词检索，返回带来源切片的答案"

    def __init__(self, store: ClaimStore):
        self.store = store

    def handle(self, ctx: AgentContext) -> AgentAnswer:
        hits = self.store.search_evidence(ctx.question, limit=3)
        if not hits:
            return AgentAnswer(
                answer="未在文档证据中找到相关内容。",
                data={"evidence": [], "contract": {"entity": "", "key_points": [], "basis": [], "confidence": 0.0}},
                validation={"source_anchored": True},
                path="template",
            )

        lines = ["根据文档证据："]
        basis: list[str] = []
        key_points: list[str] = []
        for ev in hits:
            snippet = ev.content[:80] + ("…" if len(ev.content) > 80 else "")
            lines.append(f"- {ev.title}（来源 {ev.source_id}）：{snippet}")
            basis.append(ev.id)
            key_points.append(ev.title)
        contract = {
            "entity": "", "key_points": key_points, "basis": basis,
            "risks": [], "confidence": round(min(1.0, 0.4 + 0.2 * len(hits)), 2),
        }
        return AgentAnswer(
            answer="\n".join(lines),
            data={"evidence": [h.id for h in hits], "contract": contract},
            validation={"source_anchored": True},
            path="template",
        )
