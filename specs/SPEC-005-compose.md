---
spec_id: SPEC-005
title: 组合边界 (compose)
status: approved
area: compose
path: src/gateway/compose/**
adrs: [ADR-0003]
author: joema
created: 2026-08-18
updated: 2026-08-18
---

## 1. 背景 / 动机

把确定性 Harness 控制与 LLM 措辞分离（ADR-0003）。LLM 只负责措辞，声明填充与路径选择由代码完成。

## 2. 目标（Goals）

- template_composer：确定性模板填充（不调 LLM）
- llm_composer：声明 + 合约 → LLM 生成自然语言答案
- boundary：默认 LLM 路径，失败回退模板，双失败抛 GateRejectedError

## 3. 非目标（Non-Goals）

- 不引入声明之外的事实；不做判断/推理

## 4. 验收标准（Acceptance Criteria）

- [ ] AC-1: 无 LLM key 时走 template 路径返回答案
- [ ] AC-2: 无声明时返回"暂无可引用数据"式答案（不报错）
- [ ] AC-3: 双路径验证均失败抛 GateRejectedError
- [ ] AC-4: 返回 ComposeResult 含 path（llm|template）

## 5. 涉及代码区域（area）与路径（path）

- area：`compose`；覆盖路径：`src/gateway/compose/**`

## 6. 设计约束 / 依赖

- 依赖 core.llm.LLMProvider、validate.gate（验证回退）、core.schemas

## 7. 链接 ADR

- [ADR-0003 组合边界](../docs/adr/ADR-0003-composition-boundary.md)

## 8. 追溯标记约定

`src/gateway/compose/**` 首行注释 `# spec: SPEC-005`

## 9. 状态变更历史

| 日期       | 变更     | 由谁   |
| ---------- | -------- | ------ |
| 2026-08-18 | 创建     | joema  |
