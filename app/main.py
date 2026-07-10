"""
app/main.py
FastAPI 应用入口 (G1, FR-4.1)

提供端点：
  GET  /health        — 健康检查
  POST /api/qa        — 问答
  POST /api/ingest    — 文档导入
  POST /api/feishu/webhook — 飞书 Webhook（骨架）
  GET  /docs          — Swagger UI（FastAPI 自动生成）
"""

from fastapi import FastAPI
from fastapi.responses import JSONResponse

from app.api import qa, ingest, feishu
from app.models.schemas import HealthResponse
from app.storage.vector_store import get_vector_store
from config.settings import settings

app = FastAPI(
    title="智能影像识别知识库 Agent",
    description=(
        "基于 RAG 的工程知识智能问答系统，面向 DMS / OMS / 哨兵 / 端侧部署团队。\n\n"
        "**使用前请确保**：\n"
        "1. `.env` 中已填入有效 `OPENAI_API_KEY`\n"
        "2. Qdrant 已通过 `docker-compose up -d qdrant` 启动\n"
        "3. 已执行 `python scripts/ingest.py` 导入文档"
    ),
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# 注册路由
app.include_router(qa.router)
app.include_router(ingest.router)
app.include_router(feishu.router)


@app.get("/health", response_model=HealthResponse, tags=["System"], summary="健康检查")
def health_check() -> HealthResponse:
    """
    检查服务及 Qdrant 连接状态。
    即使 Qdrant 不可达，也返回 200（qdrant_reachable=False），不抛异常。
    """
    store = get_vector_store()
    reachable = store.is_reachable()
    return HealthResponse(
        status="ok",
        qdrant_reachable=reachable,
        collection=settings.qdrant_collection,
    )
