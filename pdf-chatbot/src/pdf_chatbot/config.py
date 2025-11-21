"""配置管理模块"""
import os
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()


class Config:
    """应用配置类"""

    # OpenAI 配置
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
    MODEL_NAME = os.getenv("MODEL_NAME", "gpt-3.5-turbo")
    TEMPERATURE = float(os.getenv("TEMPERATURE", "0.0"))
    EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "text-embedding-3-small")

    # 向量数据库配置
    CHROMA_PERSIST_DIR = os.getenv("CHROMA_PERSIST_DIR", "./chroma_db")

    # 文档处理配置
    CHUNK_SIZE = int(os.getenv("CHUNK_SIZE", "1000"))
    CHUNK_OVERLAP = int(os.getenv("CHUNK_OVERLAP", "200"))

    # 对话记忆配置
    ENABLE_MEMORY = os.getenv("ENABLE_MEMORY", "true").lower() == "true"

    @classmethod
    def validate(cls):
        """验证必需的配置是否存在"""
        if not cls.OPENAI_API_KEY:
            raise ValueError(
                "未找到 OPENAI_API_KEY！\n"
                "请创建 .env 文件并设置 OPENAI_API_KEY=your-api-key"
            )


# 验证配置
try:
    Config.validate()
except ValueError as e:
    print(f"⚠️  配置错误：{e}")
