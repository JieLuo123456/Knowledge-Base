"""
app/ingestion/pipeline.py
文档导入 Pipeline (G5, FR-1.1 – FR-1.4)

流程：
  1. 扫描目录，找到所有 PDF/MD/TXT 文件
  2. 加载文档 → 分块
  3. 调 Embedding 获取向量
  4. 写入 Qdrant

project 标签推断规则（优先级从高到低）：
  - 传入的 project 参数
  - 文件名包含 dms/oms/sentry/edge 关键字（大小写不敏感）
  - 默认 "General"
"""

import os
import sys
from typing import List, Optional, Tuple

from app.ingestion.loader import load_document
from app.ingestion.chunker import chunk_text
from app.rag.embeddings import embed_texts
from app.storage.vector_store import get_vector_store


# 关键字 → project 标签映射
_KEYWORD_MAP = {
    "dms": "DMS",
    "oms": "OMS",
    "sentry": "Sentry",
    "edge": "Edge",
}


def _infer_project(filename: str, override: Optional[str] = None) -> str:
    """根据文件名推断 project 标签 (FR-1.1)"""
    if override:
        return override
    lower = filename.lower()
    for kw, label in _KEYWORD_MAP.items():
        if kw in lower:
            return label
    return "General"


def run_pipeline(
    docs_dir: str = "data/docs",
    project_override: Optional[str] = None,
) -> Tuple[int, List[str], List[str]]:
    """
    执行完整导入 pipeline (FR-1.1 – FR-1.4)

    Args:
        docs_dir: 文档目录路径
        project_override: 强制指定所有文档的 project 标签

    Returns:
        (chunks_indexed, files_processed, errors)
    """
    supported_exts = {".pdf", ".md", ".txt"}
    files_processed: List[str] = []
    errors: List[str] = []
    all_payloads: List[dict] = []
    all_texts: List[str] = []

    # 规范化目录路径，防止路径遍历
    resolved_dir = os.path.realpath(os.path.abspath(docs_dir))

    if not os.path.isdir(resolved_dir):
        raise FileNotFoundError(f"文档目录不存在：{docs_dir}")

    for filename in sorted(os.listdir(resolved_dir)):
        ext = os.path.splitext(filename)[1].lower()
        if ext not in supported_exts:
            continue

        file_path = os.path.join(resolved_dir, filename)
        project = _infer_project(filename, project_override)

        try:
            # 传入 base_dir 确保文件在允许目录内（防止符号链接逃逸）
            title, text = load_document(file_path, base_dir=resolved_dir)
            chunks = chunk_text(text)

            for idx, chunk in enumerate(chunks):
                all_payloads.append(
                    {
                        "source_file": filename,
                        "title": title,
                        "project": project,
                        "chunk_index": idx,
                        "text": chunk,
                    }
                )
                all_texts.append(chunk)

            files_processed.append(filename)
            print(f"  [OK] {filename} → {len(chunks)} chunks (project={project})")

        except Exception as exc:
            msg = f"{filename}: {exc}"
            errors.append(msg)
            print(f"  [FAIL] {msg}", file=sys.stderr)

    if not all_texts:
        print("没有可导入的文本内容。")
        return 0, files_processed, errors

    # 批量 Embedding
    print(f"正在为 {len(all_texts)} 个 chunks 生成 Embedding...")
    vectors = embed_texts(all_texts)

    # 写入 Qdrant
    store = get_vector_store()
    store.upsert_chunks(all_payloads, vectors)
    print(f"写入完成：{len(all_texts)} 个 chunks 已存入 Qdrant。")

    return len(all_texts), files_processed, errors
