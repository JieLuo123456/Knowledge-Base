# 示例文档目录

本目录存放知识库文档（PDF / Markdown / TXT）。

**已包含的示例文档：**
- `sample_dms.md` — DMS 疲劳检测夜间红外误报排障指南

**导入方法：**
```bash
python scripts/ingest.py
```

导入后可立即通过 `POST /api/qa` 提问，例如：
> "DMS 疲劳检测夜间误报怎么排查？"

**注意：** 除示例文档外，其余文档文件已通过 `.gitignore` 排除，请勿将含敏感信息的文档提交到仓库。
