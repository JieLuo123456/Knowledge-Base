"""
app/rag/retriever.py
向量检索模块 (G1, FR-2.1, FR-2.2)

从 Qdrant 检索 Top-K 相关 chunks，支持 project 过滤。
"""

from typing import List, Optional

from config.settings import settings
from app.rag.embeddings import embed_query
from app.storage.vector_store import get_vector_store


def retrieve(
    question: str,
    top_k: Optional[int] = None,
    project: Optional[str] = None,
) -> List[dict]:
    """
    向量检索，返回最相关的 Top-K 文档片段 (FR-2.1)

    Args:
        question: 用户问题
        top_k: 返回数量，默认使用全局配置
        project: 项目标签过滤（DMS/OMS/Sentry/Edge/General），None 表示不过滤

    Returns:
        列表，每项包含:
            - payload: dict (source_file, title, project, chunk_index, text)
            - score: float (余弦相似度)
            - id: str
    """
    k = top_k or settings.top_k
    query_vector = embed_query(question)

    store = get_vector_store()
    results = store.search(
        query_vector=query_vector,
        top_k=k,
        project_filter=project,
    )
    return results
