---
spec_id: SPEC-009
title: 聊天界面 (ui)
status: approved
area: ui
path: src/gateway/ui/**
adrs: []
author: joema
created: 2026-08-18
updated: 2026-08-18
---

## 1. 背景 / 动机

让用户通过浏览器与网关对话，直观看到答案与可追踪信息（实体、置信度、依据声明、审计链接）。

## 2. 目标（Goals）

- `GET /chat` 返回单页聊天界面
- 提问调用同源 `POST /v1/ask`，展示答案 + 实体/置信度/依据声明 + 追踪链接
- "无法识别实体"、验证门拒绝等场景有友好提示

## 3. 非目标（Non-Goals）

- 不做登录鉴权 / 会话历史持久化（v1 单页、无状态）

## 4. 验收标准（Acceptance Criteria）

- [ ] AC-1: `GET /chat` 返回 200 与 HTML 页面
- [ ] AC-2: 浏览器输入问题可得到答案并展示合约信息
- [ ] AC-3: 展示 trace_id，且可跳转 `GET /v1/traces/{id}` 查看审计
- [ ] AC-4: 空问题/网络错误有提示，不白屏

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
