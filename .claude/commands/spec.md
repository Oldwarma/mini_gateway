---
description: 创建一份功能规格 (Spec)。任何代码实现之前必须先有它。
---

# /spec — 创建功能规格

按照 SDD（规格驱动开发）流程创建一个新 Spec。**写任何代码之前必须先建 Spec**（由 PreToolUse hook 强制）。

## 步骤

1. 向用户询问：
   - 规格名称 / 主题
   - 涉及代码区域的唯一短名 `area`（如 `gateway/runtime`）
   - 覆盖的代码路径通配符 `path-glob`（如 `src/gateway/runtime/**`）
2. 扫描 `specs/` 下所有 `SPEC-NNN-*.md` 的 frontmatter，取当前最大编号 +1 得新 ID（3 位，补零）。
3. 从 `specs/TEMPLATE.md` 复制为 `specs/SPEC-NNN-<slug>.md`，填写 frontmatter（`status: draft`，`created/updated` 用今天日期）。
4. 引导用户逐条填写正文，尤其**验收标准必须可测试**。
5. 在 `specs/INDEX.md` 末尾追加一行：`<area>|<path-glob>|<SPEC-NNN>`（保持 `|` 分隔格式）。
6. 向用户报告：spec ID、文件路径、下一步（批准 spec 后即可进入设计/实现）。
