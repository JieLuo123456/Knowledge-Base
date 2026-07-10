"""
tests/test_guardrail.py
纯逻辑测试：越界/无证据兜底护栏 (FR-3.4)

不依赖外部网络/服务，pytest 直接通过。
"""

import pytest
from unittest.mock import patch

from app.rag.guardrail import should_skip_llm, get_no_evidence_answer, NO_EVIDENCE_ANSWER


class TestShouldSkipLLM:
    def test_empty_chunks_returns_true(self):
        """检索结果为空时应跳过 LLM"""
        assert should_skip_llm([]) is True

    def test_none_score_treated_as_zero(self):
        """没有 score 字段的 chunk，默认分数 0.0，应跳过"""
        chunks = [{"payload": {"text": "some text"}}]
        # 默认 similarity_threshold=0.3，score=0.0 < 0.3
        assert should_skip_llm(chunks) is True

    def test_low_score_returns_true(self):
        """最高分低于阈值时应跳过 LLM"""
        chunks = [
            {"score": 0.1, "payload": {}},
            {"score": 0.2, "payload": {}},
        ]
        with patch("app.rag.guardrail.settings") as mock_settings:
            mock_settings.similarity_threshold = 0.3
            assert should_skip_llm(chunks) is True

    def test_high_score_returns_false(self):
        """最高分达到阈值时不应跳过 LLM"""
        chunks = [
            {"score": 0.1, "payload": {}},
            {"score": 0.8, "payload": {}},
        ]
        with patch("app.rag.guardrail.settings") as mock_settings:
            mock_settings.similarity_threshold = 0.3
            assert should_skip_llm(chunks) is False

    def test_exact_threshold_returns_false(self):
        """分数恰好等于阈值时不跳过（>= threshold 通过）"""
        chunks = [{"score": 0.3, "payload": {}}]
        with patch("app.rag.guardrail.settings") as mock_settings:
            mock_settings.similarity_threshold = 0.3
            assert should_skip_llm(chunks) is False

    def test_all_zero_scores(self):
        """所有 chunk 分数为 0 时应跳过"""
        chunks = [{"score": 0.0}, {"score": 0.0}]
        with patch("app.rag.guardrail.settings") as mock_settings:
            mock_settings.similarity_threshold = 0.3
            assert should_skip_llm(chunks) is True

    def test_single_high_score_chunk(self):
        """单个高分 chunk 应通过"""
        chunks = [{"score": 0.95, "payload": {"text": "相关内容"}}]
        with patch("app.rag.guardrail.settings") as mock_settings:
            mock_settings.similarity_threshold = 0.3
            assert should_skip_llm(chunks) is False

    def test_mixed_scores_uses_max(self):
        """使用最高分判断，不是平均分"""
        chunks = [
            {"score": 0.05},
            {"score": 0.06},
            {"score": 0.07},
            {"score": 0.85},  # 最高分 > 0.3
        ]
        with patch("app.rag.guardrail.settings") as mock_settings:
            mock_settings.similarity_threshold = 0.3
            assert should_skip_llm(chunks) is False


class TestGetNoEvidenceAnswer:
    def test_returns_non_empty_string(self):
        """兜底回答应为非空字符串"""
        answer = get_no_evidence_answer()
        assert isinstance(answer, str)
        assert len(answer) > 0

    def test_answer_matches_constant(self):
        """兜底回答与常量一致"""
        assert get_no_evidence_answer() == NO_EVIDENCE_ANSWER

    def test_answer_contains_key_phrase(self):
        """兜底回答应包含关键提示语"""
        answer = get_no_evidence_answer()
        assert "未在知识库中找到" in answer or "未找到" in answer
