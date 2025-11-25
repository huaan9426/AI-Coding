"""文档加载模块"""
import os
from typing import List
from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_core.documents import Document

from .config import Config


class DocumentProcessor:
    """文档处理类"""

    def __init__(self):
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=Config.CHUNK_SIZE,
            chunk_overlap=Config.CHUNK_OVERLAP,
            separators=["\n\n", "\n", "。", "！", "？", " ", ""]
        )

    def load_pdf(self, file_path: str) -> List[Document]:
        """
        加载 PDF 文件

        参数:
            file_path: PDF 文件路径

        返回:
            文档列表

        异常:
            FileNotFoundError: 文件不存在
            ValueError: 文件格式错误
            Exception: 其他加载错误
        """
        # 验证文件路径
        if not file_path:
            raise ValueError("文件路径不能为空")

        if not os.path.exists(file_path):
            raise FileNotFoundError(f"文件不存在: {file_path}")

        if not file_path.lower().endswith('.pdf'):
            raise ValueError(f"文件格式错误，仅支持 PDF 文件: {file_path}")

        # 验证文件大小（限制 100MB）
        file_size = os.path.getsize(file_path)
        max_size = 100 * 1024 * 1024  # 100MB
        if file_size > max_size:
            raise ValueError(f"文件过大（{file_size / 1024 / 1024:.1f}MB），最大支持 100MB")

        if file_size == 0:
            raise ValueError(f"文件为空: {file_path}")

        print(f"📄 正在加载 PDF: {file_path} ({file_size / 1024:.1f}KB)")

        try:
            loader = PyPDFLoader(file_path)
            documents = loader.load()

            if not documents:
                raise ValueError("PDF 文件无法解析或内容为空")

            print(f"✅ 成功加载 {len(documents)} 页")
            return documents

        except Exception as e:
            # 捕获 PyPDFLoader 的异常并转换为友好提示
            if "encrypted" in str(e).lower():
                raise ValueError(f"PDF 文件已加密，无法读取: {file_path}")
            elif "damaged" in str(e).lower() or "invalid" in str(e).lower():
                raise ValueError(f"PDF 文件已损坏或格式无效: {file_path}")
            else:
                raise Exception(f"加载 PDF 失败: {str(e)}")

    def split_documents(self, documents: List[Document]) -> List[Document]:
        """
        切分文档

        参数:
            documents: 文档列表

        返回:
            切分后的文档块列表

        异常:
            ValueError: 文档列表为空
        """
        if not documents:
            raise ValueError("文档列表为空，无法切分")

        print(f"✂️  正在切分文档...")

        try:
            chunks = self.text_splitter.split_documents(documents)

            if not chunks:
                raise ValueError("文档切分失败，未生成任何文档块")

            print(f"✅ 切分为 {len(chunks)} 个文档块")
            return chunks

        except Exception as e:
            raise Exception(f"文档切分失败: {str(e)}")

    def process_pdf(self, file_path: str) -> List[Document]:
        """
        处理 PDF 文件（加载 + 切分）

        参数:
            file_path: PDF 文件路径

        返回:
            切分后的文档块列表
        """
        documents = self.load_pdf(file_path)
        chunks = self.split_documents(documents)
        return chunks
