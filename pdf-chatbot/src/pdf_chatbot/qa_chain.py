"""问答链模块（支持对话记忆和流式输出）"""
import sys
import time
import json
from datetime import datetime
from pathlib import Path
from typing import Tuple, Optional
from langchain.chains import ConversationalRetrievalChain, RetrievalQA
from langchain_openai import ChatOpenAI
from langchain_core.memory import ConversationBufferMemory
from langchain_core.callbacks import BaseCallbackHandler

from .config import Config
from .vector_store import VectorStoreManager


class StreamingCallbackHandler(BaseCallbackHandler):
    """
    流式输出回调处理器

    功能:
        - 实时逐字符/逐词打印 LLM 生成的内容
        - 收集完整答案用于保存到历史记录
    """

    def __init__(self):
        self.answer = ""  # 收集完整答案
        self.is_first_token = True  # 是否是第一个 token

    def on_llm_new_token(self, token: str, **kwargs) -> None:
        """
        每当 LLM 生成新 token 时调用

        参数:
            token: 新生成的文本片段
        """
        # 第一个 token 前打印提示
        if self.is_first_token:
            print("\n💡 答案: ", end="", flush=True)
            self.is_first_token = False

        # 实时打印
        print(token, end="", flush=True)

        # 收集完整答案
        self.answer += token

    def reset(self):
        """重置状态，用于下一次问答"""
        self.answer = ""
        self.is_first_token = True


def get_confidence_level(distance: float) -> Tuple[str, str, float]:
    """
    根据余弦距离判断可信度

    参数:
        distance: 余弦距离（0-2，Chroma 返回值）

    返回:
        (可信度等级, 颜色图标, 相似度分数)
    """
    # 转换为相似度（0-1）
    similarity = 1 - distance

    if similarity >= 0.85:
        return "高度相关", "🟢", similarity
    elif similarity >= 0.70:
        return "较为相关", "🟡", similarity
    elif similarity >= 0.50:
        return "可能相关", "🟠", similarity
    else:
        return "不太相关", "🔴", similarity


