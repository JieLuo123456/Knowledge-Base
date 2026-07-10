"""
app/rag/llm.py
调用 OpenAI 兼容 Chat Completions 接口生成回答 (G3, FR-3.2)
"""

import sys
from typing import List, Dict

from config.settings import settings


def _get_client():
    """延迟创建 OpenAI 客户端。"""
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


def chat_completion(messages: List[Dict[str, str]]) -> str:
    """
    调用 LLM 生成回答 (FR-3.2)

    Args:
        messages: OpenAI 格式消息列表，包含 system + user roles

    Returns:
        模型回答文本

    Raises:
        EnvironmentError: API Key 未配置
        openai.APIError: API 调用失败
    """
    client = _get_client()
    response = client.chat.completions.create(
        model=settings.llm_model,
        messages=messages,
        temperature=0.1,  # 降低随机性，提升事实性
    )
    return response.choices[0].message.content or ""
