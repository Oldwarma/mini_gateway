---
spec_id: SPEC-007
title: HTTP 接口与入口 (api)
status: approved
area: api
path: src/gateway/api/**, src/gateway/main.py
adrs: [ADR-0001]
author: joema
created: 2026-08-18
updated: 2026-08-18
---

## 1. 背景 / 动机

对外暴露网关能力：提交提问、查询审计追踪、健康检查。接口契约见 docs/design/api.md。

## 2. 目标（Goals）

- POST /v1/ask：返回结构化答案 + trace_id + composition_path
- GET /v1/traces/{trace_id}：返回审计追踪
- GET /health：探活（db / llm_configured）
- FastAPI 自动生成 /docs（Swagger）与 /openapi.json

## 3. 非目标（Non-Goals）

- 不做鉴权 / 限流（v1 内部工具）

## 4. 验收标准（Acceptance Criteria）

- [ ] AC-1: /v1/ask 返回结构符合 api.md（answer/contract/trace_id/composition_path）
- [ ] AC-2: /v1/traces/{id} 可查到对应审计记录；不存在返回 404
- [ ] AC-3: /health 返回 status/db/llm_configured
- [ ] AC-4: 实体无法识别返回 200 + 提示语（confidence=0）
- [ ] AC-5: `GET /chat` 提供聊天界面（HTML）；`GET /` 重定向到 `/chat`
- [ ] AC-6: `GET /v1/agents` 列出已注册智能体（name/version/description）
- [ ] AC-7: `POST /v1/agents/{name}/ask` 统一提问，AskResponse 含 agent；未知智能体 404
- [ ] AC-8: `GET /v1/traces` 返回最近 trace 列表（limit、agent 过滤）
- [ ] AC-9: 声明管理端点：`GET/POST /v1/entities`、`/v1/sources`、`/v1/evidence`、`GET/POST /v1/claims`（行为见 SPEC-011）

## 5. 涉及代码区域（area）与路径（path）

- area：`api`；覆盖路径：`src/gateway/api/**`、`src/gateway/main.py`

## 6. 设计约束 / 依赖

- FastAPI + uvicorn；依赖 compose.boundary、response.builder、core.trace

## 7. 链接 ADR

- [ADR-0001 技术栈](../docs/adr/ADR-0001-tech-stack.md)

## 8. 追溯标记约定

`src/gateway/api/**`、`src/gateway/main.py` 首行注释 `# spec: SPEC-007`

## 9. 状态变更历史

| 日期       | 变更     | 由谁   |
| ---------- | -------- | ------ |
| 2026-08-18 | 创建     | joema  |
