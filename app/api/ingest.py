"""
app/api/ingest.py
POST /api/ingest — 触发文档导入 (FR-1.1)
"""

import os

from fastapi import APIRouter, HTTPException

from app.models.schemas import IngestRequest, IngestResponse
from app.ingestion.pipeline import run_pipeline

router = APIRouter(prefix="/api", tags=["Ingest"])

# 允许通过 API 导入的根目录（限制范围，防止路径遍历）
_ALLOWED_DOCS_ROOT = os.path.realpath(os.path.abspath("data"))


@router.post("/ingest", response_model=IngestResponse, summary="触发文档导入 (FR-1.1)")
def ingest_endpoint(req: IngestRequest = IngestRequest()) -> IngestResponse:
    """
    扫描文档目录，执行完整导入 pipeline：
    加载 → 分块 → Embedding → 写入 Qdrant。

    docs_dir 限制在项目 data/ 目录内，防止路径遍历。
    """
    docs_dir = req.docs_dir or "data/docs"

    # 路径安全验证：确保 docs_dir 在允许的根目录内
    resolved = os.path.realpath(os.path.abspath(docs_dir))
    if not resolved.startswith(_ALLOWED_DOCS_ROOT + os.sep) and resolved != _ALLOWED_DOCS_ROOT:
        raise HTTPException(
            status_code=400,
            detail=f"docs_dir 必须位于项目 data/ 目录内，拒绝访问：{docs_dir}",
        )

    try:
        chunks_indexed, files_processed, errors = run_pipeline(
            docs_dir=docs_dir,
            project_override=req.project,
        )
        status = "success" if not errors else "partial"
        return IngestResponse(
            status=status,
            chunks_indexed=chunks_indexed,
            files_processed=files_processed,
            errors=errors,
        )
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except EnvironmentError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except ConnectionError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"导入失败：{exc}") from exc
