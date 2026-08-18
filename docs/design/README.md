# 设计文档

存放需要展开的复杂设计 / 架构方案。

## 约定

- 命名：`<slug>.md`（小写短横线，不编号），如 `architecture.md`。
- 每个设计文档开头注明：
  - **对应 spec**：`SPEC-NNN`
  - **相关 ADR**：`ADR-NNNN`
- 文档类写入不受 SDD hook 限制，可随时起草。

## 当前文档

- [`architecture.md`](architecture.md) —— 网关架构方案 v1：把《可追踪的Harness架构.md》中的
  运行时引擎层 / 知识层 / 基础设施层选型落地为迷你版架构（对应 ADR-0001 ~ 0005）。
