# 什么是Harness

Harness不是一门技术，也不是一个框架，而是一种智能体的开发架构方案。
$$
Agent = LLM + Harness
$$
Harness 设计的核心：把 LLM 压缩到最小范围，用代码包围它。

AI 发展的三个阶段：

| 阶段                    | 解决的问题                                       | 典型工作                                 |
| ----------------------- | ------------------------------------------------ | ---------------------------------------- |
| **Prompt Engineering**  | 怎么把指令说清楚，模型理解减少歧义               | 系统提示词设计、Few-shot示例、思维链引导 |
| **Context Engineering** | 在合适时机给模型提供正确且必要的信息             | 上下文管理、RAG、记忆注入、Token优化     |
| **Harness Engineering** | 构建一个稳定可靠的系统（执行、纠偏、观测和恢复） | 文件系统、沙箱、约束执行、反馈回路、观测 |

# From Prompts to Contracts Harness Engineering 总结

通过**来源锚定、实体路由、追踪、输出清洁、推荐语言合约**构成了**Agent非功能性需求**的完整闭环。

## 四项贡献

#### 贡献一

Harness  Engineer用于将提示主导的企业级LLM重构为**可追踪的**智能体架构。

- 来源到声明的离线管线（清单→证据→候选→提升门→声明）
- 运行时答案组装流程（路由→收集→规划→组合→验证）
- 代码拥有的控制层（产品规则+验证门）
- 可替换的组合边界（模板引擎/LLM）
- 每个答案可审计的追踪机制


#### 贡献二

传统RAG

```mermaid
flowchart LR
    %% ==================== 样式定义 ====================
    classDef offline fill:#E3F2FD,stroke:#1565C0,stroke-width:2px;
    classDef online fill:#FFF3E0,stroke:#E65100,stroke-width:2px;
    classDef llm fill:#FFEBEE,stroke:#C62828,stroke-width:2px;
    classDef storage fill:#F3E5F5,stroke:#6A1B9A,stroke-width:2px;
    classDef output fill:#E8F5E9,stroke:#2E7D32,stroke-width:2px;

    subgraph Offline[📥 离线阶段 — 索引构建]
        direction LR
        O1[📄 原始文档]:::offline --> O2[🔪 切块<br>Chunking]:::offline
        O2 --> O3[🧮 向量化<br>Embedding]:::offline
        O3 --> O4[(🗄️ 向量库<br>Vector DB)]:::storage
    end

    subgraph Online[📤 在线阶段 — 检索与生成]
        direction LR
        U[👤 用户提问]:::online --> R[🔍 检索<br>相似度搜索]:::online
        R --> R1[📦 召回的文档块]:::online
        R1 --> L[🧠 LLM<br>直接输出]:::llm
        L --> Out[📤 输出给用户]:::output
    end

    O4 -.->|提供索引| R
```

从来源到声明的knowledge pipeline，将原始文档、证据记录、背书声明、wiki上下文和面向用户的回答分离开来。

```mermaid
graph TB
    %% ==================== 样式定义 ====================
    classDef layer1 fill:#E3F2FD,stroke:#1565C0,stroke-width:2px;
    classDef layer2 fill:#FFF3E0,stroke:#E65100,stroke-width:2px;
    classDef layer3 fill:#E8F5E9,stroke:#2E7D32,stroke-width:2px;
    classDef layer4 fill:#F3E5F5,stroke:#6A1B9A,stroke-width:2px;
    classDef comp fill:#ffffff,stroke:#333,stroke-width:1px,rx:4px;
    classDef title fill:none,stroke:none,font-weight:bold,font-size:16px;

    %% ==================== 顶部：用户入口 ====================
    User([👤 产品/业务团队 ]) 

    %% ==================== 第一层： 发现与获取 ====================
    subgraph L1[第一层： 来源发现与原始采集]
        direction LR
        L1_Title[职责：发现外部信号，获取原始素材]:::title
        
        S1[来源发现<br>监听DART/公告/新闻源]:::comp
        S2[清单注册<br>名称/URL/类型/公司/状态]:::comp
        S3[原始文档获取<br>下载PDF/HTML]:::comp
        S4[离线解析<br>OCR / 文本抽取 / 分页分行]:::comp
        
        S1 --> S2 --> S3 --> S4
    end

    %% ==================== 第二层：理解与提取 ====================
    subgraph L2[第二层： 事实提取与结构化]
        direction LR
        L2_Title[职责：将非结构化文本转化为结构化证据]:::title
        
        K1[原子化拆解<br>将复合文本拆为单条事实]:::comp
        K2[实体识别<br>提取 companyId / claimType]:::comp
        K3[哈希指纹计算<br>内容防篡改标识]:::comp
        K4[证据记录生成<br>Evidence Record 封装]:::comp
        
        K1 --> K2 --> K3 --> K4
    end

    %% ==================== 第三层：验证与背书 ====================
    subgraph L3[第三层： 确定性验证与背书]
        direction LR
        L3_Title[职责：执行四重检查，产出可信背书]:::title
        
        V1[检查1: 原子化<br>是否为单条事实]:::comp
        V2[检查2: 来源溯源<br>sourceManifest 是否有效]:::comp
        V3[检查3: 实体范围<br>companyId 是否在注册列表中]:::comp
        V4[检查4: 运行时策略<br>usePolicy 是否为 allowed]:::comp
        
        V1 --> V2 --> V3 --> V4
        V4 --> Pass[✅ 来源背书声明<br>Attestation Signature]:::comp
        V4 -->|任一失败| Fail[❌ 标记异常<br>待人工复核]:::comp
    end

    %% ==================== 数据流连接 ====================
    User --> L1
    
    L1 -->|结构化文档<br>+ 元数据坐标| L2
    L2 -->|Evidence Record<br>+ 哈希指纹| L3
    
    L3 -->|可信证据| Output([📦 可信证据库<br>供下游 RAG / Agent 使用])
    

    %% ==================== 层样式 ====================
    style L1 fill:#E3F2FD,stroke:#1565C0,stroke-width:2px
    style L2 fill:#FFF3E0,stroke:#E65100,stroke-width:2px
    style L3 fill:#E8F5E9,stroke:#2E7D32,stroke-width:2px
```

