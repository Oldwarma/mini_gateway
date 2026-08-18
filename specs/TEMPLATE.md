# SPEC-000: 规格模板

> 用法：复制本文件为 `specs/SPEC-NNN-<slug>.md`，替换 `spec_id` 并填写以下各节。
> 每个功能 / 组件一份规格，先于任何代码存在（由 `.claude/settings.json` 的 PreToolUse hook 强制）。

```yaml
---
spec_id: SPEC-000            # 占位，复制时改为实际 ID（如 SPEC-001）
title: <功能名称>
status: draft                # draft | approved | implemented | deprecated
area: <area-slug>            # 唯一短名，如 gateway/runtime（须与 specs/INDEX.md 一致）
path: <path-glob>            # 覆盖的代码路径通配符，如 src/gateway/runtime/**
adrs: []                     # 关联的架构决策记录 ID 列表，如 [ADR-0001]
author: <name>
created: YYYY-MM-DD
updated: YYYY-MM-DD
---
```

## 1. 背景 / 动机

为什么需要这个功能？要解决什么问题？

## 2. 目标（Goals）

- 功能目标 1
- 功能目标 2

## 3. 非目标（Non-Goals）

- 明确不做的事 / 边界

## 4. 验收标准（Acceptance Criteria）

每条必须可测试，测试用例命名直接对应：

- [ ] AC-1: <可验证的行为>
- [ ] AC-2: <可验证的行为>

## 5. 涉及代码区域（area）与路径（path）

- area：`<area-slug>`
- 覆盖路径：`<path-glob>`（与 specs/INDEX.md 一致）

## 6. 设计约束 / 依赖

- 技术约束、依赖的组件 / 外部系统

## 7. 链接 ADR

- [ADR-NNNN: <决策标题>](../docs/adr/ADR-NNNN-<slug>.md)

## 8. 追溯标记约定

以下代码文件必须在首行（或模块 docstring）引用本规格：

```python
# spec: SPEC-001
```

```go
// spec: SPEC-001
```

## 9. 状态变更历史

| 日期       | 变更     | 由谁   |
| ---------- | -------- | ------ |
| YYYY-MM-DD | 创建草案 | <name> |
