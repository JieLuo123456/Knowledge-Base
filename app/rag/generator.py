"""
app/rag/generator.py
RAG 生成流程编排 (G1–G3, FR-3.1, FR-3.2, FR-3.3, FR-3.4)

编排步骤：
  1. 检索相关 chunks
  2. 护栏：无充分证据则直接兜底
  3. 组装 context + prompt，调 LLM
  4. 返回答案与引用
"""

from typing import Optional, Tuple, List

from app.rag.retriever import retrieve
from app.rag.guardrail import should_skip_llm, get_no_evidence_answer
from app.rag.prompts import SYSTEM_PROMPT, build_user_message
from app.rag.llm import chat_completion
from app.models.schemas import Citation, QAResponse


def generate_answer(
    question: str,
    project: Optional[str] = None,
    top_k: Optional[int] = None,
) -> QAResponse:
    """
    端到端 RAG 问答生成 (FR-3.1)

    Args:
        question: 用户问题
        project: 可选项目过滤
        top_k: 可选检索数量

    Returns:
        QAResponse 含 answer, citations, confidence, used_evidence
    """
    # Step 1: 检索
    chunks = retrieve(question, top_k=top_k, project=project)

    # Step 2: 护栏检查 (FR-3.4)
    if should_skip_llm(chunks):
        return QAResponse(
            answer=get_no_evidence_answer(),
            citations=[],
            confidence=max((c.get("score", 0.0) for c in chunks), default=0.0),
            used_evidence=False,
        )

    # Step 3: 组装 prompt，调 LLM (FR-3.2)
    user_message = build_user_message(question, chunks)
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": user_message},
    ]
    answer = chat_completion(messages)

    # Step 4: 构建引用列表 (FR-3.3)
    citations = _build_citations(chunks)
    confidence = max(c.get("score", 0.0) for c in chunks)

    return QAResponse(
        answer=answer,
        citations=citations,
        confidence=round(confidence, 4),
        used_evidence=True,
    )


def _build_citations(chunks: List[dict]) -> List[Citation]:
    """从检索结果构造 Citation 列表。"""
    citations = []
    for chunk in chunks:
        payload = chunk.get("payload", {})
        text = payload.get("text", "")
        citations.append(
            Citation(
                source_file=payload.get("source_file", ""),
                title=payload.get("title", ""),
                chunk_index=payload.get("chunk_index", 0),
                score=round(chunk.get("score", 0.0), 4),
                snippet=text[:200],
            )
        )
    return citations