#### 贡献三

传统架构

```mermaid
flowchart LR
    %% ==================== 样式 ====================
    classDef old fill:#FFEBEE,stroke:#C62828;
    classDef new fill:#E8F5E9,stroke:#2E7D32;
    classDef llm fill:#FFF3E0,stroke:#E65100,stroke-dasharray:5 5;
    classDef code fill:#E3F2FD,stroke:#1565C0;

    subgraph 传统架构[ ]
        direction TB
        T1[用户输入] --> T2[🧠 LLM<br>理解/判断/组织/措辞/安全]:::llm
        T2 --> T3[输出]
        T2 -.-> T4[(知识库/工具)]:::old
        T4 -.-> T2
    end
```

一个可替换的组合边界，将确定性Harness控制与LLM措辞分离。

```mermaid
flowchart LR
    %% ==================== 样式 ====================
    classDef old fill:#FFEBEE,stroke:#C62828;
    classDef new fill:#E8F5E9,stroke:#2E7D32;
    classDef llm fill:#FFF3E0,stroke:#E65100,stroke-dasharray:5 5;
    classDef code fill:#E3F2FD,stroke:#1565C0;

    subgraph Harness架构[ ]
        direction LR
        N1[用户输入] --> N2[📋 代码: 实体路由]:::code
        N2 --> N3[📋 代码: 筛选声明]:::code
        N3 --> N4[📋 代码: 规划结构]:::code
        N4 --> N5[🧠 LLM: 措辞]:::llm
        N5 --> N6[📋 代码: 验证]:::code
        N6 --> N7[输出]
    end
```

#### 贡献四

传统智能体中LLM 是大脑，包揽所有决策，LLM感知出错导致后面所有的节点都错误。

```mermaid
flowchart LR
    %% ==================== 样式定义 ====================
    classDef llm fill:#FFEBEE,stroke:#C62828,stroke-width:2px,color:#B71C1C;
    classDef code fill:#ECEFF1,stroke:#78909C,stroke-width:1px,stroke-dasharray:4 4,color:#546E7A;
    classDef loop fill:#FFF8E1,stroke:#F9A825,stroke-width:2px,stroke-dasharray:8 4;

    subgraph Loop[ ]
        direction  LR

        P1[👁️ 感知<br>LLM 自己读检索结果<br>自己判断哪些相关]:::llm
        P2[🧠 推理<br>LLM 自己决定<br>怎么组织答案]:::llm
        P3[✍️ 执行<br>LLM 自己写答案]:::llm
        P4[🔍 观察<br>LLM 自己判断<br>答案好不好]:::llm
        P5[🔄 再感知<br>LLM 自己决定<br>要不要补充信息]:::llm

        P1 --> P2 --> P3 --> P4 --> P5
        P5 -.->|不满意，再次循环| P1
        P5 -->|满意| Out[📤 输出给用户]
    end
```

一套系统级验证设计：**答案输出给用户之前，必须同时通过这七道检查，任何一道不通过就不能输出**。检查来源锚定、实体路由、追踪完整性、输出清洁、运行时接口行为、延迟和实时LLM组合边界行为。

