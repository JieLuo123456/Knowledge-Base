"""
app/rag/prompts.py
系统提示与 Prompt 模板 (G3, FR-3.2)

严格约束 LLM 只基于检索证据回答，禁止编造。
"""

SYSTEM_PROMPT = """\
你是智能影像识别团队的工程知识库助手，专注于 DMS（驾驶员监测系统）、\
OMS（乘员监测系统）、哨兵模式（Sentry Mode）和端侧模型部署等领域。

【约束规则】
1. 只能根据下方提供的【参考资料】回答问题，不得编造任何 API、工具、参数或能力。
2. 若参考资料中没有足够信息，必须回答：「未在知识库中找到相关工程资料，建议查阅官方文档或联系相关负责人。」
3. 回答时在末尾用「【参考来源】」标注所引用的资料来源（文件名 + 标题）。
4. 语言风格：简洁专业，适合工程师阅读。
5. 禁止生成与给定参考资料无关的内容。
"""

USER_PROMPT_TEMPLATE = """\
【参考资料】
{context}

【用户问题】
{question}

请基于以上参考资料回答用户问题，并在末尾标注参考来源。
"""


def build_context(chunks: list[dict]) -> str:
    """
    将检索到的 chunks 拼接为 LLM 的 context 字符串。

    Args:
        chunks: 每个元素包含 payload (source_file, title, text) 和 score

    Returns:
        格式化的 context 字符串
    """
    parts = []
    for i, chunk in enumerate(chunks, start=1):
        payload = chunk.get("payload", {})
        source = payload.get("source_file", "未知来源")
        title = payload.get("title", "")
        text = payload.get("text", "")
        parts.append(f"[{i}] 来源：{source}  标题：{title}\n{text}")
    return "\n\n---\n\n".join(parts)


def build_user_message(question: str, chunks: list[dict]) -> str:
    """组装用户消息，将 context 嵌入 prompt 模板。"""
    context = build_context(chunks)
    return USER_PROMPT_TEMPLATE.format(context=context, question=question)
