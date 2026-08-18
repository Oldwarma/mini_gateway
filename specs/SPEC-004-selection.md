---
spec_id: SPEC-004
title: 声明选择与合约构建 (selector + contract)
status: approved
area: selection
path: src/gateway/selector/**, src/gateway/contract/**
adrs: [ADR-0001, ADR-0002]
author: joema
created: 2026-08-18
updated: 2026-08-18
---

## 1. 背景 / 动机

从声明库中选取与问题相关的声明（实体过滤 + FTS 相关性），并构建约束输出格式的答案合约。

## 2. 目标（Goals）

- select(entity_id, question, limit)：实体过滤 + FTS5 排序，仅返回 approved 声明
- build(entity_id, claims) -> AnswerContract（key_points/basis/confidence 加权）

## 3. 非目标（Non-Goals）

- 不做语义向量检索（v1 FTS，v2 pgvector）

## 4. 验收标准（Acceptance Criteria）

- [ ] AC-1: select 命中相关声明（按 FTS 相关性排序）
- [ ] AC-2: 无可用声明返回空列表
- [ ] AC-3: build 的 basis 与传入声明一致，confidence ∈ [0,1]

## 5. 涉及代码区域（area）与路径（path）

- area：`selection`；覆盖路径：`src/gateway/selector/**`、`src/gateway/contract/**`

## 6. 设计约束 / 依赖

- 依赖 knowledge.store.ClaimStore 与 core.schemas

## 7. 链接 ADR

- [ADR-0001 技术栈](../docs/adr/ADR-0001-tech-stack.md)
- [ADR-0002 实体路由](../docs/adr/ADR-0002-entity-router-code-driven.md)

## 8. 追溯标记约定

`src/gateway/selector/**`、`src/gateway/contract/**` 首行注释 `# spec: SPEC-004`

## 9. 状态变更历史

| 日期       | 变更     | 由谁   |
| ---------- | -------- | ------ |
| 2026-08-18 | 创建     | joema  |
