"""
app/ingestion/loader.py
文档加载器：支持 PDF / Markdown / TXT (FR-1.1)

返回统一的 (title, text) 字符串，后续交由 chunker 处理。
"""

import os
from typing import Tuple


def load_document(file_path: str, base_dir: str | None = None) -> Tuple[str, str]:
    """
    加载单个文档，返回 (title, full_text)。(FR-1.1)

    支持格式：.pdf / .md / .txt

    Args:
        file_path: 文件绝对或相对路径
        base_dir: 可选的基础目录，提供时强制验证 file_path 在该目录内，
                  防止路径遍历攻击（path traversal）。

    Returns:
        (title, text) — title 取文件名（不含扩展名），text 为全文字符串

    Raises:
        ValueError: 不支持的文件格式，或路径遍历验证失败
        FileNotFoundError: 文件不存在
    """
    # 将路径规范化为绝对路径，消除 .. 等路径遍历字符
    resolved = os.path.realpath(os.path.abspath(file_path))

    # 若指定了基础目录，验证文件路径在允许范围内
    if base_dir is not None:
        resolved_base = os.path.realpath(os.path.abspath(base_dir))
        if not resolved.startswith(resolved_base + os.sep) and resolved != resolved_base:
            raise ValueError(
                f"拒绝访问：文件路径 '{file_path}' 超出允许目录 '{base_dir}'。"
            )

    if not os.path.isfile(resolved):
        raise FileNotFoundError(f"文件不存在：{file_path}")

    ext = os.path.splitext(resolved)[1].lower()
    title = os.path.splitext(os.path.basename(resolved))[0]

    if ext == ".pdf":
        text = _load_pdf(resolved)
    elif ext in (".md", ".txt"):
        text = _load_text(resolved)
    else:
        raise ValueError(f"不支持的文件格式：{ext}。支持 PDF / Markdown / TXT。")

    return title, text


def _load_pdf(file_path: str) -> str:
    """使用 pypdf 提取 PDF 全文。"""
    try:
        from pypdf import PdfReader
    except ImportError:
        raise ImportError("请先执行 pip install pypdf")

    reader = PdfReader(file_path)
    pages = []
    for page in reader.pages:
        page_text = page.extract_text() or ""
        pages.append(page_text)
    return "\n".join(pages)


def _load_text(file_path: str) -> str:
    """加载 Markdown / TXT 纯文本文件。"""
    with open(file_path, "r", encoding="utf-8") as f:
        return f.read()
