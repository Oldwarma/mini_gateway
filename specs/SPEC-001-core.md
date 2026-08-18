---
spec_id: SPEC-001
title: 核心领域模型与基础设施 (core)
status: approved
area: core
path: src/gateway/core/**
adrs: [ADR-0001]
author: joema
created: 2026-08-18
updated: 2026-08-18
---

## 1. 背景 / 动机

运行时各层共享的领域模型、配置加载、LLM adapter 与追踪存储。是其余模块的公共底座。

## 2. 目标（Goals）

- 统一 Pydantic 领域模型（Entity/Source/Evidence/Claim/AnswerContract/AskRequest/AskResponse/Trace）
- 配置可加载（config.yaml → Config，含 llm/gate/composition/sources）
- LLM 可替换（provider 注入，支持 openai / anthropic / none）
- 每次请求可审计（TraceStore：create/get）

## 3. 非目标（Non-Goals）

- 不含业务路由 / 组合 / 验证逻辑（由对应模块负责）

## 4. 验收标准（Acceptance Criteria）

- [ ] AC-1: schemas 全部模型可实例化、可序列化、可反序列化
- [ ] AC-2: load_config 能读取 config.yaml 生成 Config
- [ ] AC-3: NullProvider 抛 NoLLMConfiguredError（触发回退路径）
- [ ] AC-4: TraceStore create/get 往返一致（含 agent 字段）
- [ ] AC-5: Trace 与 AskResponse 含 agent 字段（统一网关审计）

## 5. 涉及代码区域（area）与路径（path）

- area：`core`；覆盖路径：`src/gateway/core/**`、`src/gateway/exceptions.py`

## 6. 设计约束 / 依赖

- Pydantic v2；SQLite 标准库；LLM SDK 可选（懒加载）

## 7. 链接 ADR

- [ADR-0001 技术栈](../docs/adr/ADR-0001-tech-stack.md)

## 8. 追溯标记约定

`src/gateway/core/**` 与 `src/gateway/exceptions.py` 首行注释 `# spec: SPEC-001`

## 9. 状态变更历史

| 日期       | 变更     | 由谁   |
| ---------- | -------- | ------ |
| 2026-08-18 | 创建     | joema  |
