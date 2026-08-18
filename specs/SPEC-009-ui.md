---
spec_id: SPEC-009
title: 界面（可追踪问答 / 声明管理 / 审计中心 / 智能体总览）
status: approved
area: ui
path: src/gateway/ui/**
adrs: []
author: joema
created: 2026-08-18
updated: 2026-08-18
---

## 1. 背景 / 动机

让用户通过浏览器与网关交互：向任意智能体提问并查看可追踪信息、录入声明、浏览审计、查看智能体总览。

## 2. 目标（Goals）

- 多页面：`/chat`（可追踪问答，智能体下拉）、`/claims`（声明录入，实时校验）、`/traces`（审计中心）、`/agents`（智能体总览）
- 共享顶部导航栏；无外部 CDN 依赖（内联 CSS/JS）
- 可追踪问答调用 `POST /v1/agents/{name}/ask`，展示答案 + 验证结果 + 追踪链接
- 声明录入调用 `/v1/claims` 等，实时显示 accepted/rejected 原因

## 3. 非目标（Non-Goals）

- 不做登录鉴权 / 会话历史持久化 / 响应式移动端精修

## 4. 验收标准（Acceptance Criteria）

- [ ] AC-1: 四个页面均可访问（HTTP 200），导航栏互通
- [ ] AC-2: 可追踪问答：选智能体 → 提问 → 展示答案 + agent + trace 链接
- [ ] AC-3: 声明录入：提交声明显示 accepted 或 rejected + 具体原因
- [ ] AC-4: 审计中心：列出 trace（agent/问题/时间/通过），点击看详情
- [ ] AC-5: 智能体总览：列出已注册智能体
- [ ] AC-6: 空问题/网络错误有提示，不白屏

## 5. 涉及代码区域（area）与路径（path）

- area：`ui`；覆盖路径：`src/gateway/ui/**`

## 6. 设计约束 / 依赖

- 纯静态 HTML + 原生 JS，无外部 CDN 依赖（内联 CSS/JS）
- 依赖 API 层 `/v1/ask`、`/v1/traces/{id}`（SPEC-007）

## 7. 链接 ADR

- 无（界面层，不涉及架构决策）

## 8. 追溯标记约定

`src/gateway/ui/**` 首行注释 `# spec: SPEC-009`

## 9. 状态变更历史

| 日期       | 变更     | 由谁   |
| ---------- | -------- | ------ |
| 2026-08-18 | 创建     | joema  |
