# spec: SPEC-002
"""把 Markdown 文档按 ## 章节切分为 evidence 证据（doc-qa 种子数据）。"""
from __future__ import annotations

import re
import sys
from pathlib import Path
from typing import Optional

from ..core.schemas import Evidence, Source
from .store import SqliteClaimStore


def split_document(text: str, doc_id: str, source_id: str) -> list[tuple[str, str]]:
    """按二级标题切分，返回 [(title, content), ...]。"""
    parts = re.split(r"(?m)^##\s+", text)
    sections: list[tuple[str, str]] = []
    for part in parts[1:]:
        title_line, _, body = part.partition("\n")
        title = f"{doc_id} · {title_line.strip()}"
        content = body.strip()
        if content:
            sections.append((title, content))
    return sections


def main(argv: Optional[list[str]] = None) -> int:
    import argparse

    parser = argparse.ArgumentParser(description="把 Markdown 文档切成 evidence（doc-qa 用）")
    parser.add_argument("--input", required=True, help="Markdown 文档路径")
    parser.add_argument("--doc-id", default="doc-harness")
    parser.add_argument("--source-id", default="doc-harness")
    parser.add_argument("--db", default="gateway.db")
    args = parser.parse_args(argv)

    text = Path(args.input).read_text(encoding="utf-8")
    store = SqliteClaimStore(args.db)
    try:
        store.upsert_source(Source(id=args.source_id, name="文档知识库", type="file", policy="allowed"))
        sections = split_document(text, args.doc_id, args.source_id)
        for i, (title, content) in enumerate(sections):
            store.upsert_evidence(Evidence(
                id=f"{args.doc_id}-{i:03d}", source_id=args.source_id,
                title=title, content=content,
            ))
        print(f"已切分 {len(sections)} 个证据段落 → evidence")
        return 0
    finally:
        store.close()


if __name__ == "__main__":
    sys.exit(main())
