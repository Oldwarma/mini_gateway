# 架构决策记录 (ADR)

记录本项目的重要架构决策，让"为什么这样做"可追溯（与项目的可追踪理念一致）。

## 何时写 ADR

满足以下任一情况就应记录一条 ADR：

- 存在**多个可选方案**需要取舍（技术选型、框架、存储等）
- 决策**影响多个模块 / 组件**
- 决策**难以推翻**或会带来迁移成本
- 决策与 spec 冲突，或反过来约束了 spec

## 编号规则

- 编号 `ADR-NNNN`：4 位十进制，从 `0001` 递增，**永不复用**。
- 命名：`ADR-NNNN-<slug>.md`（slug 为短横线小写主题词）。
- 状态流转：`提议 → 已接受 → 已实现 → 已废弃`。

## 流程

1. 用 `/adr` 命令从 `TEMPLATE.md` 创建新记录。
2. 填写背景 / 决策 / 后果 / 替代方案。
3. 若关联已有 spec，回填该 spec frontmatter 的 `adrs` 字段。
4. 进入评审；通过后标记 `已接受`。

## 索引

- [ADR-0001: v1 技术栈选型（FastAPI + SQLite + 存储抽象）](ADR-0001-tech-stack.md)
- [ADR-0002: 实体路由由代码规则驱动（非 LLM）](ADR-0002-entity-router-code-driven.md)
- [ADR-0003: 组合边界（LLM 只管措辞 + 确定性模板回退）](ADR-0003-composition-boundary.md)
- [ADR-0004: 七维验证门（答案输出前必须全部通过）](ADR-0004-validation-gate.md)
- [ADR-0005: 知识层 v1 采用轻量导入（非完整离线管线）](ADR-0005-knowledge-layer-v1.md)
