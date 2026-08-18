---
spec_id: SPEC-010
title: 智能体抽象与统一网关 (agents + gateway)
status: approved
area: agents
path: src/gateway/agents/**, src/gateway/gateway.py
adrs: [ADR-0003, ADR-0004]
author: joema
created: 2026-08-18
updated: 2026-08-18
---

## 1. 背景 / 动机

把单智能体网关升级为统一管理多个智能体的平台：每个智能体 = 一个标准接口（接收问题→返回答案），网关对每个智能体统一施加验证 + 审计 + 追踪。

## 2. 目标（Goals）

- `Agent` protocol：`name / version / description / handle(ctx) -> AgentAnswer`
- `AgentRegistry`：注册 / 列表 / 按名获取
- `AgentGateway.ask(agent, question)`：路由 → handle → 统一通用验证 → 合并领域验证 → 写统一 trace（含 agent 字段）
- 内置智能体：claim-info（声明问答）、doc-qa（文档问答）、http-agent（外部接入）

## 3. 非目标（Non-Goals）

- 分布式调度、多租户、负载均衡（v2）

## 4. 验收标准（Acceptance Criteria）

- [ ] AC-1: 注册 3 个智能体，`GET /v1/agents` 列出
- [ ] AC-2: `POST /v1/agents/{name}/ask` 返回 AskResponse（含 agent 字段）；未知 agent 返回 404
- [ ] AC-3: 每个回答写统一 trace，含 agent 字段
- [ ] AC-4: 外部 http-agent 走通（HTTP 转发 + 统一验证 + 审计）

## 5. 涉及代码区域（area）与路径（path）

- area：`agents`；覆盖路径：`src/gateway/agents/**`、`src/gateway/gateway.py`

## 6. 设计约束 / 依赖

- 复用现有 `router/entity_router.py`、`selector/claim_selector.py`、`contract/builder.py`、`compose/boundary.py`、`validate/gate.py`
- 统一验证 = 通用检查（answer 非空、agent 已知、延迟）+ Agent 领域验证合并

## 7. 链接 ADR

- [ADR-0003 组合边界](../docs/adr/ADR-0003-composition-boundary.md)
- [ADR-0004 七维验证门](../docs/adr/ADR-0004-validation-gate.md)

## 8. 追溯标记约定

`src/gateway/agents/**`、`src/gateway/gateway.py` 首行注释 `# spec: SPEC-010`

## 9. 状态变更历史

| 日期       | 变更     | 由谁   |
| ---------- | -------- | ------ |
| 2026-08-18 | 创建     | joema  |
