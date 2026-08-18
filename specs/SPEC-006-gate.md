---
spec_id: SPEC-006
title: 七维验证门与响应组装 (validate + response)
status: approved
area: gate
path: src/gateway/validate/**, src/gateway/response/**
adrs: [ADR-0004]
author: joema
created: 2026-08-18
updated: 2026-08-18
---

## 1. 背景 / 动机

答案输出给用户之前必须同时通过七道检查（ADR-0004），并组装响应 + 写审计追踪。

## 2. 目标（Goals）

- gate.run(ctx) -> ValidationReport：七项检查（来源锚定/实体匹配/追踪完整/输出清洁/接口/延迟/组合冲突）并行执行
- response.build：组装 AskResponse + 写 traces 表（selected_claims/path/validation/answer）

## 3. 非目标（Non-Goals）

- 验证项③⑤⑦ 为 v1 简化实现（全链路 trace / 路径一致性 / 基础矛盾检查）

## 4. 验收标准（Acceptance Criteria）

- [ ] AC-1: 七项检查逐项判定通过/拒绝，report.all_pass 正确
- [ ] AC-2: 来源缺失的声明被检查①拒绝
- [ ] AC-3: 组合冲突（矛盾声明）被检查⑦拒绝
- [ ] AC-4: response.build 后 traces 表可查到记录

## 5. 涉及代码区域（area）与路径（path）

- area：`gate`；覆盖路径：`src/gateway/validate/**`、`src/gateway/response/**`

## 6. 设计约束 / 依赖

- 依赖 core.schemas、core.trace、knowledge.store

## 7. 链接 ADR

- [ADR-0004 七维验证门](../docs/adr/ADR-0004-validation-gate.md)

## 8. 追溯标记约定

`src/gateway/validate/**`、`src/gateway/response/**` 首行注释 `# spec: SPEC-006`

## 9. 状态变更历史

| 日期       | 变更     | 由谁   |
| ---------- | -------- | ------ |
| 2026-08-18 | 创建     | joema  |
