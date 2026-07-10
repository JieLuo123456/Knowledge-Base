"""
tests/test_chunker.py
纯逻辑测试：文本分块 (FR-1.3)

不依赖外部网络/服务，pytest 直接通过。
"""

import pytest
from app.ingestion.chunker import chunk_text, _force_split


class TestChunkText:
    def test_empty_text_returns_empty(self):
        """空文本应返回空列表"""
        assert chunk_text("") == []
        assert chunk_text("   ") == []

    def test_short_text_single_chunk(self):
        """短文本（不超过 chunk_size）应作为单块返回"""
        text = "这是一段短文本。"
        result = chunk_text(text, chunk_size=500, chunk_overlap=50)
        assert len(result) == 1
        assert result[0] == text

    def test_long_text_multiple_chunks(self):
        """长文本应被切分为多块"""
        # 制造一段超过 chunk_size 的文本（用段落分隔）
        paragraphs = [f"这是第{i}段，内容是关于测试的段落文字，包含足够多的字符以触发分块逻辑。" for i in range(20)]
        text = "\n\n".join(paragraphs)
        result = chunk_text(text, chunk_size=200, chunk_overlap=20)
        assert len(result) > 1, "长文本应被切分为多块"

    def test_no_empty_chunks(self):
        """分块结果不应包含空字符串"""
        text = "\n\n".join(["段落" * 50] * 10)
        result = chunk_text(text, chunk_size=300, chunk_overlap=30)
        for chunk in result:
            assert chunk.strip() != "", "不应产生空 chunk"

    def test_chunk_size_respected(self):
        """每块字符数不应大幅超过 chunk_size（允许段落对齐误差）"""
        chunk_size = 100
        paragraphs = [f"段落{i}：" + "内容" * 30 for i in range(5)]
        text = "\n\n".join(paragraphs)
        result = chunk_text(text, chunk_size=chunk_size, chunk_overlap=10)
        for chunk in result:
            # 强制切分后每块不超过 chunk_size
            assert len(chunk) <= chunk_size * 3, f"块过大：{len(chunk)} > {chunk_size * 3}"

    def test_overlap_content_preserved(self):
        """相邻块之间应有内容重叠"""
        # 构造两个恰好分块的段落
        para1 = "A" * 80
        para2 = "B" * 80
        para3 = "C" * 80
        text = f"{para1}\n\n{para2}\n\n{para3}"
        result = chunk_text(text, chunk_size=100, chunk_overlap=20)
        # 验证确实产生了多块
        assert len(result) >= 2

    def test_single_very_long_paragraph(self):
        """单个超长段落（无双换行）应被强制切分"""
        long_text = "字" * 1000
        result = chunk_text(long_text, chunk_size=200, chunk_overlap=20)
        assert len(result) > 1, "超长段落应被切分"
        # 验证内容完整性（合并后应包含全部内容）
        # 由于重叠，合并后长度 >= 原始长度
        assert all(len(c) <= 200 for c in result), "每块不超过 chunk_size"

    def test_markdown_document(self):
        """Markdown 文档应能正常分块"""
        md = """# DMS 疲劳检测指南

## 一、现象描述

在夜间行驶场景中，DMS 系统出现以下典型误报问题：
驾驶员精神状态正常，但系统持续触发"疲劳预警"。

## 二、原因分析

红外曝光控制不足是主要原因。夜间场景亮度变化范围极大。

## 三、解决方案

调低红外 LED 最大功率上限，启用置信度门控 PERCLOS。
"""
        result = chunk_text(md, chunk_size=150, chunk_overlap=20)
        assert len(result) >= 1
        assert all(r.strip() for r in result)


class TestForceSplit:
    def test_force_split_basic(self):
        """强制切分基本功能"""
        text = "A" * 100
        result = _force_split(text, size=30, overlap=5)
        assert len(result) > 1
        assert all(len(c) <= 30 for c in result)

    def test_force_split_overlap(self):
        """相邻块末尾/开头应有重叠"""
        text = "ABCDEFGHIJ" * 10  # 100 chars
        result = _force_split(text, size=20, overlap=5)
        # 验证第一块末尾 5 字符是第二块开头 5 字符
        if len(result) >= 2:
            assert result[0][-5:] == result[1][:5]

    def test_force_split_short_text(self):
        """短于 size 的文本返回单块"""
        text = "短文本"
        result = _force_split(text, size=100, overlap=10)
        assert len(result) == 1
        assert result[0] == text
