"""使用示例"""
from pdf_chatbot import DocumentProcessor, VectorStoreManager, QASystem


def main():
    """简单的使用示例"""

    # 1. 处理 PDF 文档
    print("1. 加载并处理 PDF...")
    processor = DocumentProcessor()
    chunks = processor.process_pdf("your_document.pdf")  # 替换成你的 PDF 路径

    # 2. 创建向量数据库
    print("\n2. 创建向量数据库...")
    vector_manager = VectorStoreManager()
    vector_manager.create_vectorstore(chunks)

    # 3. 初始化问答系统
    print("\n3. 初始化问答系统...")
    qa_system = QASystem(vector_manager)
    qa_system.initialize()

    # 4. 提问
    print("\n4. 开始提问...")
    questions = [
        "这份文档的主要内容是什么？",
        "有哪些关键数据？",
    ]

    for question in questions:
        qa_system.ask(question)
        print("\n" + "=" * 60 + "\n")


if __name__ == "__main__":
    main()
