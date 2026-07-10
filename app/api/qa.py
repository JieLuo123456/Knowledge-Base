"""
app/api/qa.py
POST /api/qa — 问答接口 (G1, FR-3.1)
"""

from fastapi import APIRouter, HTTPException

from app.models.schemas import QARequest, QAResponse
from app.rag.generator import generate_answer

router = APIRouter(prefix="/api", tags=["QA"])


@router.post("/qa", response_model=QAResponse, summary="知识库问答 (FR-3.1)")
def qa_endpoint(req: QARequest) -> QAResponse:
    """
    基于 RAG 的智能问答端点。

    - 检索相关文档片段
    - 通过护栏判断是否有充分证据
    - 有证据则调 LLM 生成带引用回答，无证据则返回兜底答案
    """
    try:
        result = generate_answer(
            question=req.question,
            project=req.project,
            top_k=req.top_k,
        )
        return result
    except EnvironmentError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except ConnectionError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"内部错误：{exc}") from exc
