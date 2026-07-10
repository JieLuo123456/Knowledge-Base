# 智能影像识别知识库 Agent

基于 **RAG（检索增强生成）** 的工程知识智能问答系统，面向智能影像识别团队，覆盖 DMS（驾驶员监测系统）、OMS（乘员监测系统）、哨兵模式（Sentry Mode）和端侧模型部署等工程场景。

> ⚠️ **重要提示**：Embedding 和 LLM 调用需要有效的 `OPENAI_API_KEY`，未配置时导入与问答会**失败并给出清晰报错**。纯逻辑测试（`pytest tests/`）**无需** API Key 或外部服务。

---

## ✨ 核心能力

- 🔍 **真实 RAG 问答**：向量检索 → 证据过滤 → LLM 生成带引用回答
- 🛡️ **越界兜底**：无相关证据时直接返回"未找到相关工程资料"，不调 LLM 编造
- 📄 **多格式导入**：支持 PDF / Markdown / TXT，自动分块、打标签、向量化
- 🏷️ **项目过滤**：DMS / OMS / Sentry / Edge / General 分类检索
- 🤖 **飞书接入骨架**：Webhook 端点预留，配置凭证即可开启
- 🔌 **OpenAI 兼容**：支持 OpenAI / Qwen / 通义 / 本地 vLLM 等兼容端点

---

## 🚀 三步快速开始

### 第一步：配置环境变量

```bash
cp .env.example .env
# 编辑 .env，填入你的 OPENAI_API_KEY
# 可选：修改 OPENAI_BASE_URL（换用 Qwen/通义/vLLM）
# 可选：修改 EMBEDDING_MODEL / LLM_MODEL
```

### 第二步：启动 Qdrant 并导入示例文档

```bash
# 1. 启动 Qdrant 向量库
docker-compose up -d qdrant

# 2. 安装依赖
pip install -r requirements.txt

# 3. 导入示例文档（data/docs/sample_dms.md）
python scripts/ingest.py
```

### 第三步：启动服务并提问

```bash
# 启动 API 服务
uvicorn app.main:app --reload

# 访问 Swagger UI
open http://localhost:8000/docs

# 调用问答接口（示例）
curl -X POST http://localhost:8000/api/qa \
  -H "Content-Type: application/json" \
  -d '{"question": "DMS 疲劳检测夜间误报怎么排查？", "project": "DMS"}'
```

---

## 🧪 运行测试

```bash
# 纯逻辑测试，无需 API Key 和外部服务
pytest tests/ -v
```

---

## 📁 项目结构

```
Knowledge-Base/
├── README.md               # 本文件
├── requirements.txt        # Python 依赖
├── .env.example            # 环境变量示例（复制为 .env 填入 Key）
├── .gitignore
├── Dockerfile
├── docker-compose.yml      # 启动 Qdrant + App
│
├── config/
│   └── settings.py         # pydantic-settings 全局配置
│
├── app/
│   ├── main.py             # FastAPI 应用入口
│   ├── api/
│   │   ├── qa.py           # POST /api/qa 问答接口
│   │   ├── ingest.py       # POST /api/ingest 导入接口
│   │   └── feishu.py       # 飞书 Webhook 骨架
│   ├── rag/
│   │   ├── embeddings.py   # OpenAI 兼容 Embedding
│   │   ├── llm.py          # OpenAI 兼容 LLM
│   │   ├── retriever.py    # Qdrant 向量检索
│   │   ├── generator.py    # RAG 生成编排
│   │   ├── guardrail.py    # 越界/无证据兜底
│   │   └── prompts.py      # System Prompt 与模板
│   ├── ingestion/
│   │   ├── loader.py       # PDF/MD/TXT 加载
│   │   ├── chunker.py      # 滑窗分块
│   │   └── pipeline.py     # 导入 Pipeline
│   ├── storage/
│   │   └── vector_store.py # Qdrant 封装
│   └── models/
│       └── schemas.py      # Pydantic 请求/响应模型
│
├── data/docs/
│   ├── README.md           # 文档目录说明
│   └── sample_dms.md       # 示例：DMS 夜间红外误报排障指南
│
├── docs/
│   └── SRS.md              # 软件需求规格说明书 v2.0
│
├── scripts/
│   └── ingest.py           # 命令行导入脚本
│
└── tests/
    ├── test_chunker.py     # 分块逻辑测试
    ├── test_guardrail.py   # 护栏逻辑测试
    └── test_schemas.py     # Pydantic 模型测试
```

---

## 🔌 API 参考

### GET /health

检查服务及 Qdrant 连接状态。

### POST /api/qa

```json
// 请求
{
  "question": "DMS 疲劳检测夜间误报怎么排查？",
  "project": "DMS",    // 可选，过滤项目范围
  "top_k": 5           // 可选，检索片段数
}

// 响应
{
  "answer": "根据知识库资料，排查步骤如下...",
  "citations": [
    {
      "source_file": "sample_dms.md",
      "title": "sample_dms",
      "chunk_index": 2,
      "score": 0.87,
      "snippet": "在夜间行驶场景中..."
    }
  ],
  "confidence": 0.87,
  "used_evidence": true
}
```

### POST /api/ingest

```json
// 请求
{
  "docs_dir": "data/docs",  // 可选
  "project": "DMS"          // 可选，强制指定 project 标签
}
```

---

## ⚙️ 配置说明

| 变量 | 默认值 | 说明 |
|------|--------|------|
| `OPENAI_API_KEY` | *(必填)* | OpenAI 或兼容端 API Key |
| `OPENAI_BASE_URL` | `https://api.openai.com/v1` | 兼容端点 URL |
| `EMBEDDING_MODEL` | `text-embedding-3-small` | Embedding 模型 |
| `LLM_MODEL` | `gpt-4o-mini` | 对话模型 |
| `QDRANT_URL` | `http://localhost:6333` | Qdrant 服务地址 |
| `QDRANT_COLLECTION` | `knowledge_base` | 向量集合名 |
| `TOP_K` | `5` | 默认检索片段数 |
| `SIMILARITY_THRESHOLD` | `0.3` | 相似度阈值，低于此值兜底 |
| `CHUNK_SIZE` | `500` | 分块目标字符数 |
| `CHUNK_OVERLAP` | `50` | 相邻块重叠字符数 |

---

## 🔒 安全说明

- `.env` 文件已加入 `.gitignore`，**请勿提交含真实 Key 的 .env**
- 文档数据不上传至任何第三方（仅调用 Embedding API 处理文本）
- 未配置 Key 时服务正常启动，调用接口时返回清晰错误提示

---

## 📖 SRS 文档

详见 [docs/SRS.md](docs/SRS.md)，包含完整的目标（G1–G11）、功能需求（FR-1 至 FR-10）、非功能需求及系统架构图。
