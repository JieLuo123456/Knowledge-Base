"""
app/storage/vector_store.py
Qdrant 向量存储封装 (FR-1.4, FR-2.1)

提供：
  - 初始化集合
  - 批量写入 chunk 向量
  - 向量检索（支持 project 过滤）
"""

import uuid
from typing import List, Optional, Dict, Any

from config.settings import settings


def _get_client():
    """延迟创建 Qdrant 客户端，连接失败给出清晰报错。"""
    try:
        from qdrant_client import QdrantClient
    except ImportError:
        raise ImportError("请先执行 pip install qdrant-client")

    try:
        client = QdrantClient(url=settings.qdrant_url)
        return client
    except Exception as exc:
        raise ConnectionError(
            f"无法连接 Qdrant（{settings.qdrant_url}）。"
            f"请确认已通过 docker-compose up -d qdrant 启动服务。原始错误：{exc}"
        ) from exc


class VectorStore:
    """Qdrant 向量库封装，支持向量写入与相似度检索。(FR-1.4, FR-2.1)"""

    def __init__(self):
        self._client = None

    @property
    def client(self):
        if self._client is None:
            self._client = _get_client()
        return self._client

    def ensure_collection(self, vector_size: int) -> None:
        """
        确保集合存在，不存在则创建。(FR-1.4)

        Args:
            vector_size: Embedding 维度，需与 Embedding 模型匹配
        """
        from qdrant_client.models import VectorParams, Distance

        existing = [c.name for c in self.client.get_collections().collections]
        if settings.qdrant_collection not in existing:
            self.client.create_collection(
                collection_name=settings.qdrant_collection,
                vectors_config=VectorParams(
                    size=vector_size,
                    distance=Distance.COSINE,
                ),
            )

    def upsert_chunks(
        self,
        chunks: List[Dict[str, Any]],
        vectors: List[List[float]],
    ) -> None:
        """
        批量写入 chunks（向量 + payload）。(FR-1.4)

        Args:
            chunks: payload 列表，每项包含 source_file/title/project/chunk_index/text
            vectors: 与 chunks 等长的向量列表
        """
        from qdrant_client.models import PointStruct

        if not chunks:
            return

        # 确保集合存在
        self.ensure_collection(len(vectors[0]))

        points = [
            PointStruct(
                id=str(uuid.uuid4()),
                vector=vec,
                payload=payload,
            )
            for vec, payload in zip(vectors, chunks)
        ]
        self.client.upsert(
            collection_name=settings.qdrant_collection,
            points=points,
        )

    def search(
        self,
        query_vector: List[float],
        top_k: int,
        project_filter: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """
        向量相似度检索 (FR-2.1, FR-2.2)

        Args:
            query_vector: 查询向量
            top_k: 返回数量
            project_filter: 按 project payload 字段过滤，None 不过滤

        Returns:
            列表，每项 {'id', 'score', 'payload'}
        """
        from qdrant_client.models import Filter, FieldCondition, MatchValue

        query_filter = None
        if project_filter:
            query_filter = Filter(
                must=[
                    FieldCondition(
                        key="project",
                        match=MatchValue(value=project_filter),
                    )
                ]
            )

        hits = self.client.search(
            collection_name=settings.qdrant_collection,
            query_vector=query_vector,
            limit=top_k,
            query_filter=query_filter,
            with_payload=True,
        )

        return [
            {
                "id": str(hit.id),
                "score": hit.score,
                "payload": hit.payload or {},
            }
            for hit in hits
        ]

    def is_reachable(self) -> bool:
        """健康检查：尝试连接 Qdrant。"""
        try:
            self.client.get_collections()
            return True
        except Exception:
            return False


# 单例
_store: Optional[VectorStore] = None


def get_vector_store() -> VectorStore:
    """获取全局 VectorStore 单例。"""
    global _store
    if _store is None:
        _store = VectorStore()
    return _store
