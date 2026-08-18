# 规格索引 (Spec Index)

本文件是 `.claude/hooks/require_spec.py` 读取的**机器可读映射表**，也是代码追溯的依据。
新增 / 变更 spec 时必须同步本文件（`/spec` 命令会自动维护）。

## 格式

每行一条映射，三段用竖线 `|` 分隔（顺序不可变）。示例：

# 格式示例（`#` 开头行会被解析器跳过，仅作说明）：
# <area>|<path-glob>|<spec-id>
# gateway/runtime|src/gateway/runtime/**|SPEC-001

- `area`：代码区域唯一短名（与 spec frontmatter 的 `area` 一致）
- `path-glob`：该 spec 覆盖的代码路径通配符（`*` 单段，`**` 跨段）
- `spec-id`：如 `SPEC-001`

解析规则：跳过空行、`#` 开头和 `<!--` 注释行；只取恰好含两个 `|` 且三段非空的行。

<!-- 以下是映射区，新条目追加在末尾 -->
core|src/gateway/core/**|SPEC-001
core|src/gateway/exceptions.py|SPEC-001
knowledge|src/gateway/knowledge/**|SPEC-002
router|src/gateway/router/**|SPEC-003
selection|src/gateway/selector/**|SPEC-004
selection|src/gateway/contract/**|SPEC-004
compose|src/gateway/compose/**|SPEC-005
gate|src/gateway/validate/**|SPEC-006
gate|src/gateway/response/**|SPEC-006
api|src/gateway/api/**|SPEC-007
api|src/gateway/main.py|SPEC-007
api|src/gateway/__init__.py|SPEC-007
agents|src/gateway/agents/**|SPEC-010
agents|src/gateway/gateway.py|SPEC-010
ui|src/gateway/ui/**|SPEC-009
tests|tests/**|SPEC-008
data|data/**|SPEC-008
