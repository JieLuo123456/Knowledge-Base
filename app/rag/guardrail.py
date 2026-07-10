"""
app/rag/guardrail.py
越界/无证据兜底逻辑 (G3, FR-3.4)

当检索结果为空或最高相似度低于阈值时，直接返回拒绝回答，不调 LLM。
"""

from typing import List

from config.settings import settings

# 标准拒绝回答文本
NO_EVIDENCE_ANSWER = (
    "未在知识库中找到相关工程资料，建议查阅官方文档或联系相关负责人。"
)


def should_skip_llm(chunks: List[dict]) -> bool:
    """
    判断是否应跳过 LLM 调用，直接返回兜底答案。(FR-3.4)

    条件：检索结果为空，或最高相似度低于 similarity_threshold。

    Args:
        chunks: 检索返回的 chunk 列表，每项包含 'score' 字段

    Returns:
        True 表示无充分证据，应兜底；False 表示有证据可送 LLM。
    """
    if not chunks:
        return True

    max_score = max(c.get("score", 0.0) for c in chunks)
    return max_score < settings.similarity_threshold


def get_no_evidence_answer() -> str:
    """返回标准兜底回答文本。"""
    return NO_EVIDENCE_ANSWER
