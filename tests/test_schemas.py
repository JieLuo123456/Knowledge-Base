"""
tests/test_schemas.py
纯逻辑测试：Pydantic 请求/响应模型 (FR-4.1)

不依赖外部网络/服务，pytest 直接通过。
"""

import pytest
from pydantic import ValidationError

from app.models.schemas import (
    QARequest,
    QAResponse,
    Citation,
    IngestRequest,
    IngestResponse,
    HealthResponse,
    PROJECT_CHOICES,
)


class TestQARequest:
    def test_valid_minimal(self):
        """最小有效请求"""
        req = QARequest(question="DMS 夜间误报怎么排查？")
        assert req.question == "DMS 夜间误报怎么排查？"
        assert req.project is None
        assert req.top_k is None

    def test_valid_with_all_fields(self):
        """含全部字段的有效请求"""
        req = QARequest(question="如何调参？", project="DMS", top_k=3)
        assert req.project == "DMS"
        assert req.top_k == 3

    def test_empty_question_raises(self):
        """空问题应触发校验错误"""
        with pytest.raises(ValidationError):
            QARequest(question="")

    def test_top_k_min_boundary(self):
        """top_k 最小值为 1"""
        req = QARequest(question="问题", top_k=1)
        assert req.top_k == 1

    def test_top_k_max_boundary(self):
        """top_k 最大值为 20"""
        req = QARequest(question="问题", top_k=20)
        assert req.top_k == 20

    def test_top_k_exceeds_max_raises(self):
        """top_k 超过 20 应触发校验错误"""
        with pytest.raises(ValidationError):
            QARequest(question="问题", top_k=21)

    def test_top_k_below_min_raises(self):
        """top_k 小于 1 应触发校验错误"""
        with pytest.raises(ValidationError):
            QARequest(question="问题", top_k=0)


class TestQAResponse:
    def test_valid_with_evidence(self):
        """含证据的有效响应"""
        citation = Citation(
            source_file="sample_dms.md",
            title="sample_dms",
            chunk_index=0,
            score=0.85,
            snippet="DMS 疲劳检测...",
        )
        resp = QAResponse(
            answer="建议检查 ISP 曝光参数。",
            citations=[citation],
            confidence=0.85,
            used_evidence=True,
        )
        assert resp.used_evidence is True
        assert len(resp.citations) == 1
        assert resp.confidence == 0.85

    def test_no_evidence_response(self):
        """无证据的兜底响应"""
        resp = QAResponse(
            answer="未在知识库中找到相关工程资料。",
            citations=[],
            confidence=0.0,
            used_evidence=False,
        )
        assert resp.used_evidence is False
        assert resp.citations == []

    def test_default_citations_empty(self):
        """citations 默认为空列表"""
        resp = QAResponse(answer="回答", confidence=0.5, used_evidence=True)
        assert resp.citations == []

    def test_confidence_range(self):
        """confidence 取值范围 [0, 1]"""
        resp = QAResponse(answer="OK", confidence=0.0, used_evidence=False)
        assert resp.confidence == 0.0

        resp2 = QAResponse(answer="OK", confidence=1.0, used_evidence=True)
        assert resp2.confidence == 1.0

    def test_confidence_out_of_range_raises(self):
        """confidence 超出 [0,1] 应触发校验错误"""
        with pytest.raises(ValidationError):
            QAResponse(answer="OK", confidence=1.1, used_evidence=True)

        with pytest.raises(ValidationError):
            QAResponse(answer="OK", confidence=-0.1, used_evidence=True)


class TestCitation:
    def test_valid_citation(self):
        """有效 Citation"""
        c = Citation(
            source_file="dms.md",
            title="DMS 文档",
            chunk_index=2,
            score=0.77,
            snippet="片段内容",
        )
        assert c.source_file == "dms.md"
        assert c.chunk_index == 2

    def test_score_field(self):
        """score 字段正常存储"""
        c = Citation(
            source_file="f.txt",
            title="T",
            chunk_index=0,
            score=0.5,
            snippet="...",
        )
        assert c.score == 0.5


class TestIngestRequest:
    def test_defaults(self):
        """默认值"""
        req = IngestRequest()
        assert req.docs_dir is None
        assert req.project is None

    def test_with_values(self):
        """指定字段"""
        req = IngestRequest(docs_dir="data/docs", project="DMS")
        assert req.docs_dir == "data/docs"
        assert req.project == "DMS"


class TestIngestResponse:
    def test_valid_response(self):
        """有效导入响应"""
        resp = IngestResponse(
            status="success",
            chunks_indexed=42,
            files_processed=["sample_dms.md"],
            errors=[],
        )
        assert resp.chunks_indexed == 42
        assert resp.errors == []

    def test_default_errors_empty(self):
        """errors 默认为空列表"""
        resp = IngestResponse(
            status="success",
            chunks_indexed=0,
            files_processed=[],
        )
        assert resp.errors == []


class TestHealthResponse:
    def test_healthy(self):
        """健康状态"""
        h = HealthResponse(
            status="ok",
            qdrant_reachable=True,
            collection="knowledge_base",
        )
        assert h.status == "ok"
        assert h.qdrant_reachable is True

    def test_unhealthy_qdrant(self):
        """Qdrant 不可达"""
        h = HealthResponse(
            status="ok",
            qdrant_reachable=False,
            collection="knowledge_base",
        )
        assert h.qdrant_reachable is False


class TestProjectChoices:
    def test_project_choices_contains_expected(self):
        """PROJECT_CHOICES 包含所有预期项目"""
        expected = {"DMS", "OMS", "Sentry", "Edge", "General"}
        assert expected == set(PROJECT_CHOICES)
