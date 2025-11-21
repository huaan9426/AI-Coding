"""命令行入口"""
import os
import sys

from pdf_chatbot import DocumentProcessor, VectorStoreManager, QASystem
from pdf_chatbot.config import Config


def main():
    """主函数"""
    print("=" * 60)
    print("📚 PDF 聊天机器人 - 基于 RAG 的文档问答系统")
    print("=" * 60)

    # 检查是否存在向量数据库
    chroma_exists = os.path.exists("./chroma_db")

    if not chroma_exists:
        print("\n🆕 首次运行，需要先加载 PDF 文档")
        pdf_path = input("📄 请输入 PDF 文件路径: ").strip()

        if not pdf_path or not os.path.exists(pdf_path):
            print("❌ 文件不存在！")
            return

        # 1. 处理文档
        print("\n" + "=" * 60)
        print("步骤 1/3: 处理文档")
        print("=" * 60)
        processor = DocumentProcessor()
        chunks = processor.process_pdf(pdf_path)

        # 2. 创建向量数据库
        print("\n" + "=" * 60)
        print("步骤 2/3: 创建向量数据库")
        print("=" * 60)
        vector_manager = VectorStoreManager()
        vector_manager.create_vectorstore(chunks)

    else:
        print("\n📂 检测到已存在的向量数据库，直接加载...")
        vector_manager = VectorStoreManager()
        vector_manager.load_vectorstore()

    # 3. 初始化问答系统
    print("\n" + "=" * 60)
    print("步骤 3/3: 初始化问答系统")
    print("=" * 60)
    qa_system = QASystem(vector_manager, enable_memory=Config.ENABLE_MEMORY)
    qa_system.initialize()

    # 4. 进入问答循环
    print("\n" + "=" * 60)
    print("🎉 系统准备就绪！开始提问吧")
    print("=" * 60)
    print("💡 提示:")
    print("  - 输入 'quit' 或 'exit' 退出")
    if Config.ENABLE_MEMORY:
        print("  - 输入 'history' 查看对话历史")
        print("  - 输入 'clear' 清空对话历史")
    print()

    while True:
        try:
            question = input("\n❓ 你的问题: ").strip()

            if not question:
                continue

            if question.lower() in ['quit', 'exit', 'q']:
                print("👋 再见！")
                break

            # 特殊命令处理（仅在启用记忆时可用）
            if Config.ENABLE_MEMORY:
                if question.lower() == 'history':
                    qa_system.show_history()
                    continue
                if question.lower() == 'clear':
                    qa_system.clear_history()
                    continue

            # 回答问题
            qa_system.ask(question)

        except KeyboardInterrupt:
            print("\n\n👋 再见！")
            break
        except Exception as e:
            print(f"❌ 错误: {e}")


if __name__ == "__main__":
    main()
