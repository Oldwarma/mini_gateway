---
spec_id: SPEC-011
title: 声明管理 API (claims)
status: approved
area: claims
path: src/gateway/api/**, src/gateway/knowledge/**
adrs: [ADR-0005]
author: joema
created: 2026-08-18
updated: 2026-08-18
---

## 1. 背景 / 动机

让用户通过界面录入声明（实体/来源/证据/声明），提交时实时跑 promotion 校验，录入即生效。

## 2. 目标（Goals）

- `GET/POST /v1/entities`、`GET/POST /v1/sources`、`GET/POST /v1/evidence`、`GET /v1/claims?entity_id=`、`POST /v1/claims`
- `POST /v1/claims` 返回 `{accepted, claim_id?, reasons[]}`，复用 `ingest.validate_claim`
- 校验规则：source_ref 指向的证据存在、entity_id 已注册、statement 非空且 ≤ 200

## 3. 非目标（Non-Goals）

- 编辑 / 删除 / 批量导入 UI（v2；批量仍走文件 ingest）

## 4. 验收标准（Acceptance Criteria）

- [ ] AC-1: 合法声明返回 accepted=true 并写入 claims 表
- [ ] AC-2: 来源不存在 / 实体未注册 / 语句为空 → accepted=false + 具体原因
- [ ] AC-3: `GET /v1/claims?entity_id=` 返回该实体声明列表

## 5. 涉及代码区域（area）与路径（path）

- area：`claims`；覆盖路径：`src/gateway/api/routes.py`、`src/gateway/knowledge/**`
  （API 路径已由 SPEC-007 覆盖，本 spec 定义声明管理的行为与校验）

## 6. 设计约束 / 依赖

- 复用 `knowledge/ingest.py` 抽取的共享 `validate_claim(claim, store)`

## 7. 链接 ADR

- [ADR-0005 知识层 v1](../docs/adr/ADR-0005-knowledge-layer-v1.md)

## 8. 追溯标记约定

相关代码位于 `src/gateway/api/routes.py` 与 `src/gateway/knowledge/**`

## 9. 状态变更历史

| 日期       | 变更     | 由谁   |
| ---------- | -------- | ------ |
| 2026-08-18 | 创建     | joema  |
