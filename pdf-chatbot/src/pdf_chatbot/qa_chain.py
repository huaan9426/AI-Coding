"""问答链模块（支持对话记忆）"""
from langchain.chains import ConversationalRetrievalChain
from langchain.chat_models import ChatOpenAI
from langchain.memory import ConversationBufferMemory

from .config import Config
from .vector_store import VectorStoreManager


class QASystem:
    """问答系统类（支持多轮对话）"""

    def __init__(self, vector_store_manager: VectorStoreManager, enable_memory: bool = True):
        """
        初始化问答系统

        参数:
            vector_store_manager: 向量存储管理器
            enable_memory: 是否启用对话记忆（默认启用）
        """
        self.vector_store_manager = vector_store_manager
        self.enable_memory = enable_memory
        self.llm = ChatOpenAI(
            model=Config.MODEL_NAME,
            temperature=Config.TEMPERATURE,
            openai_api_key=Config.OPENAI_API_KEY
        )
        self.qa_chain = None
        self.memory = None
        self.chat_history = []  # 存储对话历史（用于显示）

    def initialize(self):
        """初始化问答链"""
        if not self.vector_store_manager.vectorstore:
            raise ValueError("向量数据库未加载！请先加载或创建向量数据库")

        print(f"🤖 正在初始化问答系统（记忆功能：{'开启' if self.enable_memory else '关闭'}）...")

        if self.enable_memory:
            # 创建对话记忆
            self.memory = ConversationBufferMemory(
                memory_key="chat_history",
                return_messages=True,
                output_key="answer"  # 指定输出键
            )

            # 使用 ConversationalRetrievalChain（支持记忆）
            self.qa_chain = ConversationalRetrievalChain.from_llm(
                llm=self.llm,
                retriever=self.vector_store_manager.vectorstore.as_retriever(
                    search_kwargs={"k": 3}
                ),
                memory=self.memory,
                return_source_documents=True
            )
        else:
            # 使用普通的 RetrievalQA（不支持记忆）
            from langchain.chains import RetrievalQA
            self.qa_chain = RetrievalQA.from_chain_type(
                llm=self.llm,
                retriever=self.vector_store_manager.vectorstore.as_retriever(
                    search_kwargs={"k": 3}
                ),
                return_source_documents=True
            )

        print("✅ 问答系统初始化完成")

    def ask(self, question: str, show_source: bool = True) -> dict:
        """
        提问

        参数:
            question: 用户问题
            show_source: 是否显示来源文档（默认显示）

        返回:
            包含答案和来源文档的字典
        """
        if not self.qa_chain:
            raise ValueError("问答链未初始化！请先调用 initialize()")

        print(f"\n❓ 问题: {question}")
        print("🔍 正在搜索相关文档...")

        # 调用问答链
        if self.enable_memory:
            result = self.qa_chain({"question": question})
            answer = result['answer']
        else:
            result = self.qa_chain({"query": question})
            answer = result['result']

        print(f"\n💡 答案: {answer}")

        # 保存到历史记录
        self.chat_history.append({
            "question": question,
            "answer": answer
        })

        # 显示来源
        if show_source and result.get('source_documents'):
            print("\n📚 参考来源:")
            for i, doc in enumerate(result['source_documents'], 1):
                source = doc.metadata.get('source', '未知')
                page = doc.metadata.get('page', '?')
                print(f"  {i}. {source} (第{page}页)")
                print(f"     {doc.page_content[:100]}...")

        return result

    def get_chat_history(self) -> list:
        """
        获取对话历史

        返回:
            对话历史列表
        """
        return self.chat_history

    def clear_history(self):
        """清空对话历史"""
        self.chat_history = []
        if self.memory:
            self.memory.clear()
        print("🗑️  对话历史已清空")

    def show_history(self):
        """显示对话历史"""
        if not self.chat_history:
            print("📝 暂无对话历史")
            return

        print("\n" + "=" * 60)
        print("📝 对话历史")
        print("=" * 60)
        for i, item in enumerate(self.chat_history, 1):
            print(f"\n【第 {i} 轮对话】")
            print(f"❓ 问: {item['question']}")
            print(f"💡 答: {item['answer'][:200]}{'...' if len(item['answer']) > 200 else ''}")
        print("\n" + "=" * 60)
