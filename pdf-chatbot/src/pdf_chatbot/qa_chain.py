"""问答链模块"""
from langchain.chains import RetrievalQA
from langchain.chat_models import ChatOpenAI

from .config import Config
from .vector_store import VectorStoreManager


class QASystem:
    """问答系统类"""

    def __init__(self, vector_store_manager: VectorStoreManager):
        self.vector_store_manager = vector_store_manager
        self.llm = ChatOpenAI(
            model=Config.MODEL_NAME,
            temperature=Config.TEMPERATURE,
            openai_api_key=Config.OPENAI_API_KEY
        )
        self.qa_chain = None

    def initialize(self):
        """初始化问答链"""
        if not self.vector_store_manager.vectorstore:
            raise ValueError("向量数据库未加载！请先加载或创建向量数据库")

        print("🤖 正在初始化问答系统...")

        self.qa_chain = RetrievalQA.from_chain_type(
            llm=self.llm,
            retriever=self.vector_store_manager.vectorstore.as_retriever(
                search_kwargs={"k": 3}
            ),
            return_source_documents=True  # 返回来源文档
        )

        print("✅ 问答系统初始化完成")

    def ask(self, question: str) -> dict:
        """
        提问

        参数:
            question: 用户问题

        返回:
            包含答案和来源文档的字典
        """
        if not self.qa_chain:
            raise ValueError("问答链未初始化！请先调用 initialize()")

        print(f"\n❓ 问题: {question}")
        print("🔍 正在搜索相关文档...")

        result = self.qa_chain({"query": question})

        print(f"\n💡 答案: {result['result']}")

        # 显示来源
        print("\n📚 参考来源:")
        for i, doc in enumerate(result['source_documents'], 1):
            source = doc.metadata.get('source', '未知')
            page = doc.metadata.get('page', '?')
            print(f"  {i}. {source} (第{page}页)")
            print(f"     {doc.page_content[:100]}...")

        return result
