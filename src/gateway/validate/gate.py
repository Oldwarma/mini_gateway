# spec: SPEC-006
"""七维验证门（详细设计 §4.8，ADR-0004）：答案输出前必须全部通过。"""
from __future__ import annotations

import re

from ..core.schemas import ValidationContext, ValidationReport
from ..knowledge.store import ClaimStore


def _check_source_anchored(ctx: ValidationContext, store: ClaimStore) -> bool:
    """① 来源锚定：每个声明都有 source_ref，且指向的证据存在。"""
    for c in ctx.claims:
        ev_id = c.source_ref.split("#", 1)[0].strip() if c.source_ref else ""
        if not c.source_ref or not ev_id:
            return False
        if store.get_evidence(ev_id) is None:
            return False
    return True


def _check_entity_match(ctx: ValidationContext, store: ClaimStore) -> bool:
    """② 实体路由：声明归属与路由结果一致。"""
    if not ctx.entity_id:
        return False
    return all(c.entity_id == ctx.entity_id for c in ctx.claims)


def _check_trace_complete(ctx: ValidationContext, store: ClaimStore) -> bool:
    """③ 追踪完整性：trace 关键字段齐全。"""
    return bool(ctx.trace_id and ctx.question and ctx.claims is not None and ctx.answer.strip())


def _check_output_clean(ctx: ValidationContext, store: ClaimStore) -> bool:
    """④ 输出清洁：答案非空、不含明显越界断言（v1 简化：非空 + 无敏感占位）。"""
    answer = ctx.answer.strip()
    if not answer:
        return False
    forbidden = ("[待补充]", "TODO", "None", "nan")
    return not any(tok in answer for tok in forbidden)


def _check_interface(ctx: ValidationContext, store: ClaimStore) -> bool:
    """⑤ 接口行为：组合路径与尝试标记一致（llm 路径必须尝试过 LLM）。"""
    if ctx.path == "llm":
        return ctx.llm_attempted
    return True


def _check_latency(ctx: ValidationContext, store: ClaimStore, budget: float) -> bool:
    """⑥ 延迟：全程耗时在预算内。"""
    if ctx.started_at and ctx.ended_at:
        return (ctx.ended_at - ctx.started_at) <= budget
    return True


def _check_composition(ctx: ValidationContext, store: ClaimStore) -> bool:
    """⑦ 组合边界行为：同实体矛盾声明（除数字外完全相同但数值不同）判定冲突。"""
    claims = ctx.claims
    for i in range(len(claims)):
        for j in range(i + 1, len(claims)):
            a, b = claims[i].statement, claims[j].statement
            a_no_digits = re.sub(r"\d+", "", a)
            b_no_digits = re.sub(r"\d+", "", b)
            if a_no_digits == b_no_digits and a != b:
                return False
    return True


def run(ctx: ValidationContext, store: ClaimStore, gate_budget: float = 5.0) -> ValidationReport:
    """执行七项检查，逐项记录结果。

    注：v1 顺序执行（SQLite 连接非线程安全，多线程访问会抛错；检查本身很快）。
    """
    checks = {
        "source_anchored": lambda: _check_source_anchored(ctx, store),
        "entity_match": lambda: _check_entity_match(ctx, store),
        "trace_complete": lambda: _check_trace_complete(ctx, store),
        "output_clean": lambda: _check_output_clean(ctx, store),
        "interface": lambda: _check_interface(ctx, store),
        "latency": lambda: _check_latency(ctx, store, gate_budget),
        "composition": lambda: _check_composition(ctx, store),
    }
    results: dict[str, bool] = {}
    for key, fn in checks.items():
        try:
            results[key] = bool(fn())
        except Exception:
            results[key] = False
    return ValidationReport(results=results, all_pass=all(results.values()))
