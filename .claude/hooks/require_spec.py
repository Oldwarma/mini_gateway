#!/usr/bin/env python3
"""PreToolUse hook：写非文档代码前必须有覆盖它的 Spec。

读取 specs/INDEX.md（area|path-glob|spec-id 映射表），
对本次写入的文件做判定：
  - 文档 / 配置类（specs/ docs/ .claude/、*.md、CLAUDE.md、README.md、.gitignore）→ 放行
  - 代码文件：命中 INDEX 中任一 path-glob → 放行；否则 block，提示先运行 /spec
  - specs/INDEX.md 不存在或为空 → 视为"无规格"，所有代码写入一律 block（逼先建 spec）

环境变量：
  CLAUDE_FILE_PATHS   写入的文件路径（换行分隔）
  CLAUDE_CWD / CLAUDE_PROJECT_DIR
stdin：JSON payload（tool_name / tool_input / cwd 等），作环境变量兜底。
stdout：无输出 = 默认 allow；block 时输出 {"decision":"block","reason":...}。
"""

import fnmatch
import json
import os
import sys

DOC_PREFIXES = ("specs/", "docs/", ".claude/")
DOC_FILES = {"CLAUDE.md", "README.md", ".gitignore", ".gitattributes"}


def is_document(rel: str) -> bool:
    """文档/配置类文件永远放行，避免 hook 自锁。"""
    return (
        rel.startswith(DOC_PREFIXES)
        or rel.endswith(".md")
        or rel in DOC_FILES
    )


def load_mappings(project_root: str):
    """解析 specs/INDEX.md，返回 [(path_glob, spec_id), ...]。"""
    idx = os.path.join(project_root, "specs", "INDEX.md")
    if not os.path.isfile(idx):
        return []
    out = []
    try:
        with open(idx, encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith(("#", "<!--")):
                    continue
                parts = line.split("|")
                if len(parts) == 3 and all(p.strip() for p in parts):
                    out.append((parts[1].strip(), parts[2].strip()))
    except OSError:
        return []  # 读失败按"无规格"处理；hook 自身故障不阻塞开发（返回 [] 会拦代码，可人工处理）
    return out


def main() -> int:
    try:
        payload = json.load(sys.stdin) if not sys.stdin.isatty() else {}
    except (json.JSONDecodeError, OSError):
        payload = {}

    project_root = (
        os.environ.get("CLAUDE_PROJECT_DIR")
        or os.environ.get("CLAUDE_CWD")
        or payload.get("cwd")
        or os.getcwd()
    )

    # 本次写入的文件列表：环境变量为主，stdin payload 兜底
    raw = os.environ.get("CLAUDE_FILE_PATHS", "") or ""
    files = [p for p in raw.splitlines() if p.strip()]
    if not files:
        ti = payload.get("tool_input") or {}
        candidates = []
        for key in ("file_path", "files", "notebook_path"):
            v = ti.get(key)
            if isinstance(v, str):
                candidates.append(v)
            elif isinstance(v, list):
                candidates.extend(str(x) for x in v)
        files = [p for p in candidates if p]

    if not files:
        return 0  # 无文件信息，放行避免误拦

    mappings = load_mappings(project_root)
    offenders = []
    for f in files:
        if not f:
            continue
        if os.path.isabs(f):
            try:
                rel = os.path.relpath(f, project_root)
            except ValueError:
                rel = f
        else:
            rel = f
        if rel.startswith(".."):  # 项目外文件，无法归类，放行
            continue
        if is_document(rel):
            continue
        covered = any(fnmatch.fnmatchcase(rel, glob_) for glob_, _ in mappings)
        if not covered:
            offenders.append(rel)

    if offenders:
        covered_list = [g for g, _ in mappings] or ["（空，尚无任何规格）"]
        reason = (
            "PreToolUse 拦截（SDD 规则）：以下文件无对应 Spec，禁止直接写代码。\n"
            "文件：" + ", ".join(offenders) + "\n"
            "当前 specs/INDEX.md 覆盖的代码路径：" + ", ".join(covered_list) + "\n"
            "处理：先运行 /spec 创建覆盖对应代码区域的规格，或运行 /adr 记录相关决策；\n"
            "规格就绪并在 specs/INDEX.md 注册后重试。（specs/ docs/ .claude/ *.md 等文档写入不受此限制）"
        )
        print(json.dumps({
            "decision": "block",
            "reason": reason,
            "suppressOutput": False,
            "message": "blocked-by-spec-hook",
        }, ensure_ascii=False))
        return 2  # 非零退出 → 生效 block

    return 0  # 无违规：不输出 JSON，默认 allow


if __name__ == "__main__":
    sys.exit(main())
