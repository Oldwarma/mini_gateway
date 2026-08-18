---
spec_id: SPEC-003
title: 实体路由 (router)
status: approved
area: router
path: src/gateway/router/**
adrs: [ADR-0002]
author: joema
created: 2026-08-18
updated: 2026-08-18
---

## 1. 背景 / 动机

确定问题指向哪个实体，由确定性代码完成，不交给 LLM（ADR-0002）。实体路由是感知的关键环节，出错会级联。

## 2. 目标（Goals）

- route(question, entities) -> RouterResult(entity_id | None, matched_rule, confidence)
- 三层规则：全名精确 → 别名列表 → 正则模式，逐级放宽
- 匹配失败返回 None（而非猜测）

## 3. 非目标（Non-Goals）

- 不做复杂 NER / 指代消解（v2 轻量 NER）

## 4. 验收标准（Acceptance Criteria）

- [ ] AC-1: 全名精确匹配命中（大小写不敏感）
- [ ] AC-2: 别名命中
- [ ] AC-3: 无法识别返回 RouterResult(None, None, 0.0)
- [ ] AC-4: 命中结果含 matched_rule（可追溯）

## 5. 涉及代码区域（area）与路径（path）

- area：`router`；覆盖路径：`src/gateway/router/**`

## 6. 设计约束 / 依赖

- 纯标准库（正则）；依赖 core.schemas.Entity 与 core.schemas.RouterResult

## 7. 链接 ADR

- [ADR-0002 实体路由代码驱动](../docs/adr/ADR-0002-entity-router-code-driven.md)

## 8. 追溯标记约定

`src/gateway/router/**` 首行注释 `# spec: SPEC-003`

## 9. 状态变更历史

| 日期       | 变更     | 由谁   |
| ---------- | -------- | ------ |
| 2026-08-18 | 创建     | joema  |
