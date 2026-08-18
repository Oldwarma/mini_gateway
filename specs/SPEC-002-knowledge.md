---
spec_id: SPEC-002
title: 知识存储与轻量导入 (knowledge)
status: approved
area: knowledge
path: src/gateway/knowledge/**
adrs: [ADR-0001, ADR-0005]
author: joema
created: 2026-08-18
updated: 2026-08-18
---

## 1. 背景 / 动机

声明（Claims）的落库与导入：把整理好的知识导入存储，运行时才能被选择器检索（ADR-0005 轻量导入方案）。

## 2. 目标（Goals）

- ClaimStore 抽象 + SqliteClaimStore 实现（entities/sources/evidence/claims + claims_fts）
- query_claims：实体过滤 + FTS5 相关性排序，仅返回 approved
- ingest：从 JSON/YAML 导入，做 promotion 轻量校验（source_ref 存在、entity 已注册、statement 非空）

## 3. 非目标（Non-Goals）

- 不包含完整离线管线（抓取/抽取/人工审核）——v2

## 4. 验收标准（Acceptance Criteria）

- [ ] AC-1: 建表成功（含 claims_fts 与同步 trigger）
- [ ] AC-2: query_claims 按实体过滤 + FTS 排序返回正确
- [ ] AC-3: 合法数据可导入；非法数据（无来源/实体未注册/空 statement）被拒并报告原因

## 5. 涉及代码区域（area）与路径（path）

- area：`knowledge`；覆盖路径：`src/gateway/knowledge/**`

## 6. 设计约束 / 依赖

- 标准库 sqlite3；FTS5；数据文件在 `data/`

## 7. 链接 ADR

- [ADR-0001 技术栈](../docs/adr/ADR-0001-tech-stack.md)
- [ADR-0005 知识层 v1](../docs/adr/ADR-0005-knowledge-layer-v1.md)

## 8. 追溯标记约定

`src/gateway/knowledge/**` 首行注释 `# spec: SPEC-002`

## 9. 状态变更历史

| 日期       | 变更     | 由谁   |
| ---------- | -------- | ------ |
| 2026-08-18 | 创建     | joema  |
