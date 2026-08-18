# ADR-0001: v1 技术栈选型（FastAPI + SQLite + 存储抽象）

- 状态: 提议
- 日期: 2026-08-18
- 决策者: joema
- 涉及 spec: 无（架构层，影响后续所有 SPEC）
- 关联 ADR: 无

## 背景 / 上下文

《可追踪的Harness架构.md》的技术选型表建议：API gateway 用 FastAPI，Claims store 用 PostgreSQL + pgvector。但本仓库定位是**迷你网关**，需要权衡部署复杂度与起步速度。

约束：
- 希望本机直接能跑、零外部服务依赖。
- 又希望保留论文选型的演进路径（语义向量检索、Postgres 生态）。

## 决策

v1 技术栈：

- **API**：FastAPI + uvicorn（与论文一致）
- **存储**：SQLite（Python 内置）做 claims / sources / evidence / traces 表，全文检索用 **FTS5**
- **存储层抽象**：`knowledge/store.py` 定义存储接口，SQLite 是 v1 实现；接口保留，后续可替换 PostgreSQL + pgvector
- **LLM**：adapter 抽象（`core/llm.py`），OpenAI / Anthropic / none 可切换

## 后果

**正面：**
- 零部署依赖（Python 3.10+ 自带 sqlite3），本机直接运行
- 开发迭代快，适合先验证 Harness 闭环
- 存储抽象保留迁移路径

**负面：**
- FTS5 关键词检索弱于 pgvector 的语义向量检索（实体类问句尚可，开放式问句效果有限）
- SQLite 并发写入能力弱（v1 单用户足够）
- 迁到 pgvector 时有数据迁移工作

## 替代方案

- **PostgreSQL + pgvector（论文选型）** —— 否决：需要本地安装并维护 Postgres，违背"迷你"定位；留作 v2 演进。
- **内存存储（dict）** —— 否决：重启即失，无法支撑真实数据与追踪审计。

## 关联

- [architecture.md](../design/architecture.md) §3、§6
