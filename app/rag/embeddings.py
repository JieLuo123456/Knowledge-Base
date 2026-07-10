"""
app/rag/embeddings.py
调用 OpenAI 兼容接口获取文本向量 (G1, FR-1.2)

支持 OpenAI / Qwen / 通义 / 本地 vLLM 等兼容端点。
"""

import sys
from typing import List

from config.settings import settings


def _get_client():
    """延迟创建 OpenAI 客户端，避免无 Key 时启动报错。"""
    if not settings.openai_api_key:
        raise EnvironmentError(
            "未配置 OPENAI_API_KEY。请在 .env 中设置有效的 API Key 后重试。"
        )
    try:
        from openai import OpenAI
    except ImportError:
        print("请先执行 pip install openai", file=sys.stderr)
        raise

    return OpenAI(
        api_key=settings.openai_api_key,
        base_url=settings.openai_base_url,
    )


def embed_texts(texts: List[str]) -> List[List[float]]:
    """
    批量获取文本 Embedding 向量 (FR-1.2)

    Args:
        texts: 待编码文本列表

    Returns:
        与输入等长的浮点向量列表

    Raises:
        EnvironmentError: API Key 未配置
        openai.APIError: API 调用失败
    """
    if not texts:
        return []

    client = _get_client()
    response = client.embeddings.create(
        model=settings.embedding_model,
        input=texts,
    )
    # 按原始顺序返回
    vectors = [item.embedding for item in sorted(response.data, key=lambda x: x.index)]
    return vectors


def embed_query(text: str) -> List[float]:
    """单条查询文本编码，用于检索阶段 (FR-2.1)"""
    return embed_texts([text])[0]
