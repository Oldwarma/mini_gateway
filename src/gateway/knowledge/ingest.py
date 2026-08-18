# spec: SPEC-002
"""轻量导入器（详细设计 §4.10，ADR-0005：promotion gate 轻量版）。"""
from __future__ import annotations

import json
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

import yaml

from ..core.schemas import Claim, Entity, Evidence, Source
from .store import ClaimStore

MAX_STATEMENT_LEN = 200


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


def _evidence_ref(claim: dict) -> str:
    """从 source_ref 取 evidence_id（# 之前的部分）。"""
    ref = str(claim.get("source_ref", ""))
    return ref.split("#", 1)[0].strip()


def ingest(path: str | Path, store: ClaimStore) -> IngestReport:
    """导入 JSON/YAML 知识文件，做 promotion 轻量校验。"""
    p = Path(path)
    data = yaml.safe_load(p.read_text(encoding="utf-8")) if p.suffix.lower() in (".yaml", ".yml") else json.loads(p.read_text(encoding="utf-8"))
    report = IngestReport()

    known_evidence: set[str] = set()
    known_entities: set[str] = set()

    # 1) entities
    for e in data.get("entities", []) or []:
        store.upsert_entity(Entity(**e))
        known_entities.add(e["id"])
        report.entities += 1

    # 2) sources
    for s in data.get("sources", []) or []:
        store.upsert_source(Source(**s))
        report.sources += 1

    # 3) evidence
    for ev in data.get("evidence", []) or []:
        store.upsert_evidence(Evidence(**ev))
        known_evidence.add(ev["id"])
        report.evidence += 1

    # 4) claims（promotion 轻量校验）
    known_entities |= {e.id for e in store.list_entities()}
    for c in data.get("claims", []) or []:
        claim_id = c.get("claim_id", "?")
        ev_ref = _evidence_ref(c)
        if not ev_ref or ev_ref not in known_evidence:
            report.rejected.append(f"{claim_id}: source_ref 指向的证据不存在 ({ev_ref})")
            continue
        if c.get("entity_id") not in known_entities:
            report.rejected.append(f"{claim_id}: 实体未注册 ({c.get('entity_id')})")
            continue
        statement = str(c.get("statement", "")).strip()
        if not statement:
            report.rejected.append(f"{claim_id}: statement 为空")
            continue
        if len(statement) > MAX_STATEMENT_LEN:
            report.rejected.append(f"{claim_id}: statement 超长 (> {MAX_STATEMENT_LEN})")
            continue
        store.upsert_claim(Claim(claim_id=claim_id, entity_id=c["entity_id"], statement=statement, source_ref=c.get("source_ref", ""), page=c.get("page"), status="approved"))
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