class QASystem:
    """问答系统类（支持多轮对话和流式输出）"""

    def __init__(
        self,
        vector_store_manager: VectorStoreManager,
        enable_memory: bool = True,
        enable_streaming: bool = True
    ):
        """
        初始化问答系统

        参数:
            vector_store_manager: 向量存储管理器
            enable_memory: 是否启用对话记忆（默认启用）
            enable_streaming: 是否启用流式输出（默认启用）
        """
        self.vector_store_manager = vector_store_manager
        self.enable_memory = enable_memory
        self.enable_streaming = enable_streaming

        # 创建流式回调处理器
        self.streaming_handler = StreamingCallbackHandler() if enable_streaming else None

        # 初始化 LLM（启用流式输出）
        self.llm = ChatOpenAI(
            model=Config.MODEL_NAME,
            temperature=Config.TEMPERATURE,
            openai_api_key=Config.OPENAI_API_KEY,
            streaming=enable_streaming,  # 启用流式输出
            callbacks=[self.streaming_handler] if enable_streaming else None
        )

        self.qa_chain = None
        self.memory = None
        self.chat_history = []  # 存储对话历史（用于显示）

    def initialize(self):
        """初始化问答链"""
        if not self.vector_store_manager.vectorstore:
            raise ValueError("向量数据库未加载！请先加载或创建向量数据库")

        print(f"🤖 正在初始化问答系统...")
        print(f"   - 记忆功能：{'✅ 开启' if self.enable_memory else '❌ 关闭'}")
        print(f"   - 流式输出：{'✅ 开启' if self.enable_streaming else '❌ 关闭'}")

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

        异常:
            ValueError: 问题为空或问答链未初始化
            Exception: API 调用失败
        """
        if not self.qa_chain:
            raise ValueError("问答链未初始化！请先调用 initialize()")

        # 验证问题
        if not question or not question.strip():
            raise ValueError("问题不能为空")

        question = question.strip()

        # 问题长度限制
        if len(question) > 1000:
            raise ValueError("问题过长（超过 1000 字符），请简化问题")

        print(f"\n❓ 问题: {question}")
        print("🔍 正在搜索相关文档...")

        max_retries = 3
        retry_delay = 2

        for attempt in range(max_retries):
            try:
                # 重置流式处理器状态
                if self.enable_streaming and self.streaming_handler:
                    self.streaming_handler.reset()

                # 调用问答链
                if self.enable_memory:
                    result = self.qa_chain({"question": question})
                    answer = result['answer']
                else:
                    result = self.qa_chain({"query": question})
                    answer = result['result']

                # 流式模式下，从 callback 获取答案
                if self.enable_streaming and self.streaming_handler:
                    answer = self.streaming_handler.answer
                    print()  # 流式输出结束后换行
                else:
                    # 非流式模式，一次性打印
                    print(f"\n💡 答案: {answer}")

                # 保存到历史记录
                self.chat_history.append({
                    "question": question,
                    "answer": answer
                })

                # 显示来源（包含相似度分数）
                if show_source and result.get('source_documents'):
                    # 使用 search_with_score 获取相似度分数
                    try:
                        docs_with_scores = self.vector_store_manager.search_with_score(
                            question,
                            k=len(result['source_documents'])
                        )

                        print("\n📚 参考来源（按相似度排序）:")
                        for i, (doc, score) in enumerate(docs_with_scores, 1):
                            source = doc.metadata.get('source', '未知')
                            page = doc.metadata.get('page', '?')

                            # 获取可信度等级
                            level, icon, similarity = get_confidence_level(score)

                            print(f"  {i}. {source} (第{page}页) {icon} {level}")
                            print(f"     相似度: {similarity:.1%} | 距离: {score:.3f}")
                            print(f"     {doc.page_content[:100]}...")

                    except Exception as e:
                        # 如果获取分数失败，回退到原来的显示方式
                        print("\n📚 参考来源:")
                        for i, doc in enumerate(result['source_documents'], 1):
                            source = doc.metadata.get('source', '未知')
                            page = doc.metadata.get('page', '?')
                            print(f"  {i}. {source} (第{page}页)")
                            print(f"     {doc.page_content[:100]}...")

                return result

            except Exception as e:
                error_msg = str(e)

                # 检测常见错误类型
                if "api key" in error_msg.lower() or "authentication" in error_msg.lower():
                    raise ValueError("OpenAI API Key 无效或已过期，请检查 .env 配置")
                elif "rate limit" in error_msg.lower():
                    if attempt < max_retries - 1:
                        wait_time = retry_delay * (attempt + 1)
                        print(f"⚠️  API 调用频率限制，{wait_time} 秒后重试...")
                        time.sleep(wait_time)
                        continue
                    else:
                        raise Exception("API 调用频率限制，请稍后再试或升级 API 套餐")
                elif "timeout" in error_msg.lower() or "connection" in error_msg.lower():
                    if attempt < max_retries - 1:
                        print(f"⚠️  网络超时，正在重试（{attempt + 1}/{max_retries}）...")
                        time.sleep(retry_delay)
                        continue
                    else:
                        raise Exception("网络连接失败，请检查网络连接")
                elif "insufficient_quota" in error_msg.lower():
                    raise Exception("OpenAI API 额度不足，请充值或检查账户状态")
                else:
                    raise Exception(f"问答失败: {error_msg}")

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

    def export_to_text(self, output_dir: str = "./exports") -> str:
        """
        导出对话记录为纯文本格式

        参数:
            output_dir: 导出目录（默认 ./exports）

        返回:
            导出文件路径
        """
        if not self.chat_history:
            raise ValueError("对话历史为空，无法导出")

        # 创建导出目录
        export_path = Path(output_dir)
        export_path.mkdir(parents=True, exist_ok=True)

        # 生成文件名（包含时间戳）
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"chat_history_{timestamp}.txt"
        filepath = export_path / filename

        # 写入文件
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write("=" * 70 + "\n")
            f.write("PDF 聊天机器人对话记录\n")
            f.write("=" * 70 + "\n")
            f.write(f"导出时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"对话轮数: {len(self.chat_history)}\n")
            f.write("=" * 70 + "\n\n")

            for i, item in enumerate(self.chat_history, 1):
                f.write(f"【第 {i} 轮对话】\n")
                f.write(f"{'─' * 70}\n")
                f.write(f"问题: {item['question']}\n\n")
                f.write(f"答案:\n{item['answer']}\n")
                f.write("\n" + "=" * 70 + "\n\n")

        return str(filepath)

    def export_to_json(self, output_dir: str = "./exports") -> str:
        """
        导出对话记录为 JSON 格式

        参数:
            output_dir: 导出目录（默认 ./exports）

        返回:
            导出文件路径
        """
        if not self.chat_history:
            raise ValueError("对话历史为空，无法导出")

        # 创建导出目录
        export_path = Path(output_dir)
        export_path.mkdir(parents=True, exist_ok=True)

        # 生成文件名
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"chat_history_{timestamp}.json"
        filepath = export_path / filename

        # 构建 JSON 数据
        data = {
            "export_time": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            "total_conversations": len(self.chat_history),
            "conversations": [
                {
                    "round": i,
                    "question": item['question'],
                    "answer": item['answer']
                }
                for i, item in enumerate(self.chat_history, 1)
            ]
        }

        # 写入文件（美化输出）
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

        return str(filepath)

    def export_to_markdown(self, output_dir: str = "./exports") -> str:
        """
        导出对话记录为 Markdown 格式

        参数:
            output_dir: 导出目录（默认 ./exports）

        返回:
            导出文件路径
        """
        if not self.chat_history:
            raise ValueError("对话历史为空，无法导出")

        # 创建导出目录
        export_path = Path(output_dir)
        export_path.mkdir(parents=True, exist_ok=True)

        # 生成文件名
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"chat_history_{timestamp}.md"
        filepath = export_path / filename

        # 写入 Markdown 文件
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write("# PDF 聊天机器人对话记录\n\n")
            f.write(f"**导出时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
            f.write(f"**对话轮数**: {len(self.chat_history)}\n\n")
            f.write("---\n\n")

            for i, item in enumerate(self.chat_history, 1):
                f.write(f"## 第 {i} 轮对话\n\n")
                f.write(f"### ❓ 问题\n\n")
                f.write(f"{item['question']}\n\n")
                f.write(f"### 💡 答案\n\n")
                f.write(f"{item['answer']}\n\n")
                f.write("---\n\n")

        return str(filepath)

    def export_history(self, format_type: str = "text", output_dir: str = "./exports") -> str:
        """
        导出对话历史（统一接口）

        参数:
            format_type: 导出格式 ('text', 'json', 'markdown')
            output_dir: 导出目录

        返回:
            导出文件路径

        异常:
            ValueError: 格式不支持或对话历史为空
        """
        format_type = format_type.lower()

        if format_type == "text" or format_type == "txt":
            return self.export_to_text(output_dir)
        elif format_type == "json":
            return self.export_to_json(output_dir)
        elif format_type == "markdown" or format_type == "md":
            return self.export_to_markdown(output_dir)
        else:
            raise ValueError(f"不支持的导出格式: {format_type}，支持的格式: text, json, markdown")
