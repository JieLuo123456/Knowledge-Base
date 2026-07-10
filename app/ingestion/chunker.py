"""
app/ingestion/chunker.py
语义分块：滑窗 + 重叠 (FR-1.3)

将长文本按目标字符数切块，保留相邻块间重叠以维持上下文连续性。
"""

from typing import List

from config.settings import settings


def chunk_text(
    text: str,
    chunk_size: int | None = None,
    chunk_overlap: int | None = None,
) -> List[str]:
    """
    滑动窗口文本分块 (FR-1.3)

    策略：
      1. 优先按段落（双换行符）切分，再合并到目标块大小。
      2. 若单段落超过 chunk_size，则强制按字符数切分。
      3. 相邻块之间保留 chunk_overlap 个字符的重叠。

    Args:
        text: 输入全文
        chunk_size: 每块目标字符数，默认读取配置
        chunk_overlap: 重叠字符数，默认读取配置

    Returns:
        分块字符串列表（已去除空块）
    """
    size = chunk_size or settings.chunk_size
    overlap = chunk_overlap or settings.chunk_overlap

    if not text or not text.strip():
        return []

    # 按段落分割
    paragraphs = [p.strip() for p in text.split("\n\n") if p.strip()]

    chunks: List[str] = []
    current = ""

    for para in paragraphs:
        # 单段落超过 chunk_size，需强制切分
        if len(para) > size:
            # 先保存当前缓冲
            if current:
                chunks.append(current)
                current = ""
            # 强制切分该段落
            for sub_chunk in _force_split(para, size, overlap):
                chunks.append(sub_chunk)
        elif len(current) + len(para) + 2 <= size:
            current = (current + "\n\n" + para).strip() if current else para
        else:
            if current:
                chunks.append(current)
            # 新块以上一块末尾 overlap 字符开头
            overlap_prefix = current[-overlap:] if len(current) >= overlap else current
            current = (overlap_prefix + "\n\n" + para).strip() if overlap_prefix else para

    if current:
        chunks.append(current)

    return [c for c in chunks if c.strip()]


def _force_split(text: str, size: int, overlap: int) -> List[str]:
    """对超长段落按字符数强制切分，相邻块保持 overlap 重叠。"""
    chunks = []
    start = 0
    while start < len(text):
        end = min(start + size, len(text))
        chunks.append(text[start:end])
        start = end - overlap if end - overlap > start else end
    return chunks
