---
description: 记录一条架构决策 (ADR-NNNN)。
---

# /adr — 记录架构决策

按照 ADR（Architecture Decision Record）流程记录一次架构决策，让"为什么这样选"可追溯。

## 步骤

1. 向用户询问：
   - 决策主题（如 `选择 FastAPI 作为网关框架`）
   - 已考虑的方案（替代方案）
   - 倾向的选择
2. 扫描 `docs/adr/` 下所有 `ADR-NNNN-*.md`，取当前最大编号 +1 得新 ID（4 位，补零）。
3. 从 `docs/adr/TEMPLATE.md` 复制为 `docs/adr/ADR-NNNN-<slug>.md`。
4. 填写 背景 / 决策 / 后果（正负）/ 替代方案；日期用今天。
   - 若涉及已有 spec：填 frontmatter 的 `涉及 spec`，并回填该 spec frontmatter 的 `adrs` 列表。
5. 若该决策会触发新的设计工作，提示在 `docs/design/` 建立对应设计文档。
6. 向用户报告：ADR ID、文件路径、状态（默认 `提议`）。
