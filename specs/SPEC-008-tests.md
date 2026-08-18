---
spec_id: SPEC-008
title: 测试场景与示例数据 (tests + data)
status: approved
area: tests
path: tests/**, data/**
adrs: [ADR-0004]
author: joema
created: 2026-08-18
updated: 2026-08-18
---

## 1. 背景 / 动机

固定验证场景（pytest，对应详细设计 §7），作为 eval 框架；示例数据支撑运行时演示。

## 2. 目标（Goals）

- T1~T7 场景：实体命中 / 别名命中 / 路由失败 / 无 LLM 回退 / 来源缺失 / 延迟预算 / 组合冲突
- data/ 提供可导入的示例知识（含可测试声明）

## 3. 非目标（Non-Goals）

- 不做 UI 测试 / 压测

## 4. 验收标准（Acceptance Criteria）

- [ ] AC-1: pytest 全绿
- [ ] AC-2: 每个场景有明确断言（答案、entity、path、validation）
- [ ] AC-3: 示例数据可被 ingest 导入

## 5. 涉及代码区域（area）与路径（path）

- area：`tests`；覆盖路径：`tests/**`、`data/**`

## 6. 设计约束 / 依赖

- pytest；httpx（TestClient）；临时 SQLite（fixture）

## 7. 链接 ADR

- [ADR-0004 七维验证门](../docs/adr/ADR-0004-validation-gate.md)

## 8. 追溯标记约定

`tests/**` 首行注释 `# spec: SPEC-008`

## 9. 状态变更历史

| 日期       | 变更     | 由谁   |
| ---------- | -------- | ------ |
| 2026-08-18 | 创建     | joema  |
