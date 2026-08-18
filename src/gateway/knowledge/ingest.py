# spec: SPEC-002
"""轻量导入器（详细设计 §4.10，ADR-0005：promotion gate 轻量版）。"""
from __future__ import annotations

import json
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

import yaml

from ..core.schemas import Claim, ClaimCreate, Entity, Evidence, Source
from .store import ClaimStore

MAX_STATEMENT_LEN = 200


def _evidence_ref(source_ref: str) -> str:
    """从 source_ref 取 evidence_id（# 之前的部分）。"""
    return source_ref.split("#", 1)[0].strip()


def validate_claim(c: ClaimCreate, store: ClaimStore) -> list[str]:
    """promotion 校验（SPEC-011 声明管理 API 与 ingest 共用）：
    来源存在 / 实体已注册 / 语句非空且不超长。"""
    reasons: list[str] = []
    ev_ref = _evidence_ref(c.source_ref) if c.source_ref else ""
    if not c.source_ref or not ev_ref:
        reasons.append("来源引用缺失（source_ref）")
    elif store.get_evidence(ev_ref) is None:
        reasons.append(f"来源 {ev_ref} 不存在")
    if store.get_entity(c.entity_id) is None:
        reasons.append(f"实体 {c.entity_id} 未注册")
    statement = c.statement.strip()
    if not statement:
        reasons.append("声明语句为空")
    elif len(statement) > MAX_STATEMENT_LEN:
        reasons.append(f"声明语句超长 (> {MAX_STATEMENT_LEN})")
    return reasons


@dataclass
class IngestReport:
    entities: int = 0
    sources: int = 0
    evidence: int = 0
    claims: int = 0
    rejected: list[str] = field(default_factory=list)

    def summary(self) -> str:
        parts = [
            f"entities={self.entities}", f"sources={self.sources}",
            f"evidence={self.evidence}", f"claims={self.claims}",
        ]
        if self.rejected:
            parts.append(f"rejected={len(self.rejected)}")
        return "导入完成： " + ", ".join(parts)


def ingest(path: str | Path, store: ClaimStore) -> IngestReport:
    """导入 JSON/YAML 知识文件，做 promotion 轻量校验。"""
    p = Path(path)
    data = yaml.safe_load(p.read_text(encoding="utf-8")) if p.suffix.lower() in (".yaml", ".yml") else json.loads(p.read_text(encoding="utf-8"))
    report = IngestReport()

    # 1) entities
    for e in data.get("entities", []) or []:
        store.upsert_entity(Entity(**e))
        report.entities += 1

    # 2) sources
    for s in data.get("sources", []) or []:
        store.upsert_source(Source(**s))
        report.sources += 1

    # 3) evidence
    for ev in data.get("evidence", []) or []:
        store.upsert_evidence(Evidence(**ev))
        report.evidence += 1

    # 4) claims（promotion 校验，复用 validate_claim）
    for c in data.get("claims", []) or []:
        try:
            cc = ClaimCreate(**c)
        except Exception as e:  # pydantic 校验失败：字段缺失
            report.rejected.append(f"{c.get('claim_id', '?')}: 字段不完整 ({e})")
            continue
        reasons = validate_claim(cc, store)
        if reasons:
            report.rejected.append(f"{cc.claim_id}: " + "; ".join(reasons))
            continue
        store.upsert_claim(Claim(
            claim_id=cc.claim_id, entity_id=cc.entity_id, statement=cc.statement.strip(),
            source_ref=cc.source_ref, page=cc.page, status="approved",
        ))
        report.claims += 1

    return report


def main(argv: Optional[list[str]] = None) -> int:
    import argparse

    from .store import SqliteClaimStore

    parser = argparse.ArgumentParser(description="导入知识数据到网关存储")
    parser.add_argument("--input", required=True, help="知识数据文件 (JSON/YAML)")
    parser.add_argument("--db", default="gateway.db", help="SQLite 数据库路径")
    args = parser.parse_args(argv)

    store = SqliteClaimStore(args.db)
    try:
        report = ingest(args.input, store)
        print(report.summary())
        for r in report.rejected:
            print(f"  ✗ {r}")
        return 0
    finally:
        store.close()


if __name__ == "__main__":
    sys.exit(main())
