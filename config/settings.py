"""
config/settings.py
应用全局配置，通过 pydantic-settings 从 .env 读取。
对应 SRS G1–G11 所有模块的运行时参数。
"""

from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field


class Settings(BaseSettings):
    """所有运行时配置，均可通过环境变量或 .env 文件覆盖。"""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # -------- OpenAI 兼容端点 (G1, FR-1.2) --------
    openai_api_key: str = Field(default="", description="OpenAI 或兼容端 API Key")
    openai_base_url: str = Field(
        default="https://api.openai.com/v1",
        description="OpenAI 兼容 base URL，可换为 Qwen/通义/vLLM",
    )
    embedding_model: str = Field(
        default="text-embedding-3-small",
        description="Embedding 模型名称",
    )
    llm_model: str = Field(
        default="gpt-4o-mini",
        description="LLM 对话模型名称",
    )

    # -------- Qdrant (FR-2.1) --------
    qdrant_url: str = Field(
        default="http://localhost:6333",
        description="Qdrant 服务地址",
    )
    qdrant_collection: str = Field(
        default="knowledge_base",
        description="向量集合名称",
    )

    # -------- RAG 参数 (FR-2.2, FR-3.1) --------
    top_k: int = Field(default=5, description="检索返回 Top-K 片段数")
    similarity_threshold: float = Field(
        default=0.3,
        description="相似度阈值，低于此值视为无相关证据",
    )

    # -------- 分块参数 (FR-1.3) --------
    chunk_size: int = Field(default=500, description="语义分块目标字符数")
    chunk_overlap: int = Field(default=50, description="相邻块重叠字符数")

    # -------- 飞书（可选，G6, FR-6.2）--------
    feishu_app_id: str = Field(default="", description="飞书 App ID")
    feishu_app_secret: str = Field(default="", description="飞书 App Secret")
    feishu_verification_token: str = Field(
        default="", description="飞书事件订阅验证 Token"
    )
    feishu_encrypt_key: str = Field(default="", description="飞书加密 Key（可选）")


# 单例，全局复用
settings = Settings()
