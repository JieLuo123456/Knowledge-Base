"""app/models/schemas.py — Pydantic 请求/响应模型 (FR-4.1)"""

from __future__ import annotations

from typing import List, Optional
from pydantic import BaseModel, Field


# ---------- 通用枚举 ----------

PROJECT_CHOICES = ["DMS", "OMS", "Sentry", "Edge", "General"]


# ---------- 问答 ----------

class QARequest(BaseModel):
    """POST /api/qa 请求体 (FR-3.1)"""
    question: str = Field(..., min_length=1, description="用户问题")
    project: Optional[str] = Field(
        default=None,
        description=f"项目过滤标签，可选值: {PROJECT_CHOICES}",
    )
    top_k: Optional[int] = Field(
        default=None,
        ge=1,
        le=20,
        description="返回 Top-K 检索片段，覆盖默认配置",
    )


class Citation(BaseModel):
    """单条引用证据 (FR-3.3)"""
    source_file: str
    title: str
    chunk_index: int
    score: float = Field(description="余弦相似度")
    snippet: str = Field(description="片段前 200 字")


class QAResponse(BaseModel):
    """POST /api/qa 响应体 (FR-3.1)"""
    answer: str
    citations: List[Citation] = []
    confidence: float = Field(
        default=0.0,
        ge=0.0,
        le=1.0,
        description="最高相似度得分，作为置信度代理",
    )
    used_evidence: bool = Field(
        description="是否有证据支撑回答（False 表示未找到相关资料）"
    )


# ---------- 导入 ----------

class IngestRequest(BaseModel):
    """POST /api/ingest 请求体 (FR-1.1)"""
    docs_dir: Optional[str] = Field(
        default=None,
        description="文档目录路径，默认为 data/docs/",
    )
    project: Optional[str] = Field(
        default=None,
        description="为该批文档打上 project 标签，留空则按文件名推断",
    )


class IngestResponse(BaseModel):
    """POST /api/ingest 响应体 (FR-1.1)"""
    status: str
    chunks_indexed: int
    files_processed: List[str]
    errors: List[str] = []


# ---------- 健康检查 ----------

class HealthResponse(BaseModel):
    """GET /health 响应体"""
    status: str
    qdrant_reachable: bool
    collection: str
