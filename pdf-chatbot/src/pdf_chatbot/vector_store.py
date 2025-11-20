"""向量存储模块"""
from typing import List
from langchain.vectorstores import Chroma
from langchain.embeddings import OpenAIEmbeddings
from langchain.schema import Document

from .config import Config


class VectorStoreManager:
    """向量数据库管理类"""

    def __init__(self):
        self.embeddings = OpenAIEmbeddings(
            model=Config.EMBEDDING_MODEL,
            openai_api_key=Config.OPENAI_API_KEY
        )
        self.vectorstore = None

    def create_vectorstore(self, documents: List[Document]) -> Chroma:
        """
        创建向量数据库

        参数:
            documents: 文档列表

        返回:
            向量数据库对象
        """
        print(f"🔄 正在向量化 {len(documents)} 个文档块...")

        self.vectorstore = Chroma.from_documents(
            documents=documents,
            embedding=self.embeddings,
            persist_directory=Config.CHROMA_PERSIST_DIR
        )

        # 持久化保存
        self.vectorstore.persist()
        print(f"✅ 向量数据库创建完成，已保存到 {Config.CHROMA_PERSIST_DIR}")

        return self.vectorstore

    def load_vectorstore(self) -> Chroma:
        """
        加载已存在的向量数据库

        返回:
            向量数据库对象
        """
        print(f"📂 正在加载向量数据库...")

        self.vectorstore = Chroma(
            persist_directory=Config.CHROMA_PERSIST_DIR,
            embedding_function=self.embeddings
        )

        print(f"✅ 向量数据库加载完成")
        return self.vectorstore

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
