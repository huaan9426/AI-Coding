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

        # 验证文件路径
        if not pdf_path:
            print("❌ 文件路径不能为空！")
            return

        # 去除可能的引号
        pdf_path = pdf_path.strip('"').strip("'")

        if not os.path.exists(pdf_path):
            print(f"❌ 文件不存在: {pdf_path}")
            print("💡 提示: 请输入完整的文件路径，例如: /Users/xxx/document.pdf")
            return

        if not pdf_path.lower().endswith('.pdf'):
            print(f"❌ 文件格式错误，仅支持 PDF 文件: {pdf_path}")
            return

        # 1. 处理文档
        print("\n" + "=" * 60)
        print("步骤 1/3: 处理文档")
        print("=" * 60)
        try:
            processor = DocumentProcessor()
            chunks = processor.process_pdf(pdf_path)
        except Exception as e:
            print(f"❌ {str(e)}")
            return

        # 2. 创建向量数据库
        print("\n" + "=" * 60)
        print("步骤 2/3: 创建向量数据库")
        print("=" * 60)
        try:
            vector_manager = VectorStoreManager()
            vector_manager.create_vectorstore(chunks)
        except Exception as e:
            print(f"❌ {str(e)}")
            return

    else:
        print("\n📂 检测到已存在的向量数据库，直接加载...")
        try:
            vector_manager = VectorStoreManager()
            vector_manager.load_vectorstore()
        except Exception as e:
            print(f"❌ {str(e)}")
            print("💡 提示: 如需重新创建数据库，请删除 chroma_db 文件夹")
            return

    # 3. 初始化问答系统
    print("\n" + "=" * 60)
    print("步骤 3/3: 初始化问答系统")
    print("=" * 60)
    try:
        qa_system = QASystem(vector_manager, enable_memory=Config.ENABLE_MEMORY)
        qa_system.initialize()
    except Exception as e:
        print(f"❌ {str(e)}")
        return

    # 4. 进入问答循环
    print("\n" + "=" * 60)
    print("🎉 系统准备就绪！开始提问吧")
    print("=" * 60)
    print("💡 提示:")
    print("  - 输入 'quit' 或 'exit' 退出")
    if Config.ENABLE_MEMORY:
        print("  - 输入 'history' 查看对话历史")
        print("  - 输入 'clear' 清空对话历史")
        print("  - 输入 'export' 导出对话记录")
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
                if question.lower() == 'export':
                    try:
                        # 提示用户选择导出格式
                        print("\n📤 选择导出格式:")
                        print("  1. 纯文本 (txt)")
                        print("  2. JSON")
                        print("  3. Markdown (md)")
                        format_choice = input("请输入选项 (1/2/3, 默认为 1): ").strip() or "1"

                        format_map = {
                            "1": "text",
                            "2": "json",
                            "3": "markdown"
                        }

                        format_type = format_map.get(format_choice, "text")

                        # 导出
                        filepath = qa_system.export_history(format_type)
                        print(f"✅ 对话记录已导出到: {filepath}")
                    except ValueError as e:
                        print(f"❌ {str(e)}")
                    except Exception as e:
                        print(f"❌ 导出失败: {str(e)}")
                    continue

            # 回答问题
            try:
                qa_system.ask(question)
            except Exception as e:
                print(f"❌ {str(e)}")
                # 继续循环，不退出程序

        except KeyboardInterrupt:
            print("\n\n👋 再见！")
            break
        except Exception as e:
            print(f"❌ 未知错误: {e}")
            print("💡 提示: 如果问题持续，请检查网络连接和 API 配置")


if __name__ == "__main__":
    main()