```mermaid
flowchart LR
    %% ==================== 样式定义 ====================
    classDef check fill:#E3F2FD,stroke:#1565C0,stroke-width:2px,color:#0D47A1;
    classDef pass fill:#E8F5E9,stroke:#2E7D32,stroke-width:2px,color:#1B5E20;
    classDef fail fill:#FFEBEE,stroke:#C62828,stroke-width:2px,color:#B71C1C;
    classDef fallback fill:#FFF3E0,stroke:#E65100,stroke-width:2px,color:#BF360C;
    classDef output fill:#F3E5F5,stroke:#6A1B9A,stroke-width:2px,color:#4A148C;
    classDef parallel fill:#ECEFF1,stroke:#455A64,stroke-width:1px,stroke-dasharray:5 5;

    %% ==================== 入口 ====================
    Start([📝 答案组装完成]) --> Parallel

    %% ==================== 七维并行检查 ====================
    subgraph Parallel[🔍 七维检查（并行执行）]
        direction TB
        
        C1[① 来源锚定<br>确保事实可溯源]:::check
        C2[② 实体路由<br>确保归属正确]:::check
        C3[③ 追踪完整性<br>确保全链路Trace存在]:::check
        C4[④ 输出清洁<br>格式/敏感词/幻觉过滤]:::check
        C5[⑤ 接口行为<br>工具调用符合预期]:::check
        C6[⑥ 延迟<br>响应时间是否达标]:::check
        C7[⑦ 组合边界行为<br>多事实组合是否冲突]:::check
    end

    %% 从入口进入并行块（隐式所有节点接收）
    Start --> C1 & C2 & C3 & C4 & C5 & C6 & C7

    %% ==================== 聚合判断 ====================
    C1 & C2 & C3 & C4 & C5 & C6 & C7 --> Decision{🧩 全部通过?}

    %% ==================== 分支1：全部通过 ====================
    Decision -->|✅ 是| Pass[✅ 全部通过]:::pass
    Pass --> Output1([📤 输出给用户]):::output

    %% ==================== 分支2：任一不通过 ====================
    Decision -->|❌ 否| Fallback[🔄 回退确定性模板引擎]:::fallback

    Fallback --> Recheck[📋 模板答案<br>重新执行七项检查]:::fallback

    Recheck --> Decision2{🧩 全部通过?}

    Decision2 -->|✅ 是| Output2([📤 输出给用户]):::output
    Decision2 -->|❌ 否| Manual[🆘 标记异常<br>进入人工复核 / 熔断降级]:::fail
```

## 3个问题

RQ1 ：规则确定以后，系统实际运行时能不能每次都守住这些规则。

RQ2 ：验证换了 LLM 之后还能不能保持。

RQ3 ：要证明"代码控制层"是真正起作用的结构，不是可以靠提示词替代的。

# 基于Harness可追踪架构


知识管线层（离线构建）：把原始数据变成可验证的声明库。

| 组件            | 技术选型              | 做什么                                                       |
| :-------------- | :-------------------- | :----------------------------------------------------------- |
| Source config   | YAML + PostgreSQL     | 注册可用来源（API端点、文件路径、更新周期、使用策略），YAML做版本控制，DB做运行时查询 |
| Fetcher         | Python爬虫            | 按清单从外部获取原始文档（财报、API数据、新闻），存为结构化证据记录 |
| Claim extractor | LLM + 人工审核        | 用LLM从证据中提取可验证声明（如"三星2024年合并营收300.9万亿韩元"），人工审核确认 |
| Promotion gate  | 规则引擎              | 验证声明是否有来源锚定、页码定位、实体归属，通过后才"提升"为背书声明 |
| Claims store    | PostgreSQL + pgvector | 结构化存储声明（实体、来源、页码、声明文本），pgvector存语义向量供运行时检索 |

运行时引擎层：所有控制逻辑由代码而非提示词拥有。

| 组件                | 技术选型                      | 做什么                                                       |
| :------------------ | :---------------------------- | :----------------------------------------------------------- |
| API gateway         | FastAPI                       | 接收用户提问，返回结构化答案                                 |
| Entity router       | 代码规则 + 正则 + 轻量NER模型 | 确定问题指向哪个实体（公司/集团），不交给LLM判断             |
| Claim selector      | SQL + 向量搜索                | 从声明库中选取与问题相关的声明，SQL过滤实体范围，向量搜索匹配语义 |
| Contract builder    | Pydantic schema               | 定义答案结构（关键洞察、财务要点、风险、关注点），约束输出格式 |
| Compostion boundray | 组合边界                      | 实时组装：把声明和合约传给LLM生成自然语言答案，支持多模型切换；<BR>确定性组装：把选中的声明填入模板，不调用LLM，作为回退路径； |
| Validation gate     | 规则引擎                      | 7项检查：来源锚定、实体路由、追踪完整、输出清洁、接口行为、延迟、组合边界 |
| Response builder    | 代码组装                      | 组装最终答案 + 生成审计追踪记录                              |

基础设施层

| 组件           | 技术选型                   | 做什么                                                       |
| :------------- | :------------------------- | :----------------------------------------------------------- |
| Trace store    | PostgreSQL                 | 存储每次请求的完整审计追踪（选了哪些声明、走了哪条组合路径、验证结果） |
| Audit log      | Elasticsearch / PostgreSQL | 面向审计员的日志检索，支持按时间、实体、来源查询             |
| Eval framework | pytest                     | 固定验证场景（问题+期望声明+期望信号），CI中自动运行         |
| CI/CD          | Git + Jenkins              | 每次代码变更自动跑验证场景，合约不通过则阻止部署             |
| Monitoring     | Grafana + Prometheus       | 监控延迟、回退率、验证失败率、合约通过率                     |
| External LLMs  | OpenAI / Anthropic         | 通过LLM adapter统一调用，可随时切换模型                      |
