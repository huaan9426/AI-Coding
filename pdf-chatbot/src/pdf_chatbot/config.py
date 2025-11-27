"""配置管理模块"""
import os
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()


class Config:
    """应用配置类"""

    # LLM 提供商选择
    LLM_PROVIDER = os.getenv("LLM_PROVIDER", "qwen").lower()  # openai / qwen

    # OpenAI 配置
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

    # 通义千问配置
    DASHSCOPE_API_KEY = os.getenv("DASHSCOPE_API_KEY")

    # 模型名称
    MODEL_NAME = os.getenv("MODEL_NAME", "qwen-turbo")

    # Temperature 配置验证
    try:
        TEMPERATURE = float(os.getenv("TEMPERATURE", "0.0"))
    except ValueError:
        print("⚠️  TEMPERATURE 配置错误，使用默认值 0.0")
        TEMPERATURE = 0.0

    # Embedding 提供商选择
    EMBEDDING_PROVIDER = os.getenv("EMBEDDING_PROVIDER", "local").lower()  # openai / local

    # OpenAI Embedding 配置
    EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "text-embedding-3-small")

    # 本地 Embedding 配置
    LOCAL_EMBEDDING_MODEL = os.getenv("LOCAL_EMBEDDING_MODEL", "BAAI/bge-small-zh-v1.5")

    # 向量数据库配置
    CHROMA_PERSIST_DIR = os.getenv("CHROMA_PERSIST_DIR", "./chroma_db")

    # 文档处理配置
    try:
        CHUNK_SIZE = int(os.getenv("CHUNK_SIZE", "1000"))
    except ValueError:
        print("⚠️  CHUNK_SIZE 配置错误，使用默认值 1000")
        CHUNK_SIZE = 1000

    try:
        CHUNK_OVERLAP = int(os.getenv("CHUNK_OVERLAP", "200"))
    except ValueError:
        print("⚠️  CHUNK_OVERLAP 配置错误，使用默认值 200")
        CHUNK_OVERLAP = 200

    # 对话记忆配置
    ENABLE_MEMORY = os.getenv("ENABLE_MEMORY", "true").lower() == "true"

    @classmethod
    def validate(cls):
        """验证必需的配置是否存在和合法性"""
        errors = []

        # 验证 LLM 提供商
        if cls.LLM_PROVIDER not in ["openai", "qwen"]:
            errors.append(
                f"LLM_PROVIDER 配置错误: {cls.LLM_PROVIDER}\n"
                "  支持的提供商: openai, qwen"
            )

        # 验证对应的 API Key
        if cls.LLM_PROVIDER == "openai":
            if not cls.OPENAI_API_KEY:
                errors.append(
                    "未找到 OPENAI_API_KEY！\n"
                    "  请在 .env 文件中设置 OPENAI_API_KEY=your-api-key"
                )
            elif not cls.OPENAI_API_KEY.startswith("sk-"):
                errors.append(
                    "OPENAI_API_KEY 格式错误！\n"
                    "  API Key 应该以 'sk-' 开头"
                )
        elif cls.LLM_PROVIDER == "qwen":
            if not cls.DASHSCOPE_API_KEY:
                errors.append(
                    "未找到 DASHSCOPE_API_KEY！\n"
                    "  请访问 https://dashscope.console.aliyun.com/ 获取 API Key\n"
                    "  并在 .env 文件中设置 DASHSCOPE_API_KEY=your-api-key"
                )

        # 验证模型名称
        if cls.LLM_PROVIDER == "openai":
            valid_models = [
                "gpt-3.5-turbo", "gpt-4", "gpt-4-turbo", "gpt-4o",
                "gpt-4o-mini", "gpt-3.5-turbo-16k"
            ]
            if cls.MODEL_NAME not in valid_models:
                errors.append(
                    f"MODEL_NAME 可能不正确: {cls.MODEL_NAME}\n"
                    f"  支持的 OpenAI 模型: {', '.join(valid_models)}"
                )
        elif cls.LLM_PROVIDER == "qwen":
            valid_models = [
                "qwen-turbo", "qwen-plus", "qwen-max",
                "qwen-turbo-latest", "qwen-plus-latest", "qwen-max-latest"
            ]
            if cls.MODEL_NAME not in valid_models:
                errors.append(
                    f"MODEL_NAME 可能不正确: {cls.MODEL_NAME}\n"
                    f"  支持的通义千问模型: {', '.join(valid_models)}"
                )

        # 验证 Temperature
        if not 0 <= cls.TEMPERATURE <= 2:
            errors.append(
                f"TEMPERATURE 超出范围: {cls.TEMPERATURE}\n"
                "  有效范围: 0.0 - 2.0"
            )

        # 验证 Embedding 提供商
        if cls.EMBEDDING_PROVIDER not in ["openai", "local"]:
            errors.append(
                f"EMBEDDING_PROVIDER 配置错误: {cls.EMBEDDING_PROVIDER}\n"
                "  支持的提供商: openai, local"
            )

        # 验证 Embedding 模型
        if cls.EMBEDDING_PROVIDER == "openai":
            valid_embedding_models = [
                "text-embedding-3-small", "text-embedding-3-large",
                "text-embedding-ada-002"
            ]
            if cls.EMBEDDING_MODEL not in valid_embedding_models:
                errors.append(
                    f"EMBEDDING_MODEL 可能不正确: {cls.EMBEDDING_MODEL}\n"
                    f"  推荐的 OpenAI 模型: {', '.join(valid_embedding_models)}"
                )

        # 验证文档分块配置
        if cls.CHUNK_SIZE < 100 or cls.CHUNK_SIZE > 5000:
            errors.append(
                f"CHUNK_SIZE 超出推荐范围: {cls.CHUNK_SIZE}\n"
                "  推荐范围: 100 - 5000"
            )

        if cls.CHUNK_OVERLAP < 0 or cls.CHUNK_OVERLAP >= cls.CHUNK_SIZE:
            errors.append(
                f"CHUNK_OVERLAP 配置不合理: {cls.CHUNK_OVERLAP}\n"
                f"  应该在 0 到 {cls.CHUNK_SIZE} 之间"
            )

        if errors:
            raise ValueError("\n❌ 配置验证失败:\n" + "\n".join(errors))


# 验证配置
try:
    Config.validate()
except ValueError as e:
    print(f"⚠️  配置错误：{e}")
