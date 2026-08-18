# mini_gateway 开发规则（SDD · 规格驱动开发）

> 本文件是本仓库的**开发规则入口**，Claude Code 启动时自动加载。所有开发工作必须遵守。

## 1. 项目与核心哲学

- **智能体迷你网关 (Agent Mini Gateway)**：一个基于**可追踪 Harness 架构**的智能体网关。
- 核心公式：`Agent = LLM + Harness` —— **把 LLM 压缩到最小范围，用确定性代码包围它**。
- 核心原则：**可追踪性**（来源锚定、实体路由、追踪、输出清洁、语言合约）。
- 完整架构说明见《[可追踪的Harness架构.md](可追踪的Harness架构.md)》。

## 2. 开发工作流（SDD，每个功能强制按序）

1. **起草 Spec** → `specs/SPEC-NNN-<slug>.md`（**先于任何代码**）
2. **涉及架构取舍/技术选型** → 先记 ADR → `docs/adr/ADR-NNNN.md`
3. **复杂设计** → 设计文档 → `docs/design/<slug>.md`（网关架构方案放这里）
4. **实现代码**（每个代码文件头部引用其 spec ID）
5. **测试**（针对 spec 的验收标准，全部可自动化验证）
6. **对照 Definition of Done 清单收尾**

> **规则由 PreToolUse hook 强制**：写非文档代码前必须存在覆盖它的 spec（见 §7）。
> 用 `/spec` 快速创建规格，用 `/adr` 快速记录决策。

## 3. 文档体系与位置约定

| 文档类型 | 位置 | 命名 |
| -------- | ---- | ---- |
| 规格 Spec | `specs/` | `SPEC-NNN-<slug>.md` |
| 架构决策 ADR | `docs/adr/` | `ADR-NNNN-<slug>.md` |
| 设计文档 | `docs/design/` | `<slug>.md`（小写连字符，不编号） |
| 规则入口 | 仓库根 | `CLAUDE.md` |

## 4. 编号规则

- **SPEC-NNN**：3 位十进制，从 `001` 递增，**永不复用**；废弃用 `status: deprecated` 标记。
- **ADR-NNNN**：4 位十进制，从 `0001` 递增，**永不复用**。
- 设计文档不编号，按主题 slug 命名。
- 每个 spec 在 `specs/INDEX.md` 注册一行：`<area>|<path-glob>|<spec-id>`（hook 依赖此表）。

## 5. 追溯规则

- 代码文件首行注释引用其 spec，例如：
  - Python：`# spec: SPEC-001`
  - Go：`// spec: SPEC-001`
- spec frontmatter `adrs: [...]` 引用相关 ADR；ADR 的「涉及 spec」反向引用 spec。
- Commit message 前缀：`SPEC-001: <描述>`。

## 6. Definition of Done（DoD）清单

功能完成前，以下每项必须勾选：

- [ ] 存在已批准的 Spec（`specs/SPEC-NNN`，状态 `approved`）
- [ ] 规格中所有验收标准（AC）均有对应测试且通过
- [ ] 涉及的技术选型/取舍已记录 ADR（如有）
- [ ] 代码文件头部含追溯标记（`# spec: SPEC-NNN`）
- [ ] `specs/INDEX.md` 已注册对应代码区域
- [ ] 文档已同步更新（README / 设计文档 / ADR）
- [ ] Commit message 带 spec 前缀

## 7. 强制机制与兜底

- **PreToolUse hook**（`.claude/settings.json` → `.claude/hooks/require_spec.py`）：
  - 写非文档、非 `.md` 的代码文件时，检查 `specs/INDEX.md` 是否覆盖其路径；
  - 未覆盖 → **block**，提示先运行 `/spec`。
- **文档类永远不被拦**：`specs/`、`docs/`、`.claude/`、`*.md`、`README.md`、`CLAUDE.md`、`.gitignore`。
- **紧急修复流程**：先 `/spec` 建一个最小规格（只填背景 + 1 条验收标准），再改代码，事后再补全。

## 8. 例外说明

- 纯文档/配置改动不受 spec 限制（§7 文档类白名单）。
- 项目外路径（`..`）写入不拦截。
- hook 本身故障时**默认放行**（fail-open），避免阻塞开发。
