#!/usr/bin/env python3
"""
scripts/ingest.py
命令行文档导入脚本 (FR-1.1 – FR-1.4)

用法：
  python scripts/ingest.py                          # 导入 data/docs/ 所有文档
  python scripts/ingest.py --docs-dir path/to/docs # 指定目录
  python scripts/ingest.py --project DMS           # 强制指定 project 标签

前置条件：
  1. .env 中已填入有效 OPENAI_API_KEY
  2. Qdrant 已通过 docker-compose up -d qdrant 启动
"""

import argparse
import sys
import os

# 确保项目根目录在 Python 路径中
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.ingestion.pipeline import run_pipeline
from config.settings import settings


def main() -> None:
    parser = argparse.ArgumentParser(
        description="导入文档到智能影像识别知识库"
    )
    parser.add_argument(
        "--docs-dir",
        default="data/docs",
        help="文档目录路径（默认：data/docs）",
    )
    parser.add_argument(
        "--project",
        default=None,
        choices=["DMS", "OMS", "Sentry", "Edge", "General"],
        help="为所有文档指定 project 标签（默认：按文件名推断）",
    )
    args = parser.parse_args()

    # 配置检查
    if not settings.openai_api_key:
        print(
            "错误：未配置 OPENAI_API_KEY。\n"
            "请在项目根目录创建 .env 文件并填入 OPENAI_API_KEY=sk-xxx",
            file=sys.stderr,
        )
        sys.exit(1)

    print(f"=== 智能影像识别知识库 — 文档导入 ===")
    print(f"文档目录：{args.docs_dir}")
    print(f"Project 标签：{args.project or '按文件名推断'}")
    print(f"Qdrant 地址：{settings.qdrant_url}")
    print(f"Embedding 模型：{settings.embedding_model}")
    print()

    try:
        chunks_indexed, files_processed, errors = run_pipeline(
            docs_dir=args.docs_dir,
            project_override=args.project,
        )
    except FileNotFoundError as exc:
        print(f"错误：{exc}", file=sys.stderr)
        sys.exit(1)
    except EnvironmentError as exc:
        print(f"错误：{exc}", file=sys.stderr)
        sys.exit(1)
    except ConnectionError as exc:
        print(
            f"错误：{exc}\n"
            "请确认已执行 docker-compose up -d qdrant",
            file=sys.stderr,
        )
        sys.exit(1)

    print()
    print(f"=== 导入结果 ===")
    print(f"处理文件数：{len(files_processed)}")
    print(f"写入 chunks：{chunks_indexed}")
    if errors:
        print(f"错误数：{len(errors)}")
        for e in errors:
            print(f"  - {e}")
    else:
        print("全部成功，无错误。")

    print()
    print("导入完成！现在可以启动服务进行问答：")
    print("  uvicorn app.main:app --reload")


if __name__ == "__main__":
    main()
