"""向量存储模块"""
import os
import time
from typing import List
from langchain.vectorstores import Chroma
from langchain.embeddings import OpenAIEmbeddings, HuggingFaceEmbeddings
from langchain.schema import Document

from .config import Config


class VectorStoreManager:
    """向量数据库管理类"""

    def __init__(self):
        try:
            # 根据配置选择 Embedding 模型
            if Config.EMBEDDING_PROVIDER == "openai":
                print(f"🔧 使用 OpenAI Embedding: {Config.EMBEDDING_MODEL}")
                self.embeddings = OpenAIEmbeddings(
                    model=Config.EMBEDDING_MODEL,
                    openai_api_key=Config.OPENAI_API_KEY
                )
            elif Config.EMBEDDING_PROVIDER == "local":
                print(f"🔧 使用本地 Embedding: {Config.LOCAL_EMBEDDING_MODEL}")
                print("📥 首次使用会自动下载模型（约 100MB），请稍候...")
                self.embeddings = HuggingFaceEmbeddings(
                    model_name=Config.LOCAL_EMBEDDING_MODEL,
                    model_kwargs={'device': 'cpu'},  # 使用 CPU（无需 GPU）
                    encode_kwargs={'normalize_embeddings': True}  # 归一化向量
                )
                print("✅ 本地 Embedding 模型加载完成")
            else:
                raise ValueError(f"不支持的 Embedding 提供商: {Config.EMBEDDING_PROVIDER}")

            self.vectorstore = None
        except Exception as e:
            raise Exception(f"初始化 Embedding 模型失败: {str(e)}")

    def create_vectorstore(self, documents: List[Document]) -> Chroma:
        """
        创建向量数据库

        参数:
            documents: 文档列表

        返回:
            向量数据库对象

        异常:
            ValueError: 文档列表为空
            Exception: 向量化或保存失败
        """
        if not documents:
            raise ValueError("文档列表为空，无法创建向量数据库")

        print(f"🔄 正在向量化 {len(documents)} 个文档块...")

        # 根据 Embedding 提供商显示不同的时间估计
        if Config.EMBEDDING_PROVIDER == "openai":
            print(f"⏱️  预计需要 {len(documents) * 0.5:.0f} 秒（取决于网络速度）")
        else:
            print(f"⏱️  预计需要 {len(documents) * 0.1:.0f} 秒（本地处理）")

        max_retries = 3
        retry_delay = 2

        for attempt in range(max_retries):
            try:
                self.vectorstore = Chroma.from_documents(
                    documents=documents,
                    embedding=self.embeddings,
                    persist_directory=Config.CHROMA_PERSIST_DIR
                )

                # 持久化保存
                self.vectorstore.persist()
                print(f"✅ 向量数据库创建完成，已保存到 {Config.CHROMA_PERSIST_DIR}")

                return self.vectorstore

            except Exception as e:
                error_msg = str(e)

                # 检测常见错误类型（仅 OpenAI）
                if Config.EMBEDDING_PROVIDER == "openai":
                    if "api key" in error_msg.lower() or "authentication" in error_msg.lower():
                        raise ValueError("OpenAI API Key 无效或已过期，请检查 .env 配置")
                    elif "rate limit" in error_msg.lower():
                        if attempt < max_retries - 1:
                            wait_time = retry_delay * (attempt + 1)
                            print(f"⚠️  API 调用频率限制，{wait_time} 秒后重试...")
                            time.sleep(wait_time)
                            continue
                        else:
                            raise Exception("API 调用频率限制，请稍后再试")
                    elif "timeout" in error_msg.lower() or "connection" in error_msg.lower():
                        if attempt < max_retries - 1:
                            print(f"⚠️  网络超时，正在重试（{attempt + 1}/{max_retries}）...")
                            time.sleep(retry_delay)
                            continue
                        else:
                            raise Exception("网络连接失败，请检查网络连接")

                # 通用错误处理
                raise Exception(f"创建向量数据库失败: {error_msg}")

    def load_vectorstore(self) -> Chroma:
        """
        加载已存在的向量数据库

        返回:
            向量数据库对象

        异常:
            FileNotFoundError: 向量数据库不存在
            Exception: 加载失败
        """
        if not os.path.exists(Config.CHROMA_PERSIST_DIR):
            raise FileNotFoundError(
                f"向量数据库不存在: {Config.CHROMA_PERSIST_DIR}\n"
                "请先加载 PDF 文件创建向量数据库"
            )

        print(f"📂 正在加载向量数据库...")

        try:
            self.vectorstore = Chroma(
                persist_directory=Config.CHROMA_PERSIST_DIR,
                embedding_function=self.embeddings
            )

            # 验证数据库是否可用
            collection_count = self.vectorstore._collection.count()
            if collection_count == 0:
                raise ValueError("向量数据库为空，请重新创建")

            print(f"✅ 向量数据库加载完成（包含 {collection_count} 个文档块）")
            return self.vectorstore

        except Exception as e:
            raise Exception(f"加载向量数据库失败: {str(e)}")

    def search(self, query: str, k: int = 3) -> List[Document]:
        """
        搜索相关文档

        参数:
            query: 查询问题
            k: 返回结果数量

        返回:
            相关文档列表
        """
        if not self.vectorstore:
            raise ValueError("向量数据库未初始化！请先创建或加载向量数据库")

        results = self.vectorstore.similarity_search(query, k=k)
        return results

    def search_with_score(self, query: str, k: int = 3) -> List[tuple]:
        """
        搜索相关文档（包含相似度分数）

        参数:
            query: 查询问题
            k: 返回结果数量

        返回:
            (Document, score) 元组列表
            - Document: 文档对象
            - score: 相似度分数（距离，越小越相似）
        """
        if not self.vectorstore:
            raise ValueError("向量数据库未初始化！请先创建或加载向量数据库")

        results = self.vectorstore.similarity_search_with_score(query, k=k)
        return results
